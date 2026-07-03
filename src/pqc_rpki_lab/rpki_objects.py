from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PublishedObject:
    path: str
    object_type: str
    issuer_key_id: str
    signer_key_id: str
    payload: bytes

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.payload).hexdigest()

    def manifest_entry(self) -> dict[str, str]:
        return {"path": self.path, "sha256": self.sha256}


@dataclass(frozen=True)
class ManifestScope:
    manifest_signer_key_id: str
    expected_issuer_key_id: str
    products: tuple[PublishedObject, ...]


def manifest_payload(products: list[PublishedObject]) -> bytes:
    entries = [product.manifest_entry() for product in sorted(products, key=lambda item: item.path)]
    return json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()


def validate_manifest_hashes(products: list[PublishedObject], entries: list[dict[str, str]]) -> list[dict[str, str]]:
    expected = {product.path: product.sha256 for product in products}
    mismatches: list[dict[str, str]] = []
    for entry in entries:
        path = entry["path"]
        observed = entry["sha256"]
        if expected.get(path) != observed:
            mismatches.append({
                "path": path,
                "expected_sha256": expected.get(path, ""),
                "observed_sha256": observed,
            })
    for path, digest in expected.items():
        if path not in {entry["path"] for entry in entries}:
            mismatches.append({"path": path, "expected_sha256": digest, "observed_sha256": "missing"})
    return mismatches


def check_manifest_key_consistency(scope: ManifestScope) -> dict[str, object]:
    mismatches = []
    if scope.manifest_signer_key_id != scope.expected_issuer_key_id:
        mismatches.append({
            "path": "manifest",
            "problem": "manifest-signer-key-mismatch",
            "expected_key_id": scope.expected_issuer_key_id,
            "observed_key_id": scope.manifest_signer_key_id,
        })
    for product in scope.products:
        if product.issuer_key_id != scope.expected_issuer_key_id:
            mismatches.append({
                "path": product.path,
                "problem": "product-issuer-key-mismatch",
                "expected_key_id": scope.expected_issuer_key_id,
                "observed_key_id": product.issuer_key_id,
            })
        if product.signer_key_id != product.issuer_key_id:
            mismatches.append({
                "path": product.path,
                "problem": "product-signer-context-mismatch",
                "expected_key_id": product.issuer_key_id,
                "observed_key_id": product.signer_key_id,
            })
    return {
        "consistent": not mismatches,
        "mismatches": mismatches,
        "rule": (
            "Products in one publication scope must be associated with the Manifest "
            "signer's issuing CA key context. This models RFC 6488 EE-certificate "
            "usage and does not claim every object is directly signed by the CA key."
        ),
    }


def public_fixture_row(product: PublishedObject) -> dict[str, object]:
    row = asdict(product)
    row["payload"] = f"{len(product.payload)} bytes"
    row["sha256"] = product.sha256
    return row
