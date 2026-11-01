#!/usr/bin/env python3
"""Inspect real manifest/CRL populations and an explicitly partial XML subtotal."""
import argparse,collections,gzip,json,statistics
from pathlib import Path
from xml.sax.saxutils import quoteattr

def main():
 p=argparse.ArgumentParser();p.add_argument('inventory',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 shapes=collections.Counter();mft=[];revoked=[];subtotals=collections.Counter()
 with gzip.open(a.inventory,'rt') as f:
  for line in f:
   r=json.loads(line)
   if r['type']=='cer':shapes[r.get('subject_key_oid'),r.get('spki_bytes'),r.get('signature_bytes')]+=1
   if 'manifest_entries' in r:mft.append(r['manifest_entries'])
   if 'revoked_entries' in r:revoked.append(r['revoked_entries'])
   if not r['uri'].startswith('rsync://'):continue
   framing=len(('<publish uri='+quoteattr(r['uri'])+'></publish>').encode())
   for suite,size in r.get('sizes',{}).items():subtotals[suite]+=framing+4*((size+2)//3)
 result={'certificate_shapes':[{'subject_key_oid':k[0],'spki_der_bytes':k[1],'signature_bytes':k[2],'count':v} for k,v in shapes.items()],
  'manifest_filelist':{'count':len(mft),'min_entries':min(mft),'max_entries':max(mft),'median_entries':statistics.median(mft),'total_entries':sum(mft)},
  'crl_revoked_entries':{'count':len(revoked),'min':min(revoked),'max':max(revoked),'total':sum(revoked)},
  'hypothetical_rrdp_publish_element_subtotals':dict(subtotals),
  'snapshot_rrdp_note':'Canonical publish element subtotal for the cache paths only; no XML declaration, snapshot wrappers, notifications or session partitioning. Not measured snapshot bytes or transfer traffic.'}
 a.out.write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
