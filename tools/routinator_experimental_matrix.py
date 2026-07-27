#!/usr/bin/env python3
"""Run the experimental Routinator against isolated local rsync fixtures."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import time
from pathlib import Path

from pqc_rpki_lab.workspace import reset_generated_directory

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORK = ROOT / "local" / "routinator-experimental"
DEFAULT_RESULT = (
    ROOT / "results" / "composite-e2e" / "routinator-matrix.json"
)

EXPECTED_VRPS = [
    {"asn": "AS64496", "prefix": "192.0.2.0/24", "max_length": 24},
    {"asn": "AS64496", "prefix": "2001:db8::/32", "max_length": 48},
]


def wait_for_port(process: subprocess.Popen[str], port: int) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("local rsync daemon exited before validation")
        with socket.socket() as sock:
            sock.settimeout(0.1)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.05)
    raise RuntimeError("local rsync daemon did not become ready")


def extract_vrps(value: object) -> list[dict[str, object]]:
    text = json.dumps(value, sort_keys=True)
    prefixes = re.findall(r'"prefix"\s*:\s*"([^"]+)"', text)
    asns = re.findall(r'"asn"\s*:\s*(?:"AS)?(\d+)"?', text)
    max_lengths = re.findall(
        r'"maxLength"\s*:\s*(\d+)|"max_length"\s*:\s*(\d+)', text
    )
    lengths = [int(left or right) for left, right in max_lengths]
    if len(prefixes) == len(asns) == len(lengths):
        return sorted(
            [
                {
                    "asn": f"AS{asn}",
                    "prefix": prefix,
                    "max_length": length,
                }
                for prefix, asn, length in zip(prefixes, asns, lengths)
            ],
            key=lambda item: (str(item["prefix"]), str(item["asn"])),
        )
    return []


def reason_from(text: str) -> str:
    for line in text.splitlines():
        lower = line.lower().replace("example.invalid", "")
        if any(
            ignored in lower
            for ignored in (
                "using config file",
                "running command",
                "found valid trust anchor",
            )
        ):
            continue
        if any(
            word in lower
            for word in (
                "error",
                "failed",
                "invalid",
                "unsupported",
                "algorithm",
                "signature",
                "digest",
                "wrong",
            )
        ):
            return line.strip().replace(str(ROOT), "$REPO")[:500]
    return ""


def run_case(
    binary: Path,
    fixture: Path,
    name: str,
    experimental: bool,
    work: Path,
    port: int,
) -> dict[str, object]:
    case = work / f"{name}-{'experimental' if experimental else 'default'}"
    case.mkdir(parents=True)
    tal_dir = case / "tals"
    cache = case / "cache"
    tal_dir.mkdir()
    cache.mkdir()
    shutil.copyfile(fixture / "test.tal", tal_dir / "test.tal")
    routinator_config = case / "routinator.conf"
    routinator_config.write_text(
        f'repository-dir = "{cache}"\n'
        "no-rir-tals = true\n"
    )

    config = case / "rsyncd.conf"
    config.write_text(
        "use chroot = false\n"
        "read only = true\n"
        "[repository]\n"
        f"path = {fixture / 'repository'}\n"
    )
    wrapper = case / "rsync-wrapper.py"
    wrapper.write_text(
        "#!/usr/bin/env python3\n"
        "import os\n"
        "import sys\n"
        f"port = {port}\n"
        "args = []\n"
        "for arg in sys.argv[1:]:\n"
        "    arg = arg.replace('rsync://example.invalid:8873/', "
        "f'rsync://127.0.0.1:{port}/')\n"
        "    arg = arg.replace('rsync://example.invalid/', "
        "f'rsync://127.0.0.1:{port}/')\n"
        "    args.append(arg)\n"
        "os.execv('/usr/bin/rsync', ['rsync', *args])\n"
    )
    wrapper.chmod(0o700)
    output = case / "vrps.json"
    log = case / "routinator.log"
    daemon_log = case / "rsyncd.log"

    with daemon_log.open("w") as daemon_output:
        daemon = subprocess.Popen(
            [
                "/usr/bin/rsync",
                "--daemon",
                "--no-detach",
                f"--port={port}",
                f"--config={config}",
            ],
            stdout=daemon_output,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            wait_for_port(daemon, port)
            env = os.environ.copy()
            if experimental:
                env["PQC_RPKI_EXPERIMENTAL"] = "1"
            else:
                env.pop("PQC_RPKI_EXPERIMENTAL", None)
            process = subprocess.run(
                [
                    str(binary),
                    "--config",
                    str(routinator_config),
                    "-vv",
                    "--repository-dir",
                    str(cache),
                    "--no-rir-tals",
                    "--extra-tals-dir",
                    str(tal_dir),
                    "--disable-rrdp",
                    "--allow-dubious-hosts",
                    "--log-repository-issues",
                    "--rsync-command",
                    str(wrapper),
                    "vrps",
                    "--complete",
                    "--format",
                    "json",
                    "--output",
                    str(output),
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
        finally:
            daemon.terminate()
            try:
                daemon.wait(timeout=5)
            except subprocess.TimeoutExpired:
                daemon.kill()
                daemon.wait()

    combined = process.stdout + process.stderr
    log.write_text(combined)
    parsed = json.loads(output.read_text()) if output.exists() else {}
    vrps = extract_vrps(parsed)
    return {
        "returncode": process.returncode,
        "status": "accepted" if vrps == EXPECTED_VRPS else "rejected",
        "vrp_count": len(vrps),
        "vrps": vrps,
        "reason": "" if vrps else reason_from(combined),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--rsa-fixture", type=Path, required=True)
    parser.add_argument("--pure-fixture", type=Path, required=True)
    parser.add_argument("--composite-fixture", type=Path, required=True)
    parser.add_argument("--mixed-fixture", type=Path, required=True)
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--port", type=int, default=18873)
    args = parser.parse_args()

    work = args.work.resolve()
    reset_generated_directory(work, allowed_root=ROOT / "local")
    fixtures = {
        "rsa_baseline": args.rsa_fixture.resolve(),
        "pure_mldsa65": args.pure_fixture.resolve(),
        "composite_standalone": args.composite_fixture.resolve(),
        "mixed_tree": args.mixed_fixture.resolve(),
    }
    cases: dict[str, object] = {}
    for name, fixture in fixtures.items():
        cases[name] = {
            "default": run_case(
                args.binary.resolve(), fixture, name, False, work, args.port
            ),
            "experimental": run_case(
                args.binary.resolve(), fixture, name, True, work, args.port
            ),
        }

    success = all(
        (
            case["default"]["status"] == "accepted"
            if name == "rsa_baseline"
            else case["default"]["status"] == "rejected"
        )
        and case["experimental"]["status"] == "accepted"
        for name, case in cases.items()
    )
    result = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "classification": (
            "isolated local-rsync second-RP experiment; OpenSSL provider "
            "cryptography is shared with the generator"
        ),
        "implementation": "Routinator 0.15.2 with experimental rpki-rs backend",
        "policy": {
            "default": "Current Suite only",
            "experimental": (
                "Current Suite plus pure ML-DSA-65 and "
                "id-MLDSA65-ECDSA-P256-SHA512"
            ),
        },
        "cases": cases,
        "success": success,
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
