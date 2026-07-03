# Implementation Status

> EXPERIMENTAL / NOT FOR PRODUCTION

This document is public-safe status for the implementation and measurement
harness. It intentionally excludes private review-thread summaries and local
planning notes.

| Area | Status | Public evidence | Limitation |
|---|---|---|---|
| Primitive signature benchmarks | implemented | `results/primitive-bench.*`, `results/review-2026-06/exact-100k.*` | Primitive measurements are not complete RPKI object generation. |
| Composite component benchmarks | partially implemented | `results/review-2026-06/composite-100k.*` | Sequential component operations only; no LAMPS composite ASN.1/OID encoding. |
| Repository-size model | implemented estimate | `results/repository-impact.*` | Model-driven unless complete DER objects are measured. |
| ML-DSA certificates and CRLs | partially implemented | `results/object-generation-feasibility.*` | OpenSSL capability depends on local provider support. |
| ML-DSA CMS SignedData | implemented for ML-DSA-65 | `results/cms-probe/`, `results/cms-generation/` | Requires the OpenSSL CMS API with explicit SHA-512; the generic CLI path still fails. |
| Manifest and ROA payload model | implemented as synthetic benchmark | `results/object-benchmarks/` | Payload and hash benchmark only; not complete RFC 6488 CMS output. |
| RSA Manifest and ROA CMS fixtures | implemented | `results/rpki-objects/`, `testdata/rsa/` | Local OpenSSL CMS evidence; not independent validator acceptance. |
| ML-DSA Manifest and ROA CMS fixtures | implemented for ML-DSA-65 | `results/rpki-objects/`, `testdata/ml-dsa-65/` | ML-DSA-44/87 remain incomplete. |
| Local object validation | implemented | `results/local-validation/` | Includes CMS, EE profile, Manifest hash, and content checks; it does not replace RP validation. |
| Synthetic key-roll model | implemented | `results/key-roll/` | Uses fixture sizes and synthetic counts; not production accuracy. |
| Mixed-tree migration model | implemented synthetic fixture | `results/mixed-tree/`, `testdata/mixed-tree/` | Public model only; not validator interoperability evidence. |
| Manifest key consistency | implemented model checks | `src/pqc_rpki_lab/rpki_objects.py` | Models issuer/signing context; does not replace a validator. |
| CCR-style semantic comparison | implemented interim tool | `results/ccr-comparison/` | Local canonical JSON hash, not CCR `ROAPayloadState.hash`. |
| Validator interoperability | measured rejection | `results/validator-probe/` | Routinator 0.15.2, rpki-client 9.8, and FORT 1.6.8 accept RSA and reject ML-DSA-65. |
| Routinator/Krill extension track | implemented harness | `results/routinator-krill/` | Read-only scan and matrix only unless explicit local upstream inputs are configured. |
