import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


class DraftSubmissionTest(unittest.TestCase):
    def test_bcp14_reference_group_is_complete(self):
        root_dir = Path(__file__).resolve().parents[1]
        root = ET.parse(
            root_dir / "ietf/submission/draft-yoshikawa-sidrops-pqc-rpki-00.xml"
        ).getroot()
        self.assertIsNotNone(root.find('.//xref[@target="BCP14"]'))
        group = root.find('.//referencegroup[@anchor="BCP14"]')
        self.assertIsNotNone(group)
        self.assertEqual(
            [reference.get("anchor") for reference in group.findall("reference")],
            ["RFC2119", "RFC8174"],
        )


if __name__ == "__main__":
    unittest.main()
