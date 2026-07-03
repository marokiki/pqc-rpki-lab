import json
import unittest

from pqc_rpki_lab.mixed_tree import default_mixed_tree_fixture, validate_mixed_tree
from pqc_rpki_lab.rpki_objects import (
    ManifestScope,
    PublishedObject,
    check_manifest_key_consistency,
    manifest_payload,
    validate_manifest_hashes,
)


class RpkiObjectModelTest(unittest.TestCase):
    def product(self, path="route.roa", issuer="ca-key", signer="ca-key"):
        return PublishedObject(
            path=path,
            object_type="ROA",
            issuer_key_id=issuer,
            signer_key_id=signer,
            payload=b"AS64496 192.0.2.0/24\n",
        )

    def test_manifest_hash_validation_accepts_matching_entries(self):
        product = self.product()
        self.assertEqual(validate_manifest_hashes([product], [product.manifest_entry()]), [])

    def test_manifest_hash_validation_rejects_corrupted_hash(self):
        product = self.product()
        mismatches = validate_manifest_hashes([product], [{"path": product.path, "sha256": "00"}])
        self.assertEqual(mismatches[0]["path"], product.path)

    def test_manifest_payload_is_deterministic(self):
        left = [self.product("b.roa"), self.product("a.roa")]
        right = [self.product("a.roa"), self.product("b.roa")]
        self.assertEqual(manifest_payload(left), manifest_payload(right))
        self.assertEqual(len(json.loads(manifest_payload(left))), 2)

    def test_manifest_key_consistency_accepts_one_ca_scope(self):
        product = self.product()
        result = check_manifest_key_consistency(ManifestScope("ca-key", "ca-key", (product,)))
        self.assertTrue(result["consistent"])

    def test_manifest_key_consistency_rejects_wrong_product_scope(self):
        product = self.product(issuer="other-key")
        result = check_manifest_key_consistency(ManifestScope("ca-key", "ca-key", (product,)))
        self.assertFalse(result["consistent"])

    def test_mixed_tree_fixture_models_ca_boundary(self):
        result = validate_mixed_tree(default_mixed_tree_fixture())
        self.assertTrue(result["valid"])

