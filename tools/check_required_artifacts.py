#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "README.md",
    "Makefile",
    ".gitignore",
    "pyproject.toml",
    "ietf/draft-yoshikawa-sidrops-pqc-rpki-01.md",
    "ietf/submission/draft-yoshikawa-sidrops-pqc-rpki-01.xml",
    "ietf/draft-yoshikawa-sidrops-pqc-rpki-02.md",
    "ietf/submission/draft-yoshikawa-sidrops-pqc-rpki-02.xml",
    "ietf/submission/draft-yoshikawa-sidrops-pqc-rpki-02.txt",
    "docs/draft-01-completion-status.md",
    "docs/draft-01-remaining-tasks.md",
    "docs/implementation-status.md",
    "experiments/openssl-composite.cnf",
    "experiments/composite-dependencies.json",
    "src/pqc_rpki_lab/cms.py",
    "src/pqc_rpki_lab/rpki_asn1.py",
    "src/pqc_rpki_lab/rpki_objects.py",
    "src/pqc_rpki_lab/workspace.py",
    "tests/test_cms.py",
    "tests/test_rpki_objects.py",
    "tools/generate_rpki_objects.py",
    "tools/composite_e2e.py",
    "tools/composite_e2e_benchmark.py",
    "tools/keygen_benchmark.py",
    "tools/composite_negative_tests.py",
    "tools/composite_rp_matrix.py",
    "tools/bootstrap_composite_e2e.sh",
    "tools/bootstrap_krill_experimental.sh",
    "tools/run_krill_experimental.sh",
    "tools/run_krill_scaled_experimental.sh",
    "tools/krill_experimental_validate.py",
    "tools/profile_public_cache.py",
    "tools/summarize_scaled_krill.py",
    "tools/check_composite_evidence.py",
    "patches/rpki-client-composite-experimental.patch",
    "patches/composite-provider-private-key-decoder.patch",
    "patches/krill-experimental-pqc.patch",
    "tools/validator_container_probe.py",
    "tests/test_composite_e2e.py",
    "tests/test_composite_evidence.py",
    "tests/test_public_cache_profile.py",
    "tests/test_scaled_corpus.py",
    "results/composite-e2e/summary.json",
    "results/composite-e2e/benchmark-summary.json",
    "results/composite-e2e/keygen-summary.json",
    "results/composite-e2e/negative-summary.json",
    "results/composite-e2e/rp-validation-matrix.json",
    "results/composite-e2e/krill-rollover.json",
    "results/scaled-corpus/public-cache-profile.json",
    "results/scaled-corpus/krill-scaled-summary.json",
    "results/rpki-objects/rpki-objects.json",
    "results/validator-probe/container-matrix.json",
    "results/message-sweep/message-sweep.json",
    "testdata/ml-dsa-65/route.roa",
    "testdata/ml-dsa-65/manifest.mft",
    "testdata/composite-mldsa65-p256/ca.cer",
    "testdata/composite-mldsa65-p256/ca.crl",
    "testdata/composite-mldsa65-p256/route.roa",
    "testdata/composite-mldsa65-p256/manifest.mft",
)

REQUIRED_NONEMPTY_DIRECTORIES = (
    "src",
    "tests",
    "tools",
    "docs",
    "ietf",
    "results",
    "testdata",
)


def find_missing(root: Path = ROOT) -> list[str]:
    missing = [path for path in REQUIRED_FILES if not (root / path).is_file()]
    for path in REQUIRED_NONEMPTY_DIRECTORIES:
        directory = root / path
        if not directory.is_dir() or not any(item.is_file() for item in directory.rglob("*")):
            missing.append(f"{path}/ (missing or empty)")
    return missing


def tracked_deletions(root: Path = ROOT) -> list[str]:
    process = subprocess.run(
        ["git", "ls-files", "--deleted"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in process.stdout.splitlines() if line]


def main() -> int:
    missing = find_missing()
    deleted = tracked_deletions()
    if missing or deleted:
        for path in missing:
            print(f"missing required artifact: {path}", file=sys.stderr)
        for path in deleted:
            print(f"deleted tracked file: {path}", file=sys.stderr)
        return 1
    print(
        f"required artifact check passed: {len(REQUIRED_FILES)} files and "
        f"{len(REQUIRED_NONEMPTY_DIRECTORIES)} non-empty directories"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
