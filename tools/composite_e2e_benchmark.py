#!/usr/bin/env python3
"""Run repeated small-scale RPKI generation and validation measurements."""

from __future__ import annotations

import argparse
import csv
import json
import os
import resource
import shutil
import statistics
import subprocess
import time
from pathlib import Path

from pqc_rpki_lab.workspace import reset_generated_directory

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "local" / "measurements" / "composite-e2e"
RESULTS = ROOT / "results" / "composite-e2e"
TIME_PREFIX = "__PQC_TIME__"


def timed(command: list[str], env: dict[str, str]) -> dict[str, object]:
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = time.perf_counter_ns()
    process = subprocess.run(
        [
            "/usr/bin/time", "-f",
            f"{TIME_PREFIX},%e,%U,%S,%M",
            *command,
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    elapsed = (time.perf_counter_ns() - started) / 1_000_000_000
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    timing = None
    stderr_lines = []
    for line in process.stderr.splitlines():
        if line.startswith(f"{TIME_PREFIX},"):
            _, _wall, _user, _system, rss = line.split(",")
            user = after.ru_utime - before.ru_utime
            system = after.ru_stime - before.ru_stime
            timing = {
                "wall_seconds": elapsed,
                "user_seconds": user,
                "system_seconds": system,
                "cpu_seconds": user + system,
                "max_rss_kib": int(rss),
            }
        else:
            stderr_lines.append(line)
    if timing is None:
        raise RuntimeError(f"missing time output: {process.stderr}")
    timing.update(
        {
            "returncode": process.returncode,
            "stdout": process.stdout,
            "stderr": "\n".join(stderr_lines),
        }
    )
    return timing


def stats(values: list[float | int]) -> dict[str, float]:
    return {
        "median": statistics.median(values),
        "stdev": statistics.stdev(values),
        "min": min(values),
        "max": max(values),
    }


def summarize(
    rows: list[dict[str, object]],
    fields: tuple[str, ...] = ("wall_seconds", "cpu_seconds", "max_rss_kib"),
) -> dict[str, object]:
    return {
        field: stats([row[field] for row in rows])
        for field in fields
    }


def cache_fixture(source: Path, cache: Path, *, certificate: str) -> None:
    if cache.exists():
        shutil.rmtree(cache)
    repository = cache / "example.invalid:8873" / "repository"
    tal = cache / "ta" / "test"
    repository.mkdir(parents=True)
    tal.mkdir(parents=True)
    shutil.copytree(source / "repository", repository, dirs_exist_ok=True)
    shutil.copyfile(source / "repository" / certificate, tal / certificate)


def cache_mixed(source: Path, cache: Path) -> None:
    if cache.exists():
        shutil.rmtree(cache)
    repository = cache / "example.invalid" / "repository"
    tal = cache / "ta" / "test"
    repository.mkdir(parents=True)
    tal.mkdir(parents=True)
    shutil.copytree(source / "repository", repository, dirs_exist_ok=True)
    shutil.copyfile(source / "repository" / "ta.cer", tal / "ta.cer")


def fixture_sizes(path: Path) -> dict[str, int]:
    return {
        str(item.relative_to(path)): item.stat().st_size
        for item in sorted(path.rglob("*"))
        if item.is_file()
    }


def standalone_product_total(path: Path) -> int:
    return sum(
        (path / name).stat().st_size
        for name in ("ca.cer", "ca.crl", "route.roa", "manifest.mft")
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generation-repetitions", type=int, default=100)
    parser.add_argument("--validation-repetitions", type=int, default=1000)
    parser.add_argument("--openssl", required=True)
    parser.add_argument("--baseline-rpki-client", required=True)
    parser.add_argument("--patched-rpki-client", required=True)
    args = parser.parse_args()
    if args.generation_repetitions < 2 or args.validation_repetitions < 2:
        raise SystemExit("at least two repetitions are required for each phase")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")

    reset_generated_directory(LOCAL, allowed_root=ROOT / "local")
    RESULTS.mkdir(parents=True, exist_ok=True)

    generation_specs = {
        "rsa-baseline": ("rsa", "rsa"),
        "pure-mldsa65": ("ml-dsa-65", "ml-dsa-65"),
        "composite-standalone": (
            "composite-mldsa65-p256",
            "composite-mldsa65-p256",
        ),
    }
    raw: list[dict[str, object]] = []
    generation_rows: dict[str, list[dict[str, object]]] = {}
    for scenario, (algorithm, slug) in generation_specs.items():
        command = [
            "python3", str(ROOT / "tools" / "generate_rpki_objects.py"),
            "--algorithm", algorithm, "--output-root", str(LOCAL / "standalone"),
            "--openssl", args.openssl,
        ]
        rows = []
        for repetition in range(1, args.generation_repetitions + 1):
            result = timed(command, env)
            if result["returncode"] != 0:
                raise RuntimeError(f"{scenario} generation failed: {result}")
            row = {
                "phase": "generation",
                "scenario": scenario,
                "repetition": repetition,
                **{key: result[key] for key in (
                    "wall_seconds", "cpu_seconds", "max_rss_kib"
                )},
                "artifact_total_bytes": standalone_product_total(
                    LOCAL / "standalone" / "testdata" / slug
                ),
            }
            rows.append(row)
            raw.append(row)
        generation_rows[scenario] = rows

    mixed_rows = []
    for repetition in range(1, args.generation_repetitions + 1):
        output = LOCAL / "generated" / f"mixed-{repetition:02d}"
        summary = LOCAL / "generated" / f"mixed-{repetition:02d}.json"
        result = timed(
            [
                "python3", str(ROOT / "tools" / "composite_e2e.py"),
                "--openssl", args.openssl, "--output", str(output),
                "--summary", str(summary),
            ],
            env,
        )
        if result["returncode"] != 0:
            raise RuntimeError(f"mixed generation failed: {result}")
        row = {
            "phase": "generation",
            "scenario": "rsa-to-composite-mixed",
            "repetition": repetition,
            **{key: result[key] for key in (
                "wall_seconds", "cpu_seconds", "max_rss_kib"
            )},
            "artifact_total_bytes": sum(
                fixture_sizes(output / "repository").values()
            ),
        }
        mixed_rows.append(row)
        raw.append(row)
    generation_rows["rsa-to-composite-mixed"] = mixed_rows

    validation_specs = {
        "rsa-baseline": {
            "fixture": LOCAL / "standalone" / "testdata" / "validator" / "rsa",
            "binary": args.baseline_rpki_client,
            "flags": [],
            "certificate": "ca.cer",
            "expected_vrps": 2,
        },
        "pure-mldsa65": {
            "fixture": LOCAL / "standalone" / "testdata" / "validator"
            / "ml-dsa-65",
            "binary": args.patched_rpki_client,
            "flags": ["-x"],
            "certificate": "ca.cer",
            "expected_vrps": 0,
        },
        "composite-standalone": {
            "fixture": LOCAL / "standalone" / "testdata" / "validator"
            / "composite-mldsa65-p256",
            "binary": args.patched_rpki_client,
            "flags": ["-x"],
            "certificate": "ca.cer",
            "expected_vrps": 2,
        },
        "rsa-to-composite-mixed": {
            "fixture": ROOT / "local" / "e2e" / "current",
            "binary": args.patched_rpki_client,
            "flags": ["-x"],
            "certificate": "ta.cer",
            "expected_vrps": 2,
        },
    }
    validation_rows: dict[str, list[dict[str, object]]] = {}
    vrp_observations: dict[str, list[int]] = {}
    for scenario, spec in validation_specs.items():
        cache = LOCAL / "cache" / scenario
        if scenario == "rsa-to-composite-mixed":
            cache_mixed(spec["fixture"], cache)
        else:
            cache_fixture(
                spec["fixture"], cache, certificate=str(spec["certificate"])
            )
        rows = []
        observed_vrps = []
        for repetition in range(1, args.validation_repetitions + 1):
            output = LOCAL / "validation-output" / scenario / f"{repetition:02d}"
            output.mkdir(parents=True)
            result = timed(
                [
                    str(spec["binary"]), *spec["flags"], "-n", "-d", str(cache),
                    "-t", str(spec["fixture"] / "test.tal"), "-j", "-c",
                    str(output),
                ],
                env,
            )
            if result["returncode"] != 0:
                raise RuntimeError(f"{scenario} validation failed: {result}")
            metadata = json.loads((output / "json").read_text())["metadata"]
            vrps = int(metadata["vrps"])
            observed_vrps.append(vrps)
            row = {
                "phase": "validation",
                "scenario": scenario,
                "repetition": repetition,
                **{key: result[key] for key in (
                    "wall_seconds", "cpu_seconds", "max_rss_kib"
                )},
            }
            rows.append(row)
            raw.append(row)
        if set(observed_vrps) != {spec["expected_vrps"]}:
            raise RuntimeError(
                f"{scenario}: unexpected VRP counts {observed_vrps}"
            )
        validation_rows[scenario] = rows
        vrp_observations[scenario] = observed_vrps

    sizes = {
        "rsa-baseline": fixture_sizes(LOCAL / "standalone" / "testdata" / "rsa"),
        "pure-mldsa65": fixture_sizes(
            LOCAL / "standalone" / "testdata" / "ml-dsa-65"
        ),
        "composite-standalone": fixture_sizes(
            LOCAL / "standalone" / "testdata" / "composite-mldsa65-p256"
        ),
        "rsa-to-composite-mixed": fixture_sizes(
            ROOT / "local" / "e2e" / "current" / "repository"
        ),
    }
    summary = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "classification": (
            "repeated small-scale E2E measurement; not real-repository, "
            "RRDP, or rsync performance"
        ),
        "generation_repetitions": args.generation_repetitions,
        "validation_repetitions": args.validation_repetitions,
        "generation": {
            scenario: summarize(
                rows,
                (
                    "wall_seconds",
                    "cpu_seconds",
                    "max_rss_kib",
                    "artifact_total_bytes",
                ),
            )
            for scenario, rows in generation_rows.items()
        },
        "validation": {
            scenario: summarize(rows)
            for scenario, rows in validation_rows.items()
        },
        "artifact_sizes_bytes": sizes,
        "artifact_total_scope": {
            "standalone": "CA certificate, CRL, ROA, and manifest",
            "rsa-to-composite-mixed": (
                "all seven products across the parent and child publication points"
            ),
        },
        "vrp_counts": {
            scenario: sorted(set(values))
            for scenario, values in vrp_observations.items()
        },
        "pure_mldsa65_note": (
            "Generated and measured, but rejected by the RP because this "
            "experimental patch intentionally enables only the Composite suite."
        ),
        "timing_method": {
            "wall": "Python time.perf_counter_ns around each child process",
            "cpu": "RUSAGE_CHILDREN user plus system delta",
            "max_rss": "GNU time %M for each child process",
        },
        "fixture_lifetime": (
            "Standalone fixtures are generated inside the same benchmark run; "
            "the mixed-tree fixture is generated immediately before this target."
        ),
    }
    (LOCAL / "raw.json").write_text(
        json.dumps(raw, indent=2, sort_keys=True) + "\n"
    )
    with (LOCAL / "raw.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(raw[0]))
        writer.writeheader()
        writer.writerows(raw)
    (RESULTS / "benchmark-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
