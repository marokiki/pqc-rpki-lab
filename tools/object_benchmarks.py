#!/usr/bin/env python3
from __future__ import annotations

import argparse
import platform
import time
from pathlib import Path

from pqc_rpki_lab.result_io import markdown_table, write_csv, write_json
from pqc_rpki_lab.rpki_objects import PublishedObject, manifest_payload

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "object-benchmarks"


def timed(operation):
    start = time.perf_counter_ns()
    value = operation()
    return value, (time.perf_counter_ns() - start) / 1_000_000


def build_products(count: int) -> list[PublishedObject]:
    return [
        PublishedObject(
            path=f"roas/route-{index:06d}.roa",
            object_type="ROA",
            issuer_key_id="synthetic-ca-key",
            signer_key_id="synthetic-ca-key",
            payload=f"AS64496 192.0.{index % 256}.0/24 maxLength=24\n".encode(),
        )
        for index in range(count)
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--objects", type=int, default=100_000)
    args = parser.parse_args()
    if args.objects <= 0:
        parser.error("--objects must be positive")
    RESULTS.mkdir(parents=True, exist_ok=True)
    products, construction_ms = timed(lambda: build_products(args.objects))
    payload, payload_ms = timed(lambda: manifest_payload(products))
    _, hash_ms = timed(lambda: [product.sha256 for product in products])
    rows = [{
        "workload": "synthetic-manifest-payloads",
        "objects": args.objects,
        "payload_construction_ms": round(construction_ms, 6),
        "file_hashing_ms": round(hash_ms, 6),
        "manifest_payload_encoding_ms": round(payload_ms, 6),
        "manifest_payload_bytes": len(payload),
        "cms_assembly_status": "blocked",
        "signing_status": "not-measured-here",
        "der_serialization_status": "payload-only",
        "classification": "object-payload benchmark, not complete RFC 6488 CMS generation",
    }]
    metadata = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "platform": platform.platform(),
        "method": (
            "Build deterministic synthetic ROA-like payload records, hash each payload, "
            "and encode a deterministic Manifest file list. Complete CMS SignedData, "
            "certificate generation, DER object serialization, publication, and validator "
            "processing are outside this benchmark."
        ),
    }
    write_csv(RESULTS / "object-benchmarks.csv", rows)
    write_json(RESULTS / "object-benchmarks.json", {"metadata": metadata, "results": rows})
    (RESULTS / "object-benchmarks.md").write_text(
        "# Object-Level Payload Benchmark\n\n"
        "> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        + metadata["method"] + "\n\n"
        + markdown_table(rows, [(key, key.replace("_", " ").title()) for key in rows[0]]) + "\n"
    )


if __name__ == "__main__":
    main()
