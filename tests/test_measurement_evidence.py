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

    def test_draft_contains_measured_values_without_tbd(self):
        draft = (
            self.root / "ietf/draft-yoshikawa-sidrops-pqc-rpki-01.md"
        ).read_text()
        for row in (
            "| P-256/SHA-256 | 641 | 587 | 187 |",
            "| Ed25519 | 578 | 524 | 170 |",
            "| ML-DSA-44 | 4238 | 4184 | 2541 |",
            "| FN-DSA-512 (Falcon-512) | 2048 | 1991 | 764 |",
            "| FN-DSA-512 | 10.5 | 1.6 |",
            "| RSA-2048 + FN-DSA-512 (components) | 44.6 | 2.6 |",
        ):
            self.assertIn(row, draft)
        measurement_appendix = draft.split("# Preliminary Measurement Results", 1)[1]
        self.assertNotIn("remain TBD", measurement_appendix)


if __name__ == "__main__":
    unittest.main()
