#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import platform
import shutil
import statistics
import subprocess
import tempfile
import time
from dataclasses import asdict
from pathlib import Path

from pqc_rpki_lab.algorithms import ALL_ALGORITHMS, Algorithm
from pqc_rpki_lab.result_io import markdown_table, write_csv, write_json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def timed(operation):
    start = time.perf_counter_ns()
    result = operation()
    return result, (time.perf_counter_ns() - start) / 1_000_000


def median(values: list[float]) -> float:
    return round(statistics.median(values), 6)


def base_row(algorithm: Algorithm) -> dict[str, object]:
    row = asdict(algorithm)
    row["oqs_names"] = list(algorithm.oqs_names)
    return row


def benchmark_rsa(algorithm: Algorithm, iterations: int) -> dict[str, object]:
    row = base_row(algorithm)
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding, rsa
    except Exception as error:
        return row | {"benchmark_status": "unsupported", "reason": f"cryptography unavailable: {error}"}
    message = hashlib.sha256(b"pqc-rpki-lab").digest()
    keygen: list[float] = []
    signing: list[float] = []
    verifying: list[float] = []
    public = signature = private_bytes = b""
    for _ in range(iterations):
        private, elapsed = timed(lambda: rsa.generate_private_key(public_exponent=65537, key_size=2048))
        keygen.append(elapsed)
        public_key = private.public_key()
        signature, elapsed = timed(lambda: private.sign(message, padding.PKCS1v15(), hashes.SHA256()))
        signing.append(elapsed)
        _, elapsed = timed(lambda: public_key.verify(signature, message, padding.PKCS1v15(), hashes.SHA256()))
        verifying.append(elapsed)
        public = public_key.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
        private_bytes = private.private_bytes(
            serialization.Encoding.DER, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption())
    return row | {
        "backend": "cryptography or OpenSSL", "benchmark_status": "confirmed",
        "provider_name": "cryptography", "iterations": iterations,
        "keygen_ms_median": median(keygen), "sign_ms_median": median(signing),
        "verify_ms_median": median(verifying), "measured_public_key_bytes": len(public),
        "secret_key_bytes": len(private_bytes), "measured_signature_bytes": len(signature),
    }


def benchmark_oqs(algorithm: Algorithm, iterations: int) -> dict[str, object]:
    row = base_row(algorithm)
    try:
        import oqs  # type: ignore
    except Exception as error:
        return row | {"benchmark_status": "unsupported", "reason": f"oqs import failed: {error}"}
    enabled = set(oqs.get_enabled_sig_mechanisms())
    mechanism = next((name for name in algorithm.oqs_names if name in enabled), None)
    if mechanism is None:
        return row | {
            "benchmark_status": "unsupported",
            "reason": "candidate is not enabled by oqs-python/liboqs",
        }
    message = hashlib.sha256(b"pqc-rpki-lab").digest()
    keygen: list[float] = []
    signing: list[float] = []
    verifying: list[float] = []
    public = signature = secret = b""
    for _ in range(iterations):
        signer = oqs.Signature(mechanism)
        public, elapsed = timed(signer.generate_keypair)
        keygen.append(elapsed)
        signature, elapsed = timed(lambda: signer.sign(message))
        signing.append(elapsed)
        verified, elapsed = timed(lambda: signer.verify(message, signature, public))
        verifying.append(elapsed)
        if not verified:
            raise RuntimeError(f"verification failed for {mechanism}")
        secret = signer.export_secret_key()
    return row | {
        "benchmark_status": "confirmed", "provider_name": mechanism,
        "iterations": iterations, "keygen_ms_median": median(keygen),
        "sign_ms_median": median(signing), "verify_ms_median": median(verifying),
        "measured_public_key_bytes": len(public), "secret_key_bytes": len(secret),
        "measured_signature_bytes": len(signature),
    }


def benchmark_openssl(algorithm: Algorithm, iterations: int) -> dict[str, object]:
    row = base_row(algorithm)
    if not shutil.which("openssl"):
        return row | {"benchmark_status": "unsupported", "reason": "OpenSSL executable not found"}
    provider_name = algorithm.oqs_names[0] if algorithm.oqs_names else algorithm.name
    message = hashlib.sha256(b"pqc-rpki-lab").digest()
    keygen: list[float] = []
    signing: list[float] = []
    verifying: list[float] = []
    with tempfile.TemporaryDirectory(prefix="pqc-rpki-primitive-") as name:
        directory = Path(name)
        message_path = directory / "message.bin"
        private_path = directory / "private.pem"
        private_der = directory / "private.der"
        public_path = directory / "public.der"
        signature_path = directory / "signature.bin"
        message_path.write_bytes(message)
        for _ in range(iterations):
            process, elapsed = timed(lambda: subprocess.run(
                ["openssl", "genpkey", "-algorithm", provider_name, "-out", str(private_path)],
                capture_output=True, text=True))
            if process.returncode:
                return row | {
                    "benchmark_status": "unsupported",
                    "reason": (process.stderr or process.stdout).strip().splitlines()[-1],
                }
            keygen.append(elapsed)
            subprocess.run(
                ["openssl", "pkey", "-in", str(private_path), "-pubout", "-outform", "DER", "-out", str(public_path)],
                check=True, capture_output=True)
            subprocess.run(
                ["openssl", "pkey", "-in", str(private_path), "-outform", "DER", "-out", str(private_der)],
                check=True, capture_output=True)
            process, elapsed = timed(lambda: subprocess.run(
                ["openssl", "pkeyutl", "-sign", "-inkey", str(private_path), "-rawin",
                 "-in", str(message_path), "-out", str(signature_path)],
                capture_output=True, text=True))
            if process.returncode:
                return row | {
                    "benchmark_status": "unsupported",
                    "reason": (process.stderr or process.stdout).strip().splitlines()[-1],
                }
            signing.append(elapsed)
            process, elapsed = timed(lambda: subprocess.run(
                ["openssl", "pkeyutl", "-verify", "-pubin", "-inkey", str(public_path),
                 "-keyform", "DER", "-rawin", "-in", str(message_path), "-sigfile", str(signature_path)],
                capture_output=True, text=True))
            if process.returncode:
                raise RuntimeError(f"OpenSSL verification failed for {provider_name}: {process.stderr}")
            verifying.append(elapsed)
        return row | {
            "backend": "OpenSSL default provider", "benchmark_status": "confirmed",
            "provider_name": provider_name, "iterations": iterations,
            "keygen_ms_median": median(keygen), "sign_ms_median": median(signing),
            "verify_ms_median": median(verifying),
            "measured_public_key_bytes": public_path.stat().st_size,
            "secret_key_bytes": private_der.stat().st_size,
            "measured_signature_bytes": signature_path.stat().st_size,
            "notes": algorithm.notes + " Timing includes OpenSSL CLI process overhead.",
        }


def benchmark_pqc(algorithm: Algorithm, iterations: int) -> dict[str, object]:
    oqs_row = benchmark_oqs(algorithm, iterations)
    if oqs_row.get("benchmark_status") == "confirmed":
        return oqs_row
    if algorithm.track == "required":
        return benchmark_openssl(algorithm, iterations)
    return oqs_row


def main() -> None:
    iterations = int(os.environ.get("PQC_RPKI_ITERATIONS", "3"))
    rows = [
        benchmark_rsa(algorithm, iterations) if algorithm.family == "RSA"
        else benchmark_pqc(algorithm, iterations)
        for algorithm in ALL_ALGORITHMS
    ]
    write_csv(RESULTS / "primitive-bench.csv", rows)
    write_json(RESULTS / "primitive-bench.json", {
        "metadata": {
            "experimental": True, "iterations": iterations,
            "platform": platform.platform(), "python": platform.python_version(),
            "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        },
        "results": rows,
    })
    table = markdown_table(rows, [
        ("name", "Algorithm"), ("benchmark_status", "Status"),
        ("keygen_ms_median", "Keygen ms"), ("sign_ms_median", "Sign ms"),
        ("verify_ms_median", "Verify ms"), ("measured_signature_bytes", "Measured signature bytes"),
    ])
    (RESULTS / "primitive-bench.md").write_text(
        "# Primitive Benchmark\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\n" + table + "\n")


if __name__ == "__main__":
    main()
