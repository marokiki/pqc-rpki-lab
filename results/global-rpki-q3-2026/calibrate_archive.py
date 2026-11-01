#!/usr/bin/env python3
"""Independent baseline count/bytes from tar headers, without a DER parser."""
import argparse,collections,json,tarfile
from pathlib import Path

def calibrate(path):
 counts=collections.Counter();sizes=collections.Counter();links=[];ta=[]
 with tarfile.open(path,'r|gz') as archive:
  for item in archive:
   if '/data/' not in item.name:continue
   ext=Path(item.name).suffix
   if ext not in {'.cer','.crl','.mft','.roa','.asa','.gbr','.rsc','.tak','.spl'}:continue
   if item.isfile():counts[ext]+=1;sizes[ext]+=item.size
   else:links.append({'name':item.name,'type':item.type.decode(),'linkname':item.linkname})
   if '/data/ta/' in item.name:ta.append({'name':item.name,'bytes':item.size})
 return {'method':'independent tar-header count and byte sum, without DER parsing','counts':dict(counts),'bytes_by_type':dict(sizes),'object_count':sum(counts.values()),'object_bytes':sum(sizes.values()),'nonregular_object_members':links,'trust_anchor_cache_members':ta}
def main():
 p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=calibrate(a.archive);a.out.write_text(json.dumps(r,indent=2)+'\n')
 if r['nonregular_object_members']:raise SystemExit('Nonregular object members require explicit accounting')
if __name__=='__main__':main()
