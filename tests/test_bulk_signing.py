import unittest

from benchmarks.bulk_signing import parse_speed


class BulkSigningTest(unittest.TestCase):
    def test_parses_evp_rates(self):
        output = """+DTP:ML-DSA-44:keygen:1
+R18:20000:ML-DSA-44:1.00
+DTP:ML-DSA-44:signs:1
+R19:4000:ML-DSA-44:1.00
+DTP:ML-DSA-44:verify:1
+R20:21000:ML-DSA-44:1.00
"""
        self.assertEqual(parse_speed(output), {
            "keygen": 20000.0,
            "sign": 4000.0,
            "verify": 21000.0,
        })

    def test_parses_ecdsa_field_order(self):
        output = """+DTP:256:sign:ecdsa:1
+R7:80000:256:1.00
+DTP:256:verify:ecdsa:1
+R8:27000:256:1.00
"""
        self.assertEqual(parse_speed(output), {"sign": 80000.0, "verify": 27000.0})
