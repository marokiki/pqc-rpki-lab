#!/usr/bin/env python3
from __future__ import annotations

import os
import json
import shlex
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from pqc_rpki_lab.result_io import markdown_table, write_csv, write_json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
PROBE_RESULTS = RESULTS / "validator-probe"
TOOLS = {
    "Routinator": ("routinator", ["--version"], "PQC_RPKI_ROUTINATOR_BIN", "PQC_RPKI_ROUTINATOR_COMMAND"),
    "rpki-client": ("rpki-client", ["-V"], "PQC_RPKI_RPKI_CLIENT_BIN", "PQC_RPKI_RPKI_CLIENT_COMMAND"),
    "FORT": ("fort", ["--version"], "PQC_RPKI_FORT_BIN", "PQC_RPKI_FORT_COMMAND"),
}


def version(path: str, arguments: list[str]) -> tuple[str, str]:
    try:
        process = subprocess.run([path, *arguments], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as error:
        return "", str(error)
    text = (process.stdout or process.stderr).strip()
    return (text.splitlines()[0] if text else "", "" if process.returncode == 0 else text)


def public_path(value: str) -> str:
    try:
        return str(Path(value).resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return "$EXTERNAL_REPOSITORY"


def main() -> None:
    PROBE_RESULTS.mkdir(parents=True, exist_ok=True)
    rsa_repository = os.environ.get("PQC_RPKI_RSA_REPOSITORY", str(ROOT / "testdata" / "validator" / "rsa"))
    pqc_repository = os.environ.get("PQC_RPKI_PQC_REPOSITORY", str(ROOT / "testdata" / "validator" / "ml-dsa-65"))
    rows: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    for name, (executable, arguments, binary_env, command_env) in TOOLS.items():
        configured = os.environ.get(binary_env, "")
        path = configured or shutil.which(executable)
        if not path:
            row = {
                "validator": name, "installed": False, "version": "",
                "existence_status": "unsupported", "version_status": "unsupported",
                "rsa_baseline_status": "unsupported", "pqc_object_status": "unsupported",
                "vrp_output_status": "unsupported", "network_used": False,
                "reason": f"executable not found; set {binary_env} or {command_env}",
            }
            rows.append(row)
            errors.append({"validator": name, "stage": "existence", "status": "unsupported", "error": "executable not found"})
            write_json(PROBE_RESULTS / f"{name.lower().replace('-', '_')}.json", row)
            continue
        version_text, version_error = version(path, arguments)
        row = {
            "validator": name, "installed": True, "version": version_text,
            "existence_status": "confirmed",
            "version_status": "confirmed" if not version_error else "blocked",
            "rsa_baseline_status": "skipped",
            "pqc_object_status": "skipped",
            "vrp_output_status": "skipped",
            "network_used": False,
            "reason": (
                f"Set {command_env} to an argv template using {{repository}}, {{tal}}, and {{output}}."
            ),
        }
        command_template = os.environ.get(command_env, "")
        executions = []
        if command_template:
            for kind, repository in (("rsa", rsa_repository), ("pqc", pqc_repository)):
                output = PROBE_RESULTS / f"{name.lower().replace('-', '_')}-{kind}-vrps.json"
                values = {"repository": repository, "tal": str(Path(repository) / "test.tal"), "output": str(output), "binary": path}
                command = [part.format(**values) for part in shlex.split(command_template)]
                process = subprocess.run(command, capture_output=True, text=True, timeout=300)
                log = process.stdout + process.stderr
                (PROBE_RESULTS / f"{name.lower().replace('-', '_')}-{kind}.log").write_text(log)
                status = "confirmed" if process.returncode == 0 else "rejected"
                row[f"{kind if kind == 'rsa' else 'pqc_object'}_baseline_status" if kind == "rsa" else "pqc_object_status"] = status
                if kind == "rsa":
                    row["rsa_baseline_status"] = status
                public_command = [part.replace(repository, "$REPOSITORY").replace(str(output), "$OUTPUT") for part in command]
                executions.append({"kind": kind, "status": status, "returncode": process.returncode, "command": public_command, "log": str((PROBE_RESULTS / f"{name.lower().replace('-', '_')}-{kind}.log").relative_to(ROOT))})
        row["executions"] = executions
        rows.append(row)
        write_json(PROBE_RESULTS / f"{name.lower().replace('-', '_')}.json", row)
        if version_error:
            errors.append({"validator": name, "stage": "version", "status": "blocked", "error": version_error})
        if rsa_repository or pqc_repository:
            errors.append({
                "validator": name, "stage": "repository-execution", "status": "future work",
                "error": "No production TAL is used automatically; validator-specific isolated configuration is required.",
            })
    write_csv(RESULTS / "validator-capability.csv", rows)
    write_json(RESULTS / "validator-errors.json", errors)
    docker = shutil.which("docker")
    docker_status = {"status": "unsupported", "reason": "docker executable not found"}
    if docker:
        process = subprocess.run([docker, "version", "--format", "{{.Client.Version}}|{{.Server.Version}}"], capture_output=True, text=True, timeout=15)
        docker_status = {
            "status": "confirmed" if process.returncode == 0 else "blocked",
            "version": process.stdout.strip(),
            "reason": "" if process.returncode == 0 else "Docker daemon unavailable to this run",
        }
    write_json(PROBE_RESULTS / "summary.json", {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "repositories": {"rsa": public_path(rsa_repository), "pqc": public_path(pqc_repository)},
        "container_runtime": docker_status,
        "results": rows,
    })
    markdown = (
        "# Validator Capability\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\n" +
        markdown_table(rows, [
            ("validator", "Validator"), ("installed", "Installed"), ("version", "Version"),
            ("rsa_baseline_status", "RSA baseline"), ("pqc_object_status", "PQC object"),
            ("vrp_output_status", "VRP output"), ("reason", "Reason"),
        ]) + "\n")
    (RESULTS / "validator-capability.md").write_text(markdown)
    (RESULTS / "validator-interoperability.md").write_text(markdown)


if __name__ == "__main__":
    main()
