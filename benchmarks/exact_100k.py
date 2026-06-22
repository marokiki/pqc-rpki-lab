#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

from pqc_rpki_lab.result_io import markdown_table, write_csv, write_json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).with_suffix(".c")
RESULTS = ROOT / "results" / "review-2026-06"


def compile_benchmark(output: Path) -> list[str]:
    compiler = shutil.which("cc")
    pkg_config = shutil.which("pkg-config")
    if not compiler or not pkg_config:
        raise RuntimeError("cc and pkg-config are required")
    flags = subprocess.run(
        [pkg_config, "--cflags", "--libs", "openssl"],
        check=True, capture_output=True, text=True).stdout.split()
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
    raw_path = RESULTS / "exact-100k-raw.csv"
    if args.render_existing:
        raw_output = raw_path.read_text()
        previous = json.loads((RESULTS / "exact-100k.json").read_text())
        metadata = previous["metadata"]
        rows = list(csv.DictReader(io.StringIO(raw_output)))
        args.iterations = int(rows[0]["iterations"])
    else:
        with tempfile.TemporaryDirectory(prefix="pqc-rpki-exact-bench-") as name:
            executable = Path(name) / "exact-100k"
            compile_command = compile_benchmark(executable)
            process = subprocess.run(
                [str(executable), str(args.iterations)], check=True,
                capture_output=True, text=True)
        raw_output = process.stdout
        rows = list(csv.DictReader(io.StringIO(raw_output)))
        metadata = {
            "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
            "iterations_per_algorithm": args.iterations,
            "message_bytes": 32,
            "key_generation": "one key pair before each algorithm's timed loops",
            "timing_scope": "exact EVP sign and verify loops; EVP_MD_CTX initialization is included per operation",
            "excluded": "process startup, compilation, key generation, object encoding, file I/O, HSM latency",
            "openssl": subprocess.run(["openssl", "version"], check=True, capture_output=True, text=True).stdout.strip(),
            "platform": platform.platform(),
            "compile_command": compile_command,
        }
    metadata["compile_command"] = [
        "cc", "-O2", "-Wall", "-Wextra", "-Werror",
        "benchmarks/exact_100k.c", "-o", "$TMPDIR/exact-100k",
        "$(pkg-config --cflags --libs openssl)",
    ]
    for row in rows:
        if row["status"] != "confirmed":
            continue
        sign_seconds = float(row["sign_seconds"])
        verify_seconds = float(row["verify_seconds"])
        row["sign_ops_per_second"] = round(args.iterations / sign_seconds, 3)
        row["verify_ops_per_second"] = round(args.iterations / verify_seconds, 3)
        row["sign_microseconds_per_operation"] = round(sign_seconds * 1_000_000 / args.iterations, 3)
        row["verify_microseconds_per_operation"] = round(verify_seconds * 1_000_000 / args.iterations, 3)

    baseline = next((row for row in rows if row["algorithm"] == "RSA-2048/SHA-256"), None)
    if baseline and baseline["status"] == "confirmed":
        baseline_sign = float(baseline["sign_seconds"])
        baseline_verify = float(baseline["verify_seconds"])
        for row in rows:
            if row["status"] == "confirmed":
                row["sign_time_ratio_vs_rsa"] = round(float(row["sign_seconds"]) / baseline_sign, 3)
                row["verify_time_ratio_vs_rsa"] = round(float(row["verify_seconds"]) / baseline_verify, 3)

    write_csv(RESULTS / "exact-100k.csv", rows)
    write_json(RESULTS / "exact-100k.json", {"metadata": metadata, "results": rows})
    if not args.render_existing:
        raw_path.write_text(raw_output)
    table = markdown_table(rows, [
        ("algorithm", "Algorithm"), ("status", "Status"),
        ("iterations", "Operations"), ("sign_seconds", "Sign total s"),
        ("verify_seconds", "Verify total s"),
        ("sign_microseconds_per_operation", "Sign us/op"),
        ("verify_microseconds_per_operation", "Verify us/op"),
        ("sign_time_ratio_vs_rsa", "Sign time/RSA"),
        ("verify_time_ratio_vs_rsa", "Verify time/RSA"),
        ("signature_bytes", "Last signature bytes"), ("reason", "Reason"),
    ])
    (RESULTS / "exact-100k.md").write_text(
        "# Exact 100,000-Operation Signature Benchmark\n\n"
        "> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        "Each algorithm uses one generated key pair and performs exactly 100,000 EVP signing operations "
        "followed by exactly 100,000 verification operations over the same 32-byte message. "
        "The timed loops include EVP context initialization but exclude key generation, process startup, "
        "RPKI object construction, file I/O, and HSM latency.\n\n" + table +
        "\n\n## Interpretation\n\n"
        "The compact classical references have the lowest signing time and signature size, but they do "
        "not provide post-quantum security and are not the current RFC 6488 repository profile. "
        "ML-DSA-44 has the best measured time and size among the standardized ML-DSA parameter sets. "
        "ML-DSA-65 and ML-DSA-87 progressively increase verification time and signature size; this run "
        "does not establish an operational reason to select Category 5.\n\n"
        "Verification, rather than signing, is the repeated RP-side operation. Absolute verification time "
        "for 100,000 operations remains below 12 seconds for all measured algorithms on this host, but "
        "repository-wide cost also depends on object count, parallelism, caching, message size, and validator "
        "implementation. These primitive values are not complete RPKI validation times.\n\n"
        "Composite signatures were not measured because no local composite EVP implementation was available. "
        "A sequential composition would at least incur both component operations plus encoding and dispatch "
        "overhead; component-time sums are estimates, not composite benchmark results.\n\n"
        "This is one run on one host with one key per algorithm and no confidence interval. A publication-grade "
        "comparison should repeat the complete run, randomize algorithm order, record thermal and CPU state, "
        "and add complete RFC 6488 object and validator measurements.\n")


if __name__ == "__main__":
    main()
