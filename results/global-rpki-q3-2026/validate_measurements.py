#!/usr/bin/env python3
"""Verify lab certificate chains, CRL signatures, and CMS using the existing backend."""
import argparse,json,subprocess,tempfile
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--openssl',required=True);p.add_argument('--fixtures',type=Path,required=True);p.add_argument('--nested-generator-layout',action='store_true');p.add_argument('--out',type=Path,required=True);a=p.parse_args();rows=[]
 for suite in ('rsa','ml-dsa-44','ml-dsa-65','composite-mldsa65-p256'):
  source=a.fixtures/suite
  if a.nested_generator_layout:source=source/'testdata'/suite
  with tempfile.TemporaryDirectory(prefix='global-rpki-public-validation-') as temp:
   work=Path(temp)
   def run(label,args):
    process=subprocess.run([a.openssl,*args],capture_output=True,text=True)
    rows.append({'suite':suite,'check':label,'returncode':process.returncode,'status':'verified' if process.returncode==0 else 'failed','diagnostic':(process.stdout+process.stderr).replace(str(work),'$TMPDIR').replace(str(source),'$PUBLIC_FIXTURES').strip()})
   for name in ('ca','route.ee','manifest.ee'):
    run('decode-'+name,['x509','-inform','DER','-in',str(source/(name+'.cer')),'-out',str(work/(name+'.pem'))])
   run('ca-and-ee-certificate-signatures',['verify','-purpose','any','-CAfile',str(work/'ca.pem'),str(work/'ca.pem'),str(work/'route.ee.pem'),str(work/'manifest.ee.pem')])
   run('crl-signature',['crl','-inform','DER','-in',str(source/'ca.crl'),'-verify','-CAfile',str(work/'ca.pem'),'-noout'])
   for name in ('route.roa','manifest.mft'):
    run('cms-'+name,['cms','-verify','-inform','DER','-in',str(source/name),'-CAfile',str(work/'ca.pem'),'-binary','-out',str(work/'econtent')])
 result={'backend':subprocess.check_output([a.openssl,'version'],text=True).strip(),
  'scope':'cryptographic lab certificate-chain, CRL-signature and CMS checks using one shared backend; not independent RPKI policy/resource/path validation','checks':rows}
 a.out.write_text(json.dumps(result,indent=2)+'\n')
 if any(r['status']=='failed' for r in rows):raise SystemExit('Verification failure recorded')
if __name__=='__main__':main()
