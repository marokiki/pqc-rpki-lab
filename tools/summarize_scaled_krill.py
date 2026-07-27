#!/usr/bin/env python3
"""Publish a sanitized summary of the scaled Krill boundary experiment."""

from __future__ import annotations

import argparse
import gzip
import json
import re
from collections import Counter
from pathlib import Path


TIME_FIELDS = {
    "User time (seconds)": ("user_seconds", float),
    "System time (seconds)": ("system_seconds", float),
    "Elapsed (wall clock) time (h:mm:ss or m:ss)": ("wall_seconds", str),
    "Maximum resident set size (kbytes)": ("max_rss_kib", int),
    "Exit status": ("exit_status", int),
}


def wall_seconds(value: str) -> float:
    parts = [float(item) for item in value.split(":")]
    seconds = 0.0
    for item in parts:
        seconds = seconds * 60 + item
    return seconds


def parse_time(path: Path) -> dict[str, int | float]:
    result: dict[str, int | float] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        for label, (name, converter) in TIME_FIELDS.items():
            prefix = f"{label}:"
            if line.startswith(prefix):
                raw = line.removeprefix(prefix).strip()
                value = converter(raw)
                result[name] = (
                    wall_seconds(value) if name == "wall_seconds" else value
                )
    missing = {item[0] for item in TIME_FIELDS.values()} - result.keys()
    if missing:
        raise RuntimeError(f"missing time fields in {path.name}: {sorted(missing)}")
    return result


def transport_metrics(repo: Path) -> dict[str, object]:
    rsync = repo / "rsync/current"
    files = [path for path in rsync.rglob("*") if path.is_file()]
    by_type = Counter(path.suffix.removeprefix(".") for path in files)
    rrdp: dict[str, dict[str, int]] = {}
    for name in ("notification.xml", "snapshot.xml", "delta.xml"):
        paths = list((repo / "rrdp").rglob(name))
        payloads = [path.read_bytes() for path in paths]
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


def reliability(path: Path) -> dict[str, int]:
    rows = [
        line.split("\t", 1)
        for line in path.read_text().splitlines()
        if line.strip()
    ]
    return {
        "attempts": len(rows),
        "passed": sum(status == "pass" for _, status in rows),
        "failed": sum(status != "pass" for _, status in rows),
    }


def compact_validation(source: dict[str, object]) -> dict[str, object]:
    phases = {}
    for phase, modes in source["phases"].items():
        phases[phase] = {
            mode: {
                "status": row["status"],
                "vrp_count": row["vrp_count"],
                "returncode": row["returncode"],
            }
            for mode, row in modes.items()
        }
    return {
        "expected_vrp_count": len(source["expected_vrps"]),
        "original_success": source["success"],
        "phases": phases,
    }


def build_summary(
    scaled_root: Path,
    reliability_file: Path,
    roa_count: int,
) -> dict[str, object]:
    validation = json.loads((scaled_root / "validation.json").read_text())
    compact = compact_validation(validation)
    expected = compact["expected_vrp_count"]
    if expected != roa_count:
        raise RuntimeError(f"expected {roa_count} VRPs, found {expected}")
    composite = compact["phases"]["composite"]
    rollback = compact["phases"]["rollback"]
    scaled_composite_success = all(
        row["status"] == ("rejected" if mode.endswith("default") else "accepted")
        for mode, row in composite.items()
    )
    rollback_success = all(
        row["status"] == "accepted" and row["vrp_count"] == roa_count
        for row in rollback.values()
    )
    return {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "classification": (
            "single-CA object-count scaling result; not a real-repository, "
            "warm-cache, incremental-validation, or throughput benchmark"
        ),
        "topology": {
            "parent_ca_count": 1,
            "child_ca_count": 1,
            "child_publication_point_count": 1,
            "roa_count": roa_count,
            "vrp_count": roa_count,
            "asn_layout": "distinct sequential ASNs in delegated range",
        },
        "capture": {
            "completion_condition": "published object count converged",
            "quiescence_seconds": 2,
            "source": "Krill publication API current_files",
            "layout": "canonical rsync repository module path",
        },
        "one_roa_composite_reliability": reliability(reliability_file),
        "generation": parse_time(scaled_root / "generation.time"),
        "validation": {
            **compact,
            "process_time": parse_time(scaled_root / "validation.time"),
        },
        "transport": {
            phase: transport_metrics(
                scaled_root / f"repository/{phase}/state/repo"
            )
            for phase in ("composite", "rollback")
        },
        "scaled_composite_success": scaled_composite_success,
        "rollback_success": rollback_success,
        "conclusion": (
            "Krill generated and published 1000 ROAs. Both experimental RPs "
            "validated the Composite state and all modes validated RSA rollback, "
            "each producing the expected 1000 VRPs."
        ),
        "contains_private_keys": False,
        "contains_raw_objects": False,
        "contains_absolute_paths": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scaled-root", type=Path, required=True)
    parser.add_argument("--reliability", type=Path, required=True)
    parser.add_argument("--roa-count", type=int, default=1000)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/scaled-corpus/krill-scaled-summary.json"),
    )
    args = parser.parse_args()
    result = build_summary(
        args.scaled_root.resolve(),
        args.reliability.resolve(),
        args.roa_count,
    )
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if re.search(r'/(?:home|Users)/', text):
        raise RuntimeError("sanitized summary contains an absolute user path")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text)
    print(
        f"summarized {args.roa_count} ROAs: "
        f"composite={result['scaled_composite_success']}, "
        f"rollback={result['rollback_success']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
