#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from pqc_rpki_lab.result_io import markdown_table, write_csv, write_json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
TOOLS = {
    "Routinator": ("routinator", ["--version"]),
    "rpki-client": ("rpki-client", ["-V"]),
    "FORT": ("fort", ["--version"]),
}


def version(path: str, arguments: list[str]) -> tuple[str, str]:
    try:
        process = subprocess.run([path, *arguments], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as error:
        return "", str(error)
    text = (process.stdout or process.stderr).strip()
    return (text.splitlines()[0] if text else "", "" if process.returncode == 0 else text)


def main() -> None:
    rsa_repository = os.environ.get("PQC_RPKI_RSA_REPOSITORY", "")
    pqc_repository = os.environ.get("PQC_RPKI_PQC_REPOSITORY", "")
    rows: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    for name, (executable, arguments) in TOOLS.items():
        path = shutil.which(executable)
        if not path:
            row = {
                "validator": name, "installed": False, "version": "",
                "existence_status": "unsupported", "version_status": "unsupported",
                "rsa_baseline_status": "unsupported", "pqc_object_status": "unsupported",
                "vrp_output_status": "unsupported", "network_used": False,
                "reason": "executable not found",
            }
            rows.append(row)
            errors.append({"validator": name, "stage": "existence", "status": "unsupported", "error": "executable not found"})
            continue
        version_text, version_error = version(path, arguments)
        row = {
            "validator": name, "installed": True, "version": version_text,
            "existence_status": "confirmed",
            "version_status": "confirmed" if not version_error else "blocked",
            "rsa_baseline_status": "skipped" if not rsa_repository else "future work",
            "pqc_object_status": "skipped" if not pqc_repository else "future work",
            "vrp_output_status": "skipped",
            "network_used": False,
            "reason": (
                "No explicit isolated repository supplied; only executable and version were probed."
                if not rsa_repository and not pqc_repository
                else "Repository execution requires validator-specific isolated TAL/config adapters."
            ),
        }
        rows.append(row)
        if version_error:
            errors.append({"validator": name, "stage": "version", "status": "blocked", "error": version_error})
        if rsa_repository or pqc_repository:
            errors.append({
                "validator": name, "stage": "repository-execution", "status": "future work",
                "error": "No production TAL is used automatically; validator-specific isolated configuration is required.",
            })
    write_csv(RESULTS / "validator-capability.csv", rows)
    write_json(RESULTS / "validator-errors.json", errors)
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
