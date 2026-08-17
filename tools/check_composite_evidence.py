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
    routinator_matrix = load("results/composite-e2e/routinator-matrix.json")
    routinator_negative = load(
        "results/composite-e2e/routinator-negative-summary.json"
    )
    krill = load("results/composite-e2e/krill-rollover.json")
    cache_profile = load("results/scaled-corpus/public-cache-profile.json")
    scaled_krill = load("results/scaled-corpus/krill-scaled-summary.json")
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
    routinator_cases = set(routinator_matrix["cases"])
    if routinator_cases != expected_cases or not routinator_matrix["success"]:
        failures.append("Routinator matrix is not successful for all four scenarios")
    if (
        not routinator_negative["all_rejected"]
        or len(routinator_negative["results"]) != len(negative["results"])
    ):
        failures.append("Routinator negative evidence does not match primary RP")
    if not krill["success"]:
        failures.append("Krill issuance and rollback evidence is not successful")
    if cache_profile["synthetic_corpus"]["contains_source_objects"]:
        failures.append("public cache profile contains source objects")
    if cache_profile["object_count"] != sum(
        cache_profile["object_type_counts"].values()
    ):
        failures.append("public cache object counts are inconsistent")
    if not scaled_krill["scaled_composite_success"]:
        failures.append("scaled Krill Composite validation did not succeed")
    if not scaled_krill["rollback_success"]:
        failures.append("scaled Krill RSA rollback did not succeed")
    expected_krill = {
        "composite": {
            "rpki_client_default": "rejected",
            "rpki_client_experimental": "accepted",
            "routinator_default": "rejected",
            "routinator_experimental": "accepted",
        },
        "rollback": {
            "rpki_client_default": "accepted",
            "rpki_client_experimental": "accepted",
            "routinator_default": "accepted",
            "routinator_experimental": "accepted",
        },
    }
    for phase, modes in expected_krill.items():
        for mode, expected in modes.items():
            if krill["phases"][phase][mode]["status"] != expected:
                failures.append(
                    f"Krill {phase}/{mode} is not recorded as {expected}"
                )

    public_routinator = json.dumps(
        {
            "matrix": routinator_matrix,
            "negative": routinator_negative,
            "krill": krill,
        }
    )
    private_path_markers = ("/" + "home" + "/", "/" + "Users" + "/")
    if any(marker in public_routinator for marker in private_path_markers):
        failures.append("Routinator public evidence contains an absolute user path")

    negative_count = len(negative["results"])
    count_phrase = f"{negative_count} negative cases"
    small_number_words = (
        "Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven",
        "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
        "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen",
        "Nineteen", "Twenty",
    )
    count_phrases = {count_phrase}
    if negative_count < len(small_number_words):
        count_phrases.add(f"{small_number_words[negative_count]} negative cases")
    if not any(phrase in normalized_draft for phrase in count_phrases):
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

    required_scaled_phrases = (
        "550,210 public-cache objects",
        "54,960 publication points",
        "980,019 VRPs",
        "1,000-ROA",
    )
    for phrase in required_scaled_phrases:
        if phrase not in normalized_draft:
            failures.append(f"draft does not contain scaled evidence: {phrase}")

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
