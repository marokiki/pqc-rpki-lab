#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

from pqc_rpki_lab.algorithms import algorithm_rows
from pqc_rpki_lab.result_io import markdown_table, write_json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def read_csv(name: str) -> list[dict[str, str]]:
    path = RESULTS / name
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(name: str, default):
    path = RESULTS / name
    return json.loads(path.read_text()) if path.exists() else default


def main() -> None:
    primitive = read_csv("primitive-bench.csv")
    repository = read_csv("repository-impact.csv")
    objects = read_csv("generated-object-sizes.csv")
    real_repository = read_csv("real-repository-summary.csv")
    validators = read_csv("validator-capability.csv")
    vrp = read_json("vrp-equivalence.json", {})
    migration = read_csv("migration-scenarios.csv")
    report = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "algorithms": algorithm_rows(),
        "primitive_benchmark": primitive,
        "repository_impact": repository,
        "object_generation_feasibility": objects,
        "real_repository_measurement": real_repository,
        "validators": validators,
        "vrp_equivalence": vrp,
        "migration_scenarios": migration,
        "recommendation": {
            "primary": "ML-DSA-65",
            "performance_challenger": "Falcon-512",
            "optional_high_assurance": "ML-DSA-87",
            "not_default": ["SLH-DSA-SHAKE-128s", "SLH-DSA-SHAKE-192s"],
            "round_3_research": ["MAYO-1", "SNOVA-(24,5,4)", "HAWK-512"],
        },
    }
    write_json(RESULTS / "report.json", report)
    sections = [
        "# PQC RPKI Evaluation Report",
        "",
        "> EXPERIMENTAL / NOT FOR PRODUCTION",
        "",
        "## Summary",
        "",
        "ML-DSA-65 remains the standards-ready SIDROPS implementation target. "
        "OpenSSL generated RFC 6487-oriented CA/EE certificates and CRLs with "
        "ML-DSA, but its CMS CLI could not create pure ML-DSA SignedData. "
        "Falcon-512 remains the leading performance challenger.",
        "",
        "## RFC-profiled object generation",
        "",
        markdown_table(objects, [
            ("algorithm", "Algorithm"), ("object_type", "Object"),
            ("status", "Status"), ("bytes", "Bytes"),
            ("classification", "Classification"), ("reason", "Reason"),
        ]),
        "",
        "## Primitive benchmark",
        "",
        markdown_table(primitive, [
            ("name", "Algorithm"), ("benchmark_status", "Status"),
            ("sign_ms_median", "Sign ms"), ("verify_ms_median", "Verify ms"),
            ("measured_signature_bytes", "Measured signature bytes"),
        ]),
        "",
        "## Repository impact",
        "",
        markdown_table(repository, [
            ("algorithm", "Algorithm"), ("repository_total_bytes", "Repository bytes"),
            ("repository_growth_ratio_vs_rsa", "RSA ratio"),
            ("rrdp_snapshot_bytes", "RRDP snapshot bytes"),
        ]),
        "",
        "## Validator capability",
        "",
        markdown_table(validators, [
            ("validator", "Validator"), ("installed", "Installed"),
            ("version", "Version"), ("rsa_baseline_status", "RSA baseline"),
            ("pqc_object_status", "PQC object"), ("vrp_output_status", "VRP output"),
        ]),
        "",
        "## Real repository measurement",
        "",
        markdown_table(real_repository, [
            ("extension", "Extension"), ("status", "Status"), ("count", "Count"),
            ("total_bytes", "Total bytes"), ("median_bytes", "Median bytes"),
            ("p95_bytes", "P95 bytes"), ("reason", "Reason"),
        ]),
        "",
        "## VRP semantics",
        "",
        f"Equivalent: `{vrp.get('result', {}).get('equivalent', 'unknown')}`.",
        "",
        "## Limitations",
        "",
        "- Repository values are first-order or literature-calibrated estimates.",
        "- MFT and ROA payloads were not hand-encoded; no existing payload generator was available.",
        "- No RFC-profiled PQC RPKI object has yet been accepted by an independent validator.",
        "- Missing optional dependencies are recorded as unsupported, not suite failures.",
    ]
    (RESULTS / "report.md").write_text("\n".join(sections) + "\n")
    tables = RESULTS / "tables"
    tables.mkdir(exist_ok=True)
    table_specs = {
        "primitive-benchmark.md": (primitive, [("name", "Algorithm"), ("sign_ms_median", "Sign ms"), ("verify_ms_median", "Verify ms")]),
        "repository-impact.md": (repository, [("algorithm", "Algorithm"), ("repository_total_bytes", "Bytes"), ("repository_growth_ratio_vs_rsa", "RSA ratio")]),
        "validator-capability.md": (validators, [("validator", "Validator"), ("installed", "Installed"), ("rsa_baseline_status", "RSA baseline"), ("pqc_object_status", "PQC object")]),
        "object-generation.md": (objects, [("algorithm", "Algorithm"), ("object_type", "Object"), ("status", "Status"), ("bytes", "Bytes")]),
        "algorithm-comparison.md": (algorithm_rows(), [("name", "Algorithm"), ("track", "Track"), ("public_key_bytes", "Public key"), ("signature_bytes", "Signature")]),
    }
    for name, (rows, columns) in table_specs.items():
        (tables / name).write_text(markdown_table(rows, columns) + "\n")


if __name__ == "__main__":
    main()
