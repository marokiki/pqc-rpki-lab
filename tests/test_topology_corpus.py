from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_tool():
    path = ROOT / "tools" / "topology_corpus.py"
    spec = importlib.util.spec_from_file_location("topology_corpus", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TopologyCorpusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tool = load_tool()

    def test_children_get_distinct_publication_points_and_resources(self) -> None:
        self.assertEqual(
            self.tool.child_values(0),
            ("child-00000", 64496, "10.0.0.0/24"),
        )
        self.assertEqual(
            self.tool.child_values(257),
            ("child-00257", 64753, "10.1.1.0/24"),
        )

    def test_child_config_has_child_specific_uris(self) -> None:
        config = self.tool.config_for(
            Path("/tmp/ca"),
            Path("/tmp/ca.pem"),
            Path("/tmp/ca.key"),
            child_name="child-00042",
            asn=64538,
            prefix="10.0.42.0/24",
        )
        self.assertIn(
            "rsync://example.invalid/repository/child-00042/child.mft",
            config,
        )
        self.assertIn(
            "rsync://example.invalid/repository/child-00042.cer",
            config,
        )
        self.assertIn("IPv4=10.0.42.0/24", config)
        self.assertIn("AS.0=64538", config)
        self.assertNotIn("repository/child/", config)

    def test_parent_config_covers_the_child_asn_range(self) -> None:
        config = self.tool.config_for(
            Path("/tmp/ca"),
            Path("/tmp/ca.pem"),
            Path("/tmp/ca.key"),
            asn="64496-64595",
            prefix="10.0.0.0/8",
        )
        self.assertIn("AS.0=64496-64595", config)


if __name__ == "__main__":
    unittest.main()
