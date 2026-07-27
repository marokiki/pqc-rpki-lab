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
| Experimental rpki-client validation | implemented | pure ML-DSA-65, Composite standalone, and mixed-tree fixtures produce two VRPs in experimental mode |
| Experimental Routinator validation | implemented | a second RP parser and validation path produces the same two VRPs for all four scenarios and rejects all 15 negative cases |
| Experimental Krill issuance | implemented at small scale | an RSA testbed parent issues a Composite child; Krill publishes its CRL, Manifest, and ROA, then rolls the child back to RSA |
| Scaled Krill issuance | implemented at 1,000 ROAs | both experimental RPs produce 1,000 VRPs from Composite state; all modes produce the same 1,000 VRPs after RSA rollback |
| Independent cryptographic implementation | not implemented | both experimental RPs and the generator use the same pinned OpenSSL and Composite provider |

Current repository-scale comparisons remain synthetic or
literature-calibrated estimates. One public-cache snapshot has been reduced to
aggregate topology and size inputs, but has not yet been re-signed as a
four-suite corpus. Complete small-scale pure ML-DSA-65 and Composite RPKI objects are
generated and accepted by experimental rpki-client and Routinator extensions.
Krill 0.16.0 was also extended in the isolated test environment to exercise
CA issuance, publication, and rollback. The result does not establish
production readiness, protocol interoperability with another CA, or
repository-scale performance. A 1,000-ROA single-child run established
Composite validation and RSA rollback correctness for that object count, but
is not representative of global RPKI topology or update behavior.
The RP processing implementations are distinct, but their cryptographic
backend is shared; this is not independent cryptographic interoperability
evidence.
