from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_tool():
    path = ROOT / "tools" / "krill_scale_campaign.py"
    spec = importlib.util.spec_from_file_location("krill_scale_campaign", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class KrillScaleCampaignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tool = load_tool()

    def test_schedule_parser(self) -> None:
        self.assertEqual(
            self.tool.parse_counts("1:30,10:20,1000:10"),
            [(1, 30), (10, 20), (1000, 10)],
        )

    def test_statistics_include_required_fields(self) -> None:
        result = self.tool.time_summary(
            [
                {
                    "wall_seconds": 1.0,
                    "user_seconds": 0.5,
                    "system_seconds": 0.1,
                    "max_rss_kib": 100,
                },
                {
                    "wall_seconds": 3.0,
                    "user_seconds": 1.5,
                    "system_seconds": 0.3,
                    "max_rss_kib": 200,
                },
            ]
        )
        for field in (
            "wall_seconds",
            "user_seconds",
            "system_seconds",
            "max_rss_kib",
        ):
            self.assertEqual(result[field]["samples"], 2)
            self.assertIn("median", result[field])
            self.assertIn("stdev", result[field])
            self.assertIn("min", result[field])
            self.assertIn("max", result[field])


if __name__ == "__main__":
    unittest.main()
