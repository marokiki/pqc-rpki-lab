import json
import tempfile
import unittest
from pathlib import Path

from pqc_rpki_lab.vrp import compare, normalize_vrp


class ResultToolsTest(unittest.TestCase):
    def test_vrp_semantics_ignore_source_provenance(self):
        baseline = {normalize_vrp({"prefix": "192.0.2.0/24", "asn": 64496, "ta": "rsa-ta"})}
        candidate = {normalize_vrp({"prefix": "192.0.2.0/24", "asn": 64496, "ta": "pqc-ta"})}
        result = compare(baseline, candidate)
        self.assertTrue(result["equivalent"])
        self.assertEqual(len(result["provenance_differences"]), 1)

    def test_public_fixture_json_has_no_key_material(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "topology.json"
            path.write_text(json.dumps({"nodes": [], "products": []}))
            text = path.read_text()
        self.assertNotIn("PRIVATE KEY", text)

