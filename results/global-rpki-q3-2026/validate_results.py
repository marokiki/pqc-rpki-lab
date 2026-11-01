#!/usr/bin/env python3
"""Audit published results and run offline model regression tests."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from fetch_rrdp_snapshots import notification
HERE=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=HERE);a=p.parse_args();r=a.directory;checks=[]
 def read(name):return json.loads((r/name).read_text())
 def check(name,condition):
  checks.append({'check':name,'passed':bool(condition)})
  if not condition:raise AssertionError(name)
 snap=read('snapshot-summary.json');headers=read('archive-header-calibration.json')
 check('independent archive header object counts and DER bytes',headers['object_count']==snap['object_count'] and headers['object_bytes']==snap['object_bytes'] and not headers['nonregular_object_members'])
 check('all snapshot object types parsed',not snap['parse_errors'] and not snap['skipped_nonobject_members'])
 check('type counts and bytes reconcile',sum(x['count'] for x in snap['object_sizes'].values())==snap['object_count'] and sum(x['bytes'] for x in snap['object_sizes'].values())==snap['object_bytes'])
 check('RSA source identity',snap['projections']['rsa']['full_replacement_bytes']==snap['object_bytes'])
 check('five TA cache paths separated from publication URIs',snap['by_location']['_trust_anchors']['count']==len(headers['trust_anchor_cache_members'])==5)
 for suite,projection in snap['projections'].items():
  check('parallel footprint reconciles: '+suite,projection['status']=='estimated' and projection['idealized_parallel_publication_bytes']==snap['object_bytes']+projection['full_replacement_bytes'])
 rr=read('rrdp-summary.json');selection=read('trace-selection.json');docs={x['path']:x for x in rr['documents']}
 check('all observed delta intervals available',not selection['errors'] and all(x.get('complete_interval') for x in selection['coverage']))
 check('all selected delta files parsed once',not rr['errors'] and len(docs)==len(selection['files']) and rr['status']=='estimated')
 for source in selection['files']:
  row=docs[source['relative_path']]
  if not(row['sha256']==source['sha256_from_filename'] and row['serial']==source['serial'] and row['session_id']==source['relative_path'].split('/')[-2] and row['original_xml_bytes']==source['bytes']):raise AssertionError(source['relative_path'])
 check('individual RRDP hashes, serials, sessions, and sizes',True)
 check('RRDP baseline reconciles to selected source bytes',sum(x['original_xml_bytes'] for x in docs.values())==selection['bytes']==rr['totals']['delta_xml_bytes']==rr['projections']['delta_rsa'])
 for suite,total in rr['projections'].items():check('delta projection sum: '+suite,total==sum(x['projected_xml_bytes'][suite.removeprefix('delta_')] for x in docs.values()))
 if (r/'rrdp-snapshot-summary.json').exists():
  ss=read('rrdp-snapshot-summary.json');sm=read('rrdp-snapshot-selection.json')
  verified=[x for x in sm['endpoints'] if x['status']=='verified'];sd={x['path']:x for x in ss['documents']}
  check('all selected live snapshot endpoints acquired',len(verified)==len(sm['endpoints']))
  check('live snapshot cohort uses the pinned September endpoint-selection log',sm['selection_log_sha256']==selection['log_sha256'])
  check('all snapshot bodies parsed once',not ss['errors'] and len(sd)==len({x['snapshot_path'] for x in verified})==ss['totals']['snapshot_documents'])
  for source in verified:
   n=r/'sources/rrdp-snapshot-notifications'/Path(source['notification_path']).name
   nr=source['notification_response'];sr=source['snapshot_response'];ref=notification(n.read_bytes())
   row=sd[source['snapshot_path'].removeprefix('xml/')]
   check('notification and snapshot pin: '+source['notification_uri'],
    hashlib.sha256(n.read_bytes()).hexdigest()==nr['sha256'] and n.stat().st_size==nr['bytes'] and
    ref['snapshot_sha256']==row['sha256']==source['snapshot_sha256']==sr['sha256'] and
    ref['snapshot_uri']==source['snapshot_uri'] and
    ref['session_id']==row['session_id']==source['session_id'] and
    ref['serial']==row['serial']==source['serial'] and row['kind']=='snapshot' and
    row['withdraw_count']==row['replacement_publish_count']==0 and
    row['original_xml_bytes']==sr['bytes'] and sr['http_status']==200 and
    (not sr['response_headers'].get('Content-Encoding') or sr['response_headers']['Content-Encoding'].lower()=='identity') and
    (not sr['response_headers'].get('Content-Length') or int(sr['response_headers']['Content-Length'])==sr['bytes']))
  check('snapshot RSA XML bytes exactly reproduce captured responses',
   sum(x['original_xml_bytes'] for x in sd.values())==sm['snapshot_xml_bytes']==ss['totals']['snapshot_xml_bytes']==ss['projections']['snapshot_rsa'])
  for suite,total in ss['projections'].items():check('snapshot projection sum: '+suite,total==sum(x['projected_xml_bytes'][suite.removeprefix('snapshot_')] for x in sd.values()))
  if (r/'rrdp-snapshot-replay-verification.json').exists():
   replay=read('rrdp-snapshot-replay-verification.json')
   check('complete raw snapshot replay reproduces every document result',
    replay['status']=='passed' and replay['documents']==len(sd) and
    replay['expected_summary_sha256']==hashlib.sha256((r/'rrdp-snapshot-summary.json').read_bytes()).hexdigest() and
    replay['verified_body_sha256']==sorted(x['sha256'] for x in sd.values()))
 for x in read('object-measurements.json')['results']:
  path=r/'measurements'/x['public_path'].split('measurements/',1)[-1]
  if x['status']!='confirmed' or hashlib.sha256(path.read_bytes()).hexdigest()!=x['sha256']:raise AssertionError(x)
 check('all measured public fixture statuses and SHA-256 values',True)
 verification=read('measurement-verification.json')
 check('all certificate, CRL and CMS backend checks',all(x['status']=='verified' for x in verification['checks']))
 manifest=read('source-manifest.json')
 for name,item in manifest['local_files'].items():
  if hashlib.sha256((r/name).read_bytes()).hexdigest()!=item['sha256']:raise AssertionError(name)
 check('pinned source file hashes',True)
 for name,digest in manifest['derived_result_hashes'].items():
  if hashlib.sha256((r/name).read_bytes()).hexdigest()!=digest:raise AssertionError(name)
 check('derived result hashes match provenance',True)
 for name,digest in manifest['analysis_scripts'].items():
  if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=digest:raise AssertionError(name)
 check('analysis script hashes match provenance',True)
 run=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(HERE),'-p','test_*.py'],capture_output=True,text=True)
 check('offline model unit tests',run.returncode==0)
 result={'status':'passed','data_checks':checks,'backend_checks':len(verification['checks']),'unit_test_result':run.stderr.strip(),'internet_draft_check':'analysis scripts do not write draft files; working-tree preservation checked separately','quarter_wide_rrdp_projection':'unavailable; not manufactured'}
 (r/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
 print(f"PASS: {len(checks)} data/model checks and {len(verification['checks'])} backend verification checks")
if __name__=='__main__':main()
