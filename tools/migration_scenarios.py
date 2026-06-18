#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from pqc_rpki_lab.result_io import markdown_table, write_csv, write_json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCENARIOS = [
    ("rsa-only", "RSA only", "all", "equivalent", "confirmed", "Baseline deployment"),
    ("parallel-ml-dsa-65", "RSA + ML-DSA-65 parallel", "mixed", "equivalent", "estimated", "Preferred first transition experiment"),
    ("parallel-ml-dsa-87", "RSA + ML-DSA-87 parallel", "mixed", "equivalent", "estimated", "High-assurance transition"),
    ("parallel-slh-128s", "RSA + SLH-DSA-SHAKE-128s parallel", "mixed", "equivalent", "estimated", "Large repository and transfer impact"),
    ("pqc-only", "PQC only", "PQC-capable only", "equivalent", "future work", "Legacy validators reject or ignore branch"),
    ("partial-hierarchy", "Partial parent/child migration", "policy-dependent", "blocked", "estimated", "Algorithm suite mismatch can break path validation"),
    ("inconsistent-roa", "Inconsistent parallel ROA", "mixed", "different", "confirmed", "Must raise semantic divergence telemetry"),
    ("stale-manifest", "Stale manifest in one branch", "mixed", "different", "confirmed", "Freshness rules remain independently enforced"),
    ("mixed-validators", "Unsupported validator mixed deployment", "mixed", "policy-dependent", "estimated", "Avoid silent downgrade and split VRP views"),
]


def main() -> None:
    rows = [
        dict(zip(("scenario_id", "scenario", "validator_population", "expected_vrp_relation", "status", "observation"), values))
        for values in SCENARIOS
    ]
    write_csv(RESULTS / "migration-scenarios.csv", rows)
    write_json(RESULTS / "migration-scenarios.json", {
        "model": "deterministic policy/semantic scenario matrix", "results": rows,
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
    })
    (RESULTS / "migration-scenarios.md").write_text(
        "# Migration Scenarios\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\n" +
        markdown_table(rows, [(key, key.replace("_", " ").title()) for key in rows[0]]) + "\n")


if __name__ == "__main__":
    main()
