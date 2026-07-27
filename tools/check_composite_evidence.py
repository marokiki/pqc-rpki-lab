#!/usr/bin/env python3
"""Check that human-readable Composite claims match machine evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def find_inconsistencies() -> list[str]:
    negative = load("results/composite-e2e/negative-summary.json")
    matrix = load("results/composite-e2e/rp-validation-matrix.json")
    benchmark = load("results/composite-e2e/benchmark-summary.json")
    summary = load("results/composite-e2e/summary.json")
    pins = load("experiments/composite-dependencies.json")
    draft = (ROOT / "ietf/draft-yoshikawa-sidrops-pqc-rpki-02.md").read_text()
    readme = (ROOT / "README.md").read_text()
    normalized_draft = " ".join(draft.split())

    expected_cases = {
        "rsa_baseline",
        "pure_mldsa65",
        "composite_standalone",
        "mixed_tree",
    }
    failures: list[str] = []
    if set(matrix["cases"]) != expected_cases:
        failures.append("RP matrix does not contain the four required scenarios")
    if not matrix["success"]:
        failures.append("RP matrix is not successful")
    if not negative["all_rejected"]:
        failures.append("not all negative cases were rejected")

    negative_count = len(negative["results"])
    count_phrase = f"{negative_count} negative cases"
    if count_phrase not in normalized_draft:
        failures.append(f"draft does not contain current count: {count_phrase}")

    generation = benchmark["generation_repetitions"]
    validation = benchmark["validation_repetitions"]
    benchmark_phrase = (
        f"{generation} complete generation repetitions and "
        f"{validation} local RP-validation repetitions"
    )
    if benchmark_phrase not in normalized_draft:
        failures.append(
            f"draft does not contain current repetitions: {benchmark_phrase}"
        )

    oid = summary["composite_oid"]
    if oid not in draft or oid not in readme:
        failures.append(f"Composite OID {oid} is not recorded in draft and README")

    combined_docs = draft + readme
    for dependency in pins.values():
        commit = dependency["commit"]
        if commit not in combined_docs:
            failures.append(f"pinned dependency commit is undocumented: {commit}")

    return failures


def main() -> int:
    failures = find_inconsistencies()
    if failures:
        for failure in failures:
            print(f"Composite evidence inconsistency: {failure}", file=sys.stderr)
        return 1
    print("Composite evidence consistency check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
