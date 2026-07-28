#!/usr/bin/env python3
"""Run resumable Krill generation and RP validation repetition campaigns."""

from __future__ import annotations

import argparse
import gzip
import json
import os
import platform
import re
import statistics
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from summarize_scaled_krill import parse_time
DEFAULT_WORK = ROOT / "local" / "krill-scale-campaign"
DEFAULT_RESULT = (
    ROOT / "results" / "scaled-corpus"
    / "krill-repeated-summary.json"
)
DEFAULT_COUNTS = "1:30,10:30,100:30,1000:10"


def parse_counts(value: str) -> list[tuple[int, int]]:
    result = []
    for item in value.split(","):
        try:
            count_text, repetitions_text = item.split(":", 1)
            count, repetitions = int(count_text), int(repetitions_text)
        except ValueError as error:
            raise argparse.ArgumentTypeError(
                "counts must use ROAs:REPETITIONS comma-separated form"
            ) from error
        if count < 1 or repetitions < 1:
            raise argparse.ArgumentTypeError("counts must be positive")
        result.append((count, repetitions))
    if len({count for count, _ in result}) != len(result):
        raise argparse.ArgumentTypeError("ROA counts must be unique")
    return result


def summary(values: list[float | int]) -> dict[str, float | int]:
    if not values:
        raise ValueError("cannot summarize an empty sample")
    return {
        "samples": len(values),
        "median": statistics.median(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
    }


def time_summary(rows: list[dict[str, int | float]]) -> dict[str, object]:
    fields = ("wall_seconds", "user_seconds", "system_seconds", "max_rss_kib")
    return {field: summary([row[field] for row in rows]) for field in fields}


def run_checked(command: list[str], env: dict[str, str], log: Path) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w") as output:
        process = subprocess.run(
            command,
            env=env,
            stdout=output,
            stderr=subprocess.STDOUT,
            text=True,
        )
    if process.returncode:
        raise RuntimeError(
            f"command failed ({process.returncode}); see {log}"
        )


def generate(
    count: int,
    repetition: int,
    env: dict[str, str],
    work: Path,
) -> Path:
    run_id = f"campaign-{count:06d}-{repetition:04d}"
    scaled = ROOT / "local" / "krill-scaled" / run_id
    marker = work / f"roas-{count}" / "generation" / f"{repetition:04d}.json"
    if marker.is_file() and scaled.is_dir():
        return scaled
    run_env = env.copy()
    run_env.update(
        {
            "PQC_RPKI_KRILL_ROA_COUNT": str(count),
            "PQC_RPKI_KRILL_RUN_ID": run_id,
            "PQC_RPKI_KRILL_RUN_RELIABILITY": "0",
            "PQC_RPKI_KRILL_SUMMARY_OUTPUT": str(marker),
        }
    )
    run_checked(
        [str(ROOT / "tools" / "run_krill_scaled_experimental.sh")],
        run_env,
        work / f"roas-{count}" / "generation" / f"{repetition:04d}.log",
    )
    return scaled


def validate(
    count: int,
    repetition: int,
    scaled: Path,
    env: dict[str, str],
    work: Path,
    rpki_client: Path,
    routinator: Path,
) -> tuple[Path, Path]:
    target = work / f"roas-{count}" / "validation" / f"{repetition:04d}"
    result = target / "validation.json"
    timing = target / "validation.time"
    if result.is_file() and timing.is_file():
        return result, timing
    target.mkdir(parents=True, exist_ok=True)
    command = [
        "/usr/bin/time",
        "-v",
        "-o",
        str(timing),
        "python3",
        str(ROOT / "tools" / "krill_experimental_validate.py"),
        "--krill-output",
        str(scaled / "repository"),
        "--rpki-client",
        str(rpki_client),
        "--routinator",
        str(routinator),
        "--work",
        str(target / "work"),
        "--result",
        str(result),
        "--port",
        str(23873 + (repetition % 1000) * 2),
        "--expected-vrp-count",
        str(count),
    ]
    run_checked(command, env, target / "validation.log")
    return result, timing


def transport(repo: Path) -> dict[str, object]:
    rsync = repo / "rsync" / "current"
    files = [path for path in rsync.rglob("*") if path.is_file()]
    by_type = Counter(path.suffix.removeprefix(".") for path in files)
    rrdp = {}
    for name in ("notification.xml", "snapshot.xml", "delta.xml"):
        payloads = [
            path.read_bytes() for path in (repo / "rrdp").rglob(name)
        ]
        rrdp[name.removesuffix(".xml")] = {
            "file_count": len(payloads),
            "uncompressed_bytes": sum(map(len, payloads)),
            "gzip_bytes": sum(
                len(gzip.compress(payload, mtime=0)) for payload in payloads
            ),
        }
    return {
        "rsync": {
            "file_count": len(files),
            "bytes": sum(path.stat().st_size for path in files),
            "object_type_counts": dict(sorted(by_type.items())),
        },
        "rrdp": rrdp,
    }


def command_text(command: list[str], env: dict[str, str]) -> str:
    process = subprocess.run(
        command, env=env, capture_output=True, text=True, check=True
    )
    return (process.stdout or process.stderr).strip().splitlines()[0]


def environment_summary(
    env: dict[str, str],
    build: Path,
    rpki_client: Path,
    routinator: Path,
) -> dict[str, object]:
    cpu_model = "unknown"
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.is_file():
        for line in cpuinfo.read_text().splitlines():
            if line.startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()
                break
    memory_total_kib = 0
    meminfo = Path("/proc/meminfo")
    if meminfo.is_file():
        for line in meminfo.read_text().splitlines():
            if line.startswith("MemTotal:"):
                memory_total_kib = int(line.split()[1])
                break
    return {
        "system": platform.system(),
        "kernel": platform.release(),
        "machine": platform.machine(),
        "cpu_model": cpu_model,
        "logical_cpu_count": os.cpu_count(),
        "memory_total_kib": memory_total_kib,
        "openssl": command_text(
            [
                str(build / "openssl-3.6.2-install" / "bin" / "openssl"),
                "version",
            ],
            env,
        ),
        "rpki_client": command_text([str(rpki_client), "-V"], env),
        "routinator": command_text([str(routinator), "--version"], env),
        "krill_commit": command_text(
            [
                "git",
                "-C",
                str(ROOT / "local" / "upstream" / "krill"),
                "rev-parse",
                "HEAD",
            ],
            env,
        ),
        "routinator_commit": command_text(
            [
                "git",
                "-C",
                str(ROOT / "local" / "upstream" / "routinator"),
                "rev-parse",
                "HEAD",
            ],
            env,
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--counts", type=parse_counts, default=parse_counts(DEFAULT_COUNTS))
    parser.add_argument("--validation-repetitions", type=int, default=100)
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    args = parser.parse_args()
    if args.validation_repetitions < 1:
        raise SystemExit("--validation-repetitions must be positive")

    build = ROOT / "local" / "build"
    rpki_client = build / "rpki-client-composite" / "src" / "rpki-client"
    routinator = (
        ROOT / "local" / "upstream" / "routinator"
        / "target" / "debug" / "routinator"
    )
    for path in (rpki_client, routinator):
        if not path.is_file():
            raise SystemExit(f"required executable is missing: {path}")
    env = os.environ.copy()
    env.update(
        {
            "LD_LIBRARY_PATH": str(
                build / "openssl-3.6.2-install" / "lib64"
            ),
            "OPENSSL_CONF": str(ROOT / "experiments/openssl-composite.cnf"),
            "PQC_COMPOSITE_PROVIDER_MODULE": str(
                build / "composite-provider" / "composite.so"
            ),
            "PYTHONPATH": str(ROOT / "src"),
        }
    )
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    rows = []
    for count, generation_repetitions in args.counts:
        generated = [
            generate(count, repetition, env, work)
            for repetition in range(1, generation_repetitions + 1)
        ]
        validation_files = [
            validate(
                count,
                repetition,
                generated[-1],
                env,
                work,
                rpki_client,
                routinator,
            )
            for repetition in range(1, args.validation_repetitions + 1)
        ]
        validations = [json.loads(path.read_text()) for path, _ in validation_files]
        if not all(item["success"] for item in validations):
            raise RuntimeError(f"validation failure in {count}-ROA campaign")
        generation_times = [
            parse_time(path / "generation.time") for path in generated
        ]
        validation_times = [
            parse_time(path) for _, path in validation_files
        ]
        repo = generated[-1] / "repository" / "composite" / "state" / "repo"
        rows.append(
            {
                "roa_count": count,
                "vrp_count": count,
                "generation_repetitions": generation_repetitions,
                "validation_repetitions": args.validation_repetitions,
                "generation": time_summary(generation_times),
                "validation_matrix": time_summary(validation_times),
                "transport": transport(repo),
                "all_validations_succeeded": True,
            }
        )

    document = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "classification": (
            "single-parent, single-child, single-publication-point repeated "
            "Krill generation and fresh-validator-cache validation; not a "
            "real-repository, warm-cache, incremental, or network benchmark"
        ),
        "campaign": {
            "generation_schedule": [
                {"roa_count": count, "repetitions": repetitions}
                for count, repetitions in args.counts
            ],
            "validation_repetitions_per_size": args.validation_repetitions,
            "validation_matrix_per_repetition": (
                "Composite and RSA rollback, rpki-client and Routinator, "
                "default and experimental modes"
            ),
            "primitive_measurements_are_separate": (
                "short cryptographic primitives use the existing 100000-"
                "operation campaign and are not mixed into these E2E results"
            ),
        },
        "environment": environment_summary(
            env, build, rpki_client, routinator
        ),
        "results": rows,
        "contains_private_keys": False,
        "contains_raw_objects": False,
        "contains_absolute_paths": False,
    }
    text = json.dumps(document, indent=2, sort_keys=True) + "\n"
    if re.search(r'/(?:home|Users)/', text):
        raise RuntimeError("sanitized summary contains an absolute user path")
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
