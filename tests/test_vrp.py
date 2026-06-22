import unittest

from pqc_rpki_lab.vrp import compare, local_canonical_hash, normalize_vrp


class VrpTest(unittest.TestCase):
    def test_normalizes_asn_and_prefix(self):
        left = {normalize_vrp({
            "prefix": "192.0.2.1/24", "maxLength": "24",
            "asn": "AS64496", "ta": "test",
        })}
        right = {normalize_vrp({
            "prefix": "192.0.2.0/24", "max_length": 24,
            "origin_as": 64496, "source": "test",
        })}
        self.assertTrue(compare(left, right)["equivalent"])

    def test_detects_semantic_difference(self):
        left = {normalize_vrp({"prefix": "192.0.2.0/24", "asn": 64496, "ta": "test"})}
        right = {normalize_vrp({"prefix": "192.0.2.0/24", "asn": 64497, "ta": "test"})}
        self.assertFalse(compare(left, right)["equivalent"])

    def test_source_difference_is_not_vrp_difference(self):
        left = {normalize_vrp({"prefix": "192.0.2.0/24", "asn": 64496, "ta": "rsa-ta"})}
        right = {normalize_vrp({"prefix": "192.0.2.0/24", "asn": 64496, "ta": "pqc-ta"})}
        result = compare(left, right)
        self.assertTrue(result["equivalent"])
        self.assertEqual(result["baseline_local_hash"], result["candidate_local_hash"])
        self.assertEqual(len(result["provenance_differences"]), 1)

    def test_local_hash_is_order_independent(self):
        first = normalize_vrp({"prefix": "2001:db8::/32", "maxLength": 48, "asn": 64497})
        second = normalize_vrp({"prefix": "192.0.2.0/24", "asn": 64496})
        self.assertEqual(local_canonical_hash({first, second}), local_canonical_hash({second, first}))
