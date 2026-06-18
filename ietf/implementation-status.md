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
| Validator probing | partial | installed validators: none; unavailable: Routinator, rpki-client, FORT |
| Real cache measurement | input-dependent | requires `PQC_RPKI_CACHE` |
| RFC-profiled PQC CA/EE certificates and CRLs | confirmed | `results/object-generation-feasibility.*` |
| PQC CMS SignedData, MFT, and ROA | unsupported | OpenSSL CMS failure and dependency classification recorded |
| Multi-validator PQC object validation | not implemented | depends on generated objects |

Current repository-size results are synthetic or literature-calibrated estimates. ML-DSA certificates and CRLs were generated with OpenSSL, but MFT/ROA generation remains blocked at the CMS/payload-generator layer. No independent validator has accepted a PQC RPKI object in this repository.
