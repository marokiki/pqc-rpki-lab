#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from pqc_rpki_lab.result_io import markdown_table, write_json
from pqc_rpki_lab.vrp import compare, normalize_vrp

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "ccr-comparison"


def load(path: Path) -> list[dict[str, object]]:
    if path.suffix == ".json":
        value = json.loads(path.read_text())
        return value if isinstance(value, list) else value.get("vrps", value.get("results", []))
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--candidate", type=Path)
    args = parser.parse_args()
    synthetic = [
        {"prefix": "192.0.2.0/24", "maxLength": 24, "asn": 64496, "ta": "rsa-ta"},
        {"prefix": "2001:db8::/32", "maxLength": 48, "asn": 64497, "ta": "rsa-ta"},
    ]
    baseline_rows = load(args.baseline) if args.baseline else synthetic
    candidate_rows = load(args.candidate) if args.candidate else [
        row | {"ta": "pqc-ta"} for row in synthetic
    ]
    result = compare(
        {normalize_vrp(row) for row in baseline_rows},
        {normalize_vrp(row) for row in candidate_rows},
    )
    document = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "status": "local-interim",
        "method": "sha256-canonical-json-v1-not-ccr",
        "not_ccr": True,
        "sources": {
            "baseline": str(args.baseline) if args.baseline else "built-in synthetic RSA branch",
            "candidate": str(args.candidate) if args.candidate else "built-in synthetic PQC branch",
        },
        "result": result,
    }
    write_json(RESULTS / "ccr-comparison.json", document)
    summary = [{
        "equivalent": result["equivalent"],
        "baseline_count": result["baseline_count"],
        "candidate_count": result["candidate_count"],
        "only_baseline": len(result["only_baseline"]),
        "only_candidate": len(result["only_candidate"]),
        "provenance_differences": len(result["provenance_differences"]),
        "method": document["method"],
    }]
    (RESULTS / "ccr-comparison.md").write_text(
        "# CCR-Style Semantic Comparison\n\n"
        "> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        "This interim workflow compares normalized VRP semantics with a local canonical "
        "JSON hash. It is not `draft-ietf-sidrops-rpki-ccr` output and must not be "
        "reported as CCR `ROAPayloadState.hash` equivalence.\n\n"
        + markdown_table(summary, [(key, key.replace("_", " ").title()) for key in summary[0]]) + "\n"
    )


if __name__ == "__main__":
    main()
