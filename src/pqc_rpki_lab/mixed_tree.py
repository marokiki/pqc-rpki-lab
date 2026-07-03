from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CertificateNode:
    name: str
    subject_key_id: str
    spki_algorithm: str
    issuer: str
    issuer_signature_algorithm: str
    status: str = "synthetic-fixture"


@dataclass(frozen=True)
class MixedTreeFixture:
    nodes: tuple[CertificateNode, ...]
    products: tuple[dict[str, str], ...]


def default_mixed_tree_fixture() -> MixedTreeFixture:
    return MixedTreeFixture(
        nodes=(
            CertificateNode(
                name="rsa-ta",
                subject_key_id="rsa-ta-key",
                spki_algorithm="RSA-2048",
                issuer="self",
                issuer_signature_algorithm="RSA-2048/SHA-256",
            ),
            CertificateNode(
                name="mldsa-child-ca",
                subject_key_id="mldsa-child-key",
                spki_algorithm="ML-DSA-65",
                issuer="rsa-ta",
                issuer_signature_algorithm="RSA-2048/SHA-256",
            ),
            CertificateNode(
                name="roa-ee",
                subject_key_id="mldsa-roa-ee-key",
                spki_algorithm="ML-DSA-65",
                issuer="mldsa-child-ca",
                issuer_signature_algorithm="ML-DSA-65",
            ),
        ),
        products=(
            {
                "path": "child/manifest.mft",
                "object_type": "Manifest",
                "issuer": "mldsa-child-ca",
                "signature_algorithm": "ML-DSA-65",
                "publication_scope_key_id": "mldsa-child-key",
            },
            {
                "path": "child/ca.crl",
                "object_type": "CRL",
                "issuer": "mldsa-child-ca",
                "signature_algorithm": "ML-DSA-65",
                "publication_scope_key_id": "mldsa-child-key",
            },
            {
                "path": "child/route.roa",
                "object_type": "ROA",
                "issuer": "roa-ee",
                "signature_algorithm": "ML-DSA-65",
                "publication_scope_key_id": "mldsa-child-key",
            },
        ),
    )


def validate_mixed_tree(fixture: MixedTreeFixture) -> dict[str, object]:
    nodes = {node.name: node for node in fixture.nodes}
    failures: list[dict[str, str]] = []
    for node in fixture.nodes:
        if node.issuer != "self" and node.issuer not in nodes:
            failures.append({"name": node.name, "problem": "missing-issuer", "issuer": node.issuer})
        if node.name == "mldsa-child-ca":
            if node.issuer_signature_algorithm != "RSA-2048/SHA-256" or node.spki_algorithm != "ML-DSA-65":
                failures.append({"name": node.name, "problem": "missing-rsa-to-mldsa-ca-boundary"})
    for product in fixture.products:
        issuer = product["issuer"]
        if issuer not in nodes:
            failures.append({"name": product["path"], "problem": "missing-product-issuer", "issuer": issuer})
        if product["signature_algorithm"] != "ML-DSA-65":
            failures.append({"name": product["path"], "problem": "unexpected-product-algorithm"})
        if product["publication_scope_key_id"] != "mldsa-child-key":
            failures.append({"name": product["path"], "problem": "publication-scope-key-gap"})
    return {
        "valid": not failures,
        "failures": failures,
        "classification": "synthetic mixed-tree model; not validator interoperability evidence",
    }
