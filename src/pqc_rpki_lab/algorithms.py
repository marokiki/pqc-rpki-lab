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
    track: str = "primary"
    comparison_required: bool = True


COMPARISON_ALGORITHMS = (
    Algorithm("RSA-2048/SHA-256", "RSA", "classical", 270, 256, "confirmed",
              "RFC 7935", "OpenSSL CLI",
              "Current RPKI baseline; SPKI size is an approximate DER value.",
              track="baseline"),
    Algorithm("ML-DSA-65", "ML-DSA", "3", 1952, 3309, "confirmed",
              "FIPS 204; RFC 9881; RFC 9882", "oqs-python/liboqs",
              "Primary balanced PQC candidate.", ("ML-DSA-65", "Dilithium3")),
    Algorithm("ML-DSA-87", "ML-DSA", "5", 2592, 4627, "confirmed",
              "FIPS 204; RFC 9881; RFC 9882", "oqs-python/liboqs",
              "High-assurance candidate with larger objects.", ("ML-DSA-87", "Dilithium5"),
              "high-assurance"),
    Algorithm("SLH-DSA-SHAKE-128s", "SLH-DSA", "1", 32, 7856, "confirmed",
              "FIPS 205; RFC 9909; RFC 9814", "oqs-python/liboqs",
              "Hash-based diversity candidate; signature size is the main concern.",
              ("SLH-DSA-SHAKE-128s", "SPHINCS+-SHAKE-128s-simple"), "diversity"),
    Algorithm("SLH-DSA-SHAKE-192s", "SLH-DSA", "3", 48, 16224, "confirmed",
              "FIPS 205; RFC 9909; RFC 9814", "oqs-python/liboqs",
              "Conservative diversity candidate with very large signatures.",
              ("SLH-DSA-SHAKE-192s", "SPHINCS+-SHAKE-192s-simple"), "diversity"),
)

CLASSICAL_REFERENCE_ALGORITHMS = (
    Algorithm("P-256/SHA-256", "ECDSA", "classical-128", 65, 72, "confirmed",
              "FIPS 186-5; RFC 8608 for BGPsec", "OpenSSL CLI",
              "Compact classical counterfactual; not the current RFC 6488 RPKI profile. "
              "Signature size uses the conservative DER maximum.", track="classical-reference"),
    Algorithm("Ed25519", "EdDSA", "classical-128", 32, 64, "confirmed",
              "RFC 8032", "OpenSSL CLI",
              "Compact classical counterfactual; not the current RFC 6488 RPKI profile.",
              track="classical-reference"),
)

EXCLUDED_PROFILE_ALGORITHMS = (
    Algorithm("ML-DSA-44", "ML-DSA", "2", 1312, 2420, "confirmed",
              "FIPS 204; RFC 9881; RFC 9882", "OpenSSL default provider",
              "Measured comparison excluded from the primary profile by the Category 3 policy floor.",
              ("ML-DSA-44", "Dilithium2"), "excluded-policy", True),
)

OPTIONAL_ALGORITHMS = (
    Algorithm("Falcon-512", "Falcon/FN-DSA", "1", 897, 666, "experimental",
              "NIST-selected Falcon; FN-DSA final profile pending", "liboqs",
              "Best size/performance candidate in the 2025 RPKI study; no final RPKI-ready X.509/CMS path.",
              ("Falcon-512",), "optional", False),
    Algorithm("Falcon-1024", "Falcon/FN-DSA", "5", 1793, 1280, "experimental",
              "NIST-selected Falcon; FN-DSA final profile pending", "liboqs",
              "Category-5 Falcon comparison.", ("Falcon-1024",), "optional", False),
    Algorithm("MAYO-1", "MAYO", "1", 1420, 454, "round-3-candidate",
              "NIST Additional Signatures Round 3 (2026)", "liboqs",
              "Multivariate candidate with compact signatures; not standardized.",
              ("MAYO-1",), "optional", False),
    Algorithm("SNOVA-(24,5,4)", "SNOVA", "1", 1016, 248, "round-3-candidate",
              "NIST Additional Signatures Round 3 (2026)", "liboqs",
              "Multivariate candidate with very compact signatures; not standardized.",
              ("SNOVA_24_5_4",), "optional", False),
    Algorithm("HAWK-512", "HAWK", "1", 1024, 555, "round-3-candidate",
              "NIST Additional Signatures Round 3 (2026)", "upstream implementation required",
              "Promising lattice candidate retained as metadata-only because liboqs 0.15.0 and OpenSSL 3.6.2 do not provide it.",
              ("HAWK-512",), "optional", False),
)

COMPOSITE_ESTIMATES = (
    Algorithm("RSA-2048+ML-DSA-44", "Composite", "hybrid", 1582, 2676, "estimated",
              "draft-ietf-lamps-pq-composite-sigs", "size model only",
              "Component-size sum excluding composite ASN.1 overhead; no local X.509/CMS interoperability evidence.",
              track="composite-candidate", comparison_required=False),
    Algorithm("P-256+ML-DSA-44", "Composite", "hybrid", 1377, 2492, "estimated",
              "draft-ietf-lamps-pq-composite-sigs", "size model only",
              "Component-size sum excluding composite ASN.1 overhead; no local X.509/CMS interoperability evidence.",
              track="composite-candidate", comparison_required=False),
    Algorithm("P-256+Falcon-512", "Composite", "hybrid", 962, 738, "estimated",
              "draft-ietf-lamps-pq-composite-sigs; FN-DSA pending", "size model only",
              "Component-size sum excluding composite ASN.1 overhead; Falcon/FN-DSA profile is not final.",
              track="composite-candidate", comparison_required=False),
)

ALGORITHMS = COMPARISON_ALGORITHMS
ALL_ALGORITHMS = (COMPARISON_ALGORITHMS + CLASSICAL_REFERENCE_ALGORITHMS +
                  EXCLUDED_PROFILE_ALGORITHMS + OPTIONAL_ALGORITHMS + COMPOSITE_ESTIMATES)
BY_NAME = {algorithm.name: algorithm for algorithm in ALL_ALGORITHMS}


def algorithm_rows(include_optional: bool = True) -> list[dict[str, object]]:
    algorithms = ALL_ALGORITHMS if include_optional else COMPARISON_ALGORITHMS
    return [asdict(algorithm) for algorithm in algorithms]
