#!/usr/bin/env python3
"""Measure fresh-key generation with the E2E OpenSSL/provider configuration."""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import time
from pathlib import Path

from pqc_rpki_lab.workspace import reset_generated_directory

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULT = ROOT / "results" / "composite-e2e" / "keygen-summary.json"
DEFAULT_RAW = ROOT / "local" / "measurements" / "keygen"
ALGORITHMS = {
    "rsa-2048": ["RSA", "-pkeyopt", "rsa_keygen_bits:2048"],
    "pure-mldsa65": ["ML-DSA-65"],
    "composite-mldsa65-p256": ["MLDSA65-ECDSA-P256-SHA512"],
}


def summarize(samples: list[float]) -> dict[str, float]:
    return {
        "median": statistics.median(samples),
        "stdev": statistics.stdev(samples),
        "min": min(samples),
        "max": max(samples),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--openssl", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=1000)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    args = parser.parse_args()
    if args.repetitions < 2:
        raise SystemExit("at least two repetitions are required")

    raw = reset_generated_directory(
        args.raw.resolve(), allowed_root=ROOT / "local"
    )
    results: dict[str, dict[str, float]] = {}
    raw_results: dict[str, list[float]] = {}
    for name, algorithm in ALGORITHMS.items():
        samples = []
        for _ in range(args.repetitions):
            started = time.perf_counter_ns()
            process = subprocess.run(
                [
                    str(args.openssl.resolve()), "genpkey", "-algorithm",
                    *algorithm, "-out", "/dev/null",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            elapsed = (time.perf_counter_ns() - started) / 1_000_000_000
            if process.returncode:
                raise RuntimeError(f"{name}: {process.stderr.strip()}")
            samples.append(elapsed)
        raw_results[name] = samples
        results[name] = summarize(samples)

    (raw / "samples.json").write_text(
        json.dumps(raw_results, indent=2, sort_keys=True) + "\n"
    )
    summary = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "classification": (
            "fresh-key generation subprocess benchmark; not signing, "
            "verification, repository, RRDP, or rsync performance"
        ),
        "repetitions_per_algorithm": args.repetitions,
        "timing_scope": (
            "one OpenSSL genpkey subprocess per sample, including process and "
            "provider startup"
        ),
        "seconds": results,
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
