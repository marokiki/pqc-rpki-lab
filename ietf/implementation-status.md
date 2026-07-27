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
| Real cache measurement | input-dependent | requires `PQC_RPKI_CACHE` |
| RFC-profiled PQC CA/EE certificates and CRLs | confirmed | `results/object-generation-feasibility.*` |
| Pure ML-DSA-65 CMS SignedData, MFT, and ROA | implemented | `testdata/ml-dsa-65/`, `results/rpki-objects/` |
| Composite CMS SignedData, MFT, and ROA | implemented | `testdata/composite-mldsa65-p256/`, `results/composite-e2e/` |
| Experimental rpki-client validation | implemented | pure ML-DSA-65, Composite standalone, and mixed-tree fixtures produce two VRPs in experimental mode |
| Independent multi-validator PQC acceptance | not implemented | unmodified Routinator, rpki-client, and FORT reject the unsupported suite |

Current repository-scale results remain synthetic or literature-calibrated
estimates. Complete small-scale pure ML-DSA-65 and Composite RPKI objects are
generated and accepted by the experimental rpki-client extension. This is one
local implementation path, not independent interoperability evidence.
