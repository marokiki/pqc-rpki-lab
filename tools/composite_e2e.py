#!/usr/bin/env python3
"""Generate a small-scale RSA-to-Composite RPKI repository.

Private keys and transient validator state stay below local/.  The generator
and public result summary are suitable for reproducing the experiment.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from pqc_rpki_lab.rpki_asn1 import (
    OID_CT_MFT,
    OID_CT_ROA,
    manifest_econtent,
    roa_econtent,
)
from pqc_rpki_lab.workspace import reset_generated_directory

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "local" / "e2e" / "current"
RESULTS = ROOT / "results" / "composite-e2e"
COMPOSITE = "MLDSA65-ECDSA-P256-SHA512"
BASE_URI = "rsync://example.invalid/repository/"


def run(command: list[str], *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    process = subprocess.run(command, env=env, capture_output=True, text=True)
    if process.returncode:
        raise RuntimeError(
            f"command failed ({process.returncode}): {' '.join(command)}\n"
            f"{process.stderr or process.stdout}"
        )
    return process


def ca_config(directory: Path, *, certificate: Path, private_key: Path) -> str:
    return f"""# EXPERIMENTAL / NOT FOR PRODUCTION
[ca]
default_ca=CA_default
[CA_default]
dir={directory}
database=$dir/index.txt
new_certs_dir=$dir/newcerts
certificate={certificate}
private_key={private_key}
serial=$dir/serial
crlnumber=$dir/crlnumber
default_days=7
default_crl_days=7
default_md=sha256
crl_extensions=crl_ext
policy=policy
copy_extensions=none
unique_subject=no
[policy]
commonName=supplied
[req]
distinguished_name=dn
prompt=no
string_mask=default
[dn]
CN=EXPERIMENTAL RPKI
[ta_ext]
basicConstraints=critical,CA:true
keyUsage=critical,keyCertSign,cRLSign
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always
certificatePolicies=critical,1.3.6.1.5.5.7.14.2
subjectInfoAccess=caRepository;URI:{BASE_URI},rpkiManifest;URI:{BASE_URI}ta.mft
sbgp-ipAddrBlock=critical,@resources_ip
sbgp-autonomousSysNum=critical,@resources_as
[child_ca_ext]
basicConstraints=critical,CA:true
keyUsage=critical,keyCertSign,cRLSign
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always
certificatePolicies=critical,1.3.6.1.5.5.7.14.2
crlDistributionPoints=URI:{BASE_URI}ta.crl
authorityInfoAccess=caIssuers;URI:{BASE_URI}ta.cer
subjectInfoAccess=caRepository;URI:{BASE_URI}child/,rpkiManifest;URI:{BASE_URI}child/child.mft
sbgp-ipAddrBlock=critical,@resources_ip
sbgp-autonomousSysNum=critical,@resources_as
[parent_mft_ext]
keyUsage=critical,digitalSignature
certificatePolicies=critical,1.3.6.1.5.5.7.14.2
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid
crlDistributionPoints=URI:{BASE_URI}ta.crl
authorityInfoAccess=caIssuers;URI:{BASE_URI}ta.cer
subjectInfoAccess=signedObject;URI:{BASE_URI}ta.mft
sbgp-ipAddrBlock=critical,@inherit_ip
sbgp-autonomousSysNum=critical,@inherit_as
[child_roa_ext]
keyUsage=critical,digitalSignature
certificatePolicies=critical,1.3.6.1.5.5.7.14.2
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid
crlDistributionPoints=URI:{BASE_URI}child/child.crl
authorityInfoAccess=caIssuers;URI:{BASE_URI}child/child.cer
subjectInfoAccess=signedObject;URI:{BASE_URI}child/route.roa
sbgp-ipAddrBlock=critical,@resources_ip
[child_mft_ext]
keyUsage=critical,digitalSignature
certificatePolicies=critical,1.3.6.1.5.5.7.14.2
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid
crlDistributionPoints=URI:{BASE_URI}child/child.crl
authorityInfoAccess=caIssuers;URI:{BASE_URI}child/child.cer
subjectInfoAccess=signedObject;URI:{BASE_URI}child/child.mft
sbgp-ipAddrBlock=critical,@inherit_ip
sbgp-autonomousSysNum=critical,@inherit_as
[resources_ip]
IPv4=192.0.2.0/24
IPv6=2001:db8::/32
[resources_as]
AS.0=64496
[inherit_ip]
IPv4=inherit
IPv6=inherit
[inherit_as]
AS.0=inherit
[crl_ext]
authorityKeyIdentifier=keyid:always
"""


def init_ca(directory: Path) -> None:
    (directory / "newcerts").mkdir(parents=True)
    (directory / "index.txt").write_text("")
    (directory / "serial").write_text("1000\n")
    (directory / "crlnumber").write_text("1000\n")


def issue(
    openssl: str,
    *,
    ca_dir: Path,
    config: Path,
    key: Path,
    certificate: Path,
    common_name: str,
    extension: str,
    algorithm: str,
    digest: str,
    env: dict[str, str],
) -> None:
    csr = certificate.with_suffix(".csr")
    run([openssl, "genpkey", "-algorithm", algorithm, "-out", str(key)], env=env)
    run(
        [openssl, "req", "-new", "-config", str(config), "-key", str(key),
         "-subj", f"/CN={common_name}", "-out", str(csr)],
        env=env,
    )
    run(
        [openssl, "ca", "-batch", "-config", str(config), "-extensions", extension,
         "-md", digest, "-in", str(csr), "-out", str(certificate)],
        env=env,
    )


def to_der(openssl: str, kind: str, source: Path, output: Path, env: dict[str, str]) -> None:
    run(
        [openssl, kind, "-in", str(source), "-outform", "DER", "-out", str(output)],
        env=env,
    )


def cms_sign(
    openssl: str,
    *,
    content: Path,
    signer: Path,
    key: Path,
    output: Path,
    econtent_type: str,
    digest: str,
    env: dict[str, str],
) -> None:
    run(
        [openssl, "cms", "-sign", "-binary", "-in", str(content),
         "-signer", str(signer), "-inkey", str(key), "-md", digest,
         "-outform", "DER", "-out", str(output), "-nosmimecap", "-nodetach",
         "-keyid", "-econtent_type", econtent_type],
        env=env,
    )


def certificate_times(openssl: str, certificate: Path, env: dict[str, str]) -> tuple[str, str]:
    process = run(
        [openssl, "x509", "-in", str(certificate), "-noout", "-dates"], env=env,
    )
    values = dict(line.split("=", 1) for line in process.stdout.splitlines())
    parser = "%b %d %H:%M:%S %Y GMT"
    return tuple(
        datetime.strptime(values[field], parser)
        .replace(tzinfo=timezone.utc)
        .strftime("%Y%m%d%H%M%SZ")
        for field in ("notBefore", "notAfter")
    )


def tal_text(openssl: str, certificate: Path, env: dict[str, str]) -> str:
    public_pem = run(
        [openssl, "x509", "-in", str(certificate), "-pubkey", "-noout"], env=env,
    ).stdout
    process = subprocess.run(
        [openssl, "pkey", "-pubin", "-outform", "DER"],
        input=public_pem.encode(), env=env, capture_output=True,
    )
    if process.returncode:
        raise RuntimeError(process.stderr.decode())
    encoded = base64.b64encode(process.stdout).decode()
    wrapped = "\n".join(encoded[i:i + 64] for i in range(0, len(encoded), 64))
    return f"{BASE_URI}ta.cer\n\n{wrapped}\n"


def algorithm_fields(openssl: str, kind: str, path: Path, env: dict[str, str]) -> list[str]:
    process = run(
        [openssl, kind, "-inform", "DER", "-in", str(path), "-noout", "-text"],
        env=env,
    )
    return [
        line.strip()
        for line in process.stdout.splitlines()
        if "Signature Algorithm:" in line or "Public Key Algorithm:" in line
    ]


def generate(openssl: str, output: Path, env: dict[str, str]) -> dict[str, object]:
    reset_generated_directory(output, allowed_root=ROOT / "local")
    private = output / "private"
    repository = output / "repository"
    child_repo = repository / "child"
    parent_ca = private / "parent-ca"
    child_ca = private / "child-ca"
    for directory in (parent_ca, child_ca):
        init_ca(directory)
    child_repo.mkdir(parents=True)

    parent_key = private / "ta.key"
    parent_pem = private / "ta.pem"
    parent_cfg = parent_ca / "openssl.cnf"
    parent_cfg.write_text(
        ca_config(parent_ca, certificate=parent_pem, private_key=parent_key)
    )
    run(
        [openssl, "genpkey", "-algorithm", "RSA", "-pkeyopt",
         "rsa_keygen_bits:2048", "-out", str(parent_key)],
        env=env,
    )
    run(
        [openssl, "req", "-new", "-x509", "-key", str(parent_key),
         "-config", str(parent_cfg), "-extensions", "ta_ext", "-days", "7",
         "-sha256", "-out", str(parent_pem)],
        env=env,
    )
    to_der(openssl, "x509", parent_pem, repository / "ta.cer", env)

    child_key = private / "child-ca.key"
    child_pem = private / "child-ca.pem"
    issue(
        openssl, ca_dir=parent_ca, config=parent_cfg, key=child_key,
        certificate=child_pem, common_name="EXPERIMENTAL COMPOSITE CHILD CA",
        extension="child_ca_ext", algorithm=COMPOSITE, digest="sha256", env=env,
    )
    to_der(openssl, "x509", child_pem, repository / "child.cer", env)

    child_cfg = child_ca / "openssl.cnf"
    child_cfg.write_text(
        ca_config(child_ca, certificate=child_pem, private_key=child_key)
    )
    child_crl_pem = private / "child.crl.pem"
    run(
        [openssl, "ca", "-gencrl", "-config", str(child_cfg), "-md", "sha512",
         "-out", str(child_crl_pem)],
        env=env,
    )
    to_der(openssl, "crl", child_crl_pem, child_repo / "child.crl", env)

    roa_key = private / "route-ee.key"
    roa_pem = private / "route-ee.pem"
    issue(
        openssl, ca_dir=child_ca, config=child_cfg, key=roa_key,
        certificate=roa_pem, common_name="EXPERIMENTAL COMPOSITE ROA EE",
        extension="child_roa_ext", algorithm=COMPOSITE, digest="sha512", env=env,
    )
    mft_key = private / "child-mft-ee.key"
    mft_pem = private / "child-mft-ee.pem"
    issue(
        openssl, ca_dir=child_ca, config=child_cfg, key=mft_key,
        certificate=mft_pem, common_name="EXPERIMENTAL COMPOSITE MANIFEST EE",
        extension="child_mft_ext", algorithm=COMPOSITE, digest="sha512", env=env,
    )

    roa_content = private / "route.roa.econtent"
    roa_content.write_bytes(
        roa_econtent(64496, [("192.0.2.0/24", 24), ("2001:db8::/32", 48)])
    )
    cms_sign(
        openssl, content=roa_content, signer=roa_pem, key=roa_key,
        output=child_repo / "route.roa", econtent_type=OID_CT_ROA,
        digest="sha512", env=env,
    )

    this_update, next_update = certificate_times(openssl, mft_pem, env)
    child_mft_content = private / "child.mft.econtent"
    child_mft_content.write_bytes(
        manifest_econtent(
            [
                ("child.crl", (child_repo / "child.crl").read_bytes()),
                ("route.roa", (child_repo / "route.roa").read_bytes()),
            ],
            this_update=this_update,
            next_update=next_update,
        )
    )
    cms_sign(
        openssl, content=child_mft_content, signer=mft_pem, key=mft_key,
        output=child_repo / "child.mft", econtent_type=OID_CT_MFT,
        digest="sha512", env=env,
    )

    parent_crl_pem = private / "ta.crl.pem"
    run(
        [openssl, "ca", "-gencrl", "-config", str(parent_cfg), "-md", "sha256",
         "-out", str(parent_crl_pem)],
        env=env,
    )
    to_der(openssl, "crl", parent_crl_pem, repository / "ta.crl", env)
    parent_mft_key = private / "ta-mft-ee.key"
    parent_mft_pem = private / "ta-mft-ee.pem"
    issue(
        openssl, ca_dir=parent_ca, config=parent_cfg, key=parent_mft_key,
        certificate=parent_mft_pem, common_name="EXPERIMENTAL RSA MANIFEST EE",
        extension="parent_mft_ext", algorithm="RSA", digest="sha256", env=env,
    )
    parent_this, parent_next = certificate_times(openssl, parent_mft_pem, env)
    parent_mft_content = private / "ta.mft.econtent"
    parent_mft_content.write_bytes(
        manifest_econtent(
            [
                ("child.cer", (repository / "child.cer").read_bytes()),
                ("ta.crl", (repository / "ta.crl").read_bytes()),
            ],
            this_update=parent_this,
            next_update=parent_next,
        )
    )
    cms_sign(
        openssl, content=parent_mft_content, signer=parent_mft_pem,
        key=parent_mft_key, output=repository / "ta.mft",
        econtent_type=OID_CT_MFT, digest="sha256", env=env,
    )
    (output / "test.tal").write_text(tal_text(openssl, parent_pem, env))

    verification = {}
    for name, obj, ca in (
        ("ta", parent_pem, parent_pem),
        ("child", child_pem, parent_pem),
        ("roa-ee", roa_pem, child_pem),
        ("child-mft-ee", mft_pem, child_pem),
        ("ta-mft-ee", parent_mft_pem, parent_pem),
    ):
        run(
            [openssl, "verify", "-partial_chain", "-CAfile", str(ca), str(obj)],
            env=env,
        )
        verification[name] = "OK"
    for name, cms, ca in (
        ("route.roa", child_repo / "route.roa", child_pem),
        ("child.mft", child_repo / "child.mft", child_pem),
        ("ta.mft", repository / "ta.mft", parent_pem),
    ):
        extracted = private / f"{name}.verified"
        run(
            [openssl, "cms", "-verify", "-inform", "DER", "-binary",
             "-in", str(cms), "-partial_chain", "-CAfile", str(ca),
             "-out", str(extracted)],
            env=env,
        )
        verification[name] = "CMS Verification successful"

    artifacts = {
        str(path.relative_to(repository)): path.stat().st_size
        for path in sorted(repository.rglob("*"))
        if path.is_file()
    }
    try:
        reported_output = str(output.relative_to(ROOT))
    except ValueError:
        reported_output = str(output)
    return {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "classification": "small-scale E2E fixture; not a real repository benchmark",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output": reported_output,
        "composite_algorithm": COMPOSITE,
        "composite_oid": "1.3.6.1.5.5.7.6.45",
        "artifacts": artifacts,
        "verification": verification,
        "algorithms": {
            "ta.cer": algorithm_fields(openssl, "x509", repository / "ta.cer", env),
            "child.cer": algorithm_fields(
                openssl, "x509", repository / "child.cer", env
            ),
            "ta.crl": algorithm_fields(openssl, "crl", repository / "ta.crl", env),
            "child.crl": algorithm_fields(
                openssl, "crl", child_repo / "child.crl", env
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--openssl", default=shutil.which("openssl"))
    parser.add_argument("--summary", type=Path, default=RESULTS / "summary.json")
    args = parser.parse_args()
    if not args.openssl:
        raise SystemExit("openssl not found")
    started = time.perf_counter()
    summary = generate(args.openssl, args.output.resolve(), os.environ.copy())
    summary["generation_wall_seconds"] = time.perf_counter() - started
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
