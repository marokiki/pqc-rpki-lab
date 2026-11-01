"""Run: python3 -m unittest discover -s results/global-rpki-q3-2026 -p 'test_*.py'."""
import base64,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('global_evaluate',HERE/'evaluate.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
class GlobalProjectionTest(unittest.TestCase):
 def fixture(self,kind):return (HERE/'measurements/rsa'/kind).read_bytes()
 def test_trust_anchor_cache_paths_are_not_publication_uris(self):
  self.assertEqual(m.snapshot_uri('rpki-date/data/ta/arin/root.cer'),'ta/arin/root.cer')
  self.assertEqual(m.snapshot_uri('rpki-date/data/rpki.example/repository/a.cer'),'rsync://rpki.example/repository/a.cer')
 def test_rsa_identity_preserves_every_byte(self):
  for file in ('ca.cer','ca.crl','route.roa','manifest.mft'):
   data=self.fixture(file);self.assertEqual(m.projected(data,m.classify(file),'rsa'),data)
 def test_projected_cert_and_crl_match_measured_pure_pq_sizes(self):
  for suite in ('ml-dsa-44','ml-dsa-65'):
   for file in ('ca.cer','ca.crl','route.roa','manifest.mft'):
    actual=(HERE/'measurements'/suite/file).read_bytes()
    estimate=m.projected(self.fixture(file),m.classify(file),suite)
    self.assertEqual(len(actual),len(estimate),(suite,file))
 def test_complete_cms_embeds_exactly_one_ee_certificate(self):
  raw=self.fixture('route.roa')
  for suite in m.SUITES:
   projected=m.project_cms(raw,suite);ci,sd,idx,si,ec=m.cms_parts(projected)
   self.assertEqual(len(sd[idx].children()),1)
   self.assertEqual(ec,m.cms_parts(raw)[-1])
   self.assertEqual(len(si[5].value),m.SUITES[suite].signature_bytes)
 def test_manifest_filelist_is_preserved_without_padding(self):
  raw=self.fixture('manifest.mft')
  for suite in m.SUITES:self.assertEqual(m.cms_parts(m.project_cms(raw,suite))[-1],m.cms_parts(raw)[-1])
 def test_mixed_boundary_keeps_rsa_issuer_signature(self):
  raw=self.fixture('ca.cer');projected=m.project_certificate(raw,'ml-dsa-65','rsa')
  old=m.node(raw).children();new=m.node(projected).children()
  self.assertEqual(old[1].encoded,new[1].encoded);self.assertEqual(old[2].encoded,new[2].encoded)
  self.assertNotEqual(m.certificate_info(raw)['subject_key_oid'],m.certificate_info(projected)['subject_key_oid'])
 def test_bgpsec_subject_is_not_migrated(self):
  n=m.node(self.fixture('ca.cer'));root=n.children();t=root[0].children();parts=[x.encoded for x in t]
  ec= m.der.sequence(m.der.sequence(m.der.object_identifier('1.2.840.10045.2.1'),m.der.object_identifier('1.2.840.10045.3.1.7')),m.der.bit_string(bytes(65)))
  parts[6]=ec;data=m.der.sequence(m.rebuild(root[0],parts),root[1].encoded,root[2].encoded)
  result=m.project_certificate(data,'ml-dsa-44','ml-dsa-44')
  self.assertEqual(m.node(result).children()[0].children()[6].encoded,ec)
 def test_rrdp_counts_repeated_publication_replacement_and_withdrawal(self):
  data=self.fixture('route.roa');b64=base64.b64encode(data).decode()
  xml=('<delta xmlns="http://www.ripe.net/rpki/rrdp" version="1" session_id="s" serial="2">'
   f'<publish uri="rsync://x/a.roa">{b64}</publish>'
   f'<publish uri="rsync://x/a.roa" hash="'+ '0'*64+f'">{b64}</publish>'
   '<withdraw uri="rsync://x/old.roa" hash="'+'1'*64+'"/></delta>').encode()
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'delta.xml';p.write_bytes(xml);out=Path(td)/'out.json';m.analyze_rrdp([p,p],out)
   result=json.loads(out.read_text());row=result['documents'][0]
   self.assertEqual(len(result['documents']),1);self.assertEqual(row['publish_counts']['roa'],2)
   self.assertEqual(row['withdraw_count'],1);self.assertEqual(row['replacement_publish_count'],1)
   self.assertEqual(row['projected_xml_bytes']['rsa'],len(xml))
   new_size=len(m.project_cms(data,'ml-dsa-44'))
   self.assertEqual(row['projected_xml_bytes']['ml-dsa-44'],len(xml)+2*(4*((new_size+2)//3)-len(b64)))
 def test_bad_rrdp_does_not_create_successful_projection(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'bad.xml';p.write_text('<delta>');out=Path(td)/'out.json';m.analyze_rrdp([p],out)
   result=json.loads(out.read_text());self.assertEqual(result['status'],'incomplete');self.assertTrue(result['errors'])
 def test_snapshot_preserves_framing_and_counts_complete_embedded_objects(self):
  data=self.fixture('manifest.mft');b64=base64.b64encode(data).decode()
  xml=('<snapshot xmlns="http://www.ripe.net/rpki/rrdp" version="1" session_id="s" serial="12">\n'
       f'<publish uri="rsync://example/a.mft">\n{b64}\n</publish>\n</snapshot>').encode()
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'snapshot.xml';p.write_bytes(xml);out=Path(td)/'out.json';m.analyze_rrdp([p],out)
   result=json.loads(out.read_text());row=result['documents'][0]
   self.assertEqual((row['kind'],row['session_id'],row['serial']),('snapshot','s',12))
   self.assertEqual(row['published_der_bytes'],len(data))
   self.assertEqual(result['projections']['snapshot_rsa'],len(xml))
   self.assertEqual(row['projected_xml_bytes']['ml-dsa-65'],len(xml)+4*((len(m.projected(data,'mft','ml-dsa-65'))+2)//3)-len(b64))
 def test_invalid_snapshot_updates_and_duplicate_uris_are_rejected(self):
  b64=base64.b64encode(self.fixture('ca.cer')).decode()
  publish=f'<publish uri="rsync://example/a.cer">{b64}</publish>'
  for body in ('<withdraw uri="rsync://example/a.cer" hash="'+'0'*64+'"/>',
               publish+publish,publish.replace('<publish ','<publish hash="'+'0'*64+'" ')):
   with self.subTest(body=body[:80]),tempfile.TemporaryDirectory() as td:
    p=Path(td)/'snapshot.xml';p.write_text('<snapshot xmlns="http://www.ripe.net/rpki/rrdp" version="1" session_id="s" serial="1">'+body+'</snapshot>')
    out=Path(td)/'out.json';m.analyze_rrdp([p],out)
    result=json.loads(out.read_text());self.assertEqual(result['status'],'incomplete');self.assertFalse(result['documents'])
 def test_text_tal_is_counted_on_wire_and_explicitly_outside_der_projection(self):
  data=b'rsync://example/root.cer\n\nPUBLIC-KEY-TEXT\n';b64=base64.b64encode(data).decode()
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'snapshot.xml';p.write_text('<snapshot xmlns="http://www.ripe.net/rpki/rrdp" version="1" session_id="s" serial="1">'+f'<publish uri="rsync://example/root.tal">{b64}</publish></snapshot>')
   out=Path(td)/'out.json';m.analyze_rrdp([p],out);result=json.loads(out.read_text());row=result['documents'][0]
   self.assertFalse(result['errors']);self.assertEqual(row['published_der_bytes'],0)
   self.assertEqual(row['unmodeled_payloads'][0]['bytes'],len(data))
   self.assertEqual(row['publish_counts'],{'tal':1})
   self.assertEqual(set(row['projected_xml_bytes'].values()),{p.stat().st_size})
 def test_empty_rrdp_is_unavailable_not_a_zero_estimate(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'out.json';m.analyze_rrdp([],out)
   result=json.loads(out.read_text());self.assertEqual(result['status'],'unavailable');self.assertEqual(result['projections'],{})
 def test_composite_measured_signatures_fit_encoded_upper_bound(self):
  root=HERE/'measurements/composite-mldsa65-p256'
  for name in ('ca.cer','route.ee.cer','manifest.ee.cer'):
   self.assertLessEqual(m.certificate_info((root/name).read_bytes())['signature_bytes'],m.SUITES['composite-mldsa65-p256'].signature_bytes)
  for name in ('route.roa','manifest.mft'):
   self.assertLessEqual(len(m.cms_parts((root/name).read_bytes())[3][5].value),m.SUITES['composite-mldsa65-p256'].signature_bytes)
 def test_der_boundary_lengths_reencoded(self):
  for n in (127,128,255,256,65535,65536):
   value=m.der.octet_string(bytes(n));self.assertEqual(len(m.node(value).value),n)
if __name__=='__main__':unittest.main()
