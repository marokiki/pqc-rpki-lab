# CCR-Style Semantic Comparison

> EXPERIMENTAL / NOT FOR PRODUCTION

This interim workflow compares normalized VRP semantics with a local canonical JSON hash. It is not `draft-ietf-sidrops-rpki-ccr` output and must not be reported as CCR `ROAPayloadState.hash` equivalence.

| Equivalent | Baseline Count | Candidate Count | Only Baseline | Only Candidate | Provenance Differences | Method |
|---|---|---|---|---|---|---|
| True | 2 | 2 | 0 | 0 | 2 | sha256-canonical-json-v1-not-ccr |
