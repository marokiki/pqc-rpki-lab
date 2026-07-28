from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class KrillRepeatedResultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.result = json.loads(
            (
                ROOT
                / "results/scaled-corpus/krill-repeated-summary.json"
            ).read_text()
        )

    def test_campaign_has_the_declared_sample_counts(self) -> None:
        expected_generation = {1: 30, 10: 30, 100: 30, 1000: 10}
        rows = {row["roa_count"]: row for row in self.result["results"]}
        self.assertEqual(set(rows), set(expected_generation))
        for count, repetitions in expected_generation.items():
            row = rows[count]
            self.assertEqual(row["generation_repetitions"], repetitions)
            self.assertEqual(row["validation_repetitions"], 100)
            self.assertTrue(row["all_validations_succeeded"])
            for field in (
                "wall_seconds",
                "user_seconds",
                "system_seconds",
                "max_rss_kib",
            ):
                self.assertEqual(
                    row["generation"][field]["samples"], repetitions
                )
                self.assertEqual(
                    row["validation_matrix"][field]["samples"], 100
                )

    def test_environment_and_measurement_boundary_are_recorded(self) -> None:
        environment = self.result["environment"]
        self.assertGreater(environment["logical_cpu_count"], 0)
        self.assertGreater(environment["memory_total_kib"], 0)
        self.assertIn("OpenSSL 3.6.2", environment["openssl"])
        self.assertIn("fresh-validator-cache", self.result["classification"])
        self.assertIn(
            "100000",
            self.result["campaign"]["primitive_measurements_are_separate"],
        )

    def test_public_result_has_no_raw_or_private_material(self) -> None:
        text = json.dumps(self.result)
        self.assertNotIn("/" + "home" + "/", text)
        self.assertNotIn("/" + "Users" + "/", text)
        self.assertFalse(self.result["contains_private_keys"])
        self.assertFalse(self.result["contains_raw_objects"])


if __name__ == "__main__":
    unittest.main()
