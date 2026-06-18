import unittest

from pqc_rpki_lab.vrp import compare, normalize_vrp


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
