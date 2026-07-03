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
    "docs/draft-01-completion-status.md",
    "docs/draft-01-remaining-tasks.md",
    "docs/implementation-status.md",
    "src/pqc_rpki_lab/cms.py",
    "src/pqc_rpki_lab/rpki_asn1.py",
    "src/pqc_rpki_lab/rpki_objects.py",
    "tests/test_cms.py",
    "tests/test_rpki_objects.py",
    "tools/generate_rpki_objects.py",
    "tools/validator_container_probe.py",
    "results/rpki-objects/rpki-objects.json",
    "results/validator-probe/container-matrix.json",
    "results/message-sweep/message-sweep.json",
    "testdata/ml-dsa-65/route.roa",
    "testdata/ml-dsa-65/manifest.mft",
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
