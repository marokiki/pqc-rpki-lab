#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

from pqc_rpki_lab.algorithms import ALL_ALGORITHMS
from pqc_rpki_lab.repository_model import AlgorithmSize, Corpus, estimate_repository_bytes
from pqc_rpki_lab.result_io import markdown_table, write_csv, write_json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path(os.environ.get("PQC_RPKI_RESULTS_DIR", ROOT / "results"))


def main() -> None:
    corpus = Corpus(10, 100, 10, 10, 100, 1500, 1500, 600, 1500, 200)
    rows = [
        estimate_repository_bytes(
            corpus, AlgorithmSize(algorithm.name, algorithm.public_key_bytes, algorithm.signature_bytes))
        for algorithm in ALL_ALGORITHMS
    ]
    baseline = int(rows[0]["repository_total_bytes"])
    for row in rows:
        ratio = int(row["repository_total_bytes"]) / baseline
        row["repository_growth_ratio_vs_rsa"] = round(ratio, 4)
        row["repository_growth_percent_vs_rsa"] = round((ratio - 1) * 100, 2)
    write_csv(RESULTS / "repository-impact.csv", rows)
    write_json(RESULTS / "repository-impact.json", {
        "corpus": corpus.__dict__,
        "limitations": [
            "First-order model, not measured DER/CMS artifacts.",
            "RRDP XML and local cache overhead are configurable ratios.",
        ],
        "results": rows,
    })
    table = markdown_table(rows, [
        ("algorithm", "Algorithm"), ("repository_total_bytes", "Repository bytes"),
        ("repository_growth_ratio_vs_rsa", "RSA ratio"),
        ("rrdp_snapshot_bytes", "RRDP snapshot"), ("local_cache_bytes", "Local cache"),
    ])
    (RESULTS / "repository-impact.md").write_text(
        "# Repository Impact\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\n" + table + "\n")


if __name__ == "__main__":
    main()
