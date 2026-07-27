#!/usr/bin/env python3
"""Reduce a public RPKI cache to a non-object corpus profile."""

from __future__ import annotations

import argparse
import gzip
import json
import math
import statistics
import struct
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

KNOWN = {".cer", ".crl", ".mft", ".roa", ".asa", ".gbr", ".tak"}


def percentile(values: list[int], fraction: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    return ordered[math.ceil(fraction * len(ordered)) - 1]


def distribution(values: list[int]) -> dict[str, int | float]:
    if not values:
        return {
            "count": 0,
            "total_bytes": 0,
            "min_bytes": 0,
            "median_bytes": 0,
            "p95_bytes": 0,
            "max_bytes": 0,
        }
    return {
        "count": len(values),
        "total_bytes": sum(values),
        "min_bytes": min(values),
        "median_bytes": statistics.median(values),
        "p95_bytes": percentile(values, 0.95),
        "max_bytes": max(values),
    }


def object_roots(cache: Path) -> list[Path]:
    roots = []
    rrdp = cache / "stored" / "rrdp"
    if rrdp.is_dir():
        roots.append(rrdp)
    ta = cache / "stored" / "ta"
    if ta.is_dir():
        roots.append(ta)
    if not roots:
        roots.append(cache)
    return roots


def read_archive(path: Path) -> list[tuple[str, int]]:
    with path.open("rb") as handle:
        magic = handle.read(6)
        if magic[:5] != b"RTNR\x01" or magic[5:6] not in b"ABCDEF":
            raise RuntimeError(f"unsupported Routinator archive: {path}")
        system = chr(magic[5])
        little = system in "ABC"
        pointer_bytes = {"A": 2, "B": 4, "C": 8, "D": 2, "E": 4, "F": 8}[system]
        endian = "<" if little else ">"
        usize_format = {2: "H", 4: "I", 8: "Q"}[pointer_bytes]
        handle.read(16)
        bucket_count = struct.unpack(
            endian + usize_format, handle.read(pointer_bytes)
        )[0]
        handle.seek((bucket_count + 1) * 8, 1)
        header_format = endian + "QQB" + usize_format + usize_format
        header_size = struct.calcsize(header_format)
        result = []
        while handle.tell() < path.stat().st_size:
            start = handle.tell()
            raw = handle.read(header_size)
            if not raw:
                break
            if len(raw) != header_size:
                raise RuntimeError(f"truncated Routinator archive: {path}")
            size, _next, is_empty, name_len, data_len = struct.unpack(
                header_format, raw
            )
            if size < header_size or start + size > path.stat().st_size:
                raise RuntimeError(f"invalid object boundary in {path}")
            name = handle.read(name_len)
            if not is_empty:
                result.append((name.decode("ascii"), data_len))
            handle.seek(start + size)
        return result


def archive_profile(cache: Path) -> dict[str, object] | None:
    archives = sorted((cache / "rrdp").rglob("*.bin"))
    if not archives:
        return None
    by_type: dict[str, list[int]] = defaultdict(list)
    publication_points: Counter[str] = Counter()
    archive_object_counts: list[int] = []
    archive_object_bytes: list[int] = []
    for path in archives:
        objects = read_archive(path)
        archive_object_counts.append(len(objects))
        archive_object_bytes.append(sum(size for _, size in objects))
        for uri, size in objects:
            suffix = Path(uri).suffix.lower().removeprefix(".")
            if f".{suffix}" in KNOWN:
                by_type[suffix].append(size)
            else:
                by_type["other"].append(size)
            publication_points[uri.rsplit("/", 1)[0]] += 1
    object_types = {
        name: distribution(values) for name, values in sorted(by_type.items())
    }
    return {
        "object_types": object_types,
        "object_type_counts": {
            name: int(item["count"]) for name, item in object_types.items()
        },
        "object_count": sum(archive_object_counts),
        "object_bytes": sum(archive_object_bytes),
        "archive_count": len(archives),
        "objects_per_archive": distribution(archive_object_counts),
        "bytes_per_archive": distribution(archive_object_bytes),
        "publication_points": {
            "count": len(publication_points),
            "objects_per_point": distribution(list(publication_points.values())),
        },
        "method": (
            "Routinator v0.15 archive headers supply current object names and "
            "payload sizes; source objects are not copied"
        ),
    }


def profile(cache: Path, source_label: str) -> dict[str, object]:
    archived = archive_profile(cache)
    by_type: dict[str, list[int]] = defaultdict(list)
    publication_points: Counter[str] = Counter()
    seen: set[tuple[int, int]] = set()
    for root in object_roots(cache):
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix not in KNOWN:
                continue
            stat = path.stat()
            identity = (stat.st_dev, stat.st_ino)
            if identity in seen:
                continue
            seen.add(identity)
            by_type[suffix.removeprefix(".")].append(stat.st_size)
            publication_points[str(path.parent.relative_to(root))] += 1

    transport = {}
    for kind in ("snapshot.xml", "delta.xml", "notification.xml"):
        paths = sorted((cache / "rrdp").rglob(kind)) if (cache / "rrdp").is_dir() else []
        raw = 0
        compressed = 0
        for path in paths:
            data = path.read_bytes()
            raw += len(data)
            compressed += len(gzip.compress(data, mtime=0))
        transport[kind] = {
            "file_count": len(paths),
            "uncompressed_bytes": raw,
            "gzip_bytes": compressed,
        }

    fanout = list(publication_points.values())
    objects = {name: distribution(values) for name, values in sorted(by_type.items())}
    if archived:
        objects = archived["object_types"]
    total_objects = (
        int(archived["object_count"])
        if archived
        else sum(int(item["count"]) for item in objects.values())
    )
    total_bytes = (
        int(archived["object_bytes"])
        if archived
        else sum(int(item["total_bytes"]) for item in objects.values())
    )
    type_counts = (
        archived["object_type_counts"]
        if archived
        else {name: int(item["count"]) for name, item in objects.items()}
    )
    points = (
        archived["publication_points"]
        if archived
        else {
            "count": len(publication_points),
            "objects_per_point": distribution(fanout),
        }
    )
    return {
        "warning": "PUBLIC CACHE AGGREGATE; CONTAINS NO COPIED RPKI OBJECTS",
        "classification": "single public-cache snapshot topology and size profile",
        "collected_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_label": source_label,
        "object_types": objects,
        "object_type_counts": type_counts,
        "object_count": total_objects,
        "object_bytes": total_bytes,
        "publication_points": points,
        "routinator_archives": archived,
        "rrdp_transport_files": transport,
        "synthetic_corpus": {
            "format": "pqc-rpki-synthetic-corpus-v1",
            "seed": 20260727,
            "source": "aggregate count and size distributions above",
            "contains_source_objects": False,
            "resigning_inputs": {
                "publication_point_count": points["count"],
                "object_type_counts": type_counts,
                "mean_object_bytes": (
                    round(total_bytes / total_objects) if total_objects else 0
                ),
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--source-label", required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/scaled-corpus/public-cache-profile.json"),
    )
    args = parser.parse_args()
    result = profile(args.cache.resolve(), args.source_label)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        f"profiled {result['object_count']} objects across "
        f"{result['publication_points']['count']} publication points"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
