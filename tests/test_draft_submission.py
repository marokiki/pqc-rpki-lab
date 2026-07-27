import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


class DraftSubmissionTest(unittest.TestCase):
    def setUp(self):
        root_dir = Path(__file__).resolve().parents[1]
        self.root = ET.parse(
            root_dir / "ietf/submission/draft-yoshikawa-sidrops-pqc-rpki-00.xml"
        ).getroot()
        self.root_01 = ET.parse(
            root_dir / "ietf/submission/draft-yoshikawa-sidrops-pqc-rpki-01.xml"
        ).getroot()
        self.root_02 = ET.parse(
            root_dir / "ietf/submission/draft-yoshikawa-sidrops-pqc-rpki-02.xml"
        ).getroot()

    def test_draft_02_is_informational_experiment_report(self):
        self.assertEqual(
            self.root_02.get("docName"),
            "draft-yoshikawa-sidrops-pqc-rpki-02",
        )
        self.assertEqual(self.root_02.get("category"), "info")
        self.assertEqual(self.root_02.get("consensus"), "false")
        self.assertIsNone(self.root_02.find('.//xref[@target="BCP14"]'))
        aspa = self.root_02.find(
            './/reference[@anchor="I-D.ietf-sidrops-aspa-profile"]'
        )
        self.assertEqual(
            aspa.find("./seriesInfo").get("value"),
            "draft-ietf-sidrops-aspa-profile-28",
        )
        text = " ".join(self.root_02.itertext())
        self.assertIn("This document is informational.", text)
        self.assertIn("It does not update RFC 7935 or RFC 6916", text)
        self.assertIn("Draft-19 Composite ML-DSA Measurements", text)
        self.assertNotIn("MUST", text)
        self.assertNotIn("SHOULD", text)

    def test_draft_02_references_immutable_evidence_snapshot(self):
        self.assertEqual(
            self.root_02.find('.//reference[@anchor="pqc-rpki-lab"]').get("target"),
            "https://github.com/marokiki/pqc-rpki-lab/tree/"
            "75b745a9c69a7ca0bbe473a786b173c20fde1fd1",
        )

    def test_draft_02_records_review_boundaries(self):
        text = " ".join(self.root_02.itertext())
        self.assertIn(
            "deliberately evaluates the X.509 construction excluded by RFC 6916",
            text,
        )
        self.assertIn("TrustAnchorState is compared separately", text)
        self.assertIn("ROAPayloadState does not preserve per-VRP", text)
        self.assertIn("Composite Configuration Evaluated in This Revision", text)
        self.assertIn("Questions for Further Work", text)
        self.assertIn("EUF-CMA", text)
        self.assertNotIn("unknown algorithm", text)

    def test_draft_01_submission_is_rendered(self):
        self.assertEqual(
            self.root_01.get("docName"),
            "draft-yoshikawa-sidrops-pqc-rpki-01",
        )
        self.assertIsNotNone(self.root_01.find('.//xref[@target="RFC9882"]'))
        self.assertIsNotNone(self.root_01.find('.//xref[@target="RFC9691"]'))
        self.assertIsNotNone(self.root_01.find('.//xref[@target="RFC8183"]'))
        self.assertIsNotNone(self.root_01.find('.//section[@anchor="implementation-status"]'))
        text = " ".join(self.root_01.itertext())
        self.assertIn("id-MLDSA65-ECDSA-P256-SHA512", text)
        self.assertIn("composite plus mixed-tree migration design", text)
        self.assertEqual(
            self.root_01.findtext("./front/author/address/email"),
            "yoshikawa.tomoki.67i@st.kyoto-u.ac.jp",
        )
        self.assertEqual(
            self.root_01.find('.//reference[@anchor="pqc-rpki-lab"]').get("target"),
            "https://github.com/marokiki/pqc-rpki-lab/releases/tag/"
            "draft-yoshikawa-sidrops-pqc-rpki-01",
        )

    def test_draft_01_tables_and_acknowledgements_render_as_rfcxml(self):
        tables = self.root_01.findall(".//table")
        self.assertEqual(len(tables), 4)
        self.assertEqual(
            [cell.text for cell in tables[0].findall("./thead/tr/th")],
            ["Algorithm", "Cat.", "PubKey (B)", "Sig (B)"],
        )
        self.assertEqual(len(tables[3].findall("./tbody/tr")), 17)
        acknowledgements = self.root_01.find('.//section[@anchor="acknowledgements"]')
        self.assertEqual(acknowledgements.get("numbered"), "false")
        acknowledgement_text = " ".join(acknowledgements.itertext())
        for reviewer in (
            "Job Snijders",
            "Dirk Doesburg",
            "Loganaden Velvindron",
            "Ties de Kock",
        ):
            self.assertIn(reviewer, acknowledgement_text)

    def test_draft_01_records_reviewer_driven_operational_issues(self):
        text = " ".join(self.root_01.itertext())
        self.assertIn("issuer and publication-scope consistency", text)
        self.assertIn("BPKI trust-anchor key rollover", text)
        self.assertIn("general-purpose CPU implementation", text)

    def test_rfc8209_is_normative(self):
        reference_sections = self.root_01.findall("./back/references")
        normative = next(
            section
            for section in reference_sections
            if section.findtext("name") == "Normative References"
        )
        informative = next(
            section
            for section in reference_sections
            if section.findtext("name") == "Informative References"
        )
        self.assertIsNotNone(normative.find('./reference[@anchor="RFC8209"]'))
        self.assertIsNone(informative.find('./reference[@anchor="RFC8209"]'))

    def test_draft_01_distinguishes_issuer_signature_from_subject_spki(self):
        text = " ".join(self.root_01.itertext())
        self.assertIn(
            "A transition certificate signed by a Current Suite issuer",
            text,
        )
        self.assertIn(
            "MUST NOT infer the subject SPKI algorithm",
            text,
        )
        self.assertNotIn("verification cost grows by roughly", text)

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
