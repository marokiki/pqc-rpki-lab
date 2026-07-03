#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

from pqc_rpki_lab.result_io import markdown_table, write_csv, write_json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "key-roll"
RPKI_OBJECTS = ROOT / "results" / "rpki-objects" / "rpki-objects.csv"


def read_rows() -> list[dict[str, str]]:
    if not RPKI_OBJECTS.exists():
        return []
    with RPKI_OBJECTS.open(newline="") as handle:
        return list(csv.DictReader(handle))


def size_for(rows: list[dict[str, str]], algorithm: str, artifact: str) -> int:
    for row in rows:
        if row["algorithm"] == algorithm and row["artifact"] == artifact and row["bytes"]:
            return int(row["bytes"])
    return 0


def benchmark_row(algorithm: str, rows: list[dict[str, str]], child_cas: int, roas: int, manifests: int, aspas: int, rscs: int, taks: int) -> dict[str, object]:
    start = time.perf_counter_ns()
    ca_cert = size_for(rows, algorithm, "CA certificate")
    ee_cert = size_for(rows, algorithm, "EE certificate")
    crl = size_for(rows, algorithm, "CRL")
    roa = size_for(rows, algorithm, "ROA CMS") or (size_for(rows, algorithm, "ROA eContent") + ee_cert)
    mft = size_for(rows, algorithm, "Manifest CMS") or (size_for(rows, algorithm, "Manifest eContent") + ee_cert)
    synthetic_other = ee_cert + size_for(rows, algorithm, "ROA eContent")
    files = child_cas + 1 + roas + manifests + aspas + rscs + taks
    bytes_total = (
        child_cas * ca_cert
        + crl
        + manifests * mft
        + roas * (ee_cert + roa)
        + aspas * synthetic_other
        + rscs * synthetic_other
        + taks * synthetic_other
    )
    elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
    return {
        "algorithm": algorithm,
        "status": "estimated" if not (roa and mft and ca_cert and ee_cert and crl) else "confirmed-model",
        "child_cas": child_cas,
        "roas": roas,
        "manifests": manifests,
        "aspas": aspas,
        "rscs": rscs,
        "taks": taks,
        "file_count": files,
        "output_bytes": bytes_total,
        "rrdp_snapshot_bytes": round(bytes_total * 1.12),
        "rrdp_delta_bytes": round(bytes_total * 1.12 * 0.10),
        "rsync_transfer_bytes": bytes_total,
        "model_runtime_ms": round(elapsed_ms, 6),
        "classification": "synthetic key-roll model using measured fixture sizes where available",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child-cas", type=int, default=10)
    parser.add_argument("--roas", type=int, default=100)
    parser.add_argument("--manifests", type=int, default=1)
    parser.add_argument("--aspas", type=int, default=0)
    parser.add_argument("--rscs", type=int, default=0)
    parser.add_argument("--taks", type=int, default=0)
    args = parser.parse_args()
    rows = read_rows()
    algorithms = sorted({row["algorithm"] for row in rows}) or ["RSA-2048/SHA-256"]
    output = [
        benchmark_row(algorithm, rows, args.child_cas, args.roas, args.manifests, args.aspas, args.rscs, args.taks)
        for algorithm in algorithms
    ]
    write_csv(RESULTS / "key-roll.csv", output)
    write_json(RESULTS / "key-roll.json", {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "model": "synthetic configurable key-roll model; not production accuracy",
        "results": output,
    })
    (RESULTS / "key-roll.md").write_text(
        "# Synthetic CA Key-Roll Benchmark\n\n"
        "> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        "This model uses measured public fixture sizes where available and estimates "
        "transport bytes. It does not claim production CA, RRDP, rsync, or HSM behavior.\n\n"
        + markdown_table(output, [
            ("algorithm", "Algorithm"), ("status", "Status"), ("file_count", "Files"),
            ("output_bytes", "Output bytes"), ("rrdp_snapshot_bytes", "RRDP snapshot"),
            ("rrdp_delta_bytes", "RRDP delta"), ("rsync_transfer_bytes", "rsync bytes"),
            ("classification", "Classification"),
        ]) + "\n"
    )


if __name__ == "__main__":
    main()
