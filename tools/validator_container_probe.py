#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from pqc_rpki_lab.result_io import markdown_table, write_json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "validator-probe"

IMAGES = {
    "Routinator": "nlnetlabs/routinator@sha256:bc57d6e973c3f34fec03ef6fec09e17e405f56f084bf2252a8d54bd2ff3ca597",
    "rpki-client": "rpki/rpki-client@sha256:27f2eb021ba3bc3c35400ba9177351647187b6f20abdec848fd8c7cf68cc8ce9",
    "FORT": "nicmx/fort-validator@sha256:26766f35d0b90d61e4fb4825e10a03d66c5a249e0d9e685b1ede4a3dad23e1cd",
}


def classify(name: str, kind: str, process: subprocess.CompletedProcess[str], vrp_file: Path | None) -> dict[str, object]:
    text = process.stdout + process.stderr
    lower = text.lower()
    reported_vrps = any(int(value) > 0 for value in re.findall(r"(?:VRP Entries|Route Origin Authorizations):\s*(\d+)", text))
    file_vrps = vrp_file is not None and vrp_file.exists() and "64496" in vrp_file.read_text(errors="replace")
    accepted = process.returncode == 0 and (reported_vrps or file_vrps)
    parser = "accepted" if accepted else ("rejected" if any(word in lower for word in ("parse", "asn1", "digest", "algorithm", "invalid public key")) else "unknown")
    error_lines = [line.strip() for line in text.splitlines()
                   if any(word in line.lower() for word in ("error", "invalid", "failed", "unsupported", "unknown"))
                   and not re.search(r"\b0 (?:failed|invalid)\b", line)]
    if not accepted and error_lines and parser == "unknown":
        parser = "rejected"
    return {
        "validator": name,
        "repository_kind": kind,
        "status": "accepted" if accepted else "rejected",
        "returncode": process.returncode,
        "parser": parser,
        "signature": "accepted" if accepted else "rejected-or-not-reached",
        "certificate_path": "accepted" if accepted else "rejected-or-not-reached",
        "crl": "accepted" if accepted else "rejected-or-not-reached",
        "manifest": "accepted" if accepted else "rejected-or-not-reached",
        "roa": "accepted" if accepted else "rejected-or-not-reached",
        "vrp_output": "present" if accepted else "absent",
        "hard_error": "" if accepted else (error_lines[0] if error_lines else ""),
    }


def command_for(name: str, tal_dir: Path, cache: Path, output: Path, network: str) -> list[str]:
    common = ["docker", "run", "--rm", "--network", network]
    if name == "Routinator":
        return common + [
            "-v", f"{tal_dir}:/tals:ro", "-v", f"{cache}:/cache", IMAGES[name],
            "--repository-dir", "/cache", "--no-rir-tals", "--extra-tals-dir", "/tals",
            "--disable-rrdp", "--allow-dubious-hosts", "vrps", "--complete",
            "--format", "json", "--output", "/cache/vrps.json",
        ]
    if name == "rpki-client":
        return common + [
            "-e", "ONESHOT=true", "-v", f"{tal_dir}:/etc/tals:ro",
            "-v", f"{cache}:/var/cache/rpki-client", "-v", f"{output.parent}:/var/lib/rpki-client",
            IMAGES[name],
        ]
    return common + [
        "--platform", "linux/amd64", "-v", f"{tal_dir}:/tals:ro", "-v", f"{cache}:/cache",
        IMAGES[name], "--tal", "/tals", "--local-repository", "/cache",
        "--mode=standalone", "--http.enabled=false", "--output.roa=/cache/vrps.csv",
        "--rsync.retry.count=0", "--rsync.transfer-timeout=10",
        "--log.output=console", "--validation-log.output=console",
    ]


def run_one(name: str, kind: str, fixture: Path, work: Path, network: str) -> dict[str, object]:
    tal_dir = work / f"{name}-{kind}-tals"
    cache = work / f"{name}-{kind}-cache"
    output_dir = work / f"{name}-{kind}-output"
    tal_dir.mkdir(); cache.mkdir(); output_dir.mkdir()
    os.chmod(cache, 0o777); os.chmod(output_dir, 0o777)
    shutil.copyfile(fixture / "test.tal", tal_dir / "test.tal")
    output = output_dir / "vrps.json"
    command = command_for(name, tal_dir, cache, output, network)
    try:
        process = subprocess.run(command, capture_output=True, text=True, timeout=45)
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode(errors="replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode(errors="replace") if isinstance(error.stderr, bytes) else (error.stderr or "")
        process = subprocess.CompletedProcess(command, 124, stdout, stderr + "\nvalidator probe timed out after 45 seconds\n")
    if name == "Routinator":
        candidate = cache / "vrps.json"
    elif name == "rpki-client":
        candidate = next(output_dir.glob("*.json"), None)
    else:
        candidate = cache / "vrps.csv"
    log_path = RESULTS / f"{name.lower().replace('-', '_')}-{kind}.log"
    log_path.write_text(process.stdout + process.stderr)
    row = classify(name, kind, process, candidate)
    row["image"] = IMAGES[name]
    row["log"] = str(log_path.relative_to(ROOT))
    row["command"] = [part.replace(str(tal_dir), "$TALS").replace(str(cache), "$CACHE").replace(str(output_dir), "$OUTPUT").replace(network, "$NETWORK") for part in command]
    return row


def main() -> int:
    if not shutil.which("docker"):
        raise SystemExit("docker is required")
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = []
    with tempfile.TemporaryDirectory(prefix="pqc-rpki-validator-probe-") as name:
        work = Path(name)
        suffix = uuid.uuid4().hex[:10]
        network = f"pqc-rpki-{suffix}"
        subprocess.run(["docker", "network", "create", network], check=True, capture_output=True)
        try:
            for kind in ("rsa", "ml-dsa-65"):
                fixture = ROOT / "testdata" / "validator" / kind
                config = work / "rsyncd.conf"
                config.write_text("use chroot = false\nread only = true\n[repository]\npath = /repo\n")
                server = f"pqc-rpki-rsync-{suffix}"
                subprocess.run([
                    "docker", "run", "-d", "--name", server, "--network", network,
                    "--network-alias", "example.invalid", "-v", f"{fixture / 'repository'}:/repo:ro",
                    "-v", f"{config}:/etc/rsyncd.conf:ro", "--entrypoint", "rsync",
                    IMAGES["Routinator"], "--daemon", "--no-detach", "--port=8873",
                    "--config=/etc/rsyncd.conf",
                ], check=True, capture_output=True)
                for validator in IMAGES:
                    rows.append(run_one(validator, kind, fixture, work, network))
                subprocess.run(["docker", "rm", "-f", server], check=True, capture_output=True)
        finally:
            subprocess.run(["docker", "network", "rm", network], capture_output=True)
    document = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "network_scope": "isolated local rsync daemon at example.invalid:8873; no production TALs",
        "results": rows,
    }
    write_json(RESULTS / "container-matrix.json", document)
    (RESULTS / "container-matrix.md").write_text(
        "# Unmodified Validator Container Probe\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        + markdown_table(rows, [
            ("validator", "Validator"), ("repository_kind", "Repository"),
            ("status", "Status"), ("parser", "Parser"),
            ("certificate_path", "Certificate path"), ("manifest", "Manifest"),
            ("roa", "ROA"), ("vrp_output", "VRP output"), ("hard_error", "Hard error"),
        ]) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
