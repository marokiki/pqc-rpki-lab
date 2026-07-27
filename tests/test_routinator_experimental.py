from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RoutinatorExperimentalEvidenceTests(unittest.TestCase):
    def load(self, name: str) -> dict:
        return json.loads((ROOT / "results/composite-e2e" / name).read_text())

    def test_four_scenario_matrix(self) -> None:
        result = self.load("routinator-matrix.json")
        self.assertTrue(result["success"])
        self.assertEqual(
            set(result["cases"]),
            {"rsa_baseline", "pure_mldsa65", "composite_standalone", "mixed_tree"},
        )
        for scenario, row in result["cases"].items():
            self.assertEqual(row["experimental"]["vrp_count"], 2)
            if scenario == "rsa_baseline":
                self.assertEqual(row["default"]["status"], "accepted")
            else:
                self.assertEqual(row["default"]["status"], "rejected")
                self.assertEqual(row["experimental"]["status"], "accepted")

    def test_negative_matrix(self) -> None:
        result = self.load("routinator-negative-summary.json")
        self.assertTrue(result["all_rejected"])
        self.assertEqual(len(result["results"]), 15)
        self.assertTrue(all(row["observed_reason"] for row in result["results"]))

    def test_public_results_do_not_leak_local_paths(self) -> None:
        text = json.dumps(
            {
                "matrix": self.load("routinator-matrix.json"),
                "negative": self.load("routinator-negative-summary.json"),
            }
        )
        self.assertNotIn("/" + "home" + "/", text)
        self.assertNotIn("/" + "Users" + "/", text)

    def test_patch_is_explicitly_gated(self) -> None:
        patch = (ROOT / "patches/rpki-rs-experimental-pqc.patch").read_text()
        self.assertIn("PQC_RPKI_EXPERIMENTAL", patch)
        self.assertIn("ML_DSA_65_ECDSA_P256_SHA512", patch)
        self.assertIn("43, 6, 1, 5, 5, 7, 6, 45", patch)
        self.assertIn("0x81", patch)


if __name__ == "__main__":
    unittest.main()
