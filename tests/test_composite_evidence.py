from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CompositeEvidenceTests(unittest.TestCase):
    def test_public_claims_match_machine_evidence(self) -> None:
        path = ROOT / "tools" / "check_composite_evidence.py"
        spec = importlib.util.spec_from_file_location("check_composite_evidence", path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.find_inconsistencies(), [])


if __name__ == "__main__":
    unittest.main()
