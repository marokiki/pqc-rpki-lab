#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from pqc_rpki_lab.result_io import markdown_table, write_csv, write_json
from pqc_rpki_lab.rpki_asn1 import parse_manifest_econtent

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "local-validation"
TESTDATA = ROOT / "testdata"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, timeout=60)


def verify_cms(openssl: str, cms: Path, ca_der: Path, expected_content: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="pqc-rpki-local-verify-") as name:
        directory = Path(name)
        ca_pem = directory / "ca.pem"
        output = directory / "content.der"
        convert = run([openssl, "x509", "-inform", "DER", "-in", str(ca_der), "-out", str(ca_pem)])
        if convert.returncode:
            return {"status": "blocked", "reason": (convert.stderr or convert.stdout).strip()}
        process = run([
            openssl, "cms", "-verify", "-inform", "DER", "-in", str(cms),
            "-CAfile", str(ca_pem), "-out", str(output), "-binary",
        ])
        if process.returncode:
            return {"status": "blocked", "reason": (process.stderr or process.stdout).strip().splitlines()[-1]}
        if output.read_bytes() != expected_content.read_bytes():
            return {"status": "blocked", "reason": "verified content did not match expected eContent"}
        return {"status": "confirmed", "reason": ""}


def parse_der(openssl: str, path: Path) -> dict[str, object]:
    process = run([openssl, "asn1parse", "-inform", "DER", "-in", str(path)])
    return {
        "status": "confirmed" if process.returncode == 0 else "blocked",
        "reason": "" if process.returncode == 0 else (process.stderr or process.stdout).strip().splitlines()[-1],
    }


def certificate_text(openssl: str, path: Path) -> str:
    return run([openssl, "x509", "-inform", "DER", "-in", str(path), "-noout", "-text"]).stdout


def manifest_hash_check(root: Path) -> dict[str, object]:
    manifest = parse_manifest_econtent((root / "manifest.mft.econtent").read_bytes())
    expected = {"route.roa": root / "route.roa", "ca.crl": root / "ca.crl"}
    entries = {item["file"]: item for item in manifest["entries"]}
    valid = set(entries) == set(expected)
    for name, path in expected.items():
        valid = valid and path.exists() and entries.get(name, {}).get("unused_bits") == 0
        valid = valid and entries.get(name, {}).get("hash") == hashlib.sha256(path.read_bytes()).digest()
    return {"status": "confirmed" if valid else "blocked", "reason": "" if valid else "Manifest file list or SHA-256 hash mismatch"}


def ee_profile_check(openssl: str, root: Path, kind: str) -> dict[str, object]:
    certificate = root / f"{kind}.ee.cer"
    text = certificate_text(openssl, certificate)
    if kind == "route":
        checks = [
            "Signed Object - URI:rsync://example.invalid:8873/repository/route.roa" in text,
            "192.0.2.0/24" in text and "2001:db8::/32" in text,
            "sbgp-autonomousSysNum" not in text,
            "inherit" not in text,
            "Basic Constraints" not in text,
        ]
    else:
        dates = run([openssl, "x509", "-inform", "DER", "-in", str(certificate), "-noout", "-dates"])
        cert_dates = dict(line.split("=", 1) for line in dates.stdout.splitlines() if "=" in line)
        parser = "%b %d %H:%M:%S %Y GMT"
        normalized = [
            datetime.strptime(cert_dates[field], parser).replace(tzinfo=timezone.utc).strftime("%Y%m%d%H%M%SZ")
            for field in ("notBefore", "notAfter")
        ]
        manifest = parse_manifest_econtent((root / "manifest.mft.econtent").read_bytes())
        checks = [
            "Signed Object - URI:rsync://example.invalid:8873/repository/manifest.mft" in text,
            text.count("inherit") >= 3,
            normalized == [manifest["this_update"], manifest["next_update"]],
            "Basic Constraints" not in text,
        ]
    return {"status": "confirmed" if all(checks) else "blocked", "reason": "" if all(checks) else f"{kind} EE profile check failed"}


def main() -> None:
    openssl = "openssl"
    rows: list[dict[str, object]] = []
    for slug in ("rsa", "ml-dsa-44", "ml-dsa-65", "ml-dsa-87"):
        root = TESTDATA / slug
        if not root.exists():
            rows.append({"algorithm": slug, "layer": "fixtures", "artifact": "", "status": "skipped", "reason": "fixture directory missing"})
            continue
        for artifact in ("ca.cer", "route.ee.cer", "manifest.ee.cer", "ca.crl", "route.roa.econtent", "manifest.mft.econtent"):
            path = root / artifact
            if path.exists():
                result = parse_der(openssl, path)
                rows.append({"algorithm": slug, "layer": "DER parse", "artifact": artifact, **result})
        for artifact, econtent in (("route.roa", "route.roa.econtent"), ("manifest.mft", "manifest.mft.econtent")):
            cms = root / artifact
            if cms.exists():
                result = verify_cms(openssl, cms, root / "ca.cer", root / econtent)
                rows.append({"algorithm": slug, "layer": "CMS verify", "artifact": artifact, **result})
            else:
                rows.append({"algorithm": slug, "layer": "CMS verify", "artifact": artifact, "status": "skipped", "reason": "CMS artifact unavailable"})
        rows.append({"algorithm": slug, "layer": "EE profile", "artifact": "route.ee.cer", **ee_profile_check(openssl, root, "route")})
        rows.append({"algorithm": slug, "layer": "EE profile", "artifact": "manifest.ee.cer", **ee_profile_check(openssl, root, "manifest")})
        if (root / "route.roa").exists():
            rows.append({"algorithm": slug, "layer": "Manifest hash", "artifact": "manifest.mft.econtent", **manifest_hash_check(root)})
    write_csv(RESULTS / "local-validation.csv", rows)
    write_json(RESULTS / "local-validation.json", {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "classification": "local parser/signature evidence; not full RPKI validator interoperability",
        "results": rows,
    })
    (RESULTS / "local-validation.md").write_text(
        "# Local Object Validation\n\n"
        "> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        "This verifies DER parseability, CMS signature/content round-trips, object-specific "
        "EE certificate constraints, and Manifest product hashes with OpenSSL and the internal parser. "
        "It is not independent multi-validator interoperability.\n\n"
        + markdown_table(rows, [
            ("algorithm", "Algorithm"), ("layer", "Layer"), ("artifact", "Artifact"),
            ("status", "Status"), ("reason", "Reason"),
        ]) + "\n"
    )


if __name__ == "__main__":
    main()
