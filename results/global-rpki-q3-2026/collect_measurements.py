#!/usr/bin/env python3
"""Reuse the existing object generator, retain public fixtures only."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
SUITES=('rsa','ml-dsa-44','ml-dsa-65','composite-mldsa65-p256')
def main():
 p=argparse.ArgumentParser();p.add_argument('--openssl',required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--out',type=Path,default=HERE);a=p.parse_args()
 rows=[]
 for suite in SUITES:
  work=a.work/suite
  subprocess.run([sys.executable,str(ROOT/'tools/generate_rpki_objects.py'),'--algorithm',suite,'--openssl',a.openssl,'--output-root',str(work)],check=True,env={**os.environ,'PYTHONPATH':str(ROOT/'src')})
  report=json.loads((work/'results/rpki-objects/rpki-objects.json').read_text())
  output=a.out/'measurements'/suite;output.mkdir(parents=True,exist_ok=True)
  for row in report['results']:
   source=work/row['public_path'];target=output/source.name
   if source.is_file() and source.suffix in ('.cer','.crl','.roa','.mft','.econtent'):shutil.copy2(source,target)
   relative=target.relative_to(a.out)
   rows.append({**row,'public_path':str(relative),'sha256':hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None})
 result={'backend':subprocess.check_output([a.openssl,'version'],text=True).strip(),
  'generator':'tools/generate_rpki_objects.py','generator_sha256':hashlib.sha256((ROOT/'tools/generate_rpki_objects.py').read_bytes()).hexdigest(),
  'private_keys_persisted':False,'verification':'OpenSSL CMS cryptographic verification with the lab CA; not independent full RPKI profile validation','results':rows}
 a.out.mkdir(parents=True,exist_ok=True);(a.out/'object-measurements.json').write_text(json.dumps(result,indent=2)+'\n')
 if any(x['status']!='confirmed' for x in rows):raise SystemExit('Some object generations/validations failed; inspect recorded statuses.')
if __name__=='__main__':main()
