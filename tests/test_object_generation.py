import unittest

from tools.object_generation_feasibility import ALGORITHMS, config_text


class ObjectGenerationTest(unittest.TestCase):
    def test_comparison_algorithms_are_covered(self):
        self.assertEqual(
            [row[0] for row in ALGORITHMS],
            [
                "RSA-2048/SHA-256",
                "P-256/SHA-256",
                "Ed25519",
                "ML-DSA-44",
                "ML-DSA-65",
                "ML-DSA-87",
                "SLH-DSA-SHAKE-128s",
                "SLH-DSA-SHAKE-192s",
                "FN-DSA-512 (Falcon-512)",
            ],
        )

    def test_profile_config_contains_resource_extensions(self):
        text = config_text(__import__("pathlib").Path("/tmp/example"))
        self.assertIn("sbgp-ipAddrBlock", text)
        self.assertIn("sbgp-autonomousSysNum", text)
        self.assertIn("rpkiManifest", text)
