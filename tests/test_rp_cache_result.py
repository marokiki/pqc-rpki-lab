from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RpCacheResultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.result = json.loads(
            (
                ROOT
                / "results/scaled-corpus/rp-cache-regimes.json"
            ).read_text()
        )

    def test_all_regimes_have_thirty_successful_samples(self) -> None:
        self.assertTrue(self.result["all_expected_vrps_observed"])
        self.assertEqual(self.result["repetitions_per_regime"], 30)
        for implementation in ("rpki_client", "routinator"):
            for regime in (
                "fresh_validator_cache",
                "unchanged_repository_cache",
                "one_roa_update",
            ):
                fields = self.result[implementation][regime]
                for name in (
                    "wall_seconds",
                    "user_seconds",
                    "system_seconds",
                    "max_rss_kib",
                ):
                    self.assertEqual(fields[name]["samples"], 30)

    def test_update_changes_a_strict_subset_of_repository_files(self) -> None:
        update = self.result["update"]
        self.assertGreater(update["changed_file_count"], 0)
        self.assertLess(update["changed_file_count"], self.result["roa_count"])

    def test_public_summary_has_no_raw_or_private_material(self) -> None:
        text = json.dumps(self.result)
        self.assertNotIn("/" + "home" + "/", text)
        self.assertNotIn("/" + "Users" + "/", text)
        self.assertFalse(self.result["contains_private_keys"])
        self.assertFalse(self.result["contains_raw_objects"])

    def test_environment_identifies_both_rps(self) -> None:
        environment = self.result["environment"]
        self.assertIn("rpki-client-portable", environment["rpki_client"])
        self.assertIn("Routinator", environment["routinator"])
        self.assertEqual(environment["machine"], "x86_64")


if __name__ == "__main__":
    unittest.main()
