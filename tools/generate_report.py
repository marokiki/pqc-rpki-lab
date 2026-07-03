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
    primitive_document = read_json("primitive-bench.json", {"metadata": {}, "results": []})
    primitive = primitive_document.get("results", [])
    optional_primitive_document = read_json("review-2026-06/primitive-bench.json", {"metadata": {}, "results": []})
    optional_primitive = [row for row in optional_primitive_document.get("results", [])
                          if row.get("comparable_group") == "oqs-python-v1"]
    repository = read_csv("repository-impact.csv")
    objects = read_csv("generated-object-sizes.csv")
    rpki_objects = read_csv("rpki-objects/rpki-objects.csv")
    key_roll = read_csv("key-roll/key-roll.csv")
    local_validation = read_csv("local-validation/local-validation.csv")
    real_repository = read_csv("real-repository-summary.csv")
    validators = read_csv("validator-capability.csv")
    validator_containers = read_json("validator-probe/container-matrix.json", {})
    cms_probe = read_json("cms-probe/cms-api-probe.json", {})
    cms_generation = read_json("cms-generation/cms-generation.json", {})
    message_sweep = read_json("message-sweep/message-sweep.json", {})
    vrp = read_json("vrp-equivalence.json", {})
    ccr = read_json("ccr-comparison/ccr-comparison.json", {})
    object_benchmarks = read_csv("object-benchmarks/object-benchmarks.csv")
    mixed_tree = read_json("mixed-tree/mixed-tree.json", {})
    routinator_krill_scan = read_json("routinator-krill/source-scan.json", {})
    routinator_krill_interop = read_json("routinator-krill/interop-matrix.json", {})
    migration = read_csv("migration-scenarios.csv")
    bulk_document = read_json("review-2026-06/bulk-signing.json", {"metadata": {}, "results": []})
    bulk = bulk_document.get("results", [])
    exact_document = read_json("review-2026-06/exact-100k.json", {"metadata": {}, "results": []})
    exact = exact_document.get("results", [])
    composite_document = read_json("review-2026-06/composite-100k.json", {"metadata": {}, "results": []})
    composite = composite_document.get("results", [])
    catalog = {row["name"]: row for row in algorithm_rows()}
    algorithms = []
    for observed in primitive:
        configured = catalog.get(observed["name"], {})
        merged = configured | observed
        merged["configured_backend"] = configured.get("backend", "")
        merged["backend"] = observed.get("backend", "")
        algorithms.append(merged)
    report = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "algorithms": algorithms,
        "primitive_benchmark_metadata": primitive_document.get("metadata", {}),
        "primitive_benchmark": primitive,
        "optional_primitive_benchmark": optional_primitive,
        "repository_impact": repository,
        "object_generation_feasibility": objects,
        "rpki_objects": rpki_objects,
        "key_roll": key_roll,
        "local_validation": local_validation,
        "real_repository_measurement": real_repository,
        "validators": validators,
        "validator_container_probe": validator_containers,
        "cms_api_probe": cms_probe,
        "cms_generation": cms_generation,
        "message_sweep": message_sweep,
        "vrp_equivalence": vrp,
        "ccr_style_comparison": ccr,
        "object_benchmarks": object_benchmarks,
        "mixed_tree": mixed_tree,
        "routinator_krill_scan": routinator_krill_scan,
        "routinator_krill_interop": routinator_krill_interop,
        "migration_scenarios": migration,
        "bulk_signing_metadata": bulk_document.get("metadata", {}),
        "bulk_signing": bulk,
        "exact_100k_metadata": exact_document.get("metadata", {}),
        "exact_100k": exact,
        "composite_100k_metadata": composite_document.get("metadata", {}),
        "composite_100k": composite,
        "recommendation": {
            "draft_00_primary": "ML-DSA-65",
            "under_review": ["ML-DSA-44", "small-PQ composite suites"],
            "literature_and_model_challenger": "Falcon-512",
            "challenger_evidence": "Pinned liboqs primitive measurement plus literature and size-model evidence; no X.509/CMS interoperability.",
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
        "Draft-01 uses ML-DSA-65 as its primary experiment. Evidence includes "
        "ML-DSA-44, compact classical references, and small-PQ composite size estimates. "
        "OpenSSL 3.6.2 generated ML-DSA-65 RFC 6488 ROA and Manifest objects through "
        "the CMS API when SHA-512 was supplied explicitly; the default-digest CLI path still fails. "
        "Routinator, rpki-client, and FORT accepted the RSA baseline repository and rejected "
        "the ML-DSA-65 repository at unsupported trust-anchor or algorithm checks. "
        "Published RPKI measurements and the local size model identify Falcon-512 "
        "as the leading size challenger. Pinned liboqs now provides primitive Falcon "
        "measurements, but Falcon X.509/CMS interoperability remains unsupported.",
        "",
        "## RFC-profiled object generation",
        "",
        markdown_table(objects, [
            ("algorithm", "Algorithm"), ("object_type", "Object"),
            ("status", "Status"), ("bytes", "Bytes"),
            ("classification", "Classification"), ("reason", "Reason"),
        ]),
        "",
        "## RPKI object fixtures",
        "",
        "RSA and ML-DSA-65 `.mft` and `.roa` fixtures are generated. ML-DSA-65 uses "
        "the OpenSSL CMS API with explicit SHA-512 and is cross-checked against an "
        "independent manual DER assembly path.",
        "",
        markdown_table(rpki_objects, [
            ("algorithm", "Algorithm"), ("artifact", "Artifact"), ("status", "Status"),
            ("classification", "Classification"), ("bytes", "Bytes"),
            ("public_path", "Public Path"), ("reason", "Reason"),
        ]),
        "",
        "## Primitive benchmark",
        "",
        markdown_table(primitive, [
            ("name", "Algorithm"), ("benchmark_status", "Status"),
            ("backend", "Backend"), ("timing_scope", "Timing scope"),
            ("sign_ms_median", "Sign ms"), ("verify_ms_median", "Verify ms"),
            ("measured_signature_bytes", "Measured signature bytes"),
            ("notes", "Notes"), ("reason", "Reason"),
        ]),
        "",
        "## Optional liboqs primitive benchmark",
        "",
        "These in-process values are not directly comparable with the OpenSSL CLI table above.",
        "",
        markdown_table(optional_primitive, [
            ("name", "Algorithm"), ("benchmark_status", "Status"),
            ("keygen_ms_median", "Keygen ms"), ("sign_ms_median", "Sign ms"),
            ("verify_ms_median", "Verify ms"),
            ("measured_signature_bytes", "Measured signature bytes"),
            ("reason", "Reason"),
        ]),
        "",
        "## Bulk signing throughput",
        "",
        "These OpenSSL `speed` values exclude process startup. The 100,000-Manifest and "
        "key-roll columns are signing-only lower bounds, not complete object-generation measurements.",
        "",
        markdown_table(bulk, [
            ("algorithm", "Algorithm"), ("status", "Status"),
            ("sign_ops_per_second", "Sign/s"), ("verify_ops_per_second", "Verify/s"),
            ("estimated_100k_manifests_crypto_lower_bound_seconds", "100k MFT crypto lower bound s"),
            ("estimated_key_roll_crypto_lower_bound_seconds", "Key-roll crypto lower bound s"),
        ]),
        "",
        "## Synthetic key-roll model",
        "",
        markdown_table(key_roll, [
            ("algorithm", "Algorithm"), ("status", "Status"), ("file_count", "Files"),
            ("output_bytes", "Output bytes"), ("rrdp_snapshot_bytes", "RRDP snapshot"),
            ("rrdp_delta_bytes", "RRDP delta"), ("rsync_transfer_bytes", "rsync bytes"),
        ]),
        "",
        "## Local object validation",
        "",
        "Local validation records DER parseability, RSA and ML-DSA-65 CMS round-trips, "
        "EE profile checks, and Manifest product hashes. Independent validator results "
        "are reported separately.",
        "",
        markdown_table(local_validation, [
            ("algorithm", "Algorithm"), ("layer", "Layer"), ("artifact", "Artifact"),
            ("status", "Status"), ("reason", "Reason"),
        ]),
        "",
        "## Exact 100,000-operation benchmark",
        "",
        "Each row is a direct loop of 100,000 signing operations followed by 100,000 "
        "verification operations. Key generation and complete RPKI object processing are excluded.",
        "",
        markdown_table(exact, [
            ("algorithm", "Algorithm"), ("status", "Status"),
            ("sign_seconds", "Sign total s"), ("verify_seconds", "Verify total s"),
            ("sign_microseconds_per_operation", "Sign us/op"),
            ("verify_microseconds_per_operation", "Verify us/op"),
            ("sign_time_ratio_vs_rsa", "Sign time/RSA"),
            ("verify_time_ratio_vs_rsa", "Verify time/RSA"),
        ]),
        "",
        "## Composite component benchmark",
        "",
        "These rows execute both component operations and require both verifications to pass. "
        "They do not implement the LAMPS composite ASN.1/OID format.",
        "",
        markdown_table(composite, [
            ("algorithm", "Combination"), ("status", "Status"),
            ("sign_seconds", "Sign total s"), ("verify_seconds", "Verify total s"),
            ("combined_signature_bytes", "Component bytes"),
            ("sign_time_ratio_vs_mldsa65", "Sign time/ML-DSA-65"),
            ("verify_time_ratio_vs_mldsa65", "Verify time/ML-DSA-65"),
            ("signature_bytes_ratio_vs_mldsa65", "Bytes/ML-DSA-65"),
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
        "## Unmodified validator repository probe",
        "",
        "Pinned unmodified validator containers fetched isolated repositories from a local "
        "rsync daemon. No production TAL or Internet repository was used.",
        "",
        markdown_table(validator_containers.get("results", []), [
            ("validator", "Validator"), ("repository_kind", "Repository"),
            ("status", "Status"), ("parser", "Parser"),
            ("certificate_path", "Certificate path"), ("manifest", "Manifest"),
            ("roa", "ROA"), ("vrp_output", "VRP output"),
            ("hard_error", "Hard error"),
        ]),
        "",
        "## CMS API and object generation",
        "",
        markdown_table(cms_probe.get("results", []), [
            ("mode", "CMS API digest mode"), ("status", "Status"),
            ("returncode", "Return code"), ("output_bytes", "Output bytes"),
            ("error", "Error"),
        ]),
        "",
        markdown_table(cms_generation.get("results", []), [
            ("artifact", "Artifact"), ("status", "Status"),
            ("classification", "Backend"), ("bytes", "Bytes"),
            ("public_path", "Public path"),
        ]),
        "",
        "## Repeated message-size sweep",
        "",
        markdown_table(message_sweep.get("results", []), [
            ("algorithm", "Algorithm"), ("message_bytes", "Message bytes"),
            ("repetitions", "Repetitions"), ("status", "Status"),
            ("sign_seconds_median", "Sign median s"),
            ("sign_seconds_stdev", "Sign stdev s"),
            ("verify_seconds_median", "Verify median s"),
            ("verify_seconds_stdev", "Verify stdev s"),
            ("peak_rss_bytes_median", "Peak RSS median bytes"),
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
        "## CCR-style interim comparison",
        "",
        "The local CCR-style workflow uses canonical JSON and is not CCR "
        "`ROAPayloadState.hash` output.",
        "",
        f"Equivalent: `{ccr.get('result', {}).get('equivalent', 'unknown')}`.",
        "",
        "## Object payload benchmark",
        "",
        markdown_table(object_benchmarks, [
            ("workload", "Workload"), ("objects", "Objects"),
            ("payload_construction_ms", "Payload construction ms"),
            ("file_hashing_ms", "Hashing ms"),
            ("manifest_payload_encoding_ms", "Manifest encoding ms"),
            ("cms_assembly_status", "CMS status"),
            ("classification", "Classification"),
        ]),
        "",
        "## Mixed-tree model",
        "",
        f"Valid synthetic model: `{mixed_tree.get('validation', {}).get('valid', 'unknown')}`. "
        "This is not validator interoperability evidence.",
        "",
        "## Routinator/Krill extension track",
        "",
        "Routinator/Krill scan and interop runners are optional, read-only, and configured "
        "with explicit environment variables. External checkouts must remain under ignored "
        "`local/` or separate upstream worktrees.",
        "",
        markdown_table([
            {
                "project": row.get("project", ""),
                "role": row.get("role", ""),
                "status": row.get("status", ""),
                "source_env": row.get("source_env", ""),
                "reason": row.get("reason", ""),
            }
            for row in routinator_krill_scan.get("scan_results", [])
        ], [
            ("project", "Project"), ("role", "Role"), ("status", "Status"),
            ("source_env", "Source Env"), ("reason", "Reason"),
        ]),
        "",
        "## Limitations",
        "",
        "- Repository values are first-order or literature-calibrated estimates.",
        "- ML-DSA-44/87 and SLH-DSA complete CMS fixtures remain unimplemented.",
        "- No unmodified validator accepted the ML-DSA-65 repository; rejection is expected until algorithm support is added.",
        "- The mixed-tree fixture is still structural rather than a complete validator repository.",
        "- Missing optional dependencies are recorded as unsupported, not suite failures.",
        "- Core primitive timings include one OpenSSL process launch per timed operation; "
        "they are end-to-end CLI measurements, not pure cryptographic cycle counts.",
        "- Timing comparisons are valid only within an identical `comparable_group`.",
    ]
    (RESULTS / "report.md").write_text("\n".join(sections) + "\n")
    tables = RESULTS / "tables"
    tables.mkdir(exist_ok=True)
    table_specs = {
        "primitive-benchmark.md": (primitive, [
            ("name", "Algorithm"), ("benchmark_status", "Status"),
            ("backend", "Backend"), ("timing_scope", "Timing scope"),
            ("sign_ms_median", "Sign ms"), ("verify_ms_median", "Verify ms"),
            ("notes", "Notes"), ("reason", "Reason"),
        ]),
        "repository-impact.md": (repository, [("algorithm", "Algorithm"), ("repository_total_bytes", "Bytes"), ("repository_growth_ratio_vs_rsa", "RSA ratio")]),
        "validator-capability.md": (validators, [("validator", "Validator"), ("installed", "Installed"), ("rsa_baseline_status", "RSA baseline"), ("pqc_object_status", "PQC object")]),
        "validator-container-probe.md": (validator_containers.get("results", []), [
            ("validator", "Validator"), ("repository_kind", "Repository"),
            ("status", "Status"), ("parser", "Parser"),
            ("certificate_path", "Certificate path"), ("vrp_output", "VRP output"),
        ]),
        "object-generation.md": (objects, [("algorithm", "Algorithm"), ("object_type", "Object"), ("status", "Status"), ("bytes", "Bytes")]),
        "rpki-objects.md": (rpki_objects, [
            ("algorithm", "Algorithm"), ("artifact", "Artifact"), ("status", "Status"),
            ("classification", "Classification"), ("bytes", "Bytes"),
        ]),
        "key-roll.md": (key_roll, [
            ("algorithm", "Algorithm"), ("status", "Status"), ("file_count", "Files"),
            ("output_bytes", "Output bytes"), ("rrdp_snapshot_bytes", "RRDP snapshot"),
            ("rrdp_delta_bytes", "RRDP delta"),
        ]),
        "local-validation.md": (local_validation, [
            ("algorithm", "Algorithm"), ("layer", "Layer"), ("artifact", "Artifact"),
            ("status", "Status"),
        ]),
        "algorithm-comparison.md": (algorithm_rows(), [("name", "Algorithm"), ("track", "Track"), ("public_key_bytes", "Public key"), ("signature_bytes", "Signature")]),
        "routinator-krill-interop.md": (routinator_krill_interop.get("results", []), [
            ("project", "Project"), ("repository_kind", "Repository"), ("parser", "Parser"),
            ("signature", "Signature"), ("certificate_path", "Certificate Path"),
            ("manifest", "Manifest"), ("roa", "ROA"), ("vrp_output", "VRP Output"),
        ]),
    }
    for name, (rows, columns) in table_specs.items():
        (tables / name).write_text(markdown_table(rows, columns) + "\n")


if __name__ == "__main__":
    main()
