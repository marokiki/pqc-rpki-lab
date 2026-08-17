import csv
import unittest
from pathlib import Path


class MeasurementEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_standardized_certificate_sizes_are_measured(self):
        with (self.root / "results/generated-object-sizes.csv").open() as source:
            rows = list(csv.DictReader(source))
        requested = {
            "P-256/SHA-256",
            "Ed25519",
            "ML-DSA-44",
        }
        measured = {
            row["algorithm"]
            for row in rows
            if row["object_type"] in {"CA certificate", "EE certificate", "CRL"}
            and row["status"] == "confirmed"
            and int(row["bytes"]) > 0
        }
        self.assertTrue(requested <= measured)

    def test_fn_dsa_and_rsa_combinations_have_100k_results(self):
        with (self.root / "results/review-2026-06/composite-100k.csv").open() as source:
            rows = {row["algorithm"]: row for row in csv.DictReader(source)}
        requested = {
            "FN-DSA-512 (Falcon-512)",
            "RSA-2048+P-256",
            "RSA-2048+Ed25519",
            "RSA-2048+ML-DSA-44",
            "RSA-2048+ML-DSA-65",
            "RSA-2048+ML-DSA-87",
            "RSA-2048+FN-DSA-512",
        }
        for name in requested:
            self.assertEqual(rows[name]["status"], "confirmed", name)
            self.assertEqual(int(rows[name]["iterations"]), 100_000, name)

    def test_draft_19_composite_variants_have_100k_results(self):
        path = self.root / "results/draft-composite-2026-07/draft-composite-100k.csv"
        with path.open() as source:
            rows = {row["variant"]: row for row in csv.DictReader(source)}
        requested = {
            "ML-DSA-44 + ECDSA P-256",
            "ML-DSA-65 + ECDSA P-256",
            "ML-DSA-87 + ECDSA P-384",
        }
        self.assertEqual(set(rows), requested)
        for name in requested:
            self.assertEqual(rows[name]["status"], "confirmed", name)
            self.assertEqual(int(rows[name]["iterations"]), 100_000, name)
            self.assertGreater(float(rows[name]["sign_seconds"]), 0, name)
            self.assertGreater(float(rows[name]["verify_seconds"]), 0, name)

    def test_draft_contains_measured_values_without_tbd(self):
        draft = (
            self.root / "ietf/draft-yoshikawa-sidrops-pqc-rpki-02.md"
        ).read_text()
        for row in (
            "| P-256/SHA-256 | 641 | 587 | 187 |",
            "| Ed25519 | 578 | 524 | 170 |",
            "| ML-DSA-44 | 4238 | 4184 | 2541 |",
            "| FN-DSA-512 (Falcon-512) | 2048 | 1991 | 764 |",
            "| ML-DSA-44 + P-256 | 26.0 | 8.3 | 1377 | 2491 | 3.16 |",
            "| ML-DSA-65 + P-256 | 45.6 | 11.9 | 2017 | 3380 | 4.09 |",
            "| ML-DSA-87 + P-384 | 59.4 | 32.8 | 2689 | 4730 | 5.40 |",
        ):
            self.assertIn(row, draft)
        measurement_appendix = draft.split("# Measurement Details", 1)[1]
        self.assertNotIn("remain TBD", measurement_appendix)


if __name__ == "__main__":
    unittest.main()
