#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import statistics
import time
from pathlib import Path

from pqc_rpki_lab.result_io import markdown_table, write_csv, write_json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def percentile(values: list[int], fraction: float) -> int | str:
    if not values:
        return ""
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path)
    args = parser.parse_args()
    rows: list[dict[str, object]] = []
    now = time.time()
    if args.cache:
        if not args.cache.is_dir():
            rows.append({
                "extension": "all", "status": "blocked", "count": 0,
                "reason": f"cache path is not a directory: {args.cache}",
            })
        else:
            for suffix in (".cer", ".roa", ".mft", ".crl"):
                files = [path for path in args.cache.rglob(f"*{suffix}") if path.is_file()]
                sizes = [path.stat().st_size for path in files]
                ages = [max(0, int(now - path.stat().st_mtime)) for path in files]
                rows.append({
                    "extension": suffix, "status": "confirmed", "count": len(sizes),
                    "total_bytes": sum(sizes), "min_bytes": min(sizes) if sizes else "",
                    "median_bytes": statistics.median(sizes) if sizes else "",
                    "p95_bytes": percentile(sizes, 0.95),
                    "max_bytes": max(sizes) if sizes else "",
                    "newest_age_seconds": min(ages) if ages else "",
                    "oldest_age_seconds": max(ages) if ages else "",
                    "changed_within_24h_count": sum(age <= 86400 for age in ages),
                    "reason": "",
                })
    else:
        rows.append({
            "extension": "all", "status": "skipped", "count": 0,
            "total_bytes": "", "min_bytes": "", "median_bytes": "", "p95_bytes": "",
            "max_bytes": "", "newest_age_seconds": "", "oldest_age_seconds": "",
            "changed_within_24h_count": "", "reason": "no --cache argument supplied",
        })
    status = "confirmed" if args.cache and args.cache.is_dir() else ("blocked" if args.cache else "skipped")
    payload = {
        "status": status,
        "cache": str(args.cache) if args.cache else "",
        "measurement_type": "confirmed filesystem metadata" if status == "confirmed" else status,
        "results": rows,
    }
    write_csv(RESULTS / "real-repository-summary.csv", rows)
    write_json(RESULTS / "real-repository-summary.json", payload)
    (RESULTS / "real-repository-summary.md").write_text(
        "# Real Repository Summary\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        f"Overall status: `{status}`. Synthetic estimates are not included in this table.\n\n" +
        markdown_table(rows, [(key, key.replace("_", " ").title()) for key in rows[0]]) + "\n")
    # Keep the old adapter names for compatibility.
    write_csv(RESULTS / "local-cache-stats.csv", rows)
    write_json(RESULTS / "local-cache-stats.json", payload)


if __name__ == "__main__":
    main()
