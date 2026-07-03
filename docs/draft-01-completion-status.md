# Draft-01 Completion Status

> EXPERIMENTAL / NOT FOR PRODUCTION

This repository now contains the public-safe implementation and evidence that
can be produced without vendoring Routinator/Krill, using production TALs, or
committing private key material.

## Completed in public repo

| Area | Status | Evidence |
|---|---|---|
| Public/private repository boundary | complete | `make pre-publication` |
| Primitive and exact-count benchmarks | complete | `results/primitive-bench.*`, `results/review-2026-06/` |
| Composite component benchmark | complete with limitation | `results/review-2026-06/composite-100k.*` |
| P-256, Ed25519, ML-DSA-44, and experimental Falcon certificate/CRL sizes | complete | `results/generated-object-sizes.csv` |
| RSA `.mft` and `.roa` CMS fixtures | complete | `results/rpki-objects/`, `testdata/rsa/` |
| ML-DSA-44/65/87 cert, CRL, and eContent fixtures | complete | `testdata/ml-dsa-*/` |
| ML-DSA CMS API probe | complete | `results/cms-probe/` |
| ML-DSA-65 `.mft` and `.roa` CMS fixtures | complete | `results/cms-generation/`, `testdata/ml-dsa-65/` |
| Manual DER reference and profile verifier | complete | `src/pqc_rpki_lab/cms.py`, `tests/test_cms.py` |
| Local DER/CMS validation | complete | `results/local-validation/` |
| Synthetic key-roll model | complete | `results/key-roll/` |
| Mixed-tree model | complete as synthetic fixture | `results/mixed-tree/` |
| CCR-style interim comparison | complete with limitation | `results/ccr-comparison/` |
| Routinator/Krill extension map and runners | complete as harness | `results/routinator-krill/` |
| Unmodified validator rejection probe | complete | `results/validator-probe/` |
| Repeated message-size benchmark | complete at 1,000 operations per repetition | `results/message-sweep/` |

## Not claimed as complete

| Area | Current state | Required external input or blocker |
|---|---|---|
| ML-DSA-44/87 and SLH-DSA CMS objects | not implemented | The generic CLI still reports `CMS_add1_signer:no default digest`; only ML-DSA-65 has an explicit API path. |
| Routinator ML-DSA acceptance | rejected by unmodified release | Routinator 0.15.2 rejects the ML-DSA TAL public key; extension work is required. |
| Krill publication generation | not claimed | Requires a Krill binary or source checkout configured via env vars. |
| Real CCR `ROAPayloadState.hash` | not claimed | Requires validator/CCR output tooling. |
| Selected Composite ML-DSA suite | not implemented | Requires standards-compliant X.509 and CMS composite generation and validation. |
| LAMPS composite interoperability | not claimed | Requires the generated composite repository and an extended validator. |

RSA and pure ML-DSA-65 objects are implemented and locally verified, but they
are component-level evidence rather than an implementation of the selected
composite suite. The three unmodified validators accept the RSA baseline and
reject ML-DSA-65, so composite validator support remains an explicit extension
requirement rather than an untested assumption.
