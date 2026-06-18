from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Algorithm:
    name: str
    family: str
    nist_category: str
    public_key_bytes: int
    signature_bytes: int
    status: str
    specification: str
    backend: str
    notes: str
    oqs_names: tuple[str, ...] = ()
    track: str = "required"


REQUIRED_ALGORITHMS = (
    Algorithm("RSA-2048/SHA-256", "RSA", "classical", 270, 256, "confirmed",
              "RFC 7935", "cryptography or OpenSSL",
              "Current RPKI baseline; SPKI size is an approximate DER value."),
    Algorithm("ML-DSA-65", "ML-DSA", "3", 1952, 3309, "confirmed",
              "FIPS 204; RFC 9881; RFC 9882", "oqs-python/liboqs",
              "Primary balanced PQC candidate.", ("ML-DSA-65", "Dilithium3")),
    Algorithm("ML-DSA-87", "ML-DSA", "5", 2592, 4627, "confirmed",
              "FIPS 204; RFC 9881; RFC 9882", "oqs-python/liboqs",
              "High-assurance candidate with larger objects.", ("ML-DSA-87", "Dilithium5")),
    Algorithm("SLH-DSA-SHAKE-128s", "SLH-DSA", "1", 32, 7856, "confirmed",
              "FIPS 205; RFC 9909; RFC 9814", "oqs-python/liboqs",
              "Hash-based diversity candidate; signature size is the main concern.",
              ("SLH-DSA-SHAKE-128s", "SPHINCS+-SHAKE-128s-simple")),
    Algorithm("SLH-DSA-SHAKE-192s", "SLH-DSA", "3", 48, 16224, "confirmed",
              "FIPS 205; RFC 9909; RFC 9814", "oqs-python/liboqs",
              "Conservative diversity candidate with very large signatures.",
              ("SLH-DSA-SHAKE-192s", "SPHINCS+-SHAKE-192s-simple")),
)

OPTIONAL_ALGORITHMS = (
    Algorithm("Falcon-512", "Falcon/FN-DSA", "1", 897, 666, "experimental",
              "NIST-selected Falcon; FN-DSA final profile pending", "liboqs",
              "Best size/performance candidate in the 2025 RPKI study; no final RPKI-ready X.509/CMS path.",
              ("Falcon-512",), "optional"),
    Algorithm("Falcon-1024", "Falcon/FN-DSA", "5", 1793, 1280, "experimental",
              "NIST-selected Falcon; FN-DSA final profile pending", "liboqs",
              "Category-5 Falcon comparison.", ("Falcon-1024",), "optional"),
    Algorithm("MAYO-1", "MAYO", "1", 1420, 454, "round-3-candidate",
              "NIST Additional Signatures Round 3 (2026)", "liboqs",
              "Multivariate candidate with compact signatures; not standardized.",
              ("MAYO-1",), "optional"),
    Algorithm("SNOVA-(24,5,4)", "SNOVA", "1", 1016, 248, "round-3-candidate",
              "NIST Additional Signatures Round 3 (2026)", "liboqs",
              "Multivariate candidate with very compact signatures; not standardized.",
              ("SNOVA_24_5_4",), "optional"),
    Algorithm("HAWK-512", "HAWK", "1", 1024, 555, "round-3-candidate",
              "NIST Additional Signatures Round 3 (2026)", "upstream implementation required",
              "Promising lattice candidate retained as metadata-only because liboqs 0.15.0 and OpenSSL 3.6.2 do not provide it.",
              ("HAWK-512",), "optional"),
)

ALGORITHMS = REQUIRED_ALGORITHMS
ALL_ALGORITHMS = REQUIRED_ALGORITHMS + OPTIONAL_ALGORITHMS
BY_NAME = {algorithm.name: algorithm for algorithm in ALL_ALGORITHMS}


def algorithm_rows(include_optional: bool = True) -> list[dict[str, object]]:
    algorithms = ALL_ALGORITHMS if include_optional else REQUIRED_ALGORITHMS
    return [asdict(algorithm) for algorithm in algorithms]
