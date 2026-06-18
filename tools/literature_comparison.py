#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

from pqc_rpki_lab.algorithms import ALL_ALGORITHMS
from pqc_rpki_lab.result_io import markdown_table, write_csv, write_json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
BASELINE_BYTES = 838_030_450
PUBLIC_KEYS = 393_427
SIGNATURES = 788_916
PUBLISHED = {
    "RSA-2048/SHA-256": (838_030_450, 13.0, 10.800),
    "ML-DSA-65": (3_900_000_000, 51.8, 0.212),
    "ML-DSA-87": (5_200_000_000, 80.9, 0.257),
    "SLH-DSA-SHAKE-128s": (6_700_000_000, 1376.3, 1873.028),
    "Falcon-512": (1_400_000_000, 23.4, 0.404),
    "Falcon-1024": (2_200_000_000, 46.4, 0.821),
    "MAYO-1": (1_400_000_000, 44.3, 0.188),
    "SNOVA-(24,5,4)": (1_100_000_000, 47.3, 0.123),
    "HAWK-512": (1_400_000_000, 42.8, 0.034),
}


def csv_by_name(name: str, key: str) -> dict[str, dict[str, str]]:
    path = RESULTS / name
    if not path.exists():
        return {}
    with path.open(newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


def main() -> None:
    primitive = csv_by_name("primitive-bench.csv", "name")
    repository = csv_by_name("repository-impact.csv", "algorithm")
    non_crypto = BASELINE_BYTES - PUBLIC_KEYS * 272 - SIGNATURES * 256
    rows = []
    for algorithm in ALL_ALGORITHMS:
        public_key_bytes = 272 if algorithm.name == "RSA-2048/SHA-256" else algorithm.public_key_bytes
        calibrated = non_crypto + PUBLIC_KEYS * public_key_bytes + SIGNATURES * algorithm.signature_bytes
        published = PUBLISHED.get(algorithm.name)
        synthetic = float(repository.get(algorithm.name, {}).get("repository_growth_ratio_vs_rsa", 0))
        calibrated_ratio = calibrated / BASELINE_BYTES
        rows.append({
            "algorithm": algorithm.name,
            "approximate_median_roa_bytes": 1341 + algorithm.public_key_bytes + 2 * algorithm.signature_bytes,
            "comparison_status": "comparable-size-model",
            "literature_calibrated_ratio_vs_rsa": round(calibrated_ratio, 4),
            "literature_calibrated_repository_bytes": calibrated,
            "local_primitive_sign_ms": primitive.get(algorithm.name, {}).get("sign_ms_median", ""),
            "published_estimated_sign_ms": published[2] if published else "",
            "published_ratio_vs_rsa": round(published[0] / BASELINE_BYTES, 4) if published else "",
            "published_repository_bytes_rounded": published[0] if published else "",
            "published_validation_cpu_seconds": published[1] if published else "",
            "synthetic_difference_percent_vs_calibrated": round((synthetic / calibrated_ratio - 1) * 100, 2) if synthetic else "",
            "synthetic_ratio_vs_rsa": synthetic,
        })
    write_csv(RESULTS / "literature-comparison.csv", rows)
    write_json(RESULTS / "literature-comparison.json", {
        "baseline": {
            "snapshot_date": "2025-02-01", "repository_bytes": BASELINE_BYTES,
            "public_keys": PUBLIC_KEYS, "signatures": SIGNATURES,
            "rsa_public_key_bytes": 272, "rsa_signature_bytes": 256,
        },
        "method": "Replace RSA public-key and signature bytes while retaining non-cryptographic bytes.",
        "results": rows,
    })
    table = markdown_table(rows, [
        ("algorithm", "Algorithm"), ("synthetic_ratio_vs_rsa", "Current synthetic ratio"),
        ("literature_calibrated_ratio_vs_rsa", "Calibrated ratio"),
        ("published_ratio_vs_rsa", "Published ratio"),
        ("synthetic_difference_percent_vs_calibrated", "Synthetic difference"),
        ("published_validation_cpu_seconds", "Published validation CPU s"),
    ])
    (RESULTS / "literature-comparison.md").write_text(
        "# Literature Comparison\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        "The calibrated model uses the measured object, public-key, and signature counts "
        "from the 2025 thesis. Local primitive and published full-RPKI timings are not directly comparable.\n\n"
        + table + "\n")


if __name__ == "__main__":
    main()
