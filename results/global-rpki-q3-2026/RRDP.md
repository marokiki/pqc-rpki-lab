# RRDP transfer projection

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

