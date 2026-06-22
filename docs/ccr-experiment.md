# CCR Experiment Design

The comparison target is equality of validated VRP sets, not equality of certificates, object hashes, repository paths, or trust-anchor keys.

1. Build RSA and PQC repositories with the same ROA payloads and a fixed validation time.
2. Validate each repository with the same RP implementation and policy.
3. Export a CCR for each validated cache.
4. Verify each CCR state hash and compare `ROAPayloadState.hash`.
5. If the hashes differ, decode `ROAPayloadState.rps` and report VRPs present in only one result.
6. Report trust-anchor and source attribution separately.

`tools/vrp_equivalence.py` currently computes a stable SHA-256 hash over canonical JSON. This is an interim test helper, not the DER encoding or hash defined by `draft-ietf-sidrops-rpki-ccr`. A result produced by that helper MUST NOT be labelled a CCR hash.

Real evidence requires complete RSA and PQC RFC 6488 repositories, validator support, and CCR export tooling. Those dependencies are currently unsupported.
