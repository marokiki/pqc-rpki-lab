#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate generated evidence invariants")
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--require-confirmed", action="append", default=[])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    primitive_document = json.loads((args.results / "primitive-bench.json").read_text())
    report = json.loads((args.results / "report.json").read_text())
    primitive = primitive_document.get("results", [])
    assert primitive, "primitive benchmark results are empty"
    by_name = {row["name"]: row for row in primitive}
    assert len(by_name) == len(primitive), "duplicate primitive benchmark algorithm"

    for name in args.require_confirmed:
        assert name in by_name, f"required algorithm is missing: {name}"
        assert by_name[name].get("benchmark_status") == "confirmed", (
            f"required algorithm is not confirmed: {name}: {by_name[name].get('reason', '')}"
        )

    for row in primitive:
        assert row.get("backend"), f"backend missing for {row['name']}"
        assert row.get("timing_scope"), f"timing_scope missing for {row['name']}"
        assert row.get("comparable_group"), f"comparable_group missing for {row['name']}"
        if row.get("benchmark_status") == "confirmed":
            for field in ("keygen_ms_median", "sign_ms_median", "verify_ms_median"):
                assert isinstance(row.get(field), (int, float)), f"{field} missing for {row['name']}"

    report_algorithms = {row["name"]: row for row in report.get("algorithms", [])}
    assert report_algorithms.keys() == by_name.keys(), "report algorithm set differs from primitive results"
    for name, row in by_name.items():
        reported = report_algorithms[name]
        assert reported.get("backend") == row.get("backend"), f"backend mismatch for {name}"
        assert reported.get("benchmark_status") == row.get("benchmark_status"), (
            f"benchmark status mismatch for {name}"
        )

    for row in report.get("repository_impact", []):
        assert row.get("status") == "estimated", "repository impact must remain classified as estimated"

    print(f"validated {len(primitive)} primitive rows and report consistency")


if __name__ == "__main__":
    main()
