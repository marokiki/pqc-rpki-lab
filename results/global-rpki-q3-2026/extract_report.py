#!/usr/bin/env python3
"""Extract report tables from pinned PDFs using pdftotext -layout (no OCR guesses)."""
import argparse,csv,datetime,hashlib,json,re,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
LOCATIONS=['arin.net','ripe.net','apnic.net','registro.br','lacnic.net','amazonaws.com',
 'afrinic.net','idnic.net','paas.ripe.net','rps.cnnic.cn','nic.ad.jp','fiti.net.cn','rps.arin.net','twnic.tw']
DESCRIPTIONS={
 1:('instantaneous_cache_objects','count; k abbreviation retained','Exact sampling instant within each month and k scale not explicitly specified.'),
 2:('instantaneous_cache_der_volume','bytes; M abbreviation retained','Sum of complete DER object lengths; excludes storage/transport overhead. Exact month sample instant and M scale unspecified.'),
 3:('new_rrdp_delta_documents_and_volume','count and bytes; G abbreviation retained','Merged/deduplicated observed delta XML documents, not traffic to all RPs; excludes retries and partial downloads.'),
 4:('quarterly_rrdp_deltas_publish_elements_and_volume','count and bytes; k/G retained','Publish elements are not unique objects or issuance events; withdrawals not tabulated.'),
 5:('newly_discovered_objects','count','Distinct captured object versions newly discovered during the month, not instantaneous objects, VRPs, or guaranteed issuance timestamps.'),
 6:('newly_discovered_object_der_volume','bytes; M abbreviation retained','Newly discovered objects, not RRDP XML or network traffic.'),
 7:('newly_discovered_objects_by_type','count','Quarterly new object versions; not per-type instantaneous population or RRDP publish event counts.'),
 8:('q2_newly_discovered_objects_by_type_and_location','count','Subset of locations; no assumption that rows exhaust the global quarterly total.'),
 9:('q3_newly_discovered_objects_by_type_and_location','count','Subset of locations; no assumption that rows exhaust the global quarterly total.'),
 10:('quarterly_discovered_object_sizes','bytes; M/G abbreviations retained','Means/medians and volumes refer to quarter discovery datasets, not the initial cache.'),
}

def extract(pdf):
 text=subprocess.check_output(['pdftotext','-layout',str(pdf),'-'],text=True);pages=text.split('\f')
 tables={}
 def rows(page,part=None):
  s=pages[page-1] if part is None else part
  result=[]
  for line in s.splitlines():
   cells=line.split()
   if cells and cells[0] in LOCATIONS:result.append(cells)
  return result
 tables[1]=rows(3);tables[2]=rows(4);tables[4]=rows(5)
 for n,label in [(3,'# of Deltas'),(5,'Objects'),(6,'Volume')]:
  page=5 if n==3 else 6
  if n==3:
   tables[n]=[['deltas']+re.search(r'# of Deltas\s+([^\n]+)',pages[page-1]).group(1).split(),['volume']+re.search(r'Volume \(bytes\)\s+([^\n]+)',pages[page-1]).group(1).split()]
  else:tables[n]=[[label.lower()]+re.search(r'^\s*'+label+r'\s+([^\n]+)',pages[page-1],re.M).group(1).split()]
 tables[7]=[]
 for name in ['Manifests','CRLs','ROAs','Certificates','ASPAs']:
  tables[7].append([name]+re.search(r'^\s*'+name+r'\s+([^\n]+)',pages[5],re.M).group(1).split())
 p7=pages[6];before,after=p7.split('Table 9:',1)
 tables[8]=rows(7,before);tables[9]=rows(7,after)
 tables[10]=rows(8,pages[7].split('Table 11:',1)[0])
 page_map={1:3,2:4,3:5,4:5,5:6,6:6,7:6,8:7,9:7,10:8}
 for n,data in tables.items():
  expected=14 if n in (1,2) else 13 if n in (4,8,9,10) else 5 if n==7 else 2 if n==3 else 1
  assert len(data)==expected,(n,len(data))
 return text,[{'table':n,'pdf_page':page_map[n],'printed_page':page_map[n],
   'population':DESCRIPTIONS[n][0],'unit':DESCRIPTIONS[n][1],'definition':DESCRIPTIONS[n][2],'rows':tables[n]} for n in sorted(tables)]

def main():
 p=argparse.ArgumentParser();p.add_argument('pdf',type=Path);p.add_argument('--out',type=Path,default=HERE);a=p.parse_args()
 text,tables=extract(a.pdf);a.out.mkdir(parents=True,exist_ok=True)
 result={'source_file':a.pdf.name,'sha256':hashlib.sha256(a.pdf.read_bytes()).hexdigest(),'period_utc':['2026-07-01T00:00:00Z','2026-10-01T00:00:00Z'],
  'period_endpoint':'exclusive','period_interpretation':'Calendar-quarter UTC boundaries used for this assessment; the report labels July-September without explicit monthly capture timezones.','source_methodology_page':1,'tables':tables,
  'other_facts':[{'page':4,'quantity':'quarterly_delta_volume','q2':101.8,'q3':146.4,'unit':'GiB as explicitly printed in prose'},
   {'page':11,'quantity':'roa_payloads_milestone','value':1000000,'timestamp_utc':'2026-09-03T00:53:40Z','reported_plot_axis':'Unique VRPs per instance','definition':'Report text calls these ROA payloads; Figure 2 labels unique VRPs per instance. This is not a count of unique ROA DER objects, and this analysis has not independently recomputed the milestone VRPs.'}]}
 (a.out/'report-facts.json').write_text(json.dumps(result,indent=2)+'\n')
 for table in tables:
  with (a.out/f'report-table-{table["table"]:02d}.csv').open('w',newline='') as f:csv.writer(f).writerows(table['rows'])
 (a.out/'report-text.txt').write_text(text)
 print('Verified tables 1-10 extracted; raw abbreviations retained.')
if __name__=='__main__':main()
