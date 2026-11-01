# Global RPKI Q3 2026: source-calibrated PQ size and RRDP assessment

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
The archived collector cache contains **565,166 objects totaling 1,092,318,658 DER bytes**.
Every supported object parsed; excluded projection bytes: 0.
The RSA identity projection equals the source byte total, with the type sums reconciling to the total.
A separate tar-header scan, without the DER parser, reproduces the same count and byte total and found no omitted hardlink/symlink object members; see `archive-header-calibration.json`.
This is one collector's cache, not the report's merged, deduplicated multi-vantage dataset and not independently revalidated by this analysis.
Archived object paths are counted; identical DER bytes at distinct paths are not collapsed.
The cache includes five trust-anchor certificates; their cache paths are not treated as RRDP/rsync publication URIs. Embedded CMS EE certificates are counted within their enclosing object, not again as standalone publication objects.

| Type | Count | DER bytes | Median bytes |
|---|---|---|---|
| asa | 3352 | 6266886 | 1804.0 |
| cer | 55089 | 86913356 | 1537 |
| crl | 54963 | 46321334 | 510 |
| mft | 54963 | 147079186 | 2072 |
| roa | 396799 | 805737896 | 2125 |

`baseline-calibration.csv` compares the same listed base FQDNs to September report Tables 1-2.
The report abbreviates k/M/G without consistently defining their scale. Both decimal and binary interpretations are shown; neither is silently treated as exact.
No offsets or padding are added to force a match with rounded, differently timed report values.
The source's monthly new-object counts sum to 17,681,393; its Table 7 type counts sum to 17,565,626, a 115,767-object difference that is not assigned to invented types.
Monthly displayed RRDP volumes sum numerically to 144.7G, while the prose gives 146.4 GiB. This discrepancy is retained and prevents an exact quarter-wide traffic calibration from the aggregate figures alone.

## Complete object measurements

The existing `tools/generate_rpki_objects.py` was reused on `ssh pqc` with OpenSSL 3.6.2 and the existing Composite provider.
All four suites generated complete DER X.509 certificates, CRLs, ROAs, and manifests and passed the generator's OpenSSL CMS verification.
An additional 28 checks of public certificate decoding, CA/EE certificate chains, CRL signatures, and CMS signatures passed; see `measurement-verification.json`.
This is cryptographic verification with the laboratory CA, not independent RP interoperability or global-cache revalidation.
Public fixtures, SHA-256s and statuses are under `measurements/` and `object-measurements.json`; no private keys are retained.

| Suite | CA cert B | CRL B | ROA CMS B | Manifest CMS B |
|---|---|---|---|---|
| ML-DSA-44 | 4264 | 2575 | 7016 | 7138 |
| ML-DSA-65 | 5793 | 3464 | 9434 | 9556 |
| ML-DSA-65 + ECDSA P-256 | 5927 | 3533 | 9637 | 9758 |
| RSA-2048/SHA-256 | 1064 | 415 | 1621 | 1743 |

These laboratory measurements characterize format overhead and check the length model; their fixed two-entry manifest is never substituted for a production manifest.
The complete CMS includes its EE certificate, signed attributes and signature. Measurements depend on the documented laboratory naming/resource fields.
Composite ECDSA signature encodings vary. Projections conservatively use the evaluated profile's maximum 3,381-byte combined signature (3,309-byte ML-DSA + at most 72-byte DER ECDSA), not a measured constant from one run.

## DER-preserving global-cache projections

For every actual object, the model re-encodes the whole DER container after changing only algorithm-dependent fields: SPKI, certificate signature AlgorithmIdentifiers and BIT STRING, CRL signature, embedded CMS EE certificate, CMS signature and SHA-512 digest attributes.
It retains the observed ROA payload, manifest fileList filenames/counts/hash lengths, CRL revoked entries, naming/resource extensions, validity encodings, and serial-number sizes. DER length-of-length boundary changes are recalculated.
Manifest hash bytes would change after re-signing but retain their SHA-256 length; zero placeholders model new key/signature/digest lengths. Projected objects are **not cryptographically valid objects**.
BGPsec ECDSA subject public keys are retained; their RPKI certificate signatures are projected separately.
No residual repository bytes are placed in a manifest, and no synthetic per-type population is used.
Observed manifests contain 1 to 48,932 fileList entries (median 2); CRLs contain up to 65,312 revoked entries. These actual structures are retained.

| Suite | Full replacement DER B | Idealized parallel DER B | Mixed subtree DER B |
|---|---|---|---|
| composite-mldsa65-p256 | 5,180,716,047 | 6,273,034,705 | 3,142,342,242 |
| ml-dsa-44 | 3,842,631,184 | 4,934,949,842 | 2,471,583,884 |
| ml-dsa-65 | 5,076,188,753 | 6,168,507,411 | 3,089,928,255 |
| rsa | 1,092,318,658 | 2,184,637,316 | 1,092,318,658 |

Full replacement changes every modeled RPKI signature and RPKI RSA subject key in the observed cache.
Idealized RFC 6916 parallel publication is the original cache plus its complete Next-Suite counterpart. This is a hypothetical steady-state footprint, not a phase-by-phase production transition, timing prescription, or storage deduplication model. The RSA parallel column is a duplicate-baseline control.
The Mixed Tree scenario selects the largest observed non-self-issued CA subtree with a known parent; it migrates 9,873 CA keys and affects 265,585 published objects.
Boundary CA: `62477e1fd9e525d0d7a2bb63d914e14ee454a364`; source URI: `rsync://rpki.arin.net/repository/arin-rpki-ta/5e4a23ea-e80a-403e-b08c-2171da2157d3.cer`.
Its parent signature remains RSA while the boundary subject key changes. Descendant signatures change only when their actual issuer is in the selected subtree; other publication points stay unchanged even if they share a host.
Parent links use observed SKI/AKI values. This is a key hierarchy, not proof of every resource/path validation rule or CA operational readiness.
The five trust-anchor roots naturally have no observed parent; they are not treated as migration boundaries.
The choice is an explicitly hypothetical scenario, not an endorsement of Mixed Tree or a production migration plan.

## RRDP transfer results

Observed archive window: first-to-last notification serials in the 2026-09-30 collector log, excluding the first observed serial and including the last.
The log does not explicitly label its timezone; its timestamps are preserved verbatim.
This is not the whole quarter or every RPKI publication point. 35 complete active session intervals, 0 incomplete/unavailable active intervals, 13 selected notification hosts.

| Suite | Projected delta XML body bytes |
|---|---|
| composite-mldsa65-p256 | 3397062374 |
| ml-dsa-44 | 2937567726 |
| ml-dsa-65 | 3361818058 |
| rsa | 1969363778 |

The dataset contains 6,953 distinct delta documents, 1,969,363,778 original XML bytes, 768 withdraw elements, and 189,289 publish elements with a replacement hash.
It includes 93,357 manifest publishes, 93,265 CRL publishes, and 3,499 ROA publishes.
Each occurrence is counted, including repeated publication of an identical object in separate deltas. Files themselves are deduplicated by SHA-256.
Thus periodic republication, object replacement, and withdrawals come from real captured activity, rather than assumed ROA churn.

Baseline XML bytes are reproduced exactly by the identity transformation.
For each publish element the change is `4*ceil(new_DER_bytes/3) - 4*ceil(old_DER_bytes/3)`.
Original XML, URI lengths, base64 whitespace, hash attribute lengths, and withdrawal elements are preserved in the length model.
Different future base64 wrapping, compression, notification changes, retries, HTTP/TLS headers, polling, and client catch-up/snapshot fallback are not modeled.
The predicted bodies do not constitute newly signed or valid RRDP data.
There are 0 parse errors; results are marked `estimated`.

Snapshots and deltas are not interchangeable: the cache DER footprint is the cold-start payload baseline, while these transfer estimates count only the observed delta body sequence.
Snapshot XML bodies are assessed separately below; their capture period differs from this delta window.
Do not multiply the report's 146.4 GiB figure by any ratio here, or extrapolate this window to a global quarterly transfer total.

## Live RRDP snapshot response bodies

Capture window (UTC): 2026-10-27T00:16:18.003606+00:00 to 2026-10-27T00:19:49.093995+00:00.
Endpoint selection uses the 39 distinct notification URLs at the September delta sample's selected hosts, not a new discovery of every currently deployed repository.
Coverage: 39 of 39 endpoints verified; 0 unavailable.
One endpoint was collected from a second network vantage after the primary collector's connection was reset; the failed attempt and both capture times are retained in the selection manifest.
This is an October live cohort, **not** a September/Q3 snapshot or a simultaneous global state.
At least the archived RIPE end-of-day September snapshot reference returned HTTP 404, and its referenced hash was absent from the inspected session listing; see `sources/historical-snapshot-probe.json`. This probe does not establish absence from every archive.

| Suite | Snapshot XML body bytes (RSA observed; PQ estimated) |
|---|---|
| composite-mldsa65-p256 | 7,039,424,515 |
| ml-dsa-44 | 5,247,988,987 |
| ml-dsa-65 | 6,899,465,015 |
| rsa | 1,565,796,047 |

There are 39 distinct snapshot XML documents, containing 569,070 publish elements and 1,097,065,991 DER bytes.
Requests used `Accept-Encoding: identity`; recorded response bodies were uncompressed and their Content-Length values, when present, were checked.
Every body SHA-256 matches its captured notification; snapshot session and serial match that notification.
Complete raw-body replay with `verify_snapshot_replay.py` checks every document's DER and XML length results against the saved summary; the verification record is retained separately.
All publish payloads were parsed with 0 analysis errors; duplicate snapshot URIs, replacement hashes and withdrawals are rejected.
The AFRINIC snapshot also contains a 496-byte text TAL. It is counted on the wire but excluded from DER totals and retained at its observed size for all suites; future TAL contents are outside this model. This explicit non-DER case is not a malformed signed-object claim.
This checks the acquisition and format/size model, not complete RELAX NG or RPKI resource/path validity.
The RSA identity projection exactly equals 1,565,796,047 captured XML bytes.
The same complete-DER/base64 length transformation used for deltas estimates the PQ bodies; actual keys/signatures and changed object hash values are not generated.

Captured notification bodies for successful endpoints total 908,179 bytes and are kept separately from the snapshot table.
Their future PQ size is not modeled: current notifications list retained deltas as well as the snapshot.
One copy of each selected snapshot body measures a bootstrap/fallback payload for this cohort; it is not recurring traffic and is not added to the September delta total.
Fallback frequency, compressed transfer, HTTP/TLS overhead, retries and per-client consumption remain unmeasured.

Notifications and selection metadata are published here. Large raw snapshot bodies are retained in the collection scratch directory, not bundled in Git.
`fetch_rrdp_snapshots.py --network --replay-manifest rrdp-snapshot-selection.json --out SCRATCH` reuses matching cached bodies or fetches the exact pinned URLs; it fails if an immutable source has expired, and never substitutes a newer snapshot.
Consequently exact reanalysis requires the retained raw bodies when upstream retention has elapsed; a fresh live capture is a new cohort, not a reproduction of these numbers.


## Reproduction and tests

Use Python 3.11+, system `pdftotext`, rsync, and the existing OpenSSL/Composite environment. The analyzer itself is stdlib-only apart from the repository's existing DER/CMS module.
`reproduce.sh` describes the complete fetch/generate/analyze pipeline into a fresh scratch output directory; supply the documented environment variables. Raw archive inputs are intentionally not committed.
`fetch_sources.py` fails on source hash drift. `fetch_rrdp_day.py` derives serial intervals from collector logs and verifies every downloaded file against the SHA-256 in its archive filename.
Neither network fetching nor remote access occurs when running the tests.
`validate_results.py --directory results/global-rpki-q3-2026` checks source hashes, independent baseline sums, all delta file identities/intervals, projection sums, backend results and offline unit tests, and writes `validation.json`.
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
