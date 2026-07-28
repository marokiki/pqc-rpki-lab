# Implementation Status

> EXPERIMENTAL / NOT FOR PRODUCTION

This note is maintained in the style of an RFC 7942 implementation-status section, but it is not yet ready for direct publication.

| Component | Status | Evidence |
|---|---|---|
| Algorithm metadata | implemented | `src/pqc_rpki_lab/algorithms.py` |
| Primitive benchmark | implemented | `results/primitive-bench.*` |
| Synthetic repository estimator | implemented | `results/repository-impact.*` |
| Migration scenario scaffold | implemented | `results/migration-scenarios.*` |
| VRP equivalence fixture checker | implemented | `tools/vrp_equivalence.py`, tests |
| Validator probing | implemented baseline | `results/validator-probe/` |
| Real cache profile | one aggregate snapshot | 550,210 objects across 54,960 publication points; ARIN unavailable; no source objects published |
| RFC-profiled PQC CA/EE certificates and CRLs | confirmed | `results/object-generation-feasibility.*` |
| Pure ML-DSA-65 CMS SignedData, MFT, and ROA | implemented | `testdata/ml-dsa-65/`, `results/rpki-objects/` |
| Composite CMS SignedData, MFT, and ROA | implemented | `testdata/composite-mldsa65-p256/`, `results/composite-e2e/` |
| Experimental rpki-client validation | implemented | pure ML-DSA-65, Composite standalone, and mixed-tree fixtures |
| Experimental Routinator validation | implemented | second RP processing path; all four scenarios and 15 negative cases |
| Operational negative validation | implemented | seven expired, revoked, stale, and missing-publication cases in both RPs |
| Experimental Krill lifecycle | implemented | Composite issuance, publication, one-ROA update, and RSA rollback |
| Repeated scaled Krill validation | implemented through 1,000 ROAs | `results/scaled-corpus/krill-repeated-summary.json` |
| Multi-publication-point topology | implemented at 100 child CAs | `results/scaled-corpus/topology-pilot-summary.json` |
| RP cache regimes | implemented at 1,000 ROAs | 30 fresh, unchanged, and one-ROA-update repetitions per RP |
| RP-produced CCR state comparison | implemented | actual DER hashes from rpki-client CCR output |
| Independent cryptographic implementation | not implemented | generator, both RPs, and Krill share one OpenSSL/Composite provider |

Public-cache topology is aggregate-only, and controlled scale runs do not
represent production repository or network performance. Complete pure
ML-DSA-65 and selected Composite objects are accepted by experimental
rpki-client and Routinator paths. Krill exercises issuance, update,
publication, and rollback. Both RPs and Krill share the same OpenSSL/provider
backend, so the result is not independent cryptographic interoperability
evidence.
