#!/usr/bin/env python3
"""Compare unmodified, patched-default, and experimental RP behavior."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
from pathlib import Path

from pqc_rpki_lab.workspace import reset_generated_directory

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "local" / "e2e" / "current"
DEFAULT_PURE_FIXTURE = (
    ROOT / "local" / "e2e" / "standalone"
    / "testdata" / "validator" / "ml-dsa-65"
)
DEFAULT_COMPOSITE_FIXTURE = (
    ROOT / "testdata" / "validator" / "composite-mldsa65-p256"
)
DEFAULT_RSA_FIXTURE = ROOT / "testdata" / "validator" / "rsa"
DEFAULT_WORK = ROOT / "local" / "e2e" / "rp-matrix"
DEFAULT_RESULT = ROOT / "results" / "composite-e2e" / "rp-validation-matrix.json"


def prepare_cache(fixture: Path, cache: Path, certificate: str) -> None:
    host = "example.invalid" if certificate == "ta.cer" else "example.invalid:8873"
    repository = cache / host / "repository"
    tal = cache / "ta" / "test"
    repository.mkdir(parents=True)
    tal.mkdir(parents=True)
    shutil.copytree(fixture / "repository", repository, dirs_exist_ok=True)
    shutil.copyfile(fixture / "repository" / certificate, tal / certificate)


def run_case(
    name: str,
    binary: Path,
    flags: list[str],
    fixture: Path,
    certificate: str,
    work: Path,
    env: dict[str, str],
) -> dict[str, object]:
    cache = work / name / "cache"
    output = work / name / "output"
    prepare_cache(fixture, cache, certificate)
    output.mkdir(parents=True)
    process = subprocess.run(
        [
            str(binary), *flags, "-n", "-d", str(cache), "-t",
            str(fixture / "test.tal"), "-j", "-c", "-vv", str(output),
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    (work / name / "stdout.txt").write_text(process.stdout)
    (work / name / "stderr.txt").write_text(process.stderr)
    metadata = json.loads((output / "json").read_text())["metadata"]
    with (output / "csv").open(newline="") as handle:
        vrps = list(csv.DictReader(handle))
    rejection = ""
    for line in process.stderr.splitlines():
        if (
            "SPKI not RSAPublicKey" in line
            or "unsupported public key type" in line
            or "wrong signature algorithm" in line
            or "parameters MUST be absent" in line
        ):
            rejection = line.split(": ", 1)[-1]
            break
    return {
        "returncode": process.returncode,
        "vrp_count": metadata["vrps"],
        "invalid_certificates": metadata["invalidcertificates"],
        "manifest_count": metadata["manifests"],
        "crl_count": metadata["crls"],
        "rejection": rejection,
        "vrps": [
            {
                "asn": row["ASN"],
                "prefix": row["IP Prefix"],
                "max_length": int(row["Max Length"]),
            }
            for row in vrps
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument(
        "--pure-fixture", type=Path, default=DEFAULT_PURE_FIXTURE
    )
    parser.add_argument(
        "--composite-fixture", type=Path, default=DEFAULT_COMPOSITE_FIXTURE
    )
    parser.add_argument("--rsa-fixture", type=Path, default=DEFAULT_RSA_FIXTURE)
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--unmodified", type=Path, required=True)
    parser.add_argument("--patched", type=Path, required=True)
    args = parser.parse_args()
    fixture = args.fixture.resolve()
    pure_fixture = args.pure_fixture.resolve()
    composite_fixture = args.composite_fixture.resolve()
    rsa_fixture = args.rsa_fixture.resolve()
    work = args.work.resolve()
    reset_generated_directory(work, allowed_root=ROOT / "local")
    env = os.environ.copy()
    cases = {
        "rsa_baseline": {
            "unmodified": run_case(
                "rsa-unmodified", args.unmodified.resolve(), [], rsa_fixture,
                "ca.cer", work, env,
            ),
            "patched_default": run_case(
                "rsa-patched-default", args.patched.resolve(), [], rsa_fixture,
                "ca.cer", work, env,
            ),
            "patched_experimental": run_case(
                "rsa-patched-experimental", args.patched.resolve(), ["-x"],
                rsa_fixture, "ca.cer", work, env,
            ),
        },
        "composite_standalone": {
            "unmodified": run_case(
                "composite-unmodified", args.unmodified.resolve(), [],
                composite_fixture, "ca.cer", work, env,
            ),
            "patched_default": run_case(
                "composite-patched-default", args.patched.resolve(), [],
                composite_fixture, "ca.cer", work, env,
            ),
            "patched_experimental": run_case(
                "composite-patched-experimental", args.patched.resolve(),
                ["-x"], composite_fixture, "ca.cer", work, env,
            ),
        },
        "mixed_tree": {
            "unmodified": run_case(
                "mixed-unmodified", args.unmodified.resolve(), [], fixture,
                "ta.cer", work, env,
            ),
            "patched_default": run_case(
                "mixed-patched-default", args.patched.resolve(), [], fixture,
                "ta.cer", work, env,
            ),
            "patched_experimental": run_case(
                "mixed-patched-experimental", args.patched.resolve(), ["-x"],
                fixture, "ta.cer", work, env,
            ),
        },
        "pure_mldsa65": {
            "unmodified": run_case(
                "pure-unmodified", args.unmodified.resolve(), [],
                pure_fixture, "ca.cer", work, env,
            ),
            "patched_default": run_case(
                "pure-patched-default", args.patched.resolve(), [],
                pure_fixture, "ca.cer", work, env,
            ),
            "patched_experimental": run_case(
                "pure-patched-experimental", args.patched.resolve(), ["-x"],
                pure_fixture, "ca.cer", work, env,
            ),
        },
    }
    expected_vrps = [
        {"asn": "AS64496", "prefix": "192.0.2.0/24", "max_length": 24},
        {"asn": "AS64496", "prefix": "2001:db8::/32", "max_length": 48},
    ]
    experimental_success = all(
        suite["unmodified"]["vrp_count"] == 0
        and suite["unmodified"]["invalid_certificates"] == 1
        and suite["patched_default"]["vrp_count"] == 0
        and suite["patched_default"]["invalid_certificates"] == 1
        and suite["patched_experimental"]["invalid_certificates"] == 0
        and suite["patched_experimental"]["vrps"] == expected_vrps
        for name, suite in cases.items()
        if name != "rsa_baseline"
    )
    rsa_success = all(
        result["invalid_certificates"] == 0
        and result["vrps"] == expected_vrps
        for result in cases["rsa_baseline"].values()
    )
    success = experimental_success and rsa_success
    result = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "classification": (
            "small-scale local RSA, pure ML-DSA-65, Composite standalone, "
            "and mixed-tree RP comparison"
        ),
        "policy": {
            "unmodified": "Current Suite only",
            "patched_default": "Current Suite only",
            "patched_experimental": (
                "Current Suite plus pure ML-DSA-65 and "
                "id-MLDSA65-ECDSA-P256-SHA512"
            ),
        },
        "cases": cases,
        "success": success,
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
