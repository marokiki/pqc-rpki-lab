#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

from pqc_rpki_lab.result_io import markdown_table, write_csv, write_json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).with_suffix(".c")
RESULTS = ROOT / "results" / "review-2026-06"
OQS_PREFIX = ROOT / ".local" / "oqs"


def compile_benchmark(output: Path) -> list[str]:
    compiler = shutil.which("cc")
    pkg_config = shutil.which("pkg-config")
    if not compiler or not pkg_config or not OQS_PREFIX.exists():
        raise RuntimeError("cc, pkg-config, and repository-local liboqs are required")
    flags = subprocess.run(
        [pkg_config, "--cflags", "--libs", "openssl"],
        check=True, capture_output=True, text=True).stdout.split()
    flags.extend([f"-I{OQS_PREFIX / 'include'}", f"-L{OQS_PREFIX / 'lib'}", "-loqs"])
    command = [compiler, "-O2", "-Wall", "-Wextra", "-Werror", str(SOURCE), "-o", str(output), *flags]
    subprocess.run(command, check=True)
    return command


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=100_000)
    parser.add_argument("--render-existing", action="store_true")
    args = parser.parse_args()
    if args.iterations <= 0:
        parser.error("--iterations must be positive")

    RESULTS.mkdir(parents=True, exist_ok=True)
    raw_path = RESULTS / "composite-100k-raw.csv"
    if args.render_existing:
        raw_output = raw_path.read_text()
        previous = json.loads((RESULTS / "composite-100k.json").read_text())
        metadata = previous["metadata"]
        rows = list(csv.DictReader(io.StringIO(raw_output)))
        args.iterations = int(rows[0]["iterations"])
    else:
        with tempfile.TemporaryDirectory(prefix="pqc-rpki-composite-bench-") as name:
            executable = Path(name) / "composite-100k"
            compile_command = compile_benchmark(executable)
            environment = os.environ.copy()
            library_path = str(OQS_PREFIX / "lib")
            environment["DYLD_LIBRARY_PATH"] = library_path + (
                ":" + environment["DYLD_LIBRARY_PATH"] if environment.get("DYLD_LIBRARY_PATH") else "")
            environment["LD_LIBRARY_PATH"] = library_path + (
                ":" + environment["LD_LIBRARY_PATH"] if environment.get("LD_LIBRARY_PATH") else "")
            process = subprocess.run(
                [str(executable), str(args.iterations)], check=True,
                capture_output=True, text=True, env=environment)
        raw_output = process.stdout
        rows = list(csv.DictReader(io.StringIO(raw_output)))
        metadata = {
            "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
            "classification": "sequential component-operation benchmark, not a LAMPS composite encoding",
            "verification_policy": "both component signatures must verify",
            "iterations_per_combination": args.iterations,
            "message_bytes": 32,
            "timing_scope": "sequential component signing and verification in one process",
            "excluded": "composite OID/ASN.1 encoding, domain separation, CMS/X.509, file I/O, HSM latency",
            "openssl": subprocess.run(["openssl", "version"], check=True, capture_output=True, text=True).stdout.strip(),
            "liboqs": "0.15.0",
            "platform": platform.platform(),
            "compile_command": compile_command,
        }
    metadata["compile_command"] = [
        "cc", "-O2", "-Wall", "-Wextra", "-Werror",
        "benchmarks/composite_100k.c", "-o", "$TMPDIR/composite-100k",
        "$(pkg-config --cflags --libs openssl)",
        "-I.local/oqs/include", "-L.local/oqs/lib", "-loqs",
    ]

    exact = json.loads((RESULTS / "exact-100k.json").read_text())["results"]
    mldsa65 = next(row for row in exact if row["algorithm"] == "ML-DSA-65")
    baseline_sign = float(mldsa65["sign_seconds"])
    baseline_verify = float(mldsa65["verify_seconds"])
    baseline_bytes = int(mldsa65["signature_bytes"])
    for row in rows:
        if row["status"] != "confirmed":
            continue
        iterations = int(row["iterations"])
        sign_seconds = float(row["sign_seconds"])
        verify_seconds = float(row["verify_seconds"])
        row["sign_microseconds_per_operation"] = round(sign_seconds * 1_000_000 / iterations, 3)
        row["verify_microseconds_per_operation"] = round(verify_seconds * 1_000_000 / iterations, 3)
        row["sign_ops_per_second"] = round(iterations / sign_seconds, 3)
        row["verify_ops_per_second"] = round(iterations / verify_seconds, 3)
        row["sign_time_ratio_vs_mldsa65"] = round(sign_seconds / baseline_sign, 3)
        row["verify_time_ratio_vs_mldsa65"] = round(verify_seconds / baseline_verify, 3)
        row["signature_bytes_ratio_vs_mldsa65"] = round(
            int(row["combined_signature_bytes"]) / baseline_bytes, 3)

    write_csv(RESULTS / "composite-100k.csv", rows)
    write_json(RESULTS / "composite-100k.json", {"metadata": metadata, "results": rows})
    if not args.render_existing:
        raw_path.write_text(raw_output)
    table = markdown_table(rows, [
        ("algorithm", "Combination"), ("status", "Status"),
        ("iterations", "Operations"), ("sign_seconds", "Sign total s"),
        ("verify_seconds", "Verify total s"),
        ("sign_microseconds_per_operation", "Sign us/op"),
        ("verify_microseconds_per_operation", "Verify us/op"),
        ("combined_signature_bytes", "Component bytes"),
        ("sign_time_ratio_vs_mldsa65", "Sign time/ML-DSA-65"),
        ("verify_time_ratio_vs_mldsa65", "Verify time/ML-DSA-65"),
        ("signature_bytes_ratio_vs_mldsa65", "Bytes/ML-DSA-65"),
        ("reason", "Reason"),
    ])
    (RESULTS / "composite-100k.md").write_text(
        "# Exact 100,000-Operation Composite Component Benchmark\n\n"
        "> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        "Each operation signs the same 32-byte message with both components sequentially. "
        "Verification succeeds only when both component signatures verify. The byte count is the sum of "
        "the largest component signatures observed and excludes composite ASN.1 encoding. This is not an "
        "implementation of the LAMPS composite signature format.\n\n" + table +
        "\n\n## Interpretation\n\n"
        "P-256+Falcon-512 has the smallest component-signature total, but Falcon signing dominates "
        "its runtime. Within each ML-DSA parameter set, replacing RSA-2048 with P-256 reduces component "
        "key and signature bytes and reduces signing time, while RSA-2048 provides faster verification "
        "in this implementation. Larger ML-DSA parameter sets progressively increase both runtime and "
        "size. No measured combination dominates all others in signing time, verification time, and "
        "size simultaneously.\n\n"
        "The repository estimator remains separate because certificates contain public keys as well as "
        "signatures. Its conservative size model uses standardized maximum component sizes and adds no "
        "composite ASN.1 overhead.\n")


if __name__ == "__main__":
    main()
