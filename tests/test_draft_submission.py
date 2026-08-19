import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


class DraftSubmissionTest(unittest.TestCase):
    def setUp(self):
        root_dir = Path(__file__).resolve().parents[1]
        self.source_02 = (
            root_dir / "ietf/draft-yoshikawa-sidrops-pqc-rpki-02.md"
        ).read_text()
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
            "draft-ietf-sidrops-aspa-profile-29",
        )
        text = " ".join(self.root_02.itertext())
        self.assertIn("This document is informational.", text)
        self.assertIn("It does not update RFC 7935 or RFC 6916", text)
        self.assertIn("Composite ML-DSA Operation Measurements", text)
        self.assertNotIn("MUST", text)
        self.assertNotIn("SHOULD", text)

    def test_draft_02_references_immutable_evidence_snapshot(self):
        self.assertEqual(
            self.root_02.find('.//reference[@anchor="pqc-rpki-lab"]').get("target"),
            "https://github.com/marokiki/pqc-rpki-lab/releases/tag/"
            "draft-yoshikawa-sidrops-pqc-rpki-02",
        )
        self.assertNotIn(
            "bbbc401336b0c917b7bb89a9e8f5b783c81012db", self.source_02
        )

    def test_draft_02_records_both_authors_with_country_codes(self):
        authors = self.root_02.findall("./front/author")
        self.assertEqual(
            [
                (
                    author.get("fullname"),
                    author.get("initials"),
                    author.get("surname"),
                    author.findtext("./organization"),
                    author.findtext("./address/postal/country"),
                    author.findtext("./address/email"),
                )
                for author in authors
            ],
            [
                (
                    "Tomoki Yoshikawa",
                    "T.",
                    "Yoshikawa",
                    "Kyoto University",
                    "JP",
                    "yoshikawa.tomoki.67i@st.kyoto-u.ac.jp",
                ),
                (
                    "Loganaden Velvindron",
                    "L.",
                    "Velvindron",
                    "cyberstorm.mu",
                    "MU",
                    "logan@cyberstorm.mu",
                ),
            ],
        )
        # A co-author is no longer thanked as a reviewer.
        acknowledgements = self.root_02.find(
            './/section[@anchor="acknowledgements"]'
        )
        acknowledgement_text = " ".join(acknowledgements.itertext())
        self.assertNotIn("Loganaden Velvindron", acknowledgement_text)
        self.assertIn("Job Snijders", acknowledgement_text)

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
        self.assertIn("seven cases for repository-operation failures", text)
        self.assertIn("actual rpki-client CCR DER", text)
        self.assertIn("100 Composite child CAs", text)
        self.assertNotIn("unknown algorithm", text)

    def test_draft_02_records_final_review_corrections(self):
        text = " ".join(self.root_02.itertext())
        self.assertIn(
            "not quantum resistant as a complete certification path",
            text,
        )
        self.assertIn(
            "subject public key algorithm remains governed by the BGPsec UPDATE",
            text,
        )
        self.assertIn(
            "Composite certificate requests and proof of possession",
            text,
        )
        self.assertIn("bytes with deterministic gzip", text)
        self.assertIn("Model prediction (B)", text)
        self.assertIn("Generation wall sample stdev (s)", text)
        self.assertNotIn("median plus or minus sample standard deviation", text)
        measurement = self.root_02.find(
            './/section[@anchor="measurement-details"]'
        )
        measurement_text = " ".join(measurement.itertext())
        self.assertNotIn("removed before publication", measurement_text)
        self.assertIn("12-vCPU x86-64 host", measurement_text)
        pqrpki = self.root_02.find('.//reference[@anchor="pqRPKI"]')
        self.assertEqual(
            [author.get("fullname") for author in pqrpki.findall("./front/author")],
            ["Weitong Li", "Yuze Li", "Taejoong Chung"],
        )
        self.assertEqual(pqrpki.find("./seriesInfo").get("value"), "2603.06968")
        nullscheme = self.root_02.find(
            './/reference[@anchor="I-D.doesburg-sidrops-nullscheme"]'
        )
        self.assertIsNotNone(nullscheme)
        self.assertEqual(nullscheme.findtext("./refcontent"), "Expired and archived")
        source_references = self.source_02.split("# References", 1)[1]
        self.assertIn("[I-D.doesburg-sidrops-nullscheme] Doesburg, D.", source_references)
        self.assertIn("expired and archived", source_references)
        erik = self.root_02.find(
            './/reference[@anchor="I-D.ietf-sidrops-rpki-erik-protocol"]'
        )
        self.assertIsNotNone(erik)
        self.assertEqual(
            erik.find("./seriesInfo").get("value"),
            "draft-ietf-sidrops-rpki-erik-protocol-07",
        )
        self.assertIn("Repository Transport Measurements", self.source_02)
        self.assertIn("[RFC9842]", self.source_02)
        self.assertIsNotNone(
            self.root_02.find('.//reference[@anchor="RFC9842"]')
        )
        self.assertIsNotNone(
            self.root_02.find('.//reference[@anchor="RFC9981"]')
        )
        self.assertIn(
            "The choice of signature suite is independent of this comparison",
            text,
        )
        self.assertNotIn("## Composite Signatures", self.source_02)
        self.assertNotIn("## Single-Run 100,000-Operation Measurements", self.source_02)
        self.assertNotIn("security-critical", self.source_02)
        self.assertNotIn("APNIC Erik proof of concept", self.source_02)
        self.assertIn(
            "Next Suite public key carried in that certificate's SPKI",
            text,
        )
        self.assertIn(
            "RP support for a selected suite remains a deployment prerequisite",
            text,
        )
        self.assertIn(
            "measured and modeled results explicitly distinguished",
            text,
        )
        self.assertNotIn("while its subject key is used", self.source_02)
        self.assertNotIn("for its CA certificates", self.source_02)
        self.assertNotIn("Erik proof-of-concept validation", self.source_02)
        self.assertIn("outside the present evaluation", text)
        self.assertIn("per-object-type algorithm diversity", text)
        self.assertIn("cryptographic-object experiments", text)
        self.assertIn("EE subject public-key algorithm", text)
        self.assertNotIn("outside this profile", self.source_02)
        self.assertNotIn("would create little benefit", self.source_02)
        self.assertIn("both deterministic and randomized signing", text)
        self.assertIn("following single-run measurements", text)
        self.assertIn(
            "experimental Composite implementation recorded in the evidence snapshot",
            text,
        )
        self.assertNotIn(
            "2263161f6b058fe0195a98b6fad088c2d4a2595f", self.source_02
        )
        self.assertIn("simplified Erik model required 1,010 requests", text)
        self.assertIn("and updated by [RFC9981]", self.source_02)
        self.assertIn("a 5.54-fold increase", text)
        self.assertIn("does not modify RRDP or rsync", text)
        self.assertIn("component-algorithm combination", text)
        self.assertIn("are confined to isolated repositories", text)
        self.assertIn("Fifteen negative cases", text)
        self.assertIn("separate concerns from the Mixed Tree migration", text)
        source_references = self.source_02.split("# References", 1)[1]
        self.assertLess(
            source_references.index("[RFC9882]"),
            source_references.index("[RFC9981]"),
        )
        self.assertNotIn("randomized (hedged) signing by default", self.source_02)
        self.assertNotIn("FN-DSA verification was fast", self.source_02)
        self.assertNotIn("Matrix wall median", self.source_02)
        self.assertNotIn("model uses 12% RRDP", self.source_02)
        self.assertNotIn("repository distribution is evaluated separately below", self.source_02.lower())
        self.assertNotIn("No production RPKI CA or RP support", self.source_02)
        self.assertNotIn("public evidence snapshot has generated", self.source_02)
        self.assertNotIn("The evidence reference is fixed", self.source_02)

    def test_draft_02_measurement_appendix_is_grouped_by_experiment(self):
        self.assertEqual(self.source_02.count("# Measurement Details"), 1)
        self.assertEqual(self.source_02.count("## Reproducibility Metadata"), 1)
        measurement = self.root_02.find(
            './/section[@anchor="measurement-details"]'
        )
        self.assertIsNotNone(measurement)
        self.assertEqual(
            [name.text for name in measurement.findall("./section/name")],
            [
                "Reproducibility Metadata",
                "Repeated Cryptographic Operation Timing",
                "Composite ML-DSA Operation Measurements",
                "Measured Certificate and CRL Sizes",
                "Synthetic Repository Size Model",
                "Controlled Repository Scale Measurements",
                "Repository Transport Measurements",
                "Open Measurement Tasks",
            ],
        )
        measurement_text = " ".join(measurement.itertext())
        self.assertIn("measured repository experiments below", measurement_text)
        self.assertIn(
            "identified in the Reproducibility Metadata section", measurement_text
        )
        self.assertNotIn("## Small-Scale End-to-End Measurement", self.source_02)
        self.assertNotIn(
            "## Public-Cache Profile and Controlled Scale Measurements",
            self.source_02,
        )

    def test_draft_02_unifies_parallel_publication_terminology(self):
        text = " ".join(self.root_02.itertext())
        self.assertIn("correspond as defined in", text)
        self.assertIn("RFC 6916 Parallel Publication", text)
        self.assertNotIn('This document uses "correspond" as defined', self.source_02)
        self.assertNotIn("RFC 6916 parallel hierarchy", self.source_02)
        self.assertNotIn(
            "An implementation that assumes the two are equal", self.source_02
        )

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
