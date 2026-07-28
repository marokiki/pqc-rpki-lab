from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OperationalNegativeEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.result = json.loads(
            (
                ROOT
                / "results/composite-e2e/operational-negative-summary.json"
            ).read_text()
        )

    def test_all_operational_cases_are_rejected_by_both_rps(self) -> None:
        self.assertTrue(self.result["all_rejected"])
        self.assertEqual(len(self.result["results"]), 7)
        for row in self.result["results"]:
            for rp in ("rpki_client", "routinator"):
                self.assertEqual(row[rp]["status"], "rejected")
                self.assertEqual(row[rp]["vrp_count"], 0)

    def test_cases_cover_freshness_revocation_and_missing_objects(self) -> None:
        codes = {row["reason_code"] for row in self.result["results"]}
        self.assertEqual(
            codes,
            {
                "manifest-expired",
                "crl-expired",
                "ee-certificate-expired",
                "ee-certificate-revoked",
                "manifest-object-missing",
                "manifest-missing",
                "crl-missing",
            },
        )

    def test_public_summary_has_no_private_material_or_paths(self) -> None:
        text = json.dumps(self.result)
        self.assertNotIn("/" + "home" + "/", text)
        self.assertNotIn("/" + "Users" + "/", text)
        self.assertFalse(self.result["contains_private_keys"])
        self.assertFalse(self.result["contains_raw_objects"])


if __name__ == "__main__":
    unittest.main()
