from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TopologyResultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.result = json.loads(
            (
                ROOT
                / "results/scaled-corpus/topology-pilot-summary.json"
            ).read_text()
        )

    def test_hundred_publication_points_validate(self) -> None:
        topology = self.result["topology"]
        self.assertEqual(topology["composite_child_ca_count"], 100)
        self.assertEqual(topology["child_publication_point_count"], 100)
        self.assertEqual(topology["roa_count"], 100)
        self.assertEqual(topology["vrp_count"], 100)
        self.assertTrue(self.result["validation"]["success"])

    def test_missing_branch_does_not_remove_sibling_vrps(self) -> None:
        branch = self.result["branch_isolation"]
        self.assertEqual(branch["expected_surviving_vrps"], 99)
        self.assertTrue(branch["validation"]["success"])
        for name, row in branch["validation"]["modes"].items():
            expected = 99 if name.endswith("experimental") else 0
            self.assertEqual(row["vrp_count"], expected)

    def test_public_summary_has_no_raw_or_private_material(self) -> None:
        text = json.dumps(self.result)
        self.assertNotIn("/" + "home" + "/", text)
        self.assertNotIn("/" + "Users" + "/", text)
        self.assertFalse(self.result["contains_private_keys"])
        self.assertFalse(self.result["contains_raw_objects"])


if __name__ == "__main__":
    unittest.main()
