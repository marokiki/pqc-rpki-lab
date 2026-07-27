#!/usr/bin/env python3
"""Exercise generated negative repositories with experimental Routinator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pqc_rpki_lab.workspace import reset_generated_directory
from routinator_experimental_matrix import run_case

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "local" / "negative" / "summary.json"
DEFAULT_WORK = ROOT / "local" / "routinator-negative"
DEFAULT_RESULT = (
    ROOT / "results" / "composite-e2e"
    / "routinator-negative-summary.json"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--port", type=int, default=18873)
    args = parser.parse_args()

    source = json.loads(args.input.read_text())
    reason_codes = {
        item["name"]: item["reason_code"] for item in source["results"]
    }
    repositories = source["routinator_repositories"]
    work = args.work.resolve()
    reset_generated_directory(work, allowed_root=ROOT / "local")
    results = []
    for name, repository in sorted(repositories.items()):
        observed = run_case(
            args.binary.resolve(),
            Path(repository).resolve(),
            name,
            True,
            work,
            args.port,
        )
        results.append(
            {
                "name": name,
                "reason_code": reason_codes[name],
                "expected": "reject",
                "rejected": observed["status"] == "rejected",
                "returncode": observed["returncode"],
                "vrp_count": observed["vrp_count"],
                "observed_reason": observed["reason"],
            }
        )
    document = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "classification": (
            "sanitized second-RP negative-test results; generated "
            "repositories and full logs stay below local/"
        ),
        "implementation": (
            "Routinator 0.15.2 with experimental rpki-rs backend"
        ),
        "all_rejected": all(item["rejected"] for item in results),
        "results": results,
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(document, indent=2, sort_keys=True))
    return 0 if document["all_rejected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
