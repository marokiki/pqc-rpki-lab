from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class KrillExperimentalEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.result = json.loads(
            (ROOT / "results/composite-e2e/krill-rollover.json").read_text()
        )

    def test_composite_issuance_and_rsa_rollback(self) -> None:
        self.assertTrue(self.result["success"])
        for mode, row in self.result["phases"]["composite"].items():
            expected = "accepted" if mode.endswith("experimental") else "rejected"
            self.assertEqual(row["status"], expected)
        for row in self.result["phases"]["rollback"].values():
            self.assertEqual(row["status"], "accepted")
            self.assertEqual(row["vrp_count"], 1)

    def test_both_experimental_rps_produce_expected_vrp(self) -> None:
        expected = self.result["expected_vrps"]
        phase = self.result["phases"]["composite"]
        self.assertEqual(phase["rpki_client_experimental"]["vrps"], expected)
        self.assertEqual(phase["routinator_experimental"]["vrps"], expected)

    def test_one_roa_update_is_validated_before_rollback(self) -> None:
        phase = self.result["phases"]["composite-updated"]
        expected = self.result["updated_expected_vrps"]
        self.assertEqual(expected[0]["prefix"], "192.0.2.0/25")
        for mode, row in phase.items():
            status = (
                "accepted" if mode.endswith("experimental") else "rejected"
            )
            self.assertEqual(row["status"], status)
        self.assertEqual(
            phase["rpki_client_experimental"]["vrps"], expected
        )
        self.assertEqual(
            phase["routinator_experimental"]["vrps"], expected
        )

    def test_public_evidence_has_no_local_path(self) -> None:
        text = json.dumps(self.result)
        self.assertNotIn("/" + "home" + "/", text)
        self.assertNotIn("/" + "Users" + "/", text)

    def test_patch_contains_research_gates_and_issuance_test(self) -> None:
        patch = (ROOT / "patches/krill-experimental-pqc.patch").read_text()
        self.assertIn("PQC_RPKI_EXPERIMENTAL", patch)
        self.assertIn("PQC_RPKI_KRILL_SUITE_FILE", patch)
        self.assertIn("sign_oneshot_to_vec", patch)
        self.assertIn("functional_pqc_rollover", patch)
        self.assertIn("MlDsa65EcdsaP256Sha512", patch)
        self.assertIn("PQC_RPKI_KRILL_ROA_COUNT", patch)
        self.assertIn("publisher_details", patch)
        self.assertIn("composite-updated", patch)

    def test_scaled_runner_repeats_and_summarizes(self) -> None:
        runner = (
            ROOT / "tools/run_krill_scaled_experimental.sh"
        ).read_text()
        self.assertIn("PQC_RPKI_KRILL_RELIABILITY_REPETITIONS", runner)
        self.assertIn("PQC_RPKI_KRILL_ROA_COUNT", runner)
        self.assertIn("/usr/bin/time", runner)
        self.assertIn("summarize_scaled_krill.py", runner)


if __name__ == "__main__":
    unittest.main()
