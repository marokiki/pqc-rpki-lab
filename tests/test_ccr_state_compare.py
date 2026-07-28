from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

from pqc_rpki_lab import der

ROOT = Path(__file__).resolve().parents[1]


def load_tool():
    path = ROOT / "tools" / "ccr_state_compare.py"
    spec = importlib.util.spec_from_file_location("ccr_state_compare", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CcrStateCompareTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tool = load_tool()

    def test_extracts_and_verifies_roa_and_ta_state_hashes(self) -> None:
        rps = der.sequence(der.sequence(der.integer(64496), der.sequence()))
        skis = der.sequence(der.octet_string(b"\x01" * 20))
        content = der.sequence(
            der.algorithm_identifier(self.tool.SHA256_OID),
            der.generalized_time("20260728000000Z"),
            der.tlv(
                0xA2,
                der.sequence(rps, der.octet_string(hashlib.sha256(rps).digest())),
            ),
            der.tlv(
                0xA4,
                der.sequence(
                    skis, der.octet_string(hashlib.sha256(skis).digest())
                ),
            ),
        )
        encoded = der.sequence(
            der.object_identifier(self.tool.CCR_OID),
            der.tlv(0xA0, content),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.ccr"
            path.write_bytes(encoded)
            result = self.tool.extract(path)
        self.assertTrue(
            result["states"]["roa_payload_state"]["hash_verified"]
        )
        self.assertTrue(
            result["states"]["trust_anchor_state"]["hash_verified"]
        )
        self.assertEqual(
            result["states"]["roa_payload_state"]["item_count"], 1
        )


if __name__ == "__main__":
    unittest.main()
