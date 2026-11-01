"""Fail-closed checks at the notification/snapshot trust boundary."""
import tempfile
import unittest
from pathlib import Path
import fetch_rrdp_snapshots as m

class SnapshotFetchTest(unittest.TestCase):
 def notification(self, elements):
  return ('<notification xmlns="'+m.NS+'" version="1" session_id="s" serial="123">'+elements+'</notification>').encode()
 def test_one_https_hashed_reference_required(self):
  item='<snapshot uri="https://example/s.xml" hash="'+'a'*64+'"/>'
  self.assertEqual(m.notification(self.notification(item))['serial'],123)
  for body in ('',item+item,item.replace('https:','http:'),item.replace('a'*64,'bad')):
   with self.subTest(body=body),self.assertRaises(ValueError):m.notification(self.notification(body))
 def test_snapshot_session_and_serial_must_match_notification(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'s.xml';p.write_text('<snapshot xmlns="'+m.NS+'" version="1" session_id="s" serial="123"/>')
   m.check_snapshot(p,{'session_id':'s','serial':123})
   for expected in ({'session_id':'other','serial':123},{'session_id':'s','serial':124}):
    with self.assertRaises(ValueError):m.check_snapshot(p,expected)

if __name__=='__main__':unittest.main()
