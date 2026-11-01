"""Check that submission conversion preserves the finalized Markdown source."""
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from tools import render_draft_submission as renderer

ROOT = Path(__file__).resolve().parents[1]


class Draft03SubmissionTest(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / 'ietf/draft-yoshikawa-sidrops-pqc-rpki.md').read_text()
        self.xml = ET.parse(ROOT / 'ietf/submission/draft-yoshikawa-sidrops-pqc-rpki-03.xml').getroot()

    def test_source_and_generated_xml_are_in_sync(self):
        old_name = renderer.DOCNAME
        try:
            renderer.DOCNAME = 'draft-yoshikawa-sidrops-pqc-rpki-03'
            rebuilt = renderer.build_xml(*renderer.split_source(self.source))
            ET.indent(rebuilt)
            self.assertEqual(ET.tostring(rebuilt), ET.tostring(self.xml))
        finally:
            renderer.DOCNAME = old_name

    def test_bibliography_and_citations_are_complete_and_pinned(self):
        references = {r.get('anchor'): r for r in self.xml.findall('.//reference')}
        keys = re.findall(r'^\[([^]]+)\]', self.source.split('# References', 1)[1], re.M)
        self.assertEqual(set(references), set(keys))
        self.assertEqual(len(references), len(keys))
        self.assertEqual({x.get('target') for x in self.xml.findall('.//xref')} - set(keys), set())
        self.assertNotIn('RFC9842', references)
        for key in keys:
            if key.startswith('I-D.'):
                source_entry = next(l for l in self.source.splitlines() if l.startswith(f'[{key}]'))
                revision = re.search(r'draft-[a-z0-9-]+-\d{2}', source_entry).group()
                self.assertEqual(references[key].find('seriesInfo').get('value'), revision)
        self.assertEqual(references['pqc-rpki-lab'].get('target'),
                         'https://github.com/marokiki/pqc-rpki-lab/releases/tag/draft-yoshikawa-sidrops-pqc-rpki-03')
        self.assertEqual(references['LibreSSL-Releases'].find('front/date').attrib,
                         {'day': '22', 'month': 'October', 'year': '2026'})
        self.assertFalse(references['OpenSSL-3.5'].find('front/date').attrib)
        self.assertIsNone(references['pqc-rpki-lab'].find('seriesInfo'))
        composite = references['I-D.ietf-lamps-pq-composite-sigs']
        self.assertGreater(len(composite.findall('front/author')), 1)
        self.assertNotIn('Work in Progress', composite.findtext('refcontent', ''))

    def test_tables_preserve_every_cell(self):
        meta, abstract, middle, back = renderer.split_source(self.source)
        blocks = [b for s in renderer.parse_sections(middle + '\n' + back.split('# References', 1)[0]) for b in s.blocks if isinstance(b, renderer.Table)]
        tables = self.xml.findall('.//table')
        self.assertEqual(len(tables), len(blocks))
        for table, block in zip(tables, blocks):
            self.assertEqual([''.join(x.itertext()) for x in table.findall('./thead/tr/th')], block.headers)
            self.assertEqual([[''.join(x.itertext()) for x in row.findall('td')] for row in table.findall('./tbody/tr')], block.rows)

    def test_section_order_authors_and_date(self):
        _, _, middle, back = renderer.split_source(self.source)
        expected = [s.title for s in renderer.parse_sections(middle) + renderer.parse_sections(back.split('# References', 1)[0])]
        actual = [s.findtext('name') for s in self.xml.findall('.//section')]
        self.assertEqual(actual, expected)
        self.assertEqual(self.xml.get('docName'), 'draft-yoshikawa-sidrops-pqc-rpki-03')
        self.assertEqual(self.xml.get('category'), 'info')
        self.assertEqual(self.xml.find('front/date').attrib, {'year': '2026', 'month': 'November', 'day': '1'})
        self.assertEqual(len(self.xml.findall('front/author')), 2)


if __name__ == '__main__':
    unittest.main()
