import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from pqc_rpki_lab import der
from pqc_rpki_lab.cms import (
    assemble_mldsa65_signed_object,
    profile_check,
    sign_raw_mldsa,
    signed_attributes,
    verify_raw_signature,
)
from pqc_rpki_lab.rpki_asn1 import OID_CT_ROA, roa_econtent


class CmsProfileTest(unittest.TestCase):
    def fixture(self) -> tuple[bytes, bytes]:
        ski = bytes(range(20))
        content = roa_econtent(64496, [("192.0.2.0/24", 24)])
        cms = assemble_mldsa65_signed_object(
            econtent_type=OID_CT_ROA,
            econtent=content,
            ee_certificate_der=der.sequence(der.integer(1)),
            subject_key_identifier=ski,
            signature=b"signature-placeholder",
            signing_time="260702120000Z",
        )
        return cms, ski

    def test_profile_accepts_required_structure(self):
        cms, ski = self.fixture()
        report = profile_check(cms, expected_econtent_type=OID_CT_ROA, expected_ski=ski)
        self.assertTrue(report["valid"], report)

    def test_profile_rejects_wrong_subject_key_identifier(self):
        cms, _ = self.fixture()
        report = profile_check(cms, expected_econtent_type=OID_CT_ROA, expected_ski=b"wrong")
        self.assertFalse(report["valid"])
        self.assertFalse(report["checks"]["sid_matches_ee_ski"])

    def test_profile_rejects_changed_message_digest(self):
        cms, ski = self.fixture()
        marker = __import__("hashlib").sha512(roa_econtent(64496, [("192.0.2.0/24", 24)])).digest()
        self.assertIn(marker, cms)
        changed = cms.replace(marker, bytes([marker[0] ^ 1]) + marker[1:], 1)
        report = profile_check(changed, expected_econtent_type=OID_CT_ROA, expected_ski=ski)
        self.assertFalse(report["checks"]["message_digest_matches"])

    def test_profile_rejects_malformed_der(self):
        cms, ski = self.fixture()
        report = profile_check(cms[:-1], expected_econtent_type=OID_CT_ROA, expected_ski=ski)
        self.assertFalse(report["valid"])
        self.assertFalse(report["checks"]["der_structure"])

    def test_raw_mldsa_signature_and_wrong_key(self):
        openssl = shutil.which("openssl")
        if not openssl:
            self.skipTest("OpenSSL unavailable")
        with tempfile.TemporaryDirectory(prefix="pqc-rpki-cms-test-") as name:
            directory = Path(name)
            keys = [directory / "one.pem", directory / "two.pem"]
            pubs = [directory / "one.pub.pem", directory / "two.pub.pem"]
            for key, public in zip(keys, pubs):
                generated = subprocess.run(
                    [openssl, "genpkey", "-algorithm", "ML-DSA-65", "-out", str(key)],
                    capture_output=True,
                )
                if generated.returncode:
                    self.skipTest("OpenSSL does not provide ML-DSA-65")
                subprocess.run(
                    [openssl, "pkey", "-in", str(key), "-pubout", "-out", str(public)],
                    check=True, capture_output=True,
                )
            content = roa_econtent(64496, [("192.0.2.0/24", 24)])
            attrs = signed_attributes(OID_CT_ROA, content, "260702120000Z")
            signature = sign_raw_mldsa(openssl, keys[0], attrs)
            cms = assemble_mldsa65_signed_object(
                econtent_type=OID_CT_ROA,
                econtent=content,
                ee_certificate_der=der.sequence(der.integer(1)),
                subject_key_identifier=bytes(range(20)),
                signature=signature,
                signing_time="260702120000Z",
            )
            self.assertTrue(verify_raw_signature(openssl, pubs[0], cms))
            self.assertFalse(verify_raw_signature(openssl, pubs[1], cms))
