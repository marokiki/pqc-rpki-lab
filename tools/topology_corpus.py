#!/usr/bin/env python3
"""Generate and validate a multi-publication-point Composite RPKI corpus."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_DIR))
import composite_e2e as e2e
from composite_rp_matrix import run_case as run_rpki_client
from pqc_rpki_lab.rpki_asn1 import (
    OID_CT_MFT,
    OID_CT_ROA,
    manifest_econtent,
    roa_econtent,
)
from pqc_rpki_lab.workspace import reset_generated_directory
from routinator_experimental_matrix import run_case as run_routinator

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "local" / "topology-corpus"
DEFAULT_RESULT = (
    ROOT / "results" / "scaled-corpus"
    / "topology-pilot-summary.json"
)
BASE_URI = "rsync://example.invalid/repository/"


def child_values(index: int) -> tuple[str, int, str]:
    if not 0 <= index < 65536:
        raise ValueError("child index is outside the synthetic IPv4 range")
    second, third = divmod(index, 256)
    return f"child-{index:05d}", 64496 + index, f"10.{second}.{third}.0/24"


def config_for(
    directory: Path,
    certificate: Path,
    private_key: Path,
    *,
    child_name: str | None = None,
    asn: int | str = 64496,
    prefix: str = "10.0.0.0/8",
) -> str:
    text = e2e.ca_config(
        directory,
        certificate=certificate,
        private_key=private_key,
    )
    text = text.replace("IPv4=192.0.2.0/24", f"IPv4={prefix}")
    text = text.replace("IPv6=2001:db8::/32\n", "")
    text = text.replace("AS.0=64496", f"AS.0={asn}")
    if child_name is None:
        return text
    child_uri = f"{BASE_URI}{child_name}/"
    replacements = {
        f"{BASE_URI}child/child.crl": f"{child_uri}child.crl",
        f"{BASE_URI}child/child.cer": f"{BASE_URI}{child_name}.cer",
        f"{BASE_URI}child/route.roa": f"{child_uri}route.roa",
        f"{BASE_URI}child/child.mft": f"{child_uri}child.mft",
        f"{BASE_URI}child/": child_uri,
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def artifact_metrics(repository: Path) -> dict[str, object]:
    files = [path for path in repository.rglob("*") if path.is_file()]
    by_type: dict[str, dict[str, int]] = {}
    for path in files:
        kind = path.suffix.removeprefix(".")
        row = by_type.setdefault(kind, {"files": 0, "bytes": 0})
        row["files"] += 1
        row["bytes"] += path.stat().st_size
    return {
        "file_count": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "by_type": dict(sorted(by_type.items())),
    }


def generate(
    openssl: str,
    output: Path,
    child_count: int,
    env: dict[str, str],
) -> list[dict[str, object]]:
    reset_generated_directory(output, allowed_root=ROOT / "local")
    private = output / "private"
    repository = output / "repository"
    parent_ca = private / "parent-ca"
    e2e.init_ca(parent_ca)
    repository.mkdir(parents=True)

    parent_key = private / "ta.key"
    parent_pem = private / "ta.pem"
    parent_cfg = parent_ca / "openssl.cnf"
    parent_cfg.write_text(
        config_for(
            parent_ca,
            parent_pem,
            parent_key,
            asn=f"64496-{64496 + child_count - 1}",
            prefix="10.0.0.0/8",
        )
    )
    e2e.run(
        [
            openssl,
            "genpkey",
            "-algorithm",
            "RSA",
            "-pkeyopt",
            "rsa_keygen_bits:2048",
            "-out",
            str(parent_key),
        ],
        env=env,
    )
    e2e.run(
        [
            openssl,
            "req",
            "-new",
            "-x509",
            "-key",
            str(parent_key),
            "-config",
            str(parent_cfg),
            "-extensions",
            "ta_ext",
            "-days",
            "7",
            "-sha256",
            "-out",
            str(parent_pem),
        ],
        env=env,
    )
    e2e.to_der(openssl, "x509", parent_pem, repository / "ta.cer", env)

    expected = []
    parent_entries = []
    for index in range(child_count):
        name, asn, prefix = child_values(index)
        child_private = private / name
        child_ca = child_private / "ca"
        child_repo = repository / name
        e2e.init_ca(child_ca)
        child_repo.mkdir()
        child_key = child_private / "ca.key"
        child_pem = child_private / "ca.pem"

        parent_cfg.write_text(
            config_for(
                parent_ca,
                parent_pem,
                parent_key,
                child_name=name,
                asn=asn,
                prefix=prefix,
            )
        )
        e2e.issue(
            openssl,
            ca_dir=parent_ca,
            config=parent_cfg,
            key=child_key,
            certificate=child_pem,
            common_name=f"EXPERIMENTAL COMPOSITE CA {index}",
            extension="child_ca_ext",
            algorithm=e2e.COMPOSITE,
            digest="sha256",
            env=env,
        )
        child_cer = repository / f"{name}.cer"
        e2e.to_der(openssl, "x509", child_pem, child_cer, env)
        parent_entries.append((child_cer.name, child_cer.read_bytes()))

        child_cfg = child_ca / "openssl.cnf"
        child_cfg.write_text(
            config_for(
                child_ca,
                child_pem,
                child_key,
                child_name=name,
                asn=asn,
                prefix=prefix,
            )
        )
        child_crl = child_private / "child.crl.pem"
        e2e.run(
            [
                openssl,
                "ca",
                "-gencrl",
                "-config",
                str(child_cfg),
                "-md",
                "sha512",
                "-out",
                str(child_crl),
            ],
            env=env,
        )
        e2e.to_der(
            openssl, "crl", child_crl, child_repo / "child.crl", env
        )

        roa_key = child_private / "route-ee.key"
        roa_pem = child_private / "route-ee.pem"
        e2e.issue(
            openssl,
            ca_dir=child_ca,
            config=child_cfg,
            key=roa_key,
            certificate=roa_pem,
            common_name=f"EXPERIMENTAL COMPOSITE ROA EE {index}",
            extension="child_roa_ext",
            algorithm=e2e.COMPOSITE,
            digest="sha512",
            env=env,
        )
        mft_key = child_private / "manifest-ee.key"
        mft_pem = child_private / "manifest-ee.pem"
        e2e.issue(
            openssl,
            ca_dir=child_ca,
            config=child_cfg,
            key=mft_key,
            certificate=mft_pem,
            common_name=f"EXPERIMENTAL COMPOSITE MFT EE {index}",
            extension="child_mft_ext",
            algorithm=e2e.COMPOSITE,
            digest="sha512",
            env=env,
        )
        roa_content = child_private / "route.roa.econtent"
        roa_content.write_bytes(roa_econtent(asn, [(prefix, 24)]))
        e2e.cms_sign(
            openssl,
            content=roa_content,
            signer=roa_pem,
            key=roa_key,
            output=child_repo / "route.roa",
            econtent_type=OID_CT_ROA,
            digest="sha512",
            env=env,
        )
        this_update, next_update = e2e.certificate_times(
            openssl, mft_pem, env
        )
        mft_content = child_private / "child.mft.econtent"
        mft_content.write_bytes(
            manifest_econtent(
                [
                    ("child.crl", (child_repo / "child.crl").read_bytes()),
                    ("route.roa", (child_repo / "route.roa").read_bytes()),
                ],
                manifest_number=index + 1,
                this_update=this_update,
                next_update=next_update,
            )
        )
        e2e.cms_sign(
            openssl,
            content=mft_content,
            signer=mft_pem,
            key=mft_key,
            output=child_repo / "child.mft",
            econtent_type=OID_CT_MFT,
            digest="sha512",
            env=env,
        )
        expected.append(
            {"asn": f"AS{asn}", "prefix": prefix, "max_length": 24}
        )

    parent_cfg.write_text(
        config_for(
            parent_ca,
            parent_pem,
            parent_key,
            asn=f"64496-{64496 + child_count - 1}",
            prefix="10.0.0.0/8",
        )
    )
    parent_crl = private / "ta.crl.pem"
    e2e.run(
        [
            openssl,
            "ca",
            "-gencrl",
            "-config",
            str(parent_cfg),
            "-md",
            "sha256",
            "-out",
            str(parent_crl),
        ],
        env=env,
    )
    e2e.to_der(openssl, "crl", parent_crl, repository / "ta.crl", env)
    parent_entries.append(("ta.crl", (repository / "ta.crl").read_bytes()))

    mft_key = private / "ta-mft-ee.key"
    mft_pem = private / "ta-mft-ee.pem"
    e2e.issue(
        openssl,
        ca_dir=parent_ca,
        config=parent_cfg,
        key=mft_key,
        certificate=mft_pem,
        common_name="EXPERIMENTAL RSA TOPOLOGY MANIFEST EE",
        extension="parent_mft_ext",
        algorithm="RSA",
        digest="sha256",
        env=env,
    )
    this_update, next_update = e2e.certificate_times(
        openssl, mft_pem, env
    )
    content = private / "ta.mft.econtent"
    content.write_bytes(
        manifest_econtent(
            parent_entries,
            this_update=this_update,
            next_update=next_update,
        )
    )
    e2e.cms_sign(
        openssl,
        content=content,
        signer=mft_pem,
        key=mft_key,
        output=repository / "ta.mft",
        econtent_type=OID_CT_MFT,
        digest="sha256",
        env=env,
    )
    (output / "test.tal").write_text(e2e.tal_text(openssl, parent_pem, env))
    return sorted(expected, key=lambda row: (row["prefix"], row["asn"]))


def validate(
    output: Path,
    work: Path,
    rpki_client: Path,
    routinator: Path,
    expected: list[dict[str, object]],
    env: dict[str, str],
    port: int,
) -> dict[str, object]:
    rows = {
        "rpki_client_default": run_rpki_client(
            "rpki-client-default",
            rpki_client,
            [],
            output,
            "ta.cer",
            work / "rpki-client",
            env,
        ),
        "rpki_client_experimental": run_rpki_client(
            "rpki-client-experimental",
            rpki_client,
            ["-x"],
            output,
            "ta.cer",
            work / "rpki-client",
            env,
        ),
        "routinator_default": run_routinator(
            routinator,
            output,
            "routinator",
            False,
            work / "routinator-default",
            port,
        ),
        "routinator_experimental": run_routinator(
            routinator,
            output,
            "routinator",
            True,
            work / "routinator-experimental",
            port + 1,
        ),
    }
    compact = {}
    for name, row in rows.items():
        vrps = sorted(
            row["vrps"], key=lambda item: (item["prefix"], item["asn"])
        )
        experimental = name.endswith("experimental")
        accepted = vrps == expected
        compact[name] = {
            "status": "accepted" if accepted else "rejected",
            "vrp_count": len(vrps),
            "returncode": row["returncode"],
            "expected_policy": (
                "accept" if experimental else "reject-experimental-suite"
            ),
        }
    success = all(
        row["status"]
        == ("accepted" if name.endswith("experimental") else "rejected")
        for name, row in compact.items()
    )
    return {"success": success, "modes": compact}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--children", type=int, default=100)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--openssl", type=Path, required=True)
    parser.add_argument("--rpki-client", type=Path, required=True)
    parser.add_argument("--routinator", type=Path, required=True)
    parser.add_argument("--port", type=int, default=25873)
    args = parser.parse_args()
    if not 1 <= args.children <= 65536:
        raise SystemExit("--children must be between 1 and 65536")

    output = args.output.resolve()
    env = os.environ.copy()
    started = time.perf_counter()
    expected = generate(
        str(args.openssl.resolve()), output, args.children, env
    )
    generation_seconds = time.perf_counter() - started
    validation = validate(
        output,
        output / "validation-work",
        args.rpki_client.resolve(),
        args.routinator.resolve(),
        expected,
        env,
        args.port,
    )
    branch_fixture = output / "branch-divergence"
    shutil.copytree(output / "repository", branch_fixture / "repository")
    shutil.copyfile(output / "test.tal", branch_fixture / "test.tal")
    shutil.rmtree(branch_fixture / "repository" / "child-00000")
    branch_expected = [
        row for row in expected if row["asn"] != "AS64496"
    ]
    branch_validation = validate(
        branch_fixture,
        output / "branch-validation-work",
        args.rpki_client.resolve(),
        args.routinator.resolve(),
        branch_expected,
        env,
        args.port + 2,
    )
    result = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "classification": (
            "synthetic multi-publication-point topology pilot; not a "
            "real-repository, Krill, RRDP, rsync-throughput, or incremental "
            "validation benchmark"
        ),
        "topology": {
            "parent_ca_count": 1,
            "composite_child_ca_count": args.children,
            "child_publication_point_count": args.children,
            "roa_count": args.children,
            "vrp_count": len(expected),
            "roas_per_child": 1,
        },
        "generation_wall_seconds": generation_seconds,
        "artifacts": artifact_metrics(output / "repository"),
        "validation": validation,
        "branch_isolation": {
            "mutation": "child-00000 publication point missing",
            "expected_surviving_vrps": len(branch_expected),
            "validation": branch_validation,
        },
        "contains_private_keys": False,
        "contains_raw_objects": False,
        "contains_absolute_paths": False,
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if re.search(r'/(?:home|Users)/', text):
        raise RuntimeError("sanitized summary contains an absolute user path")
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(text)
    print(text, end="")
    return 0 if validation["success"] and branch_validation["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
