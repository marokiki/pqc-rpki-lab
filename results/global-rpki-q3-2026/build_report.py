#!/usr/bin/env python3
"""Build derived tables/report without network access or changing historical evidence."""
import argparse,csv,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def read(root,name):return json.loads((root/name).read_text())
def write(root,name,data):(root/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
def csv_file(root,name,rows):
 if not rows:return
 with (root/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(str(x) for x in row)+' |' for row in rows])
def main():
 p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=HERE);a=p.parse_args();r=a.directory
 snap=read(r,'snapshot-summary.json')
 if (r/'archive-header-calibration.json').exists():
  headers=read(r,'archive-header-calibration.json')
  assert headers['object_count']==snap['object_count'] and headers['object_bytes']==snap['object_bytes']
  assert not headers['nonregular_object_members']
 measure=read(r,'object-measurements.json');facts=read(r,'sources/report-facts.json')
 tables={x['table']:x for x in facts['tables']}
 csv_file(r,'object-measurements.csv',[{k:x.get(k) for k in ['algorithm','artifact','bytes','status','sha256','public_path']} for x in measure['results']])
 csv_file(r,'repository-projections.csv',[{'suite':suite,**x} for suite,x in snap['projections'].items()])
 calibration=[];counts={row[0]:row[-1] for row in tables[1]['rows']};sizes={row[0]:row[-1] for row in tables[2]['rows']}
 for loc in counts:
  actual=snap['by_location'].get(loc,{'count':0,'bytes':0});n=int(counts[loc].rstrip('k'));v=int(sizes[loc].rstrip('M'))
  calibration.append({'location':loc,'snapshot_count':actual['count'],'snapshot_der_bytes':actual['bytes'],
    'report_count_display':counts[loc],'report_bytes_display':sizes[loc],
    'count_if_decimal_k':n*1000,'count_if_binary_k':n*1024,
    'bytes_if_decimal_M':v*1000000,'bytes_if_binary_M':v*1048576,
    'difference_from_decimal_bytes':actual['bytes']-v*1000000,'difference_from_binary_bytes':actual['bytes']-v*1048576})
 qc={'q3_monthly_newly_discovered_count_sum':sum(int(x.replace(',','')) for x in tables[5]['rows'][0][-3:]),
  'q3_type_table_count_sum':sum(int(x[2].replace(',','')) for x in tables[7]['rows']),
  'q3_monthly_delta_volume_displays':tables[3]['rows'][1][-3:],
  'q3_monthly_delta_volume_numeric_sum_same_display_scale':sum(float(x.rstrip('G')) for x in tables[3]['rows'][1][-3:]),
  'q3_prose_delta_volume_GiB':146.4,
  'interpretation':'Keep the discrepancies; do not force rounded or differently scoped figures to match. No aggregate RRDP multiplier is used.'}
 qc['difference_monthly_minus_types']=qc['q3_monthly_newly_discovered_count_sum']-qc['q3_type_table_count_sum']
 write(r,'baseline-calibration.json',{'snapshot_self_calibration':{'objects':sum(x['count'] for x in snap['object_sizes'].values()),'bytes':sum(x['bytes'] for x in snap['object_sizes'].values()),'matches_all_parsed_members':not snap['parse_errors']},
  'report_comparison_status':'contextual only: initial-state sample instants and k/M scales are not explicit','by_location':calibration,'report_internal_cross_checks':qc})
 csv_file(r,'baseline-calibration.csv',calibration)
 object_rows=[]
 for algorithm in sorted({x['algorithm'] for x in measure['results']}):
  by={x['artifact']:x for x in measure['results'] if x['algorithm']==algorithm}
  object_rows.append([algorithm]+[by[k]['bytes'] for k in ('CA certificate','CRL','ROA CMS','Manifest CMS')])
 projection_rows=[[k,f"{x['full_replacement_bytes']:,}",f"{x['idealized_parallel_publication_bytes']:,}",f"{x['mixed_tree_bytes']:,}"] for k,x in snap['projections'].items()]
 rr=read(r,'rrdp-summary.json') if (r/'rrdp-summary.json').exists() else None
 selection=read(r,'trace-selection.json') if (r/'trace-selection.json').exists() else None
 rrdp_text='No trace projection is available. Do not infer it from report traffic and a repository ratio.'
 if rr:
  docs=rr.pop('documents',[])
  csv_file(r,'rrdp-documents.csv',[{'source_relative_path':x['path'].split('/xml/',1)[-1],'sha256':x['sha256'],'kind':x['kind'],'session_id':x['session_id'],'serial':x['serial'],
    'original_xml_bytes':x['original_xml_bytes'],'withdraw_count':x['withdraw_count'],'replacement_publish_count':x['replacement_publish_count'],
    **{'publish_'+k:v for k,v in {kind:x['publish_counts'].get(kind,0) for kind in ['cer','crl','mft','roa','asa']}.items()},
    **{k+'_xml_bytes':v for k,v in x['projected_xml_bytes'].items()}} for x in docs])
  write(r,'rrdp-totals.json',rr)
  if selection:
   coverage=selection['coverage'];active=[x for x in coverage if x['serial_end_inclusive']>x['serial_start_exclusive']]
   complete=[x for x in active if x.get('complete_interval')]
   missing=[x for x in active if not x.get('complete_interval')]
   scope=f"{len(complete)} complete active session intervals, {len(missing)} incomplete/unavailable active intervals, {len(selection['selected_hosts'])} selected notification hosts."
  else:scope='See source manifest for interval coverage.'
  t=rr['totals'];rows=[[k,rr['projections'].get('delta_'+k)] for k in snap['projections']]
  rrdp_text=f"""Observed archive window: first-to-last notification serials in the 2026-09-30 collector log, excluding the first observed serial and including the last.
The log does not explicitly label its timezone; its timestamps are preserved verbatim.
This is not the whole quarter or every RPKI publication point. {scope}

{table(['Suite','Projected delta XML body bytes'],rows)}

The dataset contains {t.get('delta_documents',0):,} distinct delta documents, {t.get('delta_xml_bytes',0):,} original XML bytes, {t.get('delta_withdrawals',0):,} withdraw elements, and {t.get('delta_replacement_publishes',0):,} publish elements with a replacement hash.
It includes {t.get('delta_publish_mft',0):,} manifest publishes, {t.get('delta_publish_crl',0):,} CRL publishes, and {t.get('delta_publish_roa',0):,} ROA publishes.
Each occurrence is counted, including repeated publication of an identical object in separate deltas. Files themselves are deduplicated by SHA-256.
Thus periodic republication, object replacement, and withdrawals come from real captured activity, rather than assumed ROA churn.

Baseline XML bytes are reproduced exactly by the identity transformation.
For each publish element the change is `4*ceil(new_DER_bytes/3) - 4*ceil(old_DER_bytes/3)`.
Original XML, URI lengths, base64 whitespace, hash attribute lengths, and withdrawal elements are preserved in the length model.
Different future base64 wrapping, compression, notification changes, retries, HTTP/TLS headers, polling, and client catch-up/snapshot fallback are not modeled.
The predicted bodies do not constitute newly signed or valid RRDP data.
There are {len(rr['errors'])} parse errors; results are marked `{rr['status']}`.

Snapshots and deltas are not interchangeable: the cache DER footprint is the cold-start payload baseline, while these transfer estimates count only the observed delta body sequence.
Snapshot XML bodies are assessed separately below; their capture period differs from this delta window.
Do not multiply the report's 146.4 GiB figure by any ratio here, or extrapolate this window to a global quarterly transfer total.
"""
 ss=read(r,'rrdp-snapshot-summary.json') if (r/'rrdp-snapshot-summary.json').exists() else None
 sm=read(r,'rrdp-snapshot-selection.json') if (r/'rrdp-snapshot-selection.json').exists() else None
 if ss and sm:
  verified=[x for x in sm['endpoints'] if x['status']=='verified']
  failed=[x for x in sm['endpoints'] if x['status']!='verified']
  snapshots={x['path']:x for x in ss['documents']}
  rows=[]
  for x in verified:
   doc=snapshots[x['snapshot_path'].removeprefix('xml/')]
   rows.append({'notification_uri':x['notification_uri'],'snapshot_uri':x['snapshot_uri'],
    'session_id':doc['session_id'],'serial':doc['serial'],'sha256':doc['sha256'],
    'captured_utc':x['snapshot_response']['finished_utc'],
    'original_xml_bytes':doc['original_xml_bytes'],'published_der_bytes':doc['published_der_bytes'],
    'unmodeled_payload_bytes':sum(v['bytes'] for v in doc.get('unmodeled_payloads',[])),
    **{'publish_'+k:doc['publish_counts'].get(k,0) for k in ('cer','crl','mft','roa','asa','tal')},
    **{k+'_xml_bytes':v for k,v in doc['projected_xml_bytes'].items()}})
  csv_file(r,'rrdp-snapshot-documents.csv',rows)
  snapshot_rows=[[suite,f"{ss['projections']['snapshot_'+suite]:,}"] for suite in snap['projections']]
  notification_bytes=sum(x['notification_response']['bytes'] for x in verified)
  total_der=sum(x['published_der_bytes'] for x in ss['documents'])
  unmodeled=[v for x in ss['documents'] for v in x.get('unmodeled_payloads',[])]
  snapshot_text=f"""## Live RRDP snapshot response bodies

Capture window (UTC): {sm['started_utc']} to {sm['finished_utc']}.
Endpoint selection uses the 39 distinct notification URLs at the September delta sample's selected hosts, not a new discovery of every currently deployed repository.
Coverage: {len(verified)} of {len(sm['endpoints'])} endpoints verified; {len(failed)} unavailable.
One endpoint was collected from a second network vantage after the primary collector's connection was reset; the failed attempt and both capture times are retained in the selection manifest.
This is an October live cohort, **not** a September/Q3 snapshot or a simultaneous global state.
At least the archived RIPE end-of-day September snapshot reference returned HTTP 404, and its referenced hash was absent from the inspected session listing; see `sources/historical-snapshot-probe.json`. This probe does not establish absence from every archive.

{table(['Suite','Snapshot XML body bytes (RSA observed; PQ estimated)'],snapshot_rows)}

There are {ss['totals']['snapshot_documents']} distinct snapshot XML documents, containing {sum(sum(x['publish_counts'].values()) for x in ss['documents']):,} publish elements and {total_der:,} DER bytes.
Requests used `Accept-Encoding: identity`; recorded response bodies were uncompressed and their Content-Length values, when present, were checked.
Every body SHA-256 matches its captured notification; snapshot session and serial match that notification.
Complete raw-body replay with `verify_snapshot_replay.py` checks every document's DER and XML length results against the saved summary; the verification record is retained separately.
All publish payloads were parsed with {len(ss['errors'])} analysis errors; duplicate snapshot URIs, replacement hashes and withdrawals are rejected.
The AFRINIC snapshot also contains a {sum(x['bytes'] for x in unmodeled):,}-byte text TAL. It is counted on the wire but excluded from DER totals and retained at its observed size for all suites; future TAL contents are outside this model. This explicit non-DER case is not a malformed signed-object claim.
This checks the acquisition and format/size model, not complete RELAX NG or RPKI resource/path validity.
The RSA identity projection exactly equals {ss['totals']['snapshot_xml_bytes']:,} captured XML bytes.
The same complete-DER/base64 length transformation used for deltas estimates the PQ bodies; actual keys/signatures and changed object hash values are not generated.

Captured notification bodies for successful endpoints total {notification_bytes:,} bytes and are kept separately from the snapshot table.
Their future PQ size is not modeled: current notifications list retained deltas as well as the snapshot.
One copy of each selected snapshot body measures a bootstrap/fallback payload for this cohort; it is not recurring traffic and is not added to the September delta total.
Fallback frequency, compressed transfer, HTTP/TLS overhead, retries and per-client consumption remain unmeasured.

Notifications and selection metadata are published here. Large raw snapshot bodies are retained in the collection scratch directory, not bundled in Git.
`fetch_rrdp_snapshots.py --network --replay-manifest rrdp-snapshot-selection.json --out SCRATCH` reuses matching cached bodies or fetches the exact pinned URLs; it fails if an immutable source has expired, and never substitutes a newer snapshot.
Consequently exact reanalysis requires the retained raw bodies when upstream retention has elapsed; a fresh live capture is a new cohort, not a reproduction of these numbers.
"""
  rrdp_text+='\n'+snapshot_text
 rrdp_file=r/'RRDP.md';rrdp_file.write_text('# RRDP transfer projection\n\n'+rrdp_text+'\n')
 report=f"""# Global RPKI Q3 2026: source-calibrated PQ size and RRDP assessment

EXPERIMENTAL / NOT FOR PRODUCTION. Assessment date: 2026-10-27.
This supersedes arbitrary fixed-object and ROA-churn workloads for the scope quantified here; older evidence is retained unchanged.
The cache and delta observations are from September 30; the separately reported live RRDP snapshots were captured on October 27 and are not Q3 measurements.
These scripts write only analysis artifacts; selected results are incorporated separately into the Internet-Draft.

## Verified sources and population definitions

The author's [report](https://bsd.nl/publications/Global_RPKI_Report_2026_Q3.pdf) and the [Zenodo DOI](https://doi.org/10.5281/zenodo.23512896) are distinct 13-page PDF files.
The author copy was last modified on 2026-10-21; Zenodo records publication on 2026-10-20.
Their numerical Tables 1-10 match. Table 11 and some editorial wording differ; both files and their hashes are retained in `sources/`.
License of the DOI version: CC BY 4.0; author: Job Snijders. Source attribution and the unmodified originals are retained.
The source manifest records the exact bytes used. Raw cell strings, definitions, units, printed/PDF page numbers, and periods are in `sources/report-facts.json` and the table CSVs.

- Tables 1-2 (pp. 3-4): initial cache object counts and complete DER bytes; neither is a VRP count. Exact sampling instants within each month are not stated.
- Tables 3-4 (p. 5), with definitions on p. 4: newly observed RRDP delta documents and publish elements/bytes, not all-client network traffic. Retry/partial-download waste is excluded; invalid objects may be present.
- Tables 5-9 (pp. 6-7): newly discovered object versions in the deduplicated capture. Discovery is not an issuance timestamp or a publish event count. These counts must not be used as instantaneous populations.
- Table 10 (p. 8): sizes over quarterly discovery data; not the mean size of the initial cache.
- The one-million milestone (p. 11) is dated 2026-09-03 00:53:40 UTC. The text says ROA payloads and Figure 2 labels unique VRPs per instance. This is not the number of unique DER ROA objects; this assessment does not independently recompute those VRPs or use the milestone as an object population.

## Calibration, discrepancies, and scope

Primary byte baseline: [RPKIViews dango snapshot](https://dango.attn.jp/rpkidata/2026/09/30/rpki-20260930T234958Z.tgz), timestamp label 2026-09-30T23:49:58Z.
The archived collector cache contains **{snap['object_count']:,} objects totaling {snap['object_bytes']:,} DER bytes**.
Every supported object parsed; excluded projection bytes: {sum(x['bytes'] for x in snap['parse_errors']):,}.
The RSA identity projection equals the source byte total, with the type sums reconciling to the total.\nA separate tar-header scan, without the DER parser, reproduces the same count and byte total and found no omitted hardlink/symlink object members; see `archive-header-calibration.json`.
This is one collector's cache, not the report's merged, deduplicated multi-vantage dataset and not independently revalidated by this analysis.
Archived object paths are counted; identical DER bytes at distinct paths are not collapsed.\nThe cache includes five trust-anchor certificates; their cache paths are not treated as RRDP/rsync publication URIs. Embedded CMS EE certificates are counted within their enclosing object, not again as standalone publication objects.

{table(['Type','Count','DER bytes','Median bytes'],[[k,v['count'],v['bytes'],v['median_bytes']] for k,v in snap['object_sizes'].items()])}

`baseline-calibration.csv` compares the same listed base FQDNs to September report Tables 1-2.
The report abbreviates k/M/G without consistently defining their scale. Both decimal and binary interpretations are shown; neither is silently treated as exact.
No offsets or padding are added to force a match with rounded, differently timed report values.
The source's monthly new-object counts sum to {qc['q3_monthly_newly_discovered_count_sum']:,}; its Table 7 type counts sum to {qc['q3_type_table_count_sum']:,}, a {qc['difference_monthly_minus_types']:,}-object difference that is not assigned to invented types.
Monthly displayed RRDP volumes sum numerically to 144.7G, while the prose gives 146.4 GiB. This discrepancy is retained and prevents an exact quarter-wide traffic calibration from the aggregate figures alone.

## Complete object measurements

The existing `tools/generate_rpki_objects.py` was reused on `ssh pqc` with OpenSSL 3.6.2 and the existing Composite provider.
All four suites generated complete DER X.509 certificates, CRLs, ROAs, and manifests and passed the generator's OpenSSL CMS verification.\nAn additional 28 checks of public certificate decoding, CA/EE certificate chains, CRL signatures, and CMS signatures passed; see `measurement-verification.json`.
This is cryptographic verification with the laboratory CA, not independent RP interoperability or global-cache revalidation.
Public fixtures, SHA-256s and statuses are under `measurements/` and `object-measurements.json`; no private keys are retained.

{table(['Suite','CA cert B','CRL B','ROA CMS B','Manifest CMS B'],object_rows)}

These laboratory measurements characterize format overhead and check the length model; their fixed two-entry manifest is never substituted for a production manifest.
The complete CMS includes its EE certificate, signed attributes and signature. Measurements depend on the documented laboratory naming/resource fields.
Composite ECDSA signature encodings vary. Projections conservatively use the evaluated profile's maximum 3,381-byte combined signature (3,309-byte ML-DSA + at most 72-byte DER ECDSA), not a measured constant from one run.

## DER-preserving global-cache projections

For every actual object, the model re-encodes the whole DER container after changing only algorithm-dependent fields: SPKI, certificate signature AlgorithmIdentifiers and BIT STRING, CRL signature, embedded CMS EE certificate, CMS signature and SHA-512 digest attributes.
It retains the observed ROA payload, manifest fileList filenames/counts/hash lengths, CRL revoked entries, naming/resource extensions, validity encodings, and serial-number sizes. DER length-of-length boundary changes are recalculated.
Manifest hash bytes would change after re-signing but retain their SHA-256 length; zero placeholders model new key/signature/digest lengths. Projected objects are **not cryptographically valid objects**.
BGPsec ECDSA subject public keys are retained; their RPKI certificate signatures are projected separately.
No residual repository bytes are placed in a manifest, and no synthetic per-type population is used.

{table(['Suite','Full replacement DER B','Idealized parallel DER B','Mixed subtree DER B'],projection_rows)}

Full replacement changes every modeled RPKI signature and RPKI RSA subject key in the observed cache.
Idealized RFC 6916 parallel publication is the original cache plus its complete Next-Suite counterpart. This is a hypothetical steady-state footprint, not a phase-by-phase production transition, timing prescription, or storage deduplication model. The RSA parallel column is a duplicate-baseline control.
The Mixed Tree scenario selects the largest observed non-self-issued CA subtree with a known parent; it migrates {snap['hierarchy']['migrated_ca_keys']:,} CA keys and affects {snap['projections']['ml-dsa-65']['mixed_affected_objects']:,} published objects.
Boundary CA: `{snap['hierarchy']['selected_ca_ski']}`; source URI: `{snap['hierarchy']['selected_ca_uri']}`.
Its parent signature remains RSA while the boundary subject key changes. Descendant signatures change only when their actual issuer is in the selected subtree; other publication points stay unchanged even if they share a host.
Parent links use observed SKI/AKI values. This is a key hierarchy, not proof of every resource/path validation rule or CA operational readiness.
The five trust-anchor roots naturally have no observed parent; they are not treated as migration boundaries.\nThe choice is an explicitly hypothetical scenario, not an endorsement of Mixed Tree or a production migration plan.

## RRDP transfer results

{rrdp_text}

## Reproduction and tests

Use Python 3.11+, system `pdftotext`, rsync, and the existing OpenSSL/Composite environment. The analyzer itself is stdlib-only apart from the repository's existing DER/CMS module.
`reproduce.sh` describes the complete fetch/generate/analyze pipeline into a fresh scratch output directory; supply the documented environment variables. Raw archive inputs are intentionally not committed.
`fetch_sources.py` fails on source hash drift. `fetch_rrdp_day.py` derives serial intervals from collector logs and verifies every downloaded file against the SHA-256 in its archive filename.
Neither network fetching nor remote access occurs when running the tests.\n`validate_results.py --directory results/global-rpki-q3-2026` checks source hashes, independent baseline sums, all delta file identities/intervals, projection sums, backend results and offline unit tests, and writes `validation.json`.
For example, on the existing `ssh pqc` environment, from a checkout containing this task:

```sh
export PQC_GLOBAL_WORK="$(mktemp -d -t pqc-global-q3.XXXXXX)"
export PQC_GLOBAL_OPENSSL="$PWD/local/build/openssl-3.6.2-install/bin/openssl"
export LD_LIBRARY_PATH="$PWD/local/build/openssl-3.6.2-install/lib64"
export OPENSSL_CONF="$PWD/experiments/openssl-composite.cnf"
export PQC_COMPOSITE_PROVIDER_MODULE="$PWD/local/build/composite-provider/composite.so"
sh results/global-rpki-q3-2026/reproduce.sh
```

Use a scratch filesystem with at least 8 GB free for these pinned inputs.
The committed PDF copies seed the scratch inputs and are hash-verified; the mutable author URL need not still serve the same version.
The public RRDP archive and snapshot still have to be reachable. They are not bundled in Git.

```sh
python3 -m unittest discover -s results/global-rpki-q3-2026 -p 'test_*.py'
```

Tests exercise exact RSA byte identity, complete pure-PQ object-size agreement with generated fixtures, embedded EE counting, payload/fileList preservation, mixed-boundary signatures, BGPsec subject-key retention, DER length boundaries, repeated RRDP publishes, replacements, withdrawals, snapshot framing and URI uniqueness, notification references, session/serial matching, and malformed-input rejection.
Raw snapshot inventory is reproducible with `evaluate.py snapshot`; it is retained in scratch storage rather than committed as a large duplicate of the public archive.
The XML document-level results and serial-interval selection are included for auditing each transfer contribution.

## Remaining gaps

- A contemporaneous globally merged dataset with exact per-type initial counts/bytes and the report's exact initial-state sample instants is not available from the report itself. This cache snapshot is the verified baseline, not a reconstructed claim about that unavailable dataset.
- No complete three-month, all-publication-point RRDP replay was performed. Quarter-wide PQ RRDP totals remain **unavailable**; no numeric substitute is manufactured from aggregate growth ratios or unique-discovery counts.
- Issuance times/events are not inferred from object discovery or file mtimes. The collector log's timezone is not explicit.
- Replayed XML has not been independently validated as a complete state chain under TALs; absence of an XML parse error is not RPKI validity.
- No actual PQ global repository was signed/validated, no deployment costs are estimated, and no algorithm is recommended.
- Snapshot body bytes are measured for a separately dated live cohort. September snapshot bytes, fallback frequency, compression, retries, request headers, network effects and validator memory remain unmeasured. Erik and rsync transfer comparisons are deliberately separate and absent.
"""
 diagnostics=read(r,'snapshot-diagnostics.json') if (r/'snapshot-diagnostics.json').exists() else None
 if diagnostics:
  detail=diagnostics['manifest_filelist'];crl=diagnostics['crl_revoked_entries']
  report=report.replace('No residual repository bytes are placed in a manifest, and no synthetic per-type population is used.',
   f"No residual repository bytes are placed in a manifest, and no synthetic per-type population is used.\nObserved manifests contain {detail['min_entries']:,} to {detail['max_entries']:,} fileList entries (median {detail['median_entries']}); CRLs contain up to {crl['max']:,} revoked entries. These actual structures are retained.")
 provenance={'assessment_date':'2026-10-27','source_code_baseline':'3cddcf7',
  'reports':{'author_url':'https://bsd.nl/publications/Global_RPKI_Report_2026_Q3.pdf','doi':'https://doi.org/10.5281/zenodo.23512896','author_pdf_last_modified_utc':'2026-10-21T18:10:12Z','doi_publication_date':'2026-10-20','tables_1_to_10_match_between_copies':True,'license':'CC-BY-4.0 (DOI record)','author':'Job Snijders'},
  'snapshot':{'url':'https://dango.attn.jp/rpkidata/2026/09/30/rpki-20260930T234958Z.tgz','timestamp_label_utc':'2026-09-30T23:49:58Z','sha256':snap['archive_sha256'],'bytes':snap['archive_bytes'],'scope':'one collector cache; not the merged report dataset'},
  'rrdp_archive':{'base':'rsync://rrdp.rpkiviews.org/data/2026/09/','announcement':'https://mailarchive.ietf.org/arch/msg/sidrops/w2BUb4-MGj_T383S58yTBEbn9so/','collector_log':'20260930.log','log_sha256':selection['log_sha256'] if selection else None,'file_count':len(selection['files']) if selection else 0,'file_hash_manifest':'trace-selection.json','full_quarter_replay':False},
  'measurements':{'backend':measure['backend'],'generator':'tools/generate_rpki_objects.py','generator_sha256':hashlib.sha256((HERE.parents[1]/'tools/generate_rpki_objects.py').read_bytes()).hexdigest(),'private_keys_retained':False},
  'analysis_scripts':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in HERE.glob('*.py')},
  'derived_result_hashes':{n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in ('snapshot-summary.json','archive-header-calibration.json','snapshot-diagnostics.json','rrdp-summary.json','trace-selection.json','rrdp-snapshot-summary.json','rrdp-snapshot-selection.json','rrdp-snapshot-replay-verification.json','object-measurements.json','measurement-verification.json') if (r/n).exists()},
  'local_files':{}}
 if sm:provenance['live_rrdp_snapshots']={'selection_manifest':'rrdp-snapshot-selection.json','capture_started_utc':sm['started_utc'],'capture_finished_utc':sm['finished_utc'],'same_period_as_september_delta_trace':False,'raw_bodies_bundled':False,'raw_body_retention':'collection scratch; pinned origin URLs may expire'}
 for item in sorted((r/'sources').rglob('*')):
  if item.is_file():provenance['local_files'][str(item.relative_to(r))]={'sha256':hashlib.sha256(item.read_bytes()).hexdigest(),'bytes':item.stat().st_size}
 write(r,'source-manifest.json',provenance)
 (r/'README.md').write_text(report)
 print('Generated source-calibrated tables, calibration, RRDP scope and assessment README.')
if __name__=='__main__':main()
