#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_PREFIXES = ("local/", "tmp/", "scratch/", "private/")
FORBIDDEN_PARTS = (
    "mailing-list-feedback", "reviewer-thread", "private-note",
    "upstream-notes", "work-in-progress", "wip-patch",
)
FORBIDDEN_SUFFIXES = (".key", ".priv", ".private.pem", "-private.pem")
FORBIDDEN_CONTENT = (
    (b"-----BEGIN " + b"PRIVATE KEY-----", "private key material"),
    (b"-----BEGIN RSA " + b"PRIVATE KEY-----", "private key material"),
    (b"-----BEGIN EC " + b"PRIVATE KEY-----", "private key material"),
    (b"/" + b"Users/", "host-specific user path"),
    (b"/var/" + b"folders/", "host-specific private cache path"),
)


def git_files(arguments: list[str]) -> list[str]:
    process = subprocess.run(["git", *arguments], cwd=ROOT, check=True, capture_output=True, text=True)
    return [line for line in process.stdout.splitlines() if line]


def classify(path: str) -> str | None:
    if path.startswith(FORBIDDEN_PREFIXES):
        return "local/private path must not be tracked or staged"
    if any(part in path for part in FORBIDDEN_PARTS):
        return "review-only filename must stay local-only"
    if path.endswith(FORBIDDEN_SUFFIXES):
        return "private key material pattern must not be tracked or staged"
    return None


def find_violations(paths: list[str]) -> list[dict[str, str]]:
    return [{"path": path, "reason": reason} for path in paths if (reason := classify(path))]


def classify_content(data: bytes) -> str | None:
    return next((reason for marker, reason in FORBIDDEN_CONTENT if marker in data), None)


def find_content_violations(paths: list[str]) -> list[dict[str, str]]:
    violations = []
    for path in paths:
        candidate = ROOT / path
        if not candidate.is_file():
            continue
        data = candidate.read_bytes()
        if reason := classify_content(data):
            violations.append({"path": path, "reason": reason})
    return violations


def main() -> int:
    tracked = git_files(["ls-files", "--cached", "--others", "--exclude-standard"])
    staged = git_files(["diff", "--cached", "--name-only"])
    public_candidates = sorted(set(tracked + staged))
    violations = find_violations(public_candidates)
    violations.extend(find_content_violations(public_candidates))
    if violations:
        for violation in violations:
            print(f"{violation['path']}: {violation['reason']}", file=sys.stderr)
        return 1
    print("pre-publication check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
