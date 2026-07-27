#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import tempfile
import json
import base64
import platform
import argparse
from datetime import datetime, timezone
from pathlib import Path

from pqc_rpki_lab.cms import (
    assemble_mldsa65_signed_object,
    profile_check,
    sign_raw_mldsa,
    signed_attributes,
    verify_raw_signature,
)
from pqc_rpki_lab.result_io import markdown_table, write_csv, write_json
from pqc_rpki_lab.rpki_asn1 import OID_CT_MFT, OID_CT_ROA, manifest_econtent, roa_econtent

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT
RESULTS = ROOT / "results" / "rpki-objects"
TESTDATA = ROOT / "testdata"
CMS_RESULTS = ROOT / "results" / "cms-generation"
CMS_API_SOURCE = ROOT / "tools" / "cms_api_probe.c"
BASE_URI = "rsync://example.invalid:8873/repository/"

ALGORITHMS = (
    ("RSA-2048/SHA-256", "rsa", "RSA", ["-pkeyopt", "rsa_keygen_bits:2048"]),
    ("ML-DSA-44", "ml-dsa-44", "ML-DSA-44", []),
    ("ML-DSA-65", "ml-dsa-65", "ML-DSA-65", []),
    ("ML-DSA-87", "ml-dsa-87", "ML-DSA-87", []),
    (
        "ML-DSA-65 + ECDSA P-256",
        "composite-mldsa65-p256",
        "MLDSA65-ECDSA-P256-SHA512",
        [],
    ),
)


def reason_for(process: subprocess.CompletedProcess[str], fallback: str) -> str:
    text = (process.stderr or process.stdout).strip()
    return text.splitlines()[-1] if text else fallback


def config_text(directory: Path) -> str:
    return f"""# EXPERIMENTAL / NOT FOR PRODUCTION
[ca]
default_ca=CA_default
[CA_default]
dir={directory}
database=$dir/index.txt
new_certs_dir=$dir
certificate=$dir/ca.pem
private_key=$dir/ca.key
serial=$dir/serial
crlnumber=$dir/crlnumber
default_days=1
default_crl_days=1
default_md=default
policy=policy
x509_extensions=roa_ext
crl_extensions=crl_ext
copy_extensions=none
unique_subject=no
[policy]
commonName=supplied
[req]
distinguished_name=dn
prompt=no
x509_extensions=ca_ext
[dn]
CN=EXPERIMENTAL PQC RPKI
[ca_ext]
basicConstraints=critical,CA:true
keyUsage=critical,keyCertSign,cRLSign
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always
certificatePolicies=critical,1.3.6.1.5.5.7.14.2
subjectInfoAccess=caRepository;URI:{BASE_URI},rpkiManifest;URI:{BASE_URI}manifest.mft
sbgp-ipAddrBlock=critical,@ca_ip
sbgp-autonomousSysNum=critical,@ca_as
[ca_ip]
IPv4=192.0.2.0/24
IPv6=2001:db8::/32
[ca_as]
AS.0=64496
[roa_ext]
keyUsage=critical,digitalSignature
certificatePolicies=critical,1.3.6.1.5.5.7.14.2
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid
crlDistributionPoints=URI:{BASE_URI}ca.crl
authorityInfoAccess=caIssuers;URI:{BASE_URI}ca.cer
sbgp-ipAddrBlock=critical,@roa_ip
subjectInfoAccess=signedObject;URI:{BASE_URI}route.roa
[roa_ip]
IPv4=192.0.2.0/24
IPv6=2001:db8::/32
[mft_ext]
keyUsage=critical,digitalSignature
certificatePolicies=critical,1.3.6.1.5.5.7.14.2
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid
crlDistributionPoints=URI:{BASE_URI}ca.crl
authorityInfoAccess=caIssuers;URI:{BASE_URI}ca.cer
subjectInfoAccess=signedObject;URI:{BASE_URI}manifest.mft
sbgp-ipAddrBlock=critical,@mft_ip
sbgp-autonomousSysNum=critical,@mft_as
[mft_ip]
IPv4=inherit
IPv6=inherit
[mft_as]
AS.0=inherit
[crl_ext]
authorityKeyIdentifier=keyid:always
"""


def run(command: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout)


def copy_public(path: Path, destination: Path) -> int:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, destination)
    return destination.stat().st_size


def openssl_asn1parse(openssl: str, path: Path, out: Path) -> None:
    result = run([openssl, "asn1parse", "-inform", "DER", "-in", str(path)])
    out.parent.mkdir(parents=True, exist_ok=True)
    text = result.stdout + result.stderr
    out.write_text("\n".join(line.rstrip() for line in text.splitlines()) + "\n")


def extract_ski(openssl: str, certificate: Path) -> bytes:
    result = run([openssl, "x509", "-in", str(certificate), "-noout", "-ext", "subjectKeyIdentifier"])
    if result.returncode:
        raise RuntimeError(reason_for(result, "cannot extract Subject Key Identifier"))
    hex_text = "".join(line.strip() for line in result.stdout.splitlines()[1:]).replace(":", "")
    return bytes.fromhex(hex_text)


def manual_mldsa65_cms(
    openssl: str, content: Path, signer_pem: Path, signer_der: Path, key: Path,
    output: Path, econtent_type: str, result_root: Path,
) -> tuple[bool, str]:
    signing_time = datetime.now(timezone.utc).strftime("%y%m%d%H%M%SZ")
    econtent = content.read_bytes()
    signed = signed_attributes(econtent_type, econtent, signing_time)
    signature = sign_raw_mldsa(openssl, key, signed)
    ski = extract_ski(openssl, signer_pem)
    output.write_bytes(assemble_mldsa65_signed_object(
        econtent_type=econtent_type,
        econtent=econtent,
        ee_certificate_der=signer_der.read_bytes(),
        subject_key_identifier=ski,
        signature=signature,
        signing_time=signing_time,
    ))
    public_key = output.with_suffix(output.suffix + ".pub.pem")
    key_result = run([openssl, "x509", "-in", str(signer_pem), "-pubkey", "-noout"])
    public_key.write_text(key_result.stdout)
    report = profile_check(output.read_bytes(), expected_econtent_type=econtent_type, expected_ski=ski)
    report["raw_signature_valid"] = verify_raw_signature(openssl, public_key, output.read_bytes())
    public_key.unlink(missing_ok=True)
    report["valid"] = bool(report["valid"] and report["raw_signature_valid"])
    report_path = result_root / f"{output.name}.profile.json"
    write_json(report_path, report)
    cms_print = run([openssl, "cms", "-cmsout", "-print", "-inform", "DER", "-in", str(output)])
    (result_root / f"{output.name}.cms-print.txt").write_text(cms_print.stdout + cms_print.stderr)
    return bool(report["valid"] and cms_print.returncode == 0), "" if report["valid"] else "internal CMS profile or signature verification failed"


def compile_cms_api_probe(directory: Path) -> Path | None:
    compiler = shutil.which("cc")
    pkg_config = shutil.which("pkg-config")
    if not compiler or not pkg_config:
        return None
    flags = run([pkg_config, "--cflags", "--libs", "openssl"])
    if flags.returncode:
        return None
    executable = directory / "cms-api-probe"
    process = run([
        compiler, "-O2", "-Wall", "-Wextra", "-Werror", str(CMS_API_SOURCE),
        "-o", str(executable), *flags.stdout.split(),
    ])
    return executable if process.returncode == 0 else None


def api_mldsa65_cms(
    executable: Path, openssl: str, content: Path, signer_pem: Path, key: Path,
    output: Path, econtent_type: str, result_root: Path,
) -> tuple[bool, str]:
    process = run([
        str(executable), "sha512", str(key), str(signer_pem), str(content),
        econtent_type, str(output),
    ])
    if process.returncode:
        return False, reason_for(process, "OpenSSL CMS API generation failed")
    ski = extract_ski(openssl, signer_pem)
    report = profile_check(output.read_bytes(), expected_econtent_type=econtent_type, expected_ski=ski)
    public_key = output.with_suffix(output.suffix + ".pub.pem")
    key_result = run([openssl, "x509", "-in", str(signer_pem), "-pubkey", "-noout"])
    public_key.write_text(key_result.stdout)
    report["raw_signature_valid"] = verify_raw_signature(openssl, public_key, output.read_bytes())
    public_key.unlink(missing_ok=True)
    report["valid"] = bool(report["valid"] and report["raw_signature_valid"])
    write_json(result_root / f"{output.name}.api-profile.json", report)
    return bool(report["valid"]), "" if report["valid"] else "API CMS failed the RFC 6488/RFC 9589/RFC 9882 profile check"


def compare_cms_paths(api_path: Path, manual_path: Path, output: Path) -> None:
    from pqc_rpki_lab.cms import inspect_signed_object

    api = inspect_signed_object(api_path.read_bytes())
    manual = inspect_signed_object(manual_path.read_bytes())
    ignored = {"signature", "signed_attrs_der", "attributes"}
    fields = sorted(set(api) - ignored)
    comparisons = {field: api[field] == manual[field] for field in fields}
    report = {
        "structurally_equivalent": all(comparisons.values()),
        "field_comparison": comparisons,
        "der_identical": api_path.read_bytes() == manual_path.read_bytes(),
        "explanation": "DER is expected to differ because ML-DSA signatures are randomized and signing-time may differ; all profile-relevant structural fields are compared separately.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def issue_ee(
    openssl: str, directory: Path, config: Path, provider_name: str,
    options: list[str], prefix: str, common_name: str, extension: str,
) -> tuple[Path, Path, Path, subprocess.CompletedProcess[str]]:
    key = directory / f"{prefix}.key"
    csr = directory / f"{prefix}.csr"
    pem = directory / f"{prefix}.pem"
    der_path = directory / f"{prefix}.cer"
    key_result = run([openssl, "genpkey", "-algorithm", provider_name, *options, "-out", str(key)])
    csr_result = run([openssl, "req", "-new", "-key", str(key), "-subj", f"/CN={common_name}", "-out", str(csr)]) if key_result.returncode == 0 else key_result
    ca_options = (
        ["-md", "sha512"]
        if provider_name == "MLDSA65-ECDSA-P256-SHA512"
        else []
    )
    result = run([
        openssl, "ca", "-batch", "-config", str(config), "-extensions", extension,
        *ca_options, "-in", str(csr), "-out", str(pem),
    ]) if csr_result.returncode == 0 else csr_result
    if result.returncode == 0:
        run([openssl, "x509", "-in", str(pem), "-outform", "DER", "-out", str(der_path)])
    return key, pem, der_path, result


def certificate_manifest_times(openssl: str, certificate: Path) -> tuple[str, str]:
    result = run([openssl, "x509", "-in", str(certificate), "-noout", "-dates"])
    if result.returncode:
        raise RuntimeError(reason_for(result, "cannot read certificate validity"))
    values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    parser = "%b %d %H:%M:%S %Y GMT"
    return tuple(
        datetime.strptime(values[field], parser).replace(tzinfo=timezone.utc).strftime("%Y%m%d%H%M%SZ")
        for field in ("notBefore", "notAfter")
    )


def write_validator_repository(openssl: str, slug: str, ca_pem: Path, artifact_root: Path) -> None:
    required = ("ca.cer", "ca.crl", "route.roa", "manifest.mft")
    if not all((artifact_root / name).exists() for name in required):
        return
    root = TESTDATA / "validator" / slug
    repository = root / "repository"
    repository.mkdir(parents=True, exist_ok=True)
    for name in required:
        shutil.copyfile(artifact_root / name, repository / name)
    public = run([openssl, "x509", "-in", str(ca_pem), "-pubkey", "-noout"])
    with tempfile.TemporaryDirectory(prefix="pqc-rpki-tal-") as name:
        pem = Path(name) / "public.pem"
        pem.write_text(public.stdout)
        der_result = subprocess.run(
            [openssl, "pkey", "-pubin", "-in", str(pem), "-outform", "DER"],
            capture_output=True,
        )
    encoded = base64.b64encode(der_result.stdout).decode("ascii")
    wrapped = "\n".join(encoded[index:index + 64] for index in range(0, len(encoded), 64))
    (root / "test.tal").write_text(
        f"{BASE_URI}ca.cer\n\n" + wrapped + "\n"
    )


def sign_cms(
    openssl: str,
    content: Path,
    signer: Path,
    key: Path,
    output: Path,
    econtent_type: str,
    digest: str,
) -> subprocess.CompletedProcess[str]:
    return run([
        openssl, "cms", "-sign", "-binary", "-in", str(content),
        "-signer", str(signer), "-inkey", str(key),
        "-md", digest,
        "-outform", "DER", "-out", str(output), "-nosmimecap", "-nodetach",
        "-keyid", "-econtent_type", econtent_type,
    ])


def verify_cms(openssl: str, cms: Path, ca: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return run([
        openssl, "cms", "-verify", "-inform", "DER", "-in", str(cms),
        "-CAfile", str(ca), "-out", str(output), "-binary",
    ])


def generate_algorithm(openssl: str, display: str, slug: str, provider_name: str, options: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    artifact_root = TESTDATA / slug
    result_root = RESULTS / slug
    with tempfile.TemporaryDirectory(prefix=f"pqc-rpki-{slug}-objects-") as name:
        directory = Path(name)
        cms_api_probe = compile_cms_api_probe(directory) if slug == "ml-dsa-65" else None
        (directory / "index.txt").touch()
        (directory / "serial").write_text("1000\n")
        (directory / "crlnumber").write_text("1000\n")
        config = directory / "openssl.cnf"
        config.write_text(config_text(directory))
        ca_key = directory / "ca.key"
        ca_pem = directory / "ca.pem"
        ca_der = directory / "ca.cer"
        crl_pem = directory / "ca.crl.pem"
        crl_der = directory / "ca.crl"
        roa_content = directory / "route.roa.econtent"
        mft_content = directory / "manifest.mft.econtent"
        roa_cms = directory / "route.roa"
        mft_cms = directory / "manifest.mft"
        verified_roa = directory / "route.roa.verified"
        verified_mft = directory / "manifest.mft.verified"

        roa_content.write_bytes(roa_econtent(64496, [("192.0.2.0/24", 24), ("2001:db8::/32", 48)]))

        key_result = run([openssl, "genpkey", "-algorithm", provider_name, *options, "-out", str(ca_key)])
        if key_result.returncode:
            rows.append({
                "algorithm": display, "artifact": "key-generation", "status": "unsupported",
                "classification": "provider-algorithm-unavailable", "bytes": "",
                "public_path": "", "reason": reason_for(key_result, "key generation failed"),
            })
            return rows

        ca_result = run([
            openssl, "req", "-new", "-x509", "-key", str(ca_key), "-config", str(config),
            "-extensions", "ca_ext", "-days", "1", "-out", str(ca_pem),
        ])
        if ca_result.returncode:
            rows.append({
                "algorithm": display, "artifact": "CA certificate", "status": "blocked",
                "classification": "x509-generation-failed", "bytes": "",
                "public_path": "", "reason": reason_for(ca_result, "CA generation failed"),
            })
            return rows
        run([openssl, "x509", "-in", str(ca_pem), "-outform", "DER", "-out", str(ca_der)])

        roa_key, roa_pem, roa_der, roa_ee_result = issue_ee(
            openssl, directory, config, provider_name, options,
            "route-ee", "EXPERIMENTAL ROA EE", "roa_ext",
        )
        mft_key, mft_pem, mft_der, mft_ee_result = issue_ee(
            openssl, directory, config, provider_name, options,
            "manifest-ee", "EXPERIMENTAL MANIFEST EE", "mft_ext",
        )
        ee_result = roa_ee_result if roa_ee_result.returncode else mft_ee_result
        if ee_result.returncode:
            rows.append({
                "algorithm": display, "artifact": "EE certificate", "status": "blocked",
                "classification": "certificate-signing-failed", "bytes": "",
                "public_path": "", "reason": reason_for(ee_result, "EE generation failed"),
            })
            return rows
        crl_options = (
            ["-md", "sha512"]
            if provider_name == "MLDSA65-ECDSA-P256-SHA512"
            else []
        )
        crl_result = run([
            openssl, "ca", "-gencrl", "-config", str(config),
            *crl_options, "-out", str(crl_pem),
        ])
        if crl_result.returncode == 0:
            run([openssl, "crl", "-in", str(crl_pem), "-outform", "DER", "-out", str(crl_der)])

        public_artifacts = [
            ("CA certificate", ca_der, artifact_root / "ca.cer"),
            ("ROA EE certificate", roa_der, artifact_root / "route.ee.cer"),
            ("Manifest EE certificate", mft_der, artifact_root / "manifest.ee.cer"),
        ]
        if crl_der.exists():
            public_artifacts.append(("CRL", crl_der, artifact_root / "ca.crl"))
        for artifact, source, destination in public_artifacts:
            size = copy_public(source, destination)
            openssl_asn1parse(openssl, destination, result_root / f"{destination.name}.asn1.txt")
            rows.append({
                "algorithm": display, "artifact": artifact, "status": "confirmed",
                "classification": "public-der-fixture", "bytes": size,
                "public_path": str(destination.relative_to(OUTPUT_ROOT)), "reason": "",
            })

        this_update, next_update = certificate_manifest_times(openssl, mft_pem)
        mft_content.write_bytes(manifest_econtent([
            ("route.roa", roa_content.read_bytes()),
            ("ca.crl", crl_der.read_bytes() if crl_der.exists() else b""),
        ], this_update=this_update, next_update=next_update))
        for artifact, source in (("ROA eContent", roa_content), ("Manifest eContent", mft_content)):
            destination = artifact_root / source.name
            size = copy_public(source, destination)
            openssl_asn1parse(openssl, destination, result_root / f"{source.name}.asn1.txt")
            rows.append({
                "algorithm": display, "artifact": artifact, "status": "confirmed",
                "classification": "rpki-econtent-der", "bytes": size,
                "public_path": str(destination.relative_to(OUTPUT_ROOT)), "reason": "",
            })

        cms_targets = (
            ("ROA CMS", roa_content, roa_cms, OID_CT_ROA, verified_roa, roa_pem, roa_der, roa_key),
            ("Manifest CMS", mft_content, mft_cms, OID_CT_MFT, verified_mft, mft_pem, mft_der, mft_key),
        )
        for artifact, content, cms, oid, verified, signer_pem, signer_der, signer_key in cms_targets:
            if artifact == "Manifest CMS" and roa_cms.exists():
                mft_content.write_bytes(manifest_econtent([
                    ("route.roa", roa_cms.read_bytes()),
                    ("ca.crl", crl_der.read_bytes() if crl_der.exists() else b""),
                ], this_update=this_update, next_update=next_update))
                copy_public(mft_content, artifact_root / mft_content.name)
                openssl_asn1parse(openssl, artifact_root / mft_content.name, result_root / f"{mft_content.name}.asn1.txt")
            cms_digest = "sha256" if slug == "rsa" else "sha512"
            cms_result = sign_cms(
                openssl, content, signer_pem, signer_key, cms, oid, cms_digest,
            )
            if cms_result.returncode == 0:
                verify_result = verify_cms(openssl, cms, ca_pem, verified)
                destination = artifact_root / cms.name
                size = copy_public(cms, destination)
                openssl_asn1parse(openssl, destination, result_root / f"{cms.name}.asn1.txt")
                rows.append({
                    "algorithm": display, "artifact": artifact,
                    "status": "confirmed" if verify_result.returncode == 0 else "blocked",
                    "classification": "rfc6488-cms-generated",
                    "bytes": size,
                    "public_path": str(destination.relative_to(OUTPUT_ROOT)),
                    "reason": "" if verify_result.returncode == 0 else reason_for(verify_result, "CMS verify failed"),
                })
            else:
                log_path = result_root / f"{cms.name}.cms-error.txt"
                log_path.parent.mkdir(parents=True, exist_ok=True)
                public_log = (cms_result.stdout + cms_result.stderr).replace(
                    str(directory), f"$TMPDIR/pqc-rpki-{slug}-objects"
                )
                log_path.write_text(public_log)
                if slug == "ml-dsa-65":
                    manual_cms = directory / f"{cms.name}.manual"
                    manual_valid, manual_reason = manual_mldsa65_cms(
                        openssl, content, signer_pem, signer_der, signer_key, manual_cms, oid, result_root,
                    )
                    api_valid, api_reason = (False, "C compiler or pkg-config unavailable")
                    if cms_api_probe:
                        api_valid, api_reason = api_mldsa65_cms(
                            cms_api_probe, openssl, content, signer_pem, signer_key, cms, oid, result_root,
                        )
                    if api_valid and manual_valid:
                        compare_cms_paths(cms, manual_cms, result_root / f"{cms.name}.api-vs-manual.json")
                        manual_destination = artifact_root / f"{cms.name}.manual"
                        copy_public(manual_cms, manual_destination)
                    elif manual_valid:
                        shutil.copyfile(manual_cms, cms)
                    destination = artifact_root / cms.name
                    size = copy_public(cms, destination)
                    openssl_asn1parse(openssl, destination, result_root / f"{cms.name}.asn1.txt")
                    rows.append({
                        "algorithm": display, "artifact": artifact,
                        "status": "confirmed" if api_valid or manual_valid else "blocked",
                        "classification": "rfc6488-openssl-api-cms-generated" if api_valid else "rfc6488-manual-cms-generated",
                        "bytes": size,
                        "public_path": str(destination.relative_to(OUTPUT_ROOT)),
                        "reason": "" if api_valid or manual_valid else f"API: {api_reason}; manual: {manual_reason}",
                    })
                else:
                    rows.append({
                        "algorithm": display, "artifact": artifact, "status": "blocked",
                        "classification": "cms-signing-unavailable",
                        "bytes": "", "public_path": str(log_path.relative_to(OUTPUT_ROOT)),
                        "reason": reason_for(cms_result, "CMS signing failed"),
                    })
        write_validator_repository(openssl, slug, ca_pem, artifact_root)
    return rows


def main() -> None:
    global OUTPUT_ROOT, RESULTS, TESTDATA, CMS_RESULTS
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--algorithm",
        choices=[item[1] for item in ALGORITHMS],
        help="generate only one algorithm fixture",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        help=(
            "write results/ and testdata/ below this directory instead of "
            "modifying the repository fixture set"
        ),
    )
    parser.add_argument(
        "--openssl",
        help="OpenSSL executable; defaults to the first openssl on PATH",
    )
    args = parser.parse_args()
    if args.output_root:
        OUTPUT_ROOT = args.output_root.resolve()
        RESULTS = OUTPUT_ROOT / "results" / "rpki-objects"
        TESTDATA = OUTPUT_ROOT / "testdata"
        CMS_RESULTS = OUTPUT_ROOT / "results" / "cms-generation"
    openssl = args.openssl or shutil.which("openssl")
    rows: list[dict[str, object]] = []
    if not openssl:
        rows.append({
            "algorithm": "all", "artifact": "all", "status": "unsupported",
            "classification": "openssl-unavailable", "bytes": "", "public_path": "",
            "reason": "OpenSSL executable not found",
        })
    else:
        selected = (
            item for item in ALGORITHMS
            if args.algorithm is None or item[1] == args.algorithm
        )
        for display, slug, provider_name, options in selected:
            rows.extend(generate_algorithm(openssl, display, slug, provider_name, options))
    write_csv(RESULTS / "rpki-objects.csv", rows)
    write_json(RESULTS / "rpki-objects.json", {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "private_keys_persisted": False,
        "method": "OpenSSL-generated public certificates/CRLs plus minimal DER eContent encoders; private keys remain in deleted temporary directories.",
        "results": rows,
    })
    cms_rows = [row for row in rows if row["algorithm"] == "ML-DSA-65" and row["artifact"] in ("ROA CMS", "Manifest CMS")]
    write_json(CMS_RESULTS / "cms-generation.json", {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "openssl": run([openssl, "version", "-a"]).stdout if openssl else "",
        "backend": "OpenSSL CMS API with explicit EVP_sha512; independent manual DER reference path",
        "profile": "RFC 6488 as updated by RFC 9589, with RFC 9882 ML-DSA-65 conventions",
        "private_keys_persisted": False,
        "results": cms_rows,
    })
    CMS_RESULTS.mkdir(parents=True, exist_ok=True)
    (CMS_RESULTS / "cms-generation.md").write_text(
        "# ML-DSA-65 CMS Generation\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        "OpenSSL 3.6.2 succeeds through `CMS_add1_signer` when SHA-512 is supplied explicitly. "
        "The generated objects pass the internal profile, raw-signature, OpenSSL parser, and OpenSSL CMS verification checks.\n\n"
        + markdown_table(cms_rows, [
            ("artifact", "Artifact"), ("status", "Status"),
            ("classification", "Backend"), ("bytes", "Bytes"),
            ("public_path", "Public path"),
        ]) + "\n"
    )
    (RESULTS / "rpki-objects.md").write_text(
        "# RPKI Object Fixtures\n\n"
        "> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        "Private keys are generated in temporary directories and are not persisted. "
        "Public DER artifacts are stored under `testdata/`.\n\n"
        + markdown_table(rows, [
            ("algorithm", "Algorithm"), ("artifact", "Artifact"), ("status", "Status"),
            ("classification", "Classification"), ("bytes", "Bytes"),
            ("public_path", "Public Path"), ("reason", "Reason"),
        ]) + "\n"
    )


if __name__ == "__main__":
    main()
