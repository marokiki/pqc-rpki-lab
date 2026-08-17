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

from pqc_rpki_lab.repository_model import AlgorithmSize, Corpus, estimate_repository_bytes
from pqc_rpki_lab.result_io import markdown_table, write_csv, write_json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).with_suffix(".c")
RESULTS = ROOT / "results" / "draft-composite-2026-07"
DRAFT = "draft-ietf-lamps-pq-composite-sigs-19"


def compile_benchmark(output: Path) -> list[str]:
    compiler = shutil.which("cc")
    pkg_config = shutil.which("pkg-config")
    if not compiler or not pkg_config:
        raise RuntimeError("cc and pkg-config are required")
    flags = subprocess.run(
        [pkg_config, "--cflags", "--libs", "openssl"],
        check=True, capture_output=True, text=True,
    ).stdout.split()
    command = [
        compiler, "-O3", "-Wall", "-Wextra", "-Werror",
        str(SOURCE), "-o", str(output), *flags,
    ]
    subprocess.run(command, check=True)
    return command


def add_repository_estimates(rows: list[dict[str, str]]) -> None:
    corpus = Corpus(10, 100, 10, 10, 100, 1500, 1500, 600, 1500, 200)
    baseline = estimate_repository_bytes(
        corpus, AlgorithmSize("RSA-2048/SHA-256", 270, 256)
    )["repository_total_bytes"]
    for row in rows:
        size = AlgorithmSize(
            row["variant"],
            int(row["public_key_bytes"]),
            round(float(row["signature_bytes_mean"])),
        )
        estimate = estimate_repository_bytes(corpus, size)
        row["repository_total_bytes"] = str(estimate["repository_total_bytes"])
        row["repository_growth_ratio_vs_rsa"] = f"{int(estimate['repository_total_bytes']) / int(baseline):.4f}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=100_000)
    parser.add_argument("--render-existing", action="store_true")
    args = parser.parse_args()
    if args.iterations <= 0:
        parser.error("--iterations must be positive")

    RESULTS.mkdir(parents=True, exist_ok=True)
    raw_path = RESULTS / "draft-composite-100k-raw.csv"
    if args.render_existing:
        raw_output = raw_path.read_text()
        previous = json.loads((RESULTS / "draft-composite-100k.json").read_text())
        metadata = previous["metadata"]
    else:
        with tempfile.TemporaryDirectory(prefix="pqc-rpki-draft-composite-") as name:
            executable = Path(name) / "draft-composite-100k"
            compile_command = compile_benchmark(executable)
            process = subprocess.run(
                [str(executable), str(args.iterations)],
                check=True, capture_output=True, text=True,
            )
        raw_output = process.stdout
        raw_path.write_text(raw_output)
        metadata = {
            "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
            "specification": DRAFT,
            "draft_revision_date": "2026-04-21",
            "classification": "draft-compliant raw Composite ML-DSA Sign/Verify benchmark",
            "application_context": "empty",
            "message_bytes": 32,
            "iterations_per_variant": args.iterations,
            "timing_scope": "message representative, two signatures or verifications, and signature concatenation",
            "excluded": "key generation, file I/O, X.509, CMS, and HSM latency",
            "openssl": subprocess.run(
                ["openssl", "version"], check=True, capture_output=True, text=True
            ).stdout.strip(),
            "platform": platform.platform(),
            "compile_command": compile_command,
        }

    rows = list(csv.DictReader(io.StringIO(raw_output)))
    metadata["compile_command"] = [
        "cc", "-O3", "-Wall", "-Wextra", "-Werror",
        "benchmarks/draft_composite_100k.c", "-o", "$TMPDIR/draft-composite-100k",
        "$(pkg-config --cflags --libs openssl)",
    ]
    expected = {
        "ML-DSA-44 + ECDSA P-256",
        "ML-DSA-65 + ECDSA P-256",
        "ML-DSA-87 + ECDSA P-384",
    }
    if {row["variant"] for row in rows} != expected:
        raise RuntimeError("benchmark did not return the three revision-19 variants")
    for row in rows:
        iterations = int(row["iterations"])
        row["sign_microseconds_per_operation"] = f"{float(row['sign_seconds']) * 1_000_000 / iterations:.3f}"
        row["verify_microseconds_per_operation"] = f"{float(row['verify_seconds']) * 1_000_000 / iterations:.3f}"
        row["status"] = "confirmed"
    add_repository_estimates(rows)

    write_csv(RESULTS / "draft-composite-100k.csv", rows)
    write_json(RESULTS / "draft-composite-100k.json", {"metadata": metadata, "results": rows})
    table = markdown_table(rows, [
        ("variant", "Composite variant"),
        ("iterations", "Operations"),
        ("sign_seconds", "Sign total s"),
        ("verify_seconds", "Verify total s"),
        ("public_key_bytes", "Raw public key bytes"),
        ("signature_bytes_mean", "Mean signature bytes"),
        ("repository_growth_ratio_vs_rsa", "Repository/RSA"),
        ("status", "Status"),
    ])
    (RESULTS / "draft-composite-100k.md").write_text(
        "# Composite ML-DSA Benchmark (draft revision 19)\n\n"
        "> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        f"This benchmark implements `{DRAFT}`. It constructs `M'` from the fixed Prefix, "
        "per-variant Label, one-byte application-context length, empty application context, "
        "and the specified message pre-hash. The ML-DSA component signs in pure mode with "
        "the Label supplied as its ML-DSA context. The traditional component signs the same "
        "`M'`. Verification succeeds only when both components verify. The signature value is "
        "the raw concatenation `mldsaSig || tradSig`.\n\n"
        "`ML-DSA-87 + ECDSA P-256` is not defined by revision 19, so the Category-5 row uses "
        "ECDSA P-384.\n\n" + table +
        "\n\n## Scope and limitations\n\n"
        "The timing includes construction of the message representative, both component "
        "operations, and raw signature concatenation. It excludes key generation, file I/O, "
        "X.509, CMS, validator processing, and HSM latency. Public-key and signature sizes are "
        "the raw concatenations defined by revision 19. ECDSA signatures use variable-length DER encoding, "
        "so the result records minimum, maximum, and mean signature lengths.\n\n"
        "Repository ratios are first-order model outputs using the measured raw key and mean "
        "signature lengths. They are not full-repository measurements and do not include any "
        "future RPKI-specific X.509 or CMS profile overhead.\n"
    )


if __name__ == "__main__":
    main()
