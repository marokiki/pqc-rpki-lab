#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from pqc_rpki_lab.result_io import markdown_table, write_csv, write_json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

ALGORITHMS = (
    ("RSA-2048/SHA-256", "RSA", ["-pkeyopt", "rsa_keygen_bits:2048"]),
    ("ML-DSA-65", "ML-DSA-65", []),
    ("ML-DSA-87", "ML-DSA-87", []),
    ("SLH-DSA-SHAKE-128s", "SLH-DSA-SHAKE-128s", []),
    ("SLH-DSA-SHAKE-192s", "SLH-DSA-SHAKE-192s", []),
)


def run(command: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout)


def reason_for(process: subprocess.CompletedProcess[str], fallback: str) -> str:
    text = (process.stderr or process.stdout).strip()
    return text.splitlines()[-1] if text else fallback


def record(
    rows: list[dict[str, object]], algorithm: str, object_type: str, status: str,
    classification: str, path: Path | None = None, reason: str = "",
) -> None:
    if algorithm == "RSA-2048/SHA-256":
        profile = "RFC 6487 + RFC 7935" if object_type in {"CA certificate", "EE certificate", "CRL"} else "RFC 6488 + RFC 7935"
    elif algorithm.startswith("ML-DSA"):
        profile = "RFC 6487 + RFC 9881" if object_type in {"CA certificate", "EE certificate", "CRL"} else "RFC 6488 + RFC 9882"
    else:
        profile = "RFC 6487 + RFC 9909" if object_type in {"CA certificate", "EE certificate", "CRL"} else "RFC 6488 + RFC 9814"
    rows.append({
        "algorithm": algorithm,
        "object_type": object_type,
        "status": status,
        "classification": classification,
        "bytes": path.stat().st_size if path and path.exists() else "",
        "backend": "OpenSSL CLI",
        "profile": profile,
        "reason": reason,
        "private_key_persisted": False,
    })


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
x509_extensions=ee_ext
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
subjectInfoAccess=caRepository;URI:rsync://example.invalid/repository/,rpkiManifest;URI:rsync://example.invalid/repository/manifest.mft
sbgp-ipAddrBlock=critical,@ca_ip
sbgp-autonomousSysNum=critical,@ca_as
[ca_ip]
IPv4=192.0.2.0/24
[ca_as]
AS.0=64496
[ee_ext]
basicConstraints=critical,CA:false
keyUsage=critical,digitalSignature
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid
crlDistributionPoints=URI:rsync://example.invalid/repository/ca.crl
authorityInfoAccess=caIssuers;URI:rsync://example.invalid/repository/ca.cer
sbgp-ipAddrBlock=critical,@ee_ip
sbgp-autonomousSysNum=critical,@ee_as
[ee_ip]
IPv4=inherit
[ee_as]
AS.0=inherit
"""


def generate_algorithm(openssl: str, display: str, provider_name: str, options: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="pqc-rpki-objects-") as name:
        directory = Path(name)
        (directory / "index.txt").touch()
        (directory / "serial").write_text("1000\n")
        (directory / "crlnumber").write_text("1000\n")
        config = directory / "openssl.cnf"
        config.write_text(config_text(directory))
        ca_key = directory / "ca.key"
        ca_pem = directory / "ca.pem"
        ca_der = directory / "ca.cer"
        ee_key = directory / "ee.key"
        ee_csr = directory / "ee.csr"
        ee_pem = directory / "ee.pem"
        ee_der = directory / "ee.cer"
        crl_pem = directory / "ca.crl.pem"
        crl_der = directory / "ca.crl"
        content = directory / "content.bin"
        cms = directory / "content.cms"
        content.write_bytes(b"EXPERIMENTAL / NOT FOR PRODUCTION\n")

        key_result = run([openssl, "genpkey", "-algorithm", provider_name, *options, "-out", str(ca_key)])
        if key_result.returncode:
            for object_type in ("CA certificate", "EE certificate", "CRL", "CMS SignedData", "MFT", "ROA"):
                record(rows, display, object_type, "unsupported", "provider-algorithm-unavailable",
                       reason=reason_for(key_result, "key generation failed"))
            return rows

        ca_result = run([
            openssl, "req", "-new", "-x509", "-key", str(ca_key), "-config", str(config),
            "-extensions", "ca_ext", "-days", "1", "-out", str(ca_pem),
        ])
        if ca_result.returncode == 0:
            convert = run([openssl, "x509", "-in", str(ca_pem), "-outform", "DER", "-out", str(ca_der)])
            status = "confirmed" if convert.returncode == 0 else "blocked"
            record(rows, display, "CA certificate", status, "rfc-profiled-x509-generated",
                   ca_der if status == "confirmed" else None, reason_for(convert, "") if status != "confirmed" else "")
        else:
            record(rows, display, "CA certificate", "blocked", "x509-generation-failed",
                   reason=reason_for(ca_result, "CA certificate generation failed"))

        ee_key_result = run([openssl, "genpkey", "-algorithm", provider_name, *options, "-out", str(ee_key)])
        csr_result = run([openssl, "req", "-new", "-key", str(ee_key), "-subj", "/CN=EXPERIMENTAL RPKI EE", "-out", str(ee_csr)]) if ee_key_result.returncode == 0 else ee_key_result
        ee_result = run([openssl, "ca", "-batch", "-config", str(config), "-in", str(ee_csr), "-out", str(ee_pem)]) if csr_result.returncode == 0 and ca_result.returncode == 0 else csr_result
        if ee_result.returncode == 0:
            convert = run([openssl, "x509", "-in", str(ee_pem), "-outform", "DER", "-out", str(ee_der)])
            status = "confirmed" if convert.returncode == 0 else "blocked"
            record(rows, display, "EE certificate", status, "rfc-profiled-x509-generated",
                   ee_der if status == "confirmed" else None, reason_for(convert, "") if status != "confirmed" else "")
        else:
            record(rows, display, "EE certificate", "blocked", "certificate-signing-failed",
                   reason=reason_for(ee_result, "EE certificate generation failed"))

        crl_result = run([openssl, "ca", "-gencrl", "-config", str(config), "-out", str(crl_pem)]) if ca_result.returncode == 0 else ca_result
        if crl_result.returncode == 0:
            convert = run([openssl, "crl", "-in", str(crl_pem), "-outform", "DER", "-out", str(crl_der)])
            status = "confirmed" if convert.returncode == 0 else "blocked"
            record(rows, display, "CRL", status, "rfc-profiled-crl-generated",
                   crl_der if status == "confirmed" else None, reason_for(convert, "") if status != "confirmed" else "")
        else:
            record(rows, display, "CRL", "blocked", "crl-signing-failed",
                   reason=reason_for(crl_result, "CRL generation failed"))

        cms_result = run([
            openssl, "cms", "-sign", "-binary", "-in", str(content), "-signer", str(ee_pem),
            "-inkey", str(ee_key), "-outform", "DER", "-out", str(cms), "-nosmimecap",
            "-econtent_type", "1.2.840.113549.1.9.16.1.26",
        ]) if ee_result.returncode == 0 else ee_result
        if cms_result.returncode == 0:
            record(rows, display, "CMS SignedData", "confirmed", "generic-cms-generated", cms)
        else:
            error = reason_for(cms_result, "CMS signing failed")
            classification = "cms-pure-signature-unsupported" if "no default digest" in error.lower() else "cms-signing-failed"
            record(rows, display, "CMS SignedData", "unsupported", classification, reason=error)

        if cms_result.returncode == 0:
            for object_type in ("MFT", "ROA"):
                record(rows, display, object_type, "unsupported", "rpki-payload-generator-unavailable",
                       reason="No existing MFT/ROA payload generator was available; ASN.1 payloads were not reimplemented.")
        else:
            for object_type in ("MFT", "ROA"):
                record(rows, display, object_type, "unsupported", "cms-signing-unavailable",
                       reason="RFC 6488 object generation cannot proceed because CMS signing failed.")
    return rows


def main() -> None:
    openssl = shutil.which("openssl")
    rows: list[dict[str, object]] = []
    if openssl:
        for display, provider_name, options in ALGORITHMS:
            rows.extend(generate_algorithm(openssl, display, provider_name, options))
    else:
        for display, _, _ in ALGORITHMS:
            for object_type in ("CA certificate", "EE certificate", "CRL", "CMS SignedData", "MFT", "ROA"):
                record(rows, display, object_type, "unsupported", "openssl-unavailable",
                       reason="OpenSSL executable not found")
    write_csv(RESULTS / "generated-object-sizes.csv", rows)
    write_json(RESULTS / "object-generation-feasibility.json", {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "private_keys_persisted": False,
        "results": rows,
    })
    summary = markdown_table(rows, [
        ("algorithm", "Algorithm"), ("object_type", "Object"),
        ("status", "Status"), ("bytes", "Bytes"),
        ("classification", "Classification"), ("reason", "Reason"),
    ])
    (RESULTS / "object-generation-feasibility.md").write_text(
        "# RFC-Profiled Object Generation Feasibility\n\n"
        "> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        "All keys and intermediate objects were created under an automatically deleted "
        "temporary directory. No private key is persisted or committed.\n\n" + summary + "\n")


if __name__ == "__main__":
    main()
