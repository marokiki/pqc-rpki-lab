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


def benchmark_rsa_openssl(algorithm: Algorithm, iterations: int) -> dict[str, object]:
    row = base_row(algorithm)
    if not shutil.which("openssl"):
        return row | {
            "backend": "OpenSSL CLI",
            "benchmark_status": "unsupported",
            "reason": "OpenSSL executable not found",
            "timing_scope": "end-to-end CLI wall-clock",
            "comparable_group": "openssl-cli-v1",
        }
    message = hashlib.sha256(b"pqc-rpki-lab").digest()
    keygen: list[float] = []
    signing: list[float] = []
    verifying: list[float] = []
    with tempfile.TemporaryDirectory(prefix="pqc-rpki-rsa-primitive-") as name:
        directory = Path(name)
        message_path = directory / "message.bin"
        private_path = directory / "private.pem"
        private_der = directory / "private.der"
        public_path = directory / "public.der"
        public_pem = directory / "public.pem"
        signature_path = directory / "signature.bin"
        message_path.write_bytes(message)
        for _ in range(iterations):
            process, elapsed = timed(lambda: subprocess.run(
                ["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048",
                 "-out", str(private_path)], capture_output=True, text=True))
            if process.returncode:
                return row | {
                    "backend": "OpenSSL CLI", "benchmark_status": "unsupported",
                    "reason": (process.stderr or process.stdout).strip().splitlines()[-1],
                    "timing_scope": "end-to-end CLI wall-clock",
                    "comparable_group": "openssl-cli-v1",
                }
            keygen.append(elapsed)
            subprocess.run(
                ["openssl", "pkey", "-in", str(private_path), "-pubout", "-out", str(public_pem)],
                check=True, capture_output=True)
            subprocess.run(
                ["openssl", "pkey", "-in", str(private_path), "-pubout", "-outform", "DER",
                 "-out", str(public_path)], check=True, capture_output=True)
            subprocess.run(
                ["openssl", "pkey", "-in", str(private_path), "-outform", "DER",
                 "-out", str(private_der)], check=True, capture_output=True)
            process, elapsed = timed(lambda: subprocess.run(
                ["openssl", "dgst", "-sha256", "-sign", str(private_path),
                 "-out", str(signature_path), str(message_path)], capture_output=True, text=True))
            if process.returncode:
                raise RuntimeError(f"OpenSSL RSA signing failed: {process.stderr}")
            signing.append(elapsed)
            process, elapsed = timed(lambda: subprocess.run(
                ["openssl", "dgst", "-sha256", "-verify", str(public_pem),
                 "-signature", str(signature_path), str(message_path)], capture_output=True, text=True))
            if process.returncode:
                raise RuntimeError(f"OpenSSL RSA verification failed: {process.stderr}")
            verifying.append(elapsed)
        return row | {
            "backend": "OpenSSL CLI", "benchmark_status": "confirmed",
            "provider_name": "RSA", "iterations": iterations,
            "keygen_ms_median": median(keygen), "sign_ms_median": median(signing),
            "verify_ms_median": median(verifying),
            "measured_public_key_bytes": public_path.stat().st_size,
            "secret_key_bytes": private_der.stat().st_size,
            "measured_signature_bytes": signature_path.stat().st_size,
            "timing_scope": "end-to-end CLI wall-clock",
            "comparable_group": "openssl-cli-v1",
            "notes": algorithm.notes + " Timed operations each include one OpenSSL process launch.",
        }


def benchmark_oqs(algorithm: Algorithm, iterations: int) -> dict[str, object]:
    row = base_row(algorithm)
    try:
        import oqs  # type: ignore
    except Exception as error:
        return row | {
            "backend": "oqs-python/liboqs", "benchmark_status": "unsupported",
            "reason": f"oqs import failed: {error}", "timing_scope": "in-process",
            "comparable_group": "oqs-python-v1",
        }
    enabled = set(oqs.get_enabled_sig_mechanisms())
    mechanism = next((name for name in algorithm.oqs_names if name in enabled), None)
    if mechanism is None:
        return row | {
            "backend": "oqs-python/liboqs", "benchmark_status": "unsupported",
            "reason": "candidate is not enabled by oqs-python/liboqs",
            "timing_scope": "in-process", "comparable_group": "oqs-python-v1",
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
        "backend": "oqs-python/liboqs", "benchmark_status": "confirmed", "provider_name": mechanism,
        "iterations": iterations, "keygen_ms_median": median(keygen),
        "sign_ms_median": median(signing), "verify_ms_median": median(verifying),
        "measured_public_key_bytes": len(public), "secret_key_bytes": len(secret),
        "measured_signature_bytes": len(signature),
        "timing_scope": "in-process", "comparable_group": "oqs-python-v1",
        "notes": algorithm.notes + " In-process timings are not directly comparable with OpenSSL CLI timings.",
    }


def benchmark_openssl(algorithm: Algorithm, iterations: int) -> dict[str, object]:
    row = base_row(algorithm)
    if not shutil.which("openssl"):
        return row | {
            "backend": "OpenSSL CLI", "benchmark_status": "unsupported",
            "reason": "OpenSSL executable not found", "timing_scope": "end-to-end CLI wall-clock",
            "comparable_group": "openssl-cli-v1",
        }
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
                    "backend": "OpenSSL CLI", "benchmark_status": "unsupported",
                    "reason": (process.stderr or process.stdout).strip().splitlines()[-1],
                    "timing_scope": "end-to-end CLI wall-clock",
                    "comparable_group": "openssl-cli-v1",
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
                    "backend": "OpenSSL CLI", "benchmark_status": "unsupported",
                    "reason": (process.stderr or process.stdout).strip().splitlines()[-1],
                    "timing_scope": "end-to-end CLI wall-clock",
                    "comparable_group": "openssl-cli-v1",
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
            "backend": "OpenSSL CLI", "benchmark_status": "confirmed",
            "provider_name": provider_name, "iterations": iterations,
            "keygen_ms_median": median(keygen), "sign_ms_median": median(signing),
            "verify_ms_median": median(verifying),
            "measured_public_key_bytes": public_path.stat().st_size,
            "secret_key_bytes": private_der.stat().st_size,
            "measured_signature_bytes": signature_path.stat().st_size,
            "timing_scope": "end-to-end CLI wall-clock",
            "comparable_group": "openssl-cli-v1",
            "notes": algorithm.notes + " Timed operations each include one OpenSSL process launch.",
        }


def benchmark_pqc(algorithm: Algorithm, iterations: int) -> dict[str, object]:
    if algorithm.comparison_required:
        return benchmark_openssl(algorithm, iterations)
    return benchmark_oqs(algorithm, iterations)


def main() -> None:
    iterations = int(os.environ.get("PQC_RPKI_ITERATIONS", "3"))
    rows = [
        benchmark_rsa_openssl(algorithm, iterations) if algorithm.family == "RSA"
        else benchmark_pqc(algorithm, iterations)
        for algorithm in ALL_ALGORITHMS
    ]
    write_csv(RESULTS / "primitive-bench.csv", rows)
    write_json(RESULTS / "primitive-bench.json", {
        "metadata": {
            "experimental": True, "iterations": iterations,
            "platform": platform.platform(), "python": platform.python_version(),
            "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
            "timing_scope": "Core comparison rows use end-to-end OpenSSL CLI wall-clock time.",
            "comparability": "Compare timings only when comparable_group is identical.",
        },
        "results": rows,
    })
    table = markdown_table(rows, [
        ("name", "Algorithm"), ("benchmark_status", "Status"),
        ("backend", "Backend"), ("timing_scope", "Timing scope"),
        ("keygen_ms_median", "Keygen ms"), ("sign_ms_median", "Sign ms"),
        ("verify_ms_median", "Verify ms"), ("measured_signature_bytes", "Measured signature bytes"),
        ("notes", "Notes"), ("reason", "Reason"),
    ])
    (RESULTS / "primitive-bench.md").write_text(
        "# Primitive Benchmark\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        "Core comparison timings are end-to-end OpenSSL CLI wall-clock measurements. "
        "Each timed operation includes one process launch. Compare timing values only "
        "within the same `comparable_group`; they are not pure cryptographic cycle counts.\n\n"
        + table + "\n")


if __name__ == "__main__":
    main()
