#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from pqc_rpki_lab.result_io import markdown_table, write_csv, write_json
from pqc_rpki_lab.vrp import compare, normalize_vrp

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


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
        {"prefix": "192.0.2.0/24", "maxLength": 24, "asn": 64496, "ta": "test-ta"},
        {"prefix": "2001:db8::/32", "maxLength": 48, "asn": 64497, "ta": "test-ta"},
    ]
    baseline_rows = load(args.baseline) if args.baseline else synthetic
    candidate_rows = load(args.candidate) if args.candidate else synthetic
    result = compare(
        {normalize_vrp(row) for row in baseline_rows},
        {normalize_vrp(row) for row in candidate_rows})
    summary = {
        "status": "confirmed" if args.baseline and args.candidate else "estimated",
        "method": "local canonical JSON approximation; not draft-ietf-sidrops-rpki-ccr DER",
        "ccr_design": {
            "equality": "Compare CCR ROAPayloadState.hash values when CCR output is available.",
            "diagnosis": "Decode and compare ROAPayloadState.rps when hashes differ.",
            "provenance": "Compare trust-anchor/source attribution separately from VRP-set equality.",
        },
        "sources": {
            "baseline": str(args.baseline) if args.baseline else "built-in synthetic",
            "candidate": str(args.candidate) if args.candidate else "built-in synthetic",
        },
        "result": result, "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
    }
    write_json(RESULTS / "vrp-equivalence.json", summary)
    row = {
        "baseline_count": result["baseline_count"], "candidate_count": result["candidate_count"],
        "equivalent": result["equivalent"], "only_baseline_count": len(result["only_baseline"]),
        "only_candidate_count": len(result["only_candidate"]),
        "provenance_difference_count": len(result["provenance_differences"]),
        "baseline_local_hash": result["baseline_local_hash"],
        "candidate_local_hash": result["candidate_local_hash"],
        "status": summary["status"],
    }
    write_csv(RESULTS / "vrp-equivalence.csv", [row])
    (RESULTS / "vrp-equivalence.md").write_text(
        "# VRP Set Equality\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        "The default hash is a local canonical JSON approximation, not the DER-encoded "
        "CCR `ROAPayloadState.hash`. When validator CCR output is available, that hash is "
        "the comparison target; decoded `rps` values identify individual VRP differences. "
        "Trust-anchor and source attribution are reported separately.\n\n" +
        markdown_table([row], [(key, key.replace("_", " ").title()) for key in row]) + "\n")


if __name__ == "__main__":
    main()
