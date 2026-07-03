import unittest

from pqc_rpki_lab.rpki_asn1 import (
    OID_CT_MFT,
    OID_CT_ROA,
    manifest_econtent,
    parse_manifest_econtent,
    roa_econtent,
    roa_ip_address,
)


class RpkiAsn1Test(unittest.TestCase):
    def test_content_type_oids_are_stable(self):
        self.assertEqual(OID_CT_ROA, "1.2.840.113549.1.9.16.1.24")
        self.assertEqual(OID_CT_MFT, "1.2.840.113549.1.9.16.1.26")

    def test_roa_econtent_der_sequence(self):
        value = roa_econtent(64496, [("192.0.2.0/24", 24), ("2001:db8::/32", 48)])
        self.assertEqual(value[0], 0x30)
        self.assertIn(b"\x02\x03\x00\xfb\xf0", value)

    def test_roa_rejects_invalid_max_length(self):
        with self.assertRaises(ValueError):
            roa_ip_address("192.0.2.0/24", 23)

    def test_manifest_econtent_is_deterministic(self):
        left = manifest_econtent([("b.roa", b"b"), ("a.roa", b"a")])
        right = manifest_econtent([("a.roa", b"a"), ("b.roa", b"b")])
        self.assertEqual(left, right)
        self.assertEqual(left[0], 0x30)

    def test_manifest_rejects_nested_file_name(self):
        with self.assertRaises(ValueError):
            manifest_econtent([("nested/a.roa", b"a")])

    def test_manifest_parser_returns_file_hashes_and_times(self):
        value = manifest_econtent([("route.roa", b"content")])
        parsed = parse_manifest_econtent(value)
        self.assertEqual(parsed["version"], 0)
        self.assertEqual(parsed["file_hash_algorithm"], "2.16.840.1.101.3.4.2.1")
        self.assertEqual(parsed["entries"][0]["file"], "route.roa")
