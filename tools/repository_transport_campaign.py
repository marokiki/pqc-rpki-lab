#!/usr/bin/env python3
"""Compare repository transport payloads for RSA and PQC-sized workloads.

The corpus is deterministic and size-calibrated from public DER/CMS evidence.
It is deliberately not a cryptographically valid RPKI repository.  The tool
measures rsync locally and constructs RRDP and Erik response bodies so that
transport effects remain separate from CA and RP validation behavior.
"""

from __future__ import annotations

import argparse
import base64
import csv
import gzip
import hashlib
import json
import re
import shutil
import statistics
import subprocess
import time
from pathlib import Path
from xml.sax.saxutils import quoteattr

from pqc_rpki_lab.workspace import reset_generated_directory

ROOT = Path(__file__).resolve().parents[1]
GENERATED_MARKER = ".pqc-rpki-generated"
DEFAULT_WORK = ROOT / "local" / "repository-transport-campaign"
DEFAULT_RESULT = ROOT / "results" / "repository-transport"
ROA_COUNT = 1000
COUNTS = {"cer": 2, "crl": 3, "mft": 3, "roa": ROA_COUNT}

# RSA and Composite totals are confirmed 1,000-ROA Krill captures.  Per-file
# sizes come from public generated-object fixtures and the Composite E2E
# summary.  ML-DSA-65 uses the same manifest-list overhead observed for RSA.
ALGORITHMS = {
    "rsa-2048": {
        "label": "RSA-2048",
        "target_total": 1_768_736,
        "sizes": {"cer": 1_064, "crl": 415, "mft": 1_743, "roa": 1_621},
        "classification": "captured-total plus measured-file-size workload",
    },
    "ml-dsa-65": {
        "label": "ML-DSA-65",
        "target_total": None,
        "sizes": {"cer": 5_793, "crl": 3_464, "mft": 9_556, "roa": 9_434},
        "classification": "measured-file-size workload with calibrated manifest-list overhead",
    },
    "composite-mldsa65-p256": {
        "label": "ML-DSA-65 + P-256 Composite",
        "target_total": 9_797_552,
        "sizes": {"cer": 2_926, "crl": 3_542, "mft": 9_790, "roa": 9_666},
        "classification": "captured-total plus measured-file-size workload",
    },
}


def gzip_bytes(data: bytes) -> bytes:
    return gzip.compress(data, compresslevel=9, mtime=0)


def deterministic_bytes(label: str, size: int) -> bytes:
    return hashlib.shake_256(label.encode()).digest(size)


def base_total(sizes: dict[str, int]) -> int:
    return sum(COUNTS[kind] * sizes[kind] for kind in COUNTS)


def algorithm_totals() -> dict[str, int]:
    rsa = ALGORITHMS["rsa-2048"]
    rsa_overhead = int(rsa["target_total"]) - base_total(rsa["sizes"])
    totals = {}
    for key, data in ALGORITHMS.items():
        target = data["target_total"]
        totals[key] = int(target) if target is not None else base_total(data["sizes"]) + rsa_overhead
    return totals


def paths_and_sizes(algorithm: str) -> list[tuple[Path, int]]:
    sizes = ALGORITHMS[algorithm]["sizes"]
    rows = [
        (Path("ta.cer"), sizes["cer"]),
        (Path("child.cer"), sizes["cer"]),
        (Path("ta.crl"), sizes["crl"]),
        (Path("child.crl"), sizes["crl"]),
        (Path("child-previous.crl"), sizes["crl"]),
        (Path("ta.mft"), sizes["mft"]),
        (Path("child.mft"), sizes["mft"]),
        (Path("child-previous.mft"), sizes["mft"]),
    ]
    rows.extend(
        (Path("roas") / f"route-{number:04d}.roa", sizes["roa"])
        for number in range(ROA_COUNT)
    )
    target = algorithm_totals()[algorithm]
    adjustment = target - sum(size for _, size in rows)
    child_index = next(i for i, (path, _) in enumerate(rows) if path == Path("child.mft"))
    path, size = rows[child_index]
    rows[child_index] = (path, size + adjustment)
    assert sum(size for _, size in rows) == target
    return rows


def changed_paths(scenario: str) -> set[Path]:
    common = {Path("child.mft"), Path("child.crl")}
    if scenario == "one_roa_update":
        return common | {Path("roas/route-0000.roa")}
    if scenario == "ten_percent_roa_churn":
        return common | {
            Path("roas") / f"route-{number:04d}.roa" for number in range(100)
        }
    return set()


def materialize(root: Path, algorithm: str, version: str, changed: set[Path]) -> None:
    reset_generated_directory(root, allowed_root=DEFAULT_WORK.parent)
    for path, size in paths_and_sizes(algorithm):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        generation = version if path in changed else "baseline"
        target.write_bytes(deterministic_bytes(f"{algorithm}:{path}:{generation}", size))


def update_changed(root: Path, algorithm: str, version: str, changed: set[Path]) -> None:
    for path, size in paths_and_sizes(algorithm):
        if path in changed:
            (root / path).write_bytes(deterministic_bytes(f"{algorithm}:{path}:{version}", size))


RSYNC_FIELDS = {
    "Number of files transferred": "files_transferred",
    "Total transferred file size": "object_bytes",
    "File list size": "file_list_bytes",
    "Total sent": "sent_bytes",
    "Total received": "received_bytes",
}


def parse_number(value: str) -> int:
    return int(re.sub(r"[^0-9]", "", value))


def run_rsync(source: Path, cache: Path, repetitions: int) -> dict[str, int | float]:
    baseline = cache.parent / "cache-before-scenario"
    reset_generated_directory(baseline, allowed_root=DEFAULT_WORK.parent)
    shutil.copytree(cache, baseline, dirs_exist_ok=True)
    samples = []
    parsed: dict[str, int] = {}
    for repetition in range(repetitions):
        reset_generated_directory(cache, allowed_root=DEFAULT_WORK.parent)
        shutil.copytree(baseline, cache, dirs_exist_ok=True)
        started = time.perf_counter()
        process = subprocess.run(
            [
                "/usr/bin/rsync", "-a", "--checksum", "--delete", "--stats",
                f"--exclude={GENERATED_MARKER}", f"{source}/", f"{cache}/",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        samples.append((time.perf_counter() - started) * 1000)
        if repetition == 0:
            for line in process.stdout.splitlines():
                if ":" not in line:
                    continue
                name, value = line.split(":", 1)
                if name in RSYNC_FIELDS:
                    parsed[RSYNC_FIELDS[name]] = parse_number(value)
    parsed["response_body_bytes"] = parsed["sent_bytes"] + parsed["received_bytes"]
    parsed["request_count"] = 1
    parsed["local_wall_ms_median"] = round(statistics.median(samples), 3)
    parsed["local_wall_ms_samples"] = repetitions
    return parsed


def rrdp_document(kind: str, serial: int, files: list[tuple[Path, bytes]]) -> bytes:
    lines = [f'<{kind} xmlns="http://www.ripe.net/rpki/rrdp" session_id="transport-campaign" serial="{serial}">']
    for path, content in files:
        encoded = base64.b64encode(content).decode()
        lines.append(f"  <publish uri={quoteattr('rsync://example.invalid/repository/' + str(path))}>{encoded}</publish>")
    lines.append(f"</{kind}>")
    return ("\n".join(lines) + "\n").encode()


def notification(serial: int) -> bytes:
    return (
        '<notification xmlns="http://www.ripe.net/rpki/rrdp" '
        f'session_id="transport-campaign" serial="{serial}" '
        'snapshot_uri="https://example.invalid/snapshot.xml" '
        'snapshot_hash="sha256-placeholder"/>\n'
    ).encode()


def state_files(root: Path, selected: set[Path] | None = None) -> list[tuple[Path, bytes]]:
    rows = []
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        relative = path.relative_to(root)
        if relative == Path(GENERATED_MARKER):
            continue
        if selected is None or relative in selected:
            rows.append((relative, path.read_bytes()))
    return rows


def payload_metrics(payloads: list[bytes], requests: int) -> dict[str, int]:
    return {
        "request_count": requests,
        "response_body_bytes": sum(len(payload) for payload in payloads),
        "gzip_response_body_bytes": sum(len(gzip_bytes(payload)) for payload in payloads),
    }


def rrdp_metrics(root: Path, scenario: str, serial: int) -> dict[str, int]:
    note = notification(serial)
    if scenario == "unchanged_repository":
        return payload_metrics([note], 1)
    selected = None if scenario == "cold_sync" else changed_paths(scenario)
    kind = "snapshot" if scenario == "cold_sync" else "delta"
    document = rrdp_document(kind, serial, state_files(root, selected))
    return payload_metrics([note, document], 2)


def erik_metadata(algorithm: str, version: str, kind: str, size: int) -> bytes:
    return deterministic_bytes(f"erik:{algorithm}:{version}:{kind}", size)


def erik_metrics(root: Path, algorithm: str, scenario: str, version: str) -> dict[str, object]:
    # The one-partition sizes are calibrated from the APNIC PoC trace.  Object
    # bodies are the synthetic workload files themselves.  HTTP headers, TLS,
    # HPACK/QPACK, and Compression Dictionary Transport are intentionally out
    # of scope.
    index = erik_metadata(algorithm, version, "index", 113)
    partition = erik_metadata(algorithm, version, "partition", 233)
    if scenario == "unchanged_repository":
        return {"tree_fetch": payload_metrics([index], 1)}
    if scenario == "cold_sync":
        objects = [content for _, content in state_files(root)]
        return {
            "tree_fetch": payload_metrics([index, partition, *objects], 2 + len(objects)),
            "snapshot_prefetch": payload_metrics([b"".join(objects)], 1),
        }
    objects = [content for _, content in state_files(root, changed_paths(scenario))]
    return {"tree_fetch": payload_metrics([index, partition, *objects], 2 + len(objects))}


def result_rows(result: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for algorithm, algorithm_data in result["algorithms"].items():
        for scenario, scenario_data in algorithm_data["scenarios"].items():
            for protocol in ("rsync", "rrdp"):
                metrics = scenario_data[protocol]
                rows.append({
                    "algorithm": algorithm,
                    "scenario": scenario,
                    "protocol": protocol,
                    "request_count": metrics["request_count"],
                    "response_body_bytes": metrics["response_body_bytes"],
                    "gzip_response_body_bytes": metrics.get("gzip_response_body_bytes", ""),
                    "local_wall_ms_median": metrics.get("local_wall_ms_median", ""),
                })
            for mode, metrics in scenario_data["erik"].items():
                rows.append({
                    "algorithm": algorithm,
                    "scenario": scenario,
                    "protocol": f"erik-{mode}",
                    "request_count": metrics["request_count"],
                    "response_body_bytes": metrics["response_body_bytes"],
                    "gzip_response_body_bytes": metrics["gzip_response_body_bytes"],
                    "local_wall_ms_median": "",
                })
    return rows


def write_outputs(result: dict[str, object], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "repository-transport.json").write_text(json.dumps(result, indent=2) + "\n")
    rows = result_rows(result)
    with (output / "repository-transport.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Repository transport comparison",
        "",
        "This is a deterministic, size-calibrated transport workload, not a cryptographically valid RPKI repository or a production-network benchmark.",
        "",
        "| Algorithm | Scenario | Protocol | Requests | Response body (B) | Gzip body (B) | Local wall median (ms) |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['algorithm']} | {row['scenario']} | {row['protocol']} | "
            f"{row['request_count']} | {row['response_body_bytes']} | "
            f"{row['gzip_response_body_bytes']} | {row['local_wall_ms_median']} |"
        )
    lines.extend(["", "See the JSON result for provenance, classification, and limitations.", ""])
    (output / "repository-transport.md").write_text("\n".join(lines))


def run(work: Path, repetitions: int) -> dict[str, object]:
    reset_generated_directory(work, allowed_root=ROOT / "local")
    scenarios = (
        ("cold_sync", "baseline", set()),
        ("unchanged_repository", "baseline", set()),
        ("one_roa_update", "one-roa", changed_paths("one_roa_update")),
        ("ten_percent_roa_churn", "churn-10-percent", changed_paths("ten_percent_roa_churn")),
    )
    algorithms = {}
    for algorithm, details in ALGORITHMS.items():
        source = work / algorithm / "source"
        cache = work / algorithm / "cache"
        reset_generated_directory(cache, allowed_root=ROOT / "local")
        scenario_results = {}
        for serial, (scenario, version, changed) in enumerate(scenarios, 1):
            if scenario == "cold_sync":
                materialize(source, algorithm, version, changed)
            elif changed:
                update_changed(source, algorithm, version, changed)
            scenario_results[scenario] = {
                "changed_object_count": len(changed) if scenario != "cold_sync" else sum(COUNTS.values()),
                "rsync": run_rsync(source, cache, repetitions),
                "rrdp": rrdp_metrics(source, scenario, serial),
                "erik": erik_metrics(source, algorithm, scenario, version),
            }
        algorithms[algorithm] = {
            "label": details["label"],
            "classification": details["classification"],
            "repository_bytes": algorithm_totals()[algorithm],
            "object_counts": COUNTS,
            "scenarios": scenario_results,
        }
    return {
        "classification": "deterministic size-calibrated transport workload; not cryptographically valid RPKI objects and not a production-network benchmark",
        "algorithms": algorithms,
        "method": {
            "rsync": "openrsync 2.6.9-compatible local protocol run with checksum comparison; sent plus received bytes and local wall time",
            "rrdp": "RFC 8182-shaped XML with base64 publication payloads; notification plus snapshot or delta response bodies",
            "erik": "draft-ietf-sidrops-rpki-erik-protocol-07 tree-fetch and snapshot-prefetch response-body accounting; one index and one partition",
            "compression": "gzip level 9 with deterministic mtime; HTTP headers, TLS, HPACK/QPACK, and RFC 9842 dictionary transport excluded",
        },
        "source_evidence": {
            "rsa_and_composite_totals": "results/scaled-corpus/krill-scaled-summary.json",
            "rsa_and_ml_dsa_file_sizes": "results/rpki-objects/rpki-objects.json",
            "composite_file_sizes": "results/composite-e2e/summary.json",
            "erik_specification": "draft-ietf-sidrops-rpki-erik-protocol-07 (2026-08-16)",
        },
        "erik_poc_validation": {
            "classification": "actual local HTTP execution of the APNIC proof of concept on its bundled non-PQC corpus; separate from the size-calibrated comparison",
            "repository": "https://github.com/APNIC-net/rpki-erik-demo",
            "commit": "0fc81bb83db00d7434ea444909b0dc42a63c145b",
            "test_suite": {"passed": 81, "failed": 0},
            "corpus": {"roa_objects": 150, "manifest_objects": 14},
            "response_body_bytes": {
                "cold_sync": 327395,
                "unchanged_repository": 633,
                "incremental_publication_point_addition": 3283,
            },
            "http_requests": {
                "cold_sync": 194,
                "unchanged_repository": 1,
                "incremental_publication_point_addition": 4,
            },
            "build_note": "The Docker build required zlib1g-dev for zlib.h; the workaround was applied only to the ignored local checkout.",
        },
        "limitations": [
            "The workload preserves counts and measured sizes, not DER/CMS semantics or validation.",
            "Erik metadata sizes use a one-partition APNIC PoC trace calibration; the PQC rows are size-transformed measurements, not Erik interoperability runs.",
            "Response-body bytes exclude request headers, response headers, TLS, and connection setup.",
            "Local wall time is reported only for rsync and is not a WAN latency or throughput result.",
            "Polling-interval and obsolete-intermediate-state experiments require a time-series publication workload and remain future work.",
        ],
        "contains_raw_objects": False,
        "contains_private_keys": False,
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--output", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--repetitions", type=int, default=5)
    args = parser.parse_args()
    if args.repetitions < 1:
        raise SystemExit("repetitions must be positive")
    result = run(args.work.resolve(), args.repetitions)
    write_outputs(result, args.output.resolve())
    print(args.output / "repository-transport.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
