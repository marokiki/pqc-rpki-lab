#!/usr/bin/env python3
"""Fetch pinned public inputs. No implicit network access in analysis/tests."""
import argparse,hashlib,json,urllib.request
from pathlib import Path
FILES={
 'Global_RPKI_Report_2026_Q3.pdf':('https://bsd.nl/publications/Global_RPKI_Report_2026_Q3.pdf','5938005de892b3b7b060d4035531971b3be02e4c334fd72780d4e4d67a9612f4'),
 'Global_RPKI_Report_2026_Q3-zenodo.pdf':('https://zenodo.org/api/records/23512896/files/Global_RPKI_Report_2026_Q3.pdf/content','a8e45c629405e07bbea237bf06a74b6904eb794d77484760d93197d8687ebad6'),
 'rpki-20260930T234958Z.tgz':('https://dango.attn.jp/rpkidata/2026/09/30/rpki-20260930T234958Z.tgz','68dee009a74835cb2e0dae138a5764f9bb32f8552461e4a07ab2bd47c8fb0322'),
}
def main():
 p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,required=True);p.add_argument('--snapshot',action='store_true');p.add_argument('--network',action='store_true',required=True);a=p.parse_args();a.directory.mkdir(parents=True,exist_ok=True)
 for name,(url,expected) in FILES.items():
  if name.endswith('.tgz') and not a.snapshot:continue
  dest=a.directory/name
  if not dest.exists():
   temp=dest.with_suffix(dest.suffix+'.part')
   with urllib.request.urlopen(url,timeout=60) as r,temp.open('wb') as f:
    for chunk in iter(lambda:r.read(1024*1024),b''):f.write(chunk)
   temp.rename(dest)
  h=hashlib.sha256()
  with dest.open('rb') as f:
   for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
  if h.hexdigest()!=expected:raise SystemExit('Source changed / hash mismatch: '+str(dest))
  print(name,h.hexdigest())
if __name__=='__main__':main()
