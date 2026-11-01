#!/usr/bin/env python3
"""Fetch observed serial intervals for report Table 4 locations, not synthetic churn.

Run on ssh pqc. Requires rsync and the public RPKIViews daily collector log.
Do not use filesystem mtimes as issuance/capture timestamps.
"""
import argparse,collections,datetime,hashlib,json,re,subprocess
from pathlib import Path
from urllib.parse import urlsplit
HOSTS={'rrdp.arin.net','rrdp.ripe.net','rrdp.apnic.net','rpki-repo.registro.br',
 'rrdp.lacnic.net','rpki-rrdp.us-east-2.amazonaws.com','rrdp.afrinic.net',
 'rpki-rrdp.idnic.net','rrdp.paas.rpki.ripe.net','rrdp-rps.cnnic.cn',
 'rpki-repository.nic.ad.jp','rrdp-rps.arin.net','rpkica.twnic.tw','rrdp.twnic.tw'}
PAT=re.compile(r'^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ INFO rrdp_tools.snapshot_rrdp (https?://\S+) serial=(\d+) session_id=([\w-]+)$')
LINE=re.compile(r'^-\S+\s+([\d,]+)\s+(\S+ \S+)\s+(\d+)-([0-9a-f]{64})\.xml$')

def main():
 p=argparse.ArgumentParser();p.add_argument('--log',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--max-bytes',type=int,default=3_000_000_000);p.add_argument('--expected-log-sha256');a=p.parse_args()
 if a.expected_log_sha256 and hashlib.sha256(a.log.read_bytes()).hexdigest()!=a.expected_log_sha256:raise SystemExit('Collector log hash mismatch')
 a.out.mkdir(parents=True,exist_ok=True);groups=collections.defaultdict(list);all_hosts=set()
 for line in a.log.read_text().splitlines():
  m=PAT.match(line)
  if not m:continue
  stamp,url,serial,session=m.groups();host=urlsplit(url).hostname;all_hosts.add(host)
  if host in HOSTS:groups[host,session].append((stamp,int(serial),url))
 selection=[];coverage=[];errors=[]
 base='rsync://rrdp.rpkiviews.org/data/2026/09/'
 for (host,session),observations in sorted(groups.items()):
  observations.sort();first,last=observations[0],observations[-1]
  start,end=first[1],last[1]
  record={'host':host,'session_id':session,'first_observed_log_time':first[0],'last_observed_log_time':last[0],
    'log_timezone':'not explicitly stated in source; timestamps recorded verbatim',
    'serial_start_exclusive':start,'serial_end_inclusive':end,'poll_observations':len(observations)}
  if start==end:
   record.update({'selected_documents':0,'missing_serials':[],'conflicting_serials':[], 'bytes':0,'complete_interval':True})
   coverage.append(record)
   continue
  uri_directory=urlsplit(first[2]).path.rsplit('/',1)[0].strip('/')
  archive_directory='/'.join(x for x in (host,uri_directory,session) if x)
  record['archive_directory']=archive_directory
  command=['rsync','--list-only','--timeout=30',base+archive_directory+'/']
  run=subprocess.run(command,text=True,capture_output=True)
  (a.out/(host+'-'+session+'-index.txt')).write_text(run.stdout)
  if run.returncode:errors.append({'host':host,'error':run.stderr});coverage.append(record);continue
  selected=[]
  for line in run.stdout.splitlines():
   m=LINE.match(line)
   if not m:continue
   size,mtime,serial,sha=m.groups();serial=int(serial)
   if start<serial<=end:
    selected.append({'relative_path':archive_directory+'/'+line.split()[-1],
      'bytes':int(size.replace(',','')),'serial':serial,'sha256_from_filename':sha})
  serials=collections.Counter(x['serial'] for x in selected)
  missing=sorted(set(range(start+1,end+1))-serials.keys())
  conflicts=[n for n,c in serials.items() if c>1]
  record.update({'selected_documents':len(selected),'missing_serials':missing,'conflicting_serials':conflicts,
    'bytes':sum(x['bytes'] for x in selected),'complete_interval':not missing and not conflicts})
  selection.extend(selected);coverage.append(record)
 total=sum(x['bytes'] for x in selection)
 manifest={'source_base':base,'log_sha256':hashlib.sha256(a.log.read_bytes()).hexdigest(),
  'selection':'all archived serials after first and through last observed notification serial on 2026-09-30, for report Table 4 locations; not a quarter projection',
  'all_observed_hosts_in_log':sorted(all_hosts),'selected_hosts':sorted({h for h,s in groups}),
  'coverage':coverage,'errors':errors,'bytes':total,'files':selection}
 (a.out/'trace-selection.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'files':len(selection),'bytes':total,'coverage':coverage,'errors':errors},indent=2),flush=True)
 if not selection or total>a.max_bytes:raise SystemExit('empty selection or explicit byte limit exceeded')
 names=a.out/'files.txt';names.write_text(''.join(x['relative_path']+'\n' for x in selection))
 subprocess.run(['rsync','-a','--timeout=60','--files-from='+str(names),base,str(a.out/'xml')+'/'],check=True)
 for item in selection:
  path=a.out/'xml'/item['relative_path'];raw=path.read_bytes()
  if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256_from_filename']:
   raise SystemExit('archive hash/size mismatch: '+str(path))
 print('TRACE_FILES_HASH_VERIFIED',flush=True)
if __name__=='__main__':main()
