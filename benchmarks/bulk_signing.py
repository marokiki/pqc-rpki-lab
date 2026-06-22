#!/usr/bin/env python3
from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
from pathlib import Path

from pqc_rpki_lab.result_io import markdown_table, write_csv, write_json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "review-2026-06"

SPEED_NAMES = {
    "RSA-2048/SHA-256": "rsa2048",
    "P-256/SHA-256": "ecdsap256",
    "Ed25519": "ed25519",
    "ML-DSA-44": "ML-DSA-44",
    "ML-DSA-65": "ML-DSA-65",
    "ML-DSA-87": "ML-DSA-87",
}


def operation_name(value: str) -> str | None:
    value = value.lower()
    if "verify" in value:
        return "verify"
    if "sign" in value:
        return "sign"
    if "keygen" in value:
        return "keygen"
    return None


def parse_speed(output: str) -> dict[str, float]:
    current: str | None = None
    rates: dict[str, float] = {}
    for line in output.splitlines():
        if line.startswith("+DTP:"):
            current = next((operation_name(field) for field in line.split(":")
                            if operation_name(field)), None)
            continue
        if current and re.match(r"^\+R\d+:", line):
            fields = line.split(":")
            count = float(fields[1])
            elapsed = float(fields[-1])
            if elapsed > 0:
                rates[current] = count / elapsed
            current = None
    return rates


def unsupported(name: str, reason: str) -> dict[str, object]:
    return {
        "algorithm": name,
        "status": "unsupported",
        "backend": "OpenSSL speed",
        "timing_scope": "in-process EVP throughput",
        "reason": reason,
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    seconds = int(os.environ.get("PQC_RPKI_SPEED_SECONDS", "1"))
    rows: list[dict[str, object]] = []
    raw: list[str] = []
    executable = shutil.which("openssl")
    for name, speed_name in SPEED_NAMES.items():
        if not executable:
            rows.append(unsupported(name, "OpenSSL executable not found"))
            continue
        process = subprocess.run(
            [executable, "speed", "-seconds", str(seconds), "-elapsed", "-mr", speed_name],
            capture_output=True, text=True)
        output = process.stdout + process.stderr
        raw.append(f"### {name}\n$ openssl speed -seconds {seconds} -elapsed -mr {speed_name}\n{output}")
        if process.returncode:
            rows.append(unsupported(name, output.strip().splitlines()[-1] if output.strip() else "speed failed"))
            continue
        rates = parse_speed(output)
        sign_rate = rates.get("sign")
        if not sign_rate:
            rows.append(unsupported(name, "OpenSSL speed output did not contain a signing rate"))
            continue
        keygen_rate = rates.get("keygen")
        manifest_crypto = ((100_000 / keygen_rate) + (200_000 / sign_rate)) if keygen_rate else None
        key_roll_crypto = ((102 / keygen_rate) + (213 / sign_rate)) if keygen_rate else None
        rows.append({
            "algorithm": name,
            "status": "confirmed",
            "backend": "OpenSSL speed",
            "timing_scope": "in-process EVP throughput",
            "measurement_seconds_per_operation": seconds,
            "keygen_ops_per_second": round(keygen_rate, 3) if keygen_rate else "",
            "sign_ops_per_second": round(sign_rate, 3),
            "verify_ops_per_second": round(rates.get("verify", 0), 3) or "",
            "estimated_100k_signatures_seconds": round(100_000 / sign_rate, 3),
            "estimated_100k_manifests_signing_lower_bound_seconds": round(200_000 / sign_rate, 3),
            "estimated_100k_manifests_crypto_lower_bound_seconds": round(manifest_crypto, 3)
            if manifest_crypto is not None else "",
            "estimated_key_roll_signing_lower_bound_seconds": round(213 / sign_rate, 6),
            "estimated_key_roll_crypto_lower_bound_seconds": round(key_roll_crypto, 6)
            if key_roll_crypto is not None else "",
            "reason": "",
        })

    metadata = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "platform": platform.platform(),
        "openssl": subprocess.run([executable, "version"], capture_output=True, text=True).stdout.strip()
        if executable else "unavailable",
        "method": "One OpenSSL speed process per algorithm; provider and process startup are outside timed loops.",
        "manifest_projection": (
            "The signing-only 100,000-manifest value uses two signatures per RFC 6488 object "
            "(EE certificate plus CMS signature). Where OpenSSL reports keygen throughput, the crypto lower "
            "bound also includes 100,000 one-time EE keys. Both exclude ASN.1/CMS construction, hashing, "
            "file I/O, RRDP publication, and HSM latency."
        ),
        "key_roll_projection": (
            "The synthetic key-roll lower bound uses 10 child certificates, 100 RFC 6488 objects, "
            "one manifest, and one CRL: 213 signatures and 102 key generations (one CA and 101 EE keys)."
        ),
        "complete_object_workload": {
            "status": "unsupported",
            "reason": (
                "No existing generator in this environment can produce complete PQC RFC 6488 Manifest "
                "payloads and CMS SignedData; projected crypto work is not object-level throughput."
            ),
        },
    }
    write_csv(RESULTS / "bulk-signing.csv", rows)
    write_json(RESULTS / "bulk-signing.json", {"metadata": metadata, "results": rows})
    (RESULTS / "bulk-signing-raw.txt").write_text("\n".join(raw))
    table = markdown_table(rows, [
        ("algorithm", "Algorithm"), ("status", "Status"),
        ("sign_ops_per_second", "Sign/s"), ("verify_ops_per_second", "Verify/s"),
        ("estimated_100k_signatures_seconds", "100k signatures s"),
        ("estimated_100k_manifests_signing_lower_bound_seconds", "100k MFT signing lower bound s"),
        ("estimated_100k_manifests_crypto_lower_bound_seconds", "100k MFT crypto lower bound s"),
        ("estimated_key_roll_signing_lower_bound_seconds", "Key-roll signing lower bound s"),
        ("estimated_key_roll_crypto_lower_bound_seconds", "Key-roll crypto lower bound s"),
        ("reason", "Reason"),
    ])
    (RESULTS / "bulk-signing.md").write_text(
        "# Bulk Signing Throughput\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        + metadata["method"] + "\n\n" + metadata["manifest_projection"] + "\n\n"
        + metadata["key_roll_projection"] + "\n\n"
        + "Complete PQC RFC 6488 object workload: `unsupported`. "
        + metadata["complete_object_workload"]["reason"] + "\n\n" + table + "\n")


if __name__ == "__main__":
    main()
