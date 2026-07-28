from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_tool():
    path = ROOT / "tools" / "rp_cache_campaign.py"
    spec = importlib.util.spec_from_file_location("rp_cache_campaign", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RpCacheCampaignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tool = load_tool()

    def test_changed_objects_counts_only_changed_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initial = root / "initial"
            updated = root / "updated"
            initial.mkdir()
            updated.mkdir()
            (initial / "same.roa").write_bytes(b"same")
            (updated / "same.roa").write_bytes(b"same")
            (initial / "changed.mft").write_bytes(b"old")
            (updated / "changed.mft").write_bytes(b"new-data")
            result = self.tool.changed_objects(initial, updated)
        self.assertEqual(result["changed_file_count"], 1)
        self.assertEqual(result["initial_changed_bytes"], 3)
        self.assertEqual(result["updated_changed_bytes"], 8)


if __name__ == "__main__":
    unittest.main()
