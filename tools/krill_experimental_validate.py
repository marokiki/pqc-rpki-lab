#!/usr/bin/env python3
"""Validate Krill's experimental issuance output with both lab RPs."""

from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import shutil
import socket
import subprocess
import time
import ipaddress
from pathlib import Path

from pqc_rpki_lab.workspace import reset_generated_directory

ROOT = Path(__file__).resolve().parents[1]


def expected_vrps(
    count: int, *, first_prefix: str = "192.0.2.0/24"
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = [
        {
            "asn": "AS64496",
            "prefix": first_prefix,
            "max_length": int(first_prefix.rsplit("/", 1)[1]),
        }
    ]
    for offset in range(1, count):
        address = ipaddress.IPv6Address((0x20010DB8 << 96) | (offset << 64))
        result.append(
            {
                "asn": f"AS{64496 + offset}",
                "prefix": f"{address.compressed}/64",
                "max_length": 64,
            }
        )
    return sorted(result, key=lambda item: (str(item["prefix"]), str(item["asn"])))


def walk(value: object):
    yield value
    if isinstance(value, dict):
        for item in value.values():
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)


def find_ta_certificate(state: Path) -> bytes:
    for path in sorted((state / "data" / "ta_proxy").rglob("*.json"), reverse=True):
        value = json.loads(path.read_text())
        for item in walk(value):
            if (
                isinstance(item, dict)
                and item.get("url") == "rsync://localhost/ta/ta.cer"
                and isinstance(item.get("cert"), str)
            ):
                return base64.b64decode(item["cert"], validate=True)
    raise RuntimeError("could not locate the Krill testbed TA certificate")


def prepare_fixture(phase: Path, fixture: Path) -> None:
    state = phase / "state"
    source = state / "repo" / "rsync" / "current"
    if not source.is_dir() or not (phase / "testbed.tal").is_file():
        raise RuntimeError(f"incomplete Krill phase output: {phase}")
    (fixture / "ta").mkdir(parents=True)
    shutil.copytree(source, fixture / "repo")
    shutil.copyfile(phase / "testbed.tal", fixture / "testbed.tal")
    (fixture / "ta" / "ta.cer").write_bytes(find_ta_certificate(state))


def extract_rpki_client_vrps(output: Path) -> tuple[list[dict[str, object]], dict]:
    metadata = json.loads((output / "json").read_text())["metadata"]
    with (output / "csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    vrps = sorted(
        [
            {
                "asn": row["ASN"],
                "prefix": row["IP Prefix"],
                "max_length": int(row["Max Length"]),
            }
            for row in rows
        ],
        key=lambda item: (str(item["prefix"]), str(item["asn"])),
    )
    return vrps, metadata


def run_rpki_client(
    binary: Path,
    fixture: Path,
    work: Path,
    experimental: bool,
    expected: list[dict[str, object]],
) -> dict[str, object]:
    cache = work / "cache"
    output = work / "output"
    (cache / "localhost").mkdir(parents=True)
    (cache / "ta" / "testbed").mkdir(parents=True)
    shutil.copytree(fixture / "ta", cache / "localhost" / "ta")
    shutil.copytree(fixture / "repo", cache / "localhost" / "repo")
    shutil.copyfile(
        fixture / "ta" / "ta.cer",
        cache / "ta" / "testbed" / "ta.cer",
    )
    output.mkdir(parents=True)
    flags = ["-x"] if experimental else []
    process = subprocess.run(
        [
            str(binary),
            *flags,
            "-n",
            "-d",
            str(cache),
            "-t",
            str(fixture / "testbed.tal"),
            "-j",
            "-c",
            "-vv",
            str(output),
        ],
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        timeout=60,
    )
    (work / "rpki-client.log").write_text(process.stdout + process.stderr)
    vrps, metadata = extract_rpki_client_vrps(output)
    return {
        "returncode": process.returncode,
        "status": "accepted" if vrps == expected else "rejected",
        "vrp_count": len(vrps),
        "vrps": vrps,
        "invalid_certificates": metadata["invalidcertificates"],
    }


def wait_for_port(process: subprocess.Popen[str], port: int) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("local rsync daemon exited")
        with socket.socket() as sock:
            sock.settimeout(0.1)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.05)
    raise RuntimeError("local rsync daemon did not become ready")


def extract_routinator_vrps(value: object) -> list[dict[str, object]]:
    rows = value.get("roas", []) if isinstance(value, dict) else []
    result = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        result.append(
            {
                "asn": f"AS{str(row['asn']).removeprefix('AS')}",
                "prefix": row["prefix"],
                "max_length": int(row.get("maxLength", row.get("max_length"))),
            }
        )
    return sorted(result, key=lambda item: (str(item["prefix"]), str(item["asn"])))


def run_routinator(
    binary: Path,
    fixture: Path,
    work: Path,
    experimental: bool,
    port: int,
    expected: list[dict[str, object]],
) -> dict[str, object]:
    tal_dir = work / "tals"
    cache = work / "cache"
    tal_dir.mkdir(parents=True)
    cache.mkdir()
    shutil.copyfile(fixture / "testbed.tal", tal_dir / "testbed.tal")
    config = work / "rsyncd.conf"
    config.write_text(
        "use chroot = false\nread only = true\n"
        f"[ta]\npath = {fixture / 'ta'}\n"
        f"[repo]\npath = {fixture / 'repo'}\n"
    )
    wrapper = work / "rsync-wrapper.py"
    wrapper.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        f"port = {port}\n"
        "args = [arg.replace('rsync://localhost/', "
        "f'rsync://127.0.0.1:{port}/') for arg in sys.argv[1:]]\n"
        "os.execv('/usr/bin/rsync', ['rsync', *args])\n"
    )
    wrapper.chmod(0o700)
    routinator_config = work / "routinator.conf"
    routinator_config.write_text(
        f'repository-dir = "{cache}"\nno-rir-tals = true\n'
    )
    output = work / "vrps.json"
    daemon = subprocess.Popen(
        [
            "/usr/bin/rsync",
            "--daemon",
            "--no-detach",
            f"--port={port}",
            f"--config={config}",
        ],
        stdout=subprocess.DEVNULL,
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
        daemon.wait(timeout=5)
    (work / "routinator.log").write_text(process.stdout + process.stderr)
    parsed = json.loads(output.read_text()) if output.exists() else {}
    vrps = extract_routinator_vrps(parsed)
    return {
        "returncode": process.returncode,
        "status": "accepted" if vrps == expected else "rejected",
        "vrp_count": len(vrps),
        "vrps": vrps,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--krill-output", type=Path, required=True)
    parser.add_argument("--rpki-client", type=Path, required=True)
    parser.add_argument("--routinator", type=Path, required=True)
    parser.add_argument(
        "--work", type=Path, default=ROOT / "local" / "krill-rp-validation"
    )
    parser.add_argument(
        "--result",
        type=Path,
        default=ROOT / "results/composite-e2e/krill-rollover.json",
    )
    parser.add_argument("--port", type=int, default=19873)
    parser.add_argument("--expected-vrp-count", type=int, default=1)
    args = parser.parse_args()
    if args.expected_vrp_count < 1:
        raise SystemExit("--expected-vrp-count must be positive")
    expected = expected_vrps(args.expected_vrp_count)
    updated_expected = expected_vrps(
        args.expected_vrp_count, first_prefix="192.0.2.0/25"
    )
    work = args.work.resolve()
    reset_generated_directory(work, allowed_root=ROOT / "local")
    phases: dict[str, object] = {}
    phase_names = ["composite"]
    if (args.krill_output.resolve() / "composite-updated").is_dir():
        phase_names.append("composite-updated")
    phase_names.append("rollback")
    for offset, name in enumerate(phase_names):
        phase_expected = (
            updated_expected if name == "composite-updated" else expected
        )
        fixture = work / name / "fixture"
        prepare_fixture(args.krill_output.resolve() / name, fixture)
        phases[name] = {
            "rpki_client_default": run_rpki_client(
                args.rpki_client.resolve(),
                fixture,
                work / name / "rpki-client-default",
                False,
                phase_expected,
            ),
            "rpki_client_experimental": run_rpki_client(
                args.rpki_client.resolve(),
                fixture,
                work / name / "rpki-client-experimental",
                True,
                phase_expected,
            ),
            "routinator_default": run_routinator(
                args.routinator.resolve(),
                fixture,
                work / name / "routinator-default",
                False,
                args.port + offset,
                phase_expected,
            ),
            "routinator_experimental": run_routinator(
                args.routinator.resolve(),
                fixture,
                work / name / "routinator-experimental",
                True,
                args.port + offset,
                phase_expected,
            ),
        }
    success = all(
        result["status"]
        == (
            "rejected"
            if name.startswith("composite") and mode.endswith("default")
            else "accepted"
        )
        for name, phase in phases.items()
        for mode, result in phase.items()
    )
    result = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "classification": (
            "Krill CA issuance, publication, and rollback validated through "
            "isolated local rsync; not a production deployment"
        ),
        "expected_vrps": expected,
        "updated_expected_vrps": updated_expected,
        "phases": phases,
        "success": success,
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
