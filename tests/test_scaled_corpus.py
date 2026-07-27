from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ScaledCorpusEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cache = json.loads(
            (ROOT / "results/scaled-corpus/public-cache-profile.json").read_text()
        )
        self.krill = json.loads(
            (ROOT / "results/scaled-corpus/krill-scaled-summary.json").read_text()
        )

    def test_public_cache_profile_is_aggregate_only(self) -> None:
        self.assertFalse(
            self.cache["synthetic_corpus"]["contains_source_objects"]
        )
        self.assertEqual(
            self.cache["object_count"],
            sum(self.cache["object_type_counts"].values()),
        )
        self.assertNotIn("object_types_from_materialized_files", self.cache)
        self.assertIn("object_types", self.cache)

    def test_scaled_result_records_both_phases(self) -> None:
        self.assertEqual(self.krill["topology"]["roa_count"], 1000)
        self.assertTrue(self.krill["scaled_composite_success"])
        self.assertTrue(self.krill["rollback_success"])
        self.assertTrue(self.krill["validation"]["original_success"])
        reliability = self.krill["one_roa_composite_reliability"]
        self.assertEqual(reliability, {"attempts": 10, "passed": 10, "failed": 0})

    def test_public_results_have_no_paths_or_raw_material(self) -> None:
        text = json.dumps({"cache": self.cache, "krill": self.krill})
        self.assertNotIn("/" + "home" + "/", text)
        self.assertNotIn("/" + "Users" + "/", text)
        self.assertFalse(self.krill["contains_private_keys"])
        self.assertFalse(self.krill["contains_raw_objects"])


if __name__ == "__main__":
    unittest.main()
