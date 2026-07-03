#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import platform
import statistics
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from exact_100k import compile_benchmark
from pqc_rpki_lab.result_io import markdown_table, write_csv, write_json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "message-sweep"
SIZES = (32, 512, 2048, 8192)


def aggregate(raw: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, int], list[dict[str, object]]] = {}
    for row in raw:
        grouped.setdefault((str(row["algorithm"]), int(row["message_bytes"])), []).append(row)
    output = []
    for (algorithm, size), rows in sorted(grouped.items()):
        confirmed = [row for row in rows if row["status"] == "confirmed"]
        item: dict[str, object] = {
            "algorithm": algorithm, "message_bytes": size,
            "repetitions": len(rows), "confirmed_repetitions": len(confirmed),
            "status": "confirmed" if len(confirmed) == len(rows) else "unsupported",
        }
        for field in ("keygen_seconds", "sign_seconds", "verify_seconds", "peak_rss_bytes"):
            values = [float(row[field]) for row in confirmed]
            if values:
                item[f"{field}_median"] = statistics.median(values)
                item[f"{field}_stdev"] = statistics.stdev(values) if len(values) > 1 else 0.0
        output.append(item)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=100_000)
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--render-existing", action="store_true")
    args = parser.parse_args()
    if args.iterations <= 0 or args.repetitions < 2:
        parser.error("iterations must be positive and repetitions must be at least 2")
    RESULTS.mkdir(parents=True, exist_ok=True)
    if args.render_existing:
        previous = json.loads((RESULTS / "message-sweep.json").read_text())
        raw = previous["raw_results"]
        metadata = previous["metadata"]
        args.iterations = int(metadata["iterations_per_operation_loop"])
        args.repetitions = int(metadata["repetitions_per_data_point"])
    else:
        raw: list[dict[str, object]] = []
        with tempfile.TemporaryDirectory(prefix="pqc-rpki-message-sweep-") as name:
            executable = Path(name) / "message-sweep"
            compile_command = compile_benchmark(executable)
            for size in SIZES:
                for repetition in range(1, args.repetitions + 1):
                    process = subprocess.run(
                        [str(executable), str(args.iterations), str(size)],
                        check=True, capture_output=True, text=True,
                    )
                    for row in csv.DictReader(io.StringIO(process.stdout)):
                        row["repetition"] = repetition
                        raw.append(row)
        metadata = {
            "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "platform": platform.platform(),
            "openssl": subprocess.run(["openssl", "version", "-a"], check=True, capture_output=True, text=True).stdout,
            "iterations_per_operation_loop": args.iterations,
            "repetitions_per_data_point": args.repetitions,
            "message_sizes_bytes": list(SIZES),
            "comparable_group": f"openssl-evp-message-sweep-{args.iterations}x{args.repetitions}-v1",
            "compile_command": compile_command,
            "peak_rss_scope": "maximum resident set size for the complete benchmark process, not per operation",
        }
    summary = aggregate(raw)
    metadata["compile_command"] = [
        "cc", "-O2", "-Wall", "-Wextra", "-Werror",
        "benchmarks/exact_100k.c", "-o", "$TMPDIR/message-sweep",
        "$(pkg-config --cflags --libs openssl)",
    ]
    write_csv(RESULTS / "message-sweep-raw.csv", raw)
    write_csv(RESULTS / "message-sweep.csv", summary)
    write_json(RESULTS / "message-sweep.json", {"metadata": metadata, "results": summary, "raw_results": raw})
    (RESULTS / "message-sweep.md").write_text(
        "# EVP Message-Size Sweep\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        + markdown_table(summary, [
            ("algorithm", "Algorithm"), ("message_bytes", "Message bytes"),
            ("repetitions", "Repetitions"), ("status", "Status"),
            ("keygen_seconds_median", "Keygen median s"),
            ("sign_seconds_median", "Sign median s"),
            ("sign_seconds_stdev", "Sign stdev s"),
            ("verify_seconds_median", "Verify median s"),
            ("verify_seconds_stdev", "Verify stdev s"),
            ("peak_rss_bytes_median", "Peak RSS median bytes"),
        ]) + "\n"
    )


if __name__ == "__main__":
    main()
