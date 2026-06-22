import unittest

from pqc_rpki_lab.algorithms import (
    ALL_ALGORITHMS,
    BY_NAME,
    COMPARISON_ALGORITHMS,
    EXCLUDED_PROFILE_ALGORITHMS,
    OPTIONAL_ALGORITHMS,
    CLASSICAL_REFERENCE_ALGORITHMS,
    COMPOSITE_ESTIMATES,
)


class AlgorithmsTest(unittest.TestCase):
    def test_comparison_candidates_are_present(self):
        self.assertEqual(len(COMPARISON_ALGORITHMS), 5)
        for name in (
            "RSA-2048/SHA-256",
            "ML-DSA-65",
            "ML-DSA-87",
            "SLH-DSA-SHAKE-128s",
            "SLH-DSA-SHAKE-192s",
        ):
            self.assertIn(name, BY_NAME)
            self.assertTrue(BY_NAME[name].comparison_required)

    def test_profile_tracks_are_distinct_from_comparison_scope(self):
        self.assertEqual(BY_NAME["ML-DSA-65"].track, "primary")
        self.assertEqual(BY_NAME["ML-DSA-87"].track, "high-assurance")
        self.assertEqual(BY_NAME["SLH-DSA-SHAKE-128s"].track, "diversity")
        self.assertEqual(BY_NAME["SLH-DSA-SHAKE-192s"].track, "diversity")

    def test_mldsa44_is_measured_but_excluded_by_policy(self):
        self.assertEqual(len(EXCLUDED_PROFILE_ALGORITHMS), 1)
        algorithm = BY_NAME["ML-DSA-44"]
        self.assertEqual(algorithm.track, "excluded-policy")
        self.assertTrue(algorithm.comparison_required)

    def test_sizes_are_positive(self):
        for algorithm in ALL_ALGORITHMS:
            self.assertGreater(algorithm.public_key_bytes, 0)
            self.assertGreater(algorithm.signature_bytes, 0)

    def test_optional_candidates_are_separate(self):
        self.assertEqual(len(OPTIONAL_ALGORITHMS), 5)
        for name in ("Falcon-512", "Falcon-1024", "MAYO-1", "SNOVA-(24,5,4)", "HAWK-512"):
            self.assertIn(name, BY_NAME)
            self.assertEqual(BY_NAME[name].track, "optional")

    def test_review_candidates_are_separate(self):
        self.assertEqual({value.name for value in CLASSICAL_REFERENCE_ALGORITHMS},
                         {"P-256/SHA-256", "Ed25519"})
        self.assertEqual(
            {value.name for value in COMPOSITE_ESTIMATES},
            {
                "RSA-2048+ML-DSA-44",
                "P-256+ML-DSA-44",
                "RSA-2048+ML-DSA-65",
                "P-256+ML-DSA-65",
                "RSA-2048+ML-DSA-87",
                "P-256+ML-DSA-87",
                "P-256+Falcon-512",
            },
        )
        self.assertTrue(all(value.status == "estimated" for value in COMPOSITE_ESTIMATES))
