#!/usr/bin/env python3
"""Generate and exercise negative Composite RPKI fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from pqc_rpki_lab import der
from pqc_rpki_lab.cms import (
    OID_ML_DSA_65,
    OID_SHA512,
    inspect_signed_object,
    parse_one,
)
from pqc_rpki_lab.workspace import reset_generated_directory
from pqc_rpki_lab.rpki_asn1 import (
    OID_CT_MFT,
    manifest_econtent,
    parse_manifest_econtent,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "local" / "e2e" / "current"
DEFAULT_PURE_FIXTURE = (
    ROOT / "local" / "e2e" / "standalone"
    / "testdata" / "validator" / "ml-dsa-65"
)
DEFAULT_PURE_PRIVATE = (
    ROOT / "local" / "e2e" / "rp-matrix-private" / "ml-dsa-65"
)
DEFAULT_OUTPUT = ROOT / "local" / "negative"
DEFAULT_RESULT = ROOT / "results" / "composite-e2e" / "negative-summary.json"
COMPOSITE_OID = "1.3.6.1.5.5.7.6.45"
UNKNOWN_OID = "1.3.6.1.5.5.7.6.99"
SHA256_OID = "2.16.840.1.101.3.4.2.1"
MLDSA65_SIGNATURE_BYTES = 3309
REASON_CODES = {
    "component-mldsa-corrupt": "component-signature-invalid",
    "component-ecdsa-corrupt": "component-signature-invalid",
    "component-order-reversed": "component-order-invalid",
    "signature-truncated": "signature-encoding-invalid",
    "unsupported-signature-oid": "unsupported-algorithm",
    "signature-parameters-present": "malformed-parameters",
    "cms-signature-corrupt": "cms-signature-invalid",
    "cms-sha256-intrusion": "cms-digest-mismatch",
    "crl-signature-corrupt": "crl-signature-invalid",
    "tbs-outer-signature-mismatch": "certificate-algorithm-mismatch",
    "certificate-path-invalid": "certificate-path-invalid",
    "manifest-hash-mismatch": "manifest-hash-mismatch",
    "pure-signature-corrupt": "cms-signature-invalid",
    "pure-signature-parameters-present": "malformed-parameters",
    "pure-cms-sha256-intrusion": "cms-digest-mismatch",
}


def command_result(command: list[str], env: dict[str, str]) -> dict[str, object]:
    process = subprocess.run(command, env=env, capture_output=True, text=True)
    return {
        "returncode": process.returncode,
        "stdout": process.stdout.strip(),
        "stderr": process.stderr.strip(),
    }


def prepare_cache(fixture: Path, cache: Path) -> None:
    repository = cache / "example.invalid" / "repository"
    tal = cache / "ta" / "test"
    repository.mkdir(parents=True)
    tal.mkdir(parents=True)
    shutil.copytree(fixture / "repository", repository, dirs_exist_ok=True)
    shutil.copyfile(fixture / "repository" / "ta.cer", tal / "ta.cer")


def rebuild_cms(
    source: bytes,
    *,
    signature: bytes | None = None,
    signature_oid: str = COMPOSITE_OID,
    signature_null: bool = False,
    digest_oid: str = OID_SHA512,
    certificate_der: bytes | None = None,
) -> bytes:
    item = inspect_signed_object(source)
    root, _ = parse_one(source)
    signed_data = root.children()[1].children()[0]
    fields = signed_data.children()
    actual_certificate = (
        fields[3].children()[0].encoded
        if certificate_der is None
        else certificate_der
    )
    attrs = item["signed_attrs_der"]
    assert isinstance(attrs, bytes)
    attrs_value = parse_one(attrs)[0].value
    actual_signature = item["signature"] if signature is None else signature
    assert isinstance(actual_signature, bytes)
    signer_info = der.sequence(
        der.integer(3),
        der.tlv(0x80, item["sid"]),
        der.algorithm_identifier(digest_oid),
        der.tlv(0xA0, attrs_value),
        der.algorithm_identifier(signature_oid, include_null=signature_null),
        der.octet_string(actual_signature),
    )
    rebuilt = der.sequence(
        der.integer(3),
        der.set_of(der.algorithm_identifier(digest_oid)),
        der.sequence(
            der.object_identifier(item["econtent_type"]),
            der.tlv(0xA0, der.octet_string(item["econtent"])),
        ),
        der.tlv(0xA0, actual_certificate),
        der.set_of(signer_info),
    )
    return der.sequence(
        der.object_identifier("1.2.840.113549.1.7.2"),
        der.tlv(0xA0, rebuilt),
    )


def mutate_last_bit_string(source: bytes) -> bytes:
    root, end = parse_one(source)
    if end != len(source):
        raise ValueError("trailing DER")
    fields = root.children()
    signature = fields[-1]
    if signature.tag != 0x03 or len(signature.value) < 2:
        raise ValueError("missing signature BIT STRING")
    damaged = bytearray(signature.value)
    damaged[-1] ^= 1
    return der.sequence(
        *(field.encoded for field in fields[:-1]),
        der.tlv(0x03, bytes(damaged)),
    )


def certificate_alg_mismatch(certificate: bytes) -> bytes:
    root, end = parse_one(certificate)
    if end != len(certificate):
        raise ValueError("trailing certificate DER")
    fields = root.children()
    return der.sequence(
        fields[0].encoded,
        der.algorithm_identifier(OID_ML_DSA_65),
        fields[2].encoded,
    )


def classify_cms(data: bytes) -> list[str]:
    try:
        item = inspect_signed_object(data)
    except (IndexError, ValueError) as error:
        return [f"der:{error}"]
    failures = []
    if item["digest_algorithms"] != [(OID_SHA512, True)]:
        failures.append("digestAlgorithms")
    if item["digest_algorithm"] != (OID_SHA512, True):
        failures.append("signerInfo.digestAlgorithm")
    if item["signature_algorithm"] != (COMPOSITE_OID, True):
        failures.append("signatureAlgorithm")
    signature = item["signature"]
    assert isinstance(signature, bytes)
    if len(signature) < MLDSA65_SIGNATURE_BYTES + 8:
        failures.append("signature.truncated")
    return failures


def classify_pure_mldsa65_cms(data: bytes) -> list[str]:
    try:
        item = inspect_signed_object(data)
    except (IndexError, ValueError) as error:
        return [f"der:{error}"]
    failures = []
    if item["digest_algorithms"] != [(OID_SHA512, True)]:
        failures.append("digestAlgorithms")
    if item["digest_algorithm"] != (OID_SHA512, True):
        failures.append("signerInfo.digestAlgorithm")
    if item["signature_algorithm"] != (OID_ML_DSA_65, True):
        failures.append("signatureAlgorithm")
    signature = item["signature"]
    assert isinstance(signature, bytes)
    if len(signature) != MLDSA65_SIGNATURE_BYTES:
        failures.append("signature.length")
    return failures


def compile_cms_helper(openssl: str, output: Path, env: dict[str, str]) -> Path:
    prefix = Path(openssl).resolve().parents[1]
    executable = output / "cms-api-probe"
    process = subprocess.run(
        [
            "cc",
            str(ROOT / "tools" / "cms_api_probe.c"),
            "-I",
            str(prefix / "include"),
            "-L",
            str(prefix / "lib64"),
            f"-Wl,-rpath,{prefix / 'lib64'}",
            "-lcrypto",
            "-o",
            str(executable),
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    if process.returncode:
        raise RuntimeError(process.stderr)
    return executable


def sign_manifest(
    *,
    openssl: str,
    cms_helper: Path,
    repository: Path,
    manifest_relative: Path,
    signer: Path,
    key: Path,
    digest: str,
    api: bool,
    scratch: Path,
    env: dict[str, str],
) -> None:
    manifest_path = repository / manifest_relative
    parsed = inspect_signed_object(manifest_path.read_bytes())
    details = parse_manifest_econtent(parsed["econtent"])
    directory = manifest_path.parent
    content = manifest_econtent(
        [
            (entry["file"], (directory / entry["file"]).read_bytes())
            for entry in details["entries"]
        ],
        manifest_number=int(details["manifest_number"]),
        this_update=str(details["this_update"]),
        next_update=str(details["next_update"]),
    )
    econtent = scratch / f"{manifest_relative.as_posix().replace('/', '-')}.econtent"
    econtent.write_bytes(content)
    if api:
        command = [
            str(cms_helper),
            digest,
            str(key),
            str(signer),
            str(econtent),
            OID_CT_MFT,
            str(manifest_path),
        ]
    else:
        command = [
            openssl,
            "cms",
            "-sign",
            "-binary",
            "-in",
            str(econtent),
            "-signer",
            str(signer),
            "-inkey",
            str(key),
            "-md",
            digest,
            "-outform",
            "DER",
            "-out",
            str(manifest_path),
            "-nosmimecap",
            "-nodetach",
            "-keyid",
            "-econtent_type",
            OID_CT_MFT,
        ]
    process = subprocess.run(
        command, env=env, capture_output=True, text=True
    )
    if process.returncode:
        raise RuntimeError(process.stderr)


def materialize_case(
    *,
    output: Path,
    name: str,
    fixture: Path,
    target: Path | None,
    data: bytes | None,
) -> Path:
    case = output / "repositories" / name
    repository = case / "repository"
    shutil.copytree(fixture / "repository", repository)
    shutil.copyfile(fixture / "test.tal", case / "test.tal")
    if target is not None and data is not None:
        (repository / target).write_bytes(data)
    return case


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument(
        "--pure-fixture", type=Path, default=DEFAULT_PURE_FIXTURE
    )
    parser.add_argument(
        "--pure-private", type=Path, default=DEFAULT_PURE_PRIVATE
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--openssl", required=True)
    parser.add_argument("--rpki-client", required=True)
    args = parser.parse_args()
    fixture = args.fixture.resolve()
    pure_fixture = args.pure_fixture.resolve()
    pure_private = args.pure_private.resolve()
    output = args.output.resolve()
    reset_generated_directory(output, allowed_root=ROOT / "local")
    env = os.environ.copy()
    cms_helper = compile_cms_helper(args.openssl, output, env)
    routinator_cases: dict[str, str] = {}
    file_cache = output / "file-cache"
    prepare_cache(fixture, file_cache)

    roa = (fixture / "repository" / "child" / "route.roa").read_bytes()
    item = inspect_signed_object(roa)
    signature = item["signature"]
    assert isinstance(signature, bytes)
    mutations: dict[str, bytes] = {}

    damaged_mldsa = bytearray(signature)
    damaged_mldsa[0] ^= 1
    mutations["component-mldsa-corrupt"] = rebuild_cms(
        roa, signature=bytes(damaged_mldsa)
    )
    damaged_ecdsa = bytearray(signature)
    damaged_ecdsa[MLDSA65_SIGNATURE_BYTES] ^= 1
    mutations["component-ecdsa-corrupt"] = rebuild_cms(
        roa, signature=bytes(damaged_ecdsa)
    )
    mutations["component-order-reversed"] = rebuild_cms(
        roa,
        signature=signature[MLDSA65_SIGNATURE_BYTES:]
        + signature[:MLDSA65_SIGNATURE_BYTES],
    )
    mutations["signature-truncated"] = rebuild_cms(
        roa, signature=signature[:-1]
    )
    mutations["unsupported-signature-oid"] = rebuild_cms(
        roa, signature_oid=UNKNOWN_OID
    )
    mutations["signature-parameters-present"] = rebuild_cms(
        roa, signature_null=True
    )
    mutations["cms-signature-corrupt"] = rebuild_cms(
        roa, signature=bytes(damaged_mldsa)
    )
    mutations["cms-sha256-intrusion"] = rebuild_cms(
        roa, digest_oid=SHA256_OID
    )

    results: list[dict[str, object]] = []
    for name, data in mutations.items():
        path = output / f"{name}.roa"
        path.write_bytes(data)
        observed = command_result(
            [
                args.openssl, "cms", "-verify", "-inform", "DER", "-binary",
                "-in", str(path), "-noverify", "-out", os.devnull,
            ],
            env,
        )
        rpki = command_result(
            [
                args.rpki_client, "-x", "-d",
                str(file_cache), "-t",
                str(fixture / "test.tal"), "-vv", "-f", str(path),
            ],
            env,
        )
        rpki_text = f"{rpki['stdout']}\n{rpki['stderr']}"
        rpki_rejected = (
            "Validation:               N/A" in rpki_text
            or "CMS verification error" in rpki_text
        )
        results.append(
            {
                "name": name,
                "reason_code": REASON_CODES[name],
                "class": "CMS",
                "expected": "reject",
                "profile_failures": classify_cms(data),
                "openssl": observed,
                "rpki_client": rpki,
                "rejected": rpki_rejected,
            }
        )
        case = materialize_case(
            output=output,
            name=name,
            fixture=fixture,
            target=Path("child/route.roa"),
            data=data,
        )
        sign_manifest(
            openssl=args.openssl,
            cms_helper=cms_helper,
            repository=case / "repository",
            manifest_relative=Path("child/child.mft"),
            signer=fixture / "private" / "child-mft-ee.pem",
            key=fixture / "private" / "child-mft-ee.key",
            digest="sha512",
            api=False,
            scratch=output,
            env=env,
        )
        routinator_cases[name] = str(case)

    pure_roa = (pure_fixture / "repository" / "route.roa").read_bytes()
    pure_item = inspect_signed_object(pure_roa)
    pure_signature = pure_item["signature"]
    assert isinstance(pure_signature, bytes)
    damaged_pure = bytearray(pure_signature)
    damaged_pure[0] ^= 1
    pure_mutations = {
        "pure-signature-corrupt": rebuild_cms(
            pure_roa,
            signature=bytes(damaged_pure),
            signature_oid=OID_ML_DSA_65,
        ),
        "pure-signature-parameters-present": rebuild_cms(
            pure_roa,
            signature_oid=OID_ML_DSA_65,
            signature_null=True,
        ),
        "pure-cms-sha256-intrusion": rebuild_cms(
            pure_roa,
            signature_oid=OID_ML_DSA_65,
            digest_oid=SHA256_OID,
        ),
    }
    for name, data in pure_mutations.items():
        path = output / f"{name}.roa"
        path.write_bytes(data)
        observed = command_result(
            [
                args.openssl, "cms", "-verify", "-inform", "DER", "-binary",
                "-in", str(path), "-noverify", "-out", os.devnull,
            ],
            env,
        )
        rpki = command_result(
            [
                args.rpki_client, "-x", "-d", str(file_cache), "-t",
                str(fixture / "test.tal"), "-vv", "-f", str(path),
            ],
            env,
        )
        rpki_text = f"{rpki['stdout']}\n{rpki['stderr']}"
        rpki_rejected = (
            "Validation:               N/A" in rpki_text
            or "CMS verification error" in rpki_text
            or "parameters MUST be absent" in rpki_text
            or "CMS digest is" in rpki_text
        )
        results.append(
            {
                "name": name,
                "reason_code": REASON_CODES[name],
                "class": "CMS",
                "expected": "reject",
                "profile_failures": classify_pure_mldsa65_cms(data),
                "openssl": observed,
                "rpki_client": rpki,
                "rejected": rpki_rejected,
            }
        )
        case = materialize_case(
            output=output,
            name=name,
            fixture=pure_fixture,
            target=Path("route.roa"),
            data=data,
        )
        sign_manifest(
            openssl=args.openssl,
            cms_helper=cms_helper,
            repository=case / "repository",
            manifest_relative=Path("manifest.mft"),
            signer=pure_private / "manifest-ee.pem",
            key=pure_private / "manifest-ee.key",
            digest="sha512",
            api=True,
            scratch=output,
            env=env,
        )
        routinator_cases[name] = str(case)

    crl = fixture / "repository" / "child" / "child.crl"
    corrupt_crl = output / "crl-signature-corrupt.crl"
    corrupt_crl.write_bytes(mutate_last_bit_string(crl.read_bytes()))
    child_pem = fixture / "private" / "child-ca.pem"
    crl_observed = command_result(
        [
            args.openssl, "crl", "-inform", "DER", "-in", str(corrupt_crl),
            "-CAfile", str(child_pem), "-verify", "-noout",
        ],
        env,
    )
    results.append(
        {
            "name": "crl-signature-corrupt",
            "reason_code": REASON_CODES["crl-signature-corrupt"],
            "class": "CRL",
            "expected": "reject",
            "openssl": crl_observed,
            "rejected": crl_observed["returncode"] != 0,
        }
    )
    crl_case = materialize_case(
        output=output,
        name="crl-signature-corrupt",
        fixture=fixture,
        target=Path("child/child.crl"),
        data=corrupt_crl.read_bytes(),
    )
    sign_manifest(
        openssl=args.openssl,
        cms_helper=cms_helper,
        repository=crl_case / "repository",
        manifest_relative=Path("child/child.mft"),
        signer=fixture / "private" / "child-mft-ee.pem",
        key=fixture / "private" / "child-mft-ee.key",
        digest="sha512",
        api=False,
        scratch=output,
        env=env,
    )
    routinator_cases["crl-signature-corrupt"] = str(crl_case)

    cms_root = parse_one(roa)[0]
    ee_der = cms_root.children()[1].children()[0].children()[3].children()[0].encoded
    mismatch = output / "tbs-outer-signature-mismatch.cer"
    mismatch.write_bytes(certificate_alg_mismatch(ee_der))
    mismatch_pem = mismatch.with_suffix(".pem")
    conversion = command_result(
        [
            args.openssl, "x509", "-inform", "DER", "-in", str(mismatch),
            "-out", str(mismatch_pem),
        ],
        env,
    )
    if conversion["returncode"] != 0:
        raise RuntimeError(str(conversion))
    mismatch_observed = command_result(
        [
            args.openssl, "verify", "-partial_chain", "-CAfile", str(child_pem),
            str(mismatch_pem),
        ],
        env,
    )
    results.append(
        {
            "name": "tbs-outer-signature-mismatch",
            "reason_code": REASON_CODES["tbs-outer-signature-mismatch"],
            "class": "certificate",
            "expected": "reject",
            "openssl": mismatch_observed,
            "rejected": mismatch_observed["returncode"] != 0,
        }
    )
    mismatch_roa = rebuild_cms(roa, certificate_der=mismatch.read_bytes())
    mismatch_case = materialize_case(
        output=output,
        name="tbs-outer-signature-mismatch",
        fixture=fixture,
        target=Path("child/route.roa"),
        data=mismatch_roa,
    )
    sign_manifest(
        openssl=args.openssl,
        cms_helper=cms_helper,
        repository=mismatch_case / "repository",
        manifest_relative=Path("child/child.mft"),
        signer=fixture / "private" / "child-mft-ee.pem",
        key=fixture / "private" / "child-mft-ee.key",
        digest="sha512",
        api=False,
        scratch=output,
        env=env,
    )
    routinator_cases["tbs-outer-signature-mismatch"] = str(mismatch_case)

    path_invalid = output / "certificate-path-invalid.cer"
    path_invalid.write_bytes(
        mutate_last_bit_string((fixture / "repository" / "child.cer").read_bytes())
    )
    path_invalid_pem = path_invalid.with_suffix(".pem")
    conversion = command_result(
        [
            args.openssl, "x509", "-inform", "DER", "-in", str(path_invalid),
            "-out", str(path_invalid_pem),
        ],
        env,
    )
    if conversion["returncode"] != 0:
        raise RuntimeError(str(conversion))
    parent_pem = fixture / "private" / "ta.pem"
    path_observed = command_result(
        [
            args.openssl, "verify", "-CAfile", str(parent_pem),
            str(path_invalid_pem),
        ],
        env,
    )
    results.append(
        {
            "name": "certificate-path-invalid",
            "reason_code": REASON_CODES["certificate-path-invalid"],
            "class": "certificate-path",
            "expected": "reject",
            "openssl": path_observed,
            "rejected": path_observed["returncode"] != 0,
        }
    )
    path_case = materialize_case(
        output=output,
        name="certificate-path-invalid",
        fixture=fixture,
        target=Path("child.cer"),
        data=path_invalid.read_bytes(),
    )
    sign_manifest(
        openssl=args.openssl,
        cms_helper=cms_helper,
        repository=path_case / "repository",
        manifest_relative=Path("ta.mft"),
        signer=fixture / "private" / "ta-mft-ee.pem",
        key=fixture / "private" / "ta-mft-ee.key",
        digest="sha256",
        api=False,
        scratch=output,
        env=env,
    )
    routinator_cases["certificate-path-invalid"] = str(path_case)

    bad_repo = output / "manifest-hash-repository"
    shutil.copytree(fixture / "repository", bad_repo)
    bad_roa = bad_repo / "child" / "route.roa"
    content = bytearray(bad_roa.read_bytes())
    content[-1] ^= 1
    bad_roa.write_bytes(content)
    manifest = inspect_signed_object((bad_repo / "child" / "child.mft").read_bytes())
    expected_hash = hashlib.sha256(
        (fixture / "repository" / "child" / "route.roa").read_bytes()
    ).hexdigest()
    actual_hash = hashlib.sha256(bad_roa.read_bytes()).hexdigest()
    bad_cache = output / "manifest-hash-cache"
    (bad_cache / "example.invalid" / "repository").mkdir(parents=True)
    (bad_cache / "ta" / "test").mkdir(parents=True)
    shutil.copytree(
        bad_repo,
        bad_cache / "example.invalid" / "repository",
        dirs_exist_ok=True,
    )
    shutil.copyfile(
        bad_repo / "ta.cer", bad_cache / "ta" / "test" / "ta.cer"
    )
    bad_output = output / "manifest-hash-output"
    bad_output.mkdir()
    manifest_rpki = command_result(
        [
            args.rpki_client, "-x", "-n", "-d", str(bad_cache), "-t",
            str(fixture / "test.tal"), "-j", "-vv", str(bad_output),
        ],
        env,
    )
    manifest_text = f"{manifest_rpki['stdout']}\n{manifest_rpki['stderr']}"
    results.append(
        {
            "name": "manifest-hash-mismatch",
            "reason_code": REASON_CODES["manifest-hash-mismatch"],
            "class": "Manifest",
            "expected": "reject",
            "manifest_econtent_bytes": len(manifest["econtent"]),
            "expected_hash": expected_hash,
            "actual_hash": actual_hash,
            "rpki_client": manifest_rpki,
            "rejected": (
                expected_hash != actual_hash
                and (
                    "route.roa: bad message digest" in manifest_text
                    or "Route Origin Authorizations: 0" in manifest_text
                )
            ),
        }
    )
    manifest_case = output / "repositories" / "manifest-hash-mismatch"
    shutil.copytree(bad_repo, manifest_case / "repository")
    shutil.copyfile(fixture / "test.tal", manifest_case / "test.tal")
    routinator_cases["manifest-hash-mismatch"] = str(manifest_case)

    summary = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "classification": "generated negative fixtures; artifacts stay local",
        "results": results,
        "all_rejected": all(result["rejected"] for result in results),
        "routinator_repositories": routinator_cases,
    }
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    public_summary = {
        "warning": summary["warning"],
        "classification": (
            "sanitized small-scale negative-test results; raw fixtures and "
            "validator logs stay below local/"
        ),
        "all_rejected": summary["all_rejected"],
        "results": [
            {
                key: result[key]
                for key in ("name", "reason_code", "class", "expected", "rejected")
            }
            | {"profile_failures": result.get("profile_failures", [])}
            for result in results
        ],
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(
        json.dumps(public_summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    if not summary["all_rejected"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
