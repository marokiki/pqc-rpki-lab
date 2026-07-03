#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

from pqc_rpki_lab.result_io import markdown_table, write_json
from pqc_rpki_lab.routinator_krill import PROJECTS, binary_probe, default_interop_layers

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "routinator-krill"
VALIDATOR_RESULTS = ROOT / "results" / "validator-interoperability"


def matrix_row(project: dict[str, object], repository_kind: str, repository_path: str) -> dict[str, object]:
    if project["status"] != "confirmed":
        layers = default_interop_layers(str(project["status"]), str(project["reason"]))
    elif not repository_path:
        layers = default_interop_layers("skipped", f"{repository_kind} repository path is not configured")
    elif not Path(repository_path).exists():
        layers = default_interop_layers("blocked", f"{repository_kind} repository path does not exist")
    else:
        layers = default_interop_layers(
            "future-work",
            "Repository-specific isolated TAL/config adapter is not implemented yet",
        )
    return {
        "project": project["project"],
        "role": project["role"],
        "repository_kind": repository_kind,
        "repository_path": repository_path,
        **layers,
    }


def main() -> None:
    probes = [binary_probe(spec) for spec in PROJECTS]
    rsa_repository = os.environ.get("PQC_RPKI_RSA_REPOSITORY", "")
    pqc_repository = os.environ.get("PQC_RPKI_PQC_REPOSITORY", "")
    rows = []
    for probe in probes:
        rows.append(matrix_row(probe, "rsa-baseline", rsa_repository))
        rows.append(matrix_row(probe, "pqc-or-mixed-tree", pqc_repository))
    document = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "classification": "interop harness; no production TALs or network fetches are used automatically",
        "binary_probes": probes,
        "repositories": {
            "rsa_baseline": rsa_repository,
            "pqc_or_mixed_tree": pqc_repository,
        },
        "results": rows,
    }
    write_json(RESULTS / "interop-matrix.json", document)
    write_json(VALIDATOR_RESULTS / "routinator-krill-interop.json", document)
    table = markdown_table(rows, [
        ("project", "Project"), ("repository_kind", "Repository"),
        ("parser", "Parser"), ("signature", "Signature"),
        ("certificate_path", "Certificate Path"), ("crl", "CRL"),
        ("manifest", "Manifest"), ("roa", "ROA"),
        ("vrp_output", "VRP Output"), ("reason", "Reason"),
    ])
    markdown = (
        "# Routinator/Krill Interop Matrix\n\n"
        "> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        "Runs only against explicitly configured binaries and repositories. "
        "Set `PQC_RPKI_ROUTINATOR_BIN`, `PQC_RPKI_KRILL_BIN`, "
        "`PQC_RPKI_RSA_REPOSITORY`, and `PQC_RPKI_PQC_REPOSITORY` for local experiments.\n\n"
        + table + "\n"
    )
    (RESULTS / "interop-matrix.md").write_text(markdown)
    (VALIDATOR_RESULTS / "routinator-krill-interop.md").write_text(markdown)


if __name__ == "__main__":
    main()
