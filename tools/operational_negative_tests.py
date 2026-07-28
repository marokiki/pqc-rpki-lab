#!/usr/bin/env python3
"""Exercise operationally invalid Composite RPKI repository states.

Generated repositories, copied keys, CA databases, and complete validator logs
remain below local/.  The result contains only sanitized failure summaries.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from pqc_rpki_lab.cms import inspect_signed_object
from pqc_rpki_lab.rpki_asn1 import (
    OID_CT_MFT,
    OID_CT_ROA,
    manifest_econtent,
)
from pqc_rpki_lab.workspace import reset_generated_directory

from composite_e2e import cms_sign
from composite_rp_matrix import run_case as run_rpki_case
from routinator_experimental_matrix import run_case

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "local" / "e2e" / "current"
DEFAULT_WORK = ROOT / "local" / "operational-negative"
DEFAULT_RESULT = (
    ROOT / "results" / "composite-e2e"
    / "operational-negative-summary.json"
)
EXPECTED_VRPS = [
    {"asn": "AS64496", "prefix": "192.0.2.0/24", "max_length": 24},
    {"asn": "AS64496", "prefix": "2001:db8::/32", "max_length": 48},
]
CASES = {
    "expired-child-manifest": "manifest-expired",
    "expired-child-crl": "crl-expired",
    "expired-roa-ee": "ee-certificate-expired",
    "revoked-roa-ee": "ee-certificate-revoked",
    "missing-roa": "manifest-object-missing",
    "missing-child-manifest": "manifest-missing",
    "missing-child-crl": "crl-missing",
}


def run(command: list[str], env: dict[str, str]) -> None:
    process = subprocess.run(
        command, env=env, capture_output=True, text=True
    )
    if process.returncode:
        raise RuntimeError(
            f"command failed ({process.returncode}): {' '.join(command)}\n"
            f"{process.stderr or process.stdout}"
        )


def prepare_case(source: Path, target: Path) -> Path:
    fixture = target / "fixture"
    shutil.copytree(source / "repository", fixture / "repo")
    shutil.copytree(source / "private", target / "private")
    shutil.copyfile(source / "test.tal", fixture / "testbed.tal")
    shutil.copyfile(source / "test.tal", fixture / "test.tal")
    (fixture / "repository").symlink_to("repo", target_is_directory=True)
    (fixture / "ta").mkdir()
    shutil.copyfile(source / "repository" / "ta.cer", fixture / "ta" / "ta.cer")

    source_private = str((source / "private").resolve())
    target_private = str((target / "private").resolve())
    for config in (target / "private").rglob("openssl.cnf"):
        text = config.read_text()
        if source_private not in text:
            raise RuntimeError(f"CA config does not reference {source_private}")
        config.write_text(text.replace(source_private, target_private))
    return fixture


def resign_child_manifest(
    openssl: str,
    target: Path,
    env: dict[str, str],
    *,
    this_update: str | None = None,
    next_update: str | None = None,
) -> None:
    repository = target / "fixture" / "repo" / "child"
    private = target / "private"
    current = inspect_signed_object((repository / "child.mft").read_bytes())
    details = current["econtent"]
    from pqc_rpki_lab.rpki_asn1 import parse_manifest_econtent

    parsed = parse_manifest_econtent(details)
    content = manifest_econtent(
        [
            (entry["file"], (repository / entry["file"]).read_bytes())
            for entry in parsed["entries"]
        ],
        manifest_number=int(parsed["manifest_number"]) + 1,
        this_update=this_update or str(parsed["this_update"]),
        next_update=next_update or str(parsed["next_update"]),
    )
    econtent = private / "operational-child.mft.econtent"
    econtent.write_bytes(content)
    cms_sign(
        openssl,
        content=econtent,
        signer=private / "child-mft-ee.pem",
        key=private / "child-mft-ee.key",
        output=repository / "child.mft",
        econtent_type=OID_CT_MFT,
        digest="sha512",
        env=env,
    )


def generate_expired_crl(
    openssl: str, target: Path, env: dict[str, str]
) -> None:
    private = target / "private"
    pem = private / "expired-child.crl.pem"
    run(
        [
            openssl,
            "ca",
            "-gencrl",
            "-config",
            str(private / "child-ca" / "openssl.cnf"),
            "-md",
            "sha512",
            "-crl_lastupdate",
            "20200101000000Z",
            "-crl_nextupdate",
            "20200102000000Z",
            "-out",
            str(pem),
        ],
        env,
    )
    run(
        [
            openssl,
            "crl",
            "-in",
            str(pem),
            "-outform",
            "DER",
            "-out",
            str(target / "fixture" / "repo" / "child" / "child.crl"),
        ],
        env,
    )


def generate_revoked_crl(
    openssl: str, target: Path, env: dict[str, str]
) -> None:
    private = target / "private"
    config = private / "child-ca" / "openssl.cnf"
    run(
        [
            openssl,
            "ca",
            "-batch",
            "-config",
            str(config),
            "-revoke",
            str(private / "route-ee.pem"),
        ],
        env,
    )
    pem = private / "revoked-child.crl.pem"
    run(
        [
            openssl,
            "ca",
            "-gencrl",
            "-config",
            str(config),
            "-md",
            "sha512",
            "-out",
            str(pem),
        ],
        env,
    )
    run(
        [
            openssl,
            "crl",
            "-in",
            str(pem),
            "-outform",
            "DER",
            "-out",
            str(target / "fixture" / "repo" / "child" / "child.crl"),
        ],
        env,
    )


def generate_expired_roa(
    openssl: str, target: Path, env: dict[str, str]
) -> None:
    private = target / "private"
    config = private / "child-ca" / "openssl.cnf"
    expired = private / "expired-route-ee.pem"
    run(
        [
            openssl,
            "ca",
            "-batch",
            "-config",
            str(config),
            "-extensions",
            "child_roa_ext",
            "-md",
            "sha512",
            "-startdate",
            "20200101000000Z",
            "-enddate",
            "20200102000000Z",
            "-in",
            str(private / "route-ee.csr"),
            "-out",
            str(expired),
        ],
        env,
    )
    cms_sign(
        openssl,
        content=private / "route.roa.econtent",
        signer=expired,
        key=private / "route-ee.key",
        output=target / "fixture" / "repo" / "child" / "route.roa",
        econtent_type=OID_CT_ROA,
        digest="sha512",
        env=env,
    )


def mutate(
    name: str,
    openssl: str,
    target: Path,
    env: dict[str, str],
) -> None:
    child = target / "fixture" / "repo" / "child"
    if name == "missing-roa":
        (child / "route.roa").unlink()
    elif name == "missing-child-manifest":
        (child / "child.mft").unlink()
    elif name == "missing-child-crl":
        (child / "child.crl").unlink()
    elif name == "expired-child-manifest":
        resign_child_manifest(
            openssl,
            target,
            env,
            this_update="20200101000000Z",
            next_update="20200102000000Z",
        )
    elif name == "expired-child-crl":
        generate_expired_crl(openssl, target, env)
        resign_child_manifest(openssl, target, env)
    elif name == "revoked-roa-ee":
        generate_revoked_crl(openssl, target, env)
        resign_child_manifest(openssl, target, env)
    elif name == "expired-roa-ee":
        generate_expired_roa(openssl, target, env)
        resign_child_manifest(openssl, target, env)
    else:
        raise ValueError(name)


def sanitized_reason(path: Path) -> str:
    text = path.read_text() if path.exists() else ""
    lines = text.splitlines()
    reason = ""
    for pattern in (
        "rejecting stale",
        "certificate has expired",
        "certificate has been revoked",
        "certificate revoked",
        "crl has expired",
        "unable to get certificate crl",
        "dating issue:",
        "no valid manifest",
        "failed to load",
        "bad message digest",
    ):
        reason = next(
            (line.strip() for line in lines if pattern in line.lower()),
            "",
        )
        if reason:
            break
    reason = reason.replace(str(ROOT), "$REPO")
    reason = re.sub(r"/home/[^/\s]+/", "/home/$USER/", reason)
    return reason[:500]


def compact(row: dict[str, object], log: Path) -> dict[str, object]:
    vrp_count = int(row["vrp_count"])
    return {
        "returncode": row["returncode"],
        "status": row.get(
            "status",
            "accepted" if vrp_count == len(EXPECTED_VRPS) else "rejected",
        ),
        "vrp_count": vrp_count,
        "diagnostic": sanitized_reason(log),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--openssl", type=Path, required=True)
    parser.add_argument("--rpki-client", type=Path, required=True)
    parser.add_argument("--routinator", type=Path, required=True)
    parser.add_argument("--port", type=int, default=21873)
    args = parser.parse_args()

    work = args.work.resolve()
    reset_generated_directory(work, allowed_root=ROOT / "local")
    env = os.environ.copy()
    results = []
    for offset, (name, reason_code) in enumerate(CASES.items()):
        target = work / "repositories" / name
        fixture = prepare_case(args.fixture.resolve(), target)
        mutate(name, str(args.openssl.resolve()), target, env)
        rpki_work = work / "validation" / name / "rpki-client"
        routinator_work = work / "validation" / name / "routinator"
        rpki = run_rpki_case(
            name,
            args.rpki_client.resolve(),
            ["-x"],
            fixture,
            "ta.cer",
            rpki_work,
            env,
        )
        routinator = run_case(
            args.routinator.resolve(),
            fixture,
            name,
            True,
            routinator_work,
            args.port + offset,
        )
        results.append(
            {
                "name": name,
                "reason_code": reason_code,
                "expected": "reject",
                "rpki_client": compact(
                    rpki, rpki_work / name / "stderr.txt"
                ),
                "routinator": compact(
                    routinator,
                    routinator_work
                    / f"{name}-experimental"
                    / "routinator.log",
                ),
            }
        )

    all_rejected = all(
        rp["status"] == "rejected" and rp["vrp_count"] == 0
        for row in results
        for rp in (row["rpki_client"], row["routinator"])
    )
    document = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "classification": (
            "sanitized operational-state negative tests against one "
            "Composite child; generated repositories, private keys, CA "
            "databases, and complete logs stay below local/"
        ),
        "expected_baseline_vrp_count": len(EXPECTED_VRPS),
        "all_rejected": all_rejected,
        "results": results,
        "contains_private_keys": False,
        "contains_raw_objects": False,
        "contains_absolute_paths": False,
    }
    text = json.dumps(document, indent=2, sort_keys=True) + "\n"
    if re.search(r'/(?:home|Users)/', text):
        raise RuntimeError("sanitized summary contains an absolute user path")
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(text)
    print(text, end="")
    return 0 if all_rejected else 1


if __name__ == "__main__":
    raise SystemExit(main())
