import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


class DraftSubmissionTest(unittest.TestCase):
    def setUp(self):
        root_dir = Path(__file__).resolve().parents[1]
        self.root = ET.parse(
            root_dir / "ietf/submission/draft-yoshikawa-sidrops-pqc-rpki-00.xml"
        ).getroot()

    def test_bcp14_reference_group_is_complete(self):
        self.assertIsNotNone(self.root.find('.//xref[@target="BCP14"]'))
        group = self.root.find('.//referencegroup[@anchor="BCP14"]')
        self.assertIsNotNone(group)
        self.assertEqual(
            [reference.get("anchor") for reference in group.findall("reference")],
            ["RFC2119", "RFC8174"],
        )

    def test_wrapped_lists_remain_single_lists(self):
        expected = {
            "design-goals": ("ul", 7),
            "migration-strategy": ("ol", 6),
            "implementation-status": ("ul", 10),
            "open-issues": ("ul", 11),
        }
        for anchor, (tag, count) in expected.items():
            section = self.root.find(f'.//section[@anchor="{anchor}"]')
            self.assertIsNotNone(section)
            lists = section.findall(tag)
            self.assertEqual(len(lists), 1, anchor)
            self.assertEqual(len(lists[0].findall("li")), count, anchor)


if __name__ == "__main__":
    unittest.main()
