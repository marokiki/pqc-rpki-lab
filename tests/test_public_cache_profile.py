from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.profile_public_cache import profile


class PublicCacheProfileTests(unittest.TestCase):
    def test_profile_contains_only_aggregate_resigning_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            point = cache / "stored/rrdp/example/session/rsync/repo/ca"
            point.mkdir(parents=True)
            (point / "a.cer").write_bytes(b"a" * 10)
            (point / "a.roa").write_bytes(b"b" * 20)
            (point / "a.mft").write_bytes(b"c" * 30)
            result = profile(cache, "test snapshot")
        self.assertEqual(result["object_count"], 3)
        self.assertEqual(result["publication_points"]["count"], 1)
        self.assertFalse(
            result["synthetic_corpus"]["contains_source_objects"]
        )
        self.assertNotIn(tmp, str(result))


if __name__ == "__main__":
    unittest.main()
