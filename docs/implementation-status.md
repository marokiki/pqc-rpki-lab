# Implementation Status

> EXPERIMENTAL / NOT FOR PRODUCTION

This document is public-safe status for the implementation and measurement
harness. It intentionally excludes private review-thread summaries and local
planning notes.

| Area | Status | Public evidence | Limitation |
|---|---|---|---|
| Primitive signature benchmarks | implemented | `results/primitive-bench.*`, `results/review-2026-06/exact-100k.*` | Primitive measurements are not complete RPKI object generation. |
| Composite component benchmarks | partially implemented | `results/review-2026-06/composite-100k.*` | Sequential component operations only; no LAMPS composite ASN.1/OID encoding. |
| Draft-19 raw Composite ML-DSA | implemented and measured | `results/draft-composite-2026-07/draft-composite-100k.*` | Sign/Verify, domain separation, context binding, and raw concatenation are implemented; independent interoperability remains open. |
| Repository-size model | implemented estimate | `results/repository-impact.*` | Model-driven unless complete DER objects are measured. |
| ML-DSA certificates and CRLs | partially implemented | `results/object-generation-feasibility.*` | OpenSSL capability depends on local provider support. |
| ML-DSA CMS SignedData | implemented for ML-DSA-65 | `results/cms-probe/`, `results/cms-generation/` | Requires the OpenSSL CMS API with explicit SHA-512; the generic CLI path still fails. |
| Manifest and ROA payload model | implemented as synthetic benchmark | `results/object-benchmarks/` | Payload and hash benchmark only; not complete RFC 6488 CMS output. |
| RSA Manifest and ROA CMS fixtures | implemented | `results/rpki-objects/`, `testdata/rsa/` | Local OpenSSL CMS evidence; not independent validator acceptance. |
| ML-DSA Manifest and ROA CMS fixtures | implemented for ML-DSA-65 | `results/rpki-objects/`, `testdata/ml-dsa-65/` | ML-DSA-44/87 remain incomplete. |
| Local object validation | implemented | `results/local-validation/` | Includes CMS, EE profile, Manifest hash, and content checks; it does not replace RP validation. |
| Synthetic key-roll model | implemented | `results/key-roll/` | Uses fixture sizes and synthetic counts; not production accuracy. |
| Mixed-tree migration | implemented as model and E2E fixture | `results/mixed-tree/`, `testdata/composite-e2e/mixed-tree/`, `results/composite-e2e/` | Controlled RSA-parent to Composite-child experiment; not production interoperability. |
| Manifest key consistency | implemented model checks | `src/pqc_rpki_lab/rpki_objects.py` | Models issuer/signing context; does not replace a validator. |
| CCR semantic comparison | implemented | `results/ccr-comparison/rp-produced-state-hashes.json` | Parses rpki-client CCR DER and recomputes `ROAPayloadState`, `ManifestState`, and `TrustAnchorState`; only one CCR-producing RP is represented. |
| Unmodified validator interoperability | measured rejection | `results/validator-probe/` | Routinator 0.15.2, rpki-client 9.8, and FORT 1.6.8 accept RSA and reject ML-DSA-65. |
| Experimental rpki-client E2E | implemented | `patches/rpki-client-composite-experimental.patch`, `results/composite-e2e/` | Experimental mode validates pure ML-DSA-65, Composite standalone, and RSA-to-Composite mixed-tree fixtures; default mode remains Current Suite-only. |
| Experimental Routinator E2E | implemented | `patches/rpki-rs-experimental-pqc.patch`, `patches/routinator-experimental-pqc.patch`, `results/composite-e2e/routinator-*.json` | A second RP implementation validates all four scenarios and rejects all 15 negative cases. It shares the experiment's OpenSSL/provider cryptographic backend. |
| Operational negative cases | implemented | `results/composite-e2e/operational-negative-summary.json` | Both RPs reject seven expired, revoked, stale, and missing-publication cases; the corpus remains controlled and small. |
| Experimental Krill issuance, update, and rollback | implemented | `patches/krill-experimental-pqc.patch`, `results/composite-e2e/krill-rollover.json` | An RSA parent issues a Composite child, replaces one ROA, and rolls the child back to RSA. This is isolated testbed operation, not production deployment. |
| Public-cache aggregate profile | implemented for one snapshot | `tools/profile_public_cache.py`, `results/scaled-corpus/public-cache-profile.json` | 550,210 objects across 54,960 publication points produced 980,019 VRPs; ARIN was unavailable, source objects are not published, and no time series was collected. |
| Repeated scaled Krill issuance and validation | implemented through 1,000 ROAs | `tools/krill_scale_campaign.py`, `results/scaled-corpus/krill-repeated-summary.json` | Generation is repeated 30 times through 100 ROAs and 10 times at 1,000; the eight-mode fresh-cache RP matrix is repeated 100 times per size. This remains one child publication point. |
| Multi-publication-point topology pilot | implemented at 100 child CAs | `tools/topology_corpus.py`, `results/scaled-corpus/topology-pilot-summary.json` | Both RPs produce 100 VRPs and retain 99 after one branch is removed; synthetic topology, not Krill or public-repository re-signing. |
| RP cache-regime measurement | implemented at 1,000 ROAs | `tools/rp_cache_campaign.py`, `results/scaled-corpus/rp-cache-regimes.json` | Fresh, unchanged, and one-ROA-update states are repeated 30 times; local rsync and uncontrolled OS page cache limit interpretation. |
