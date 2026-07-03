# Interoperability Plan

> EXPERIMENTAL / NOT FOR PRODUCTION

Interoperability requires more than ASN.1 parsing. A public result must state
which layer succeeded:

| Layer | Required evidence |
|---|---|
| Parser compatibility | Tool parses DER without syntax errors. |
| Signature verification | Certificate, CRL, or CMS signature verifies with the expected public key. |
| Certification path | Trust anchor to product signer chain is complete. |
| Manifest and CRL checks | File hashes, freshness, and revocation state are accepted. |
| Validator acceptance | A real RPKI validator accepts the repository objects. |
| Router-visible semantics | VRP output is equivalent to the baseline. |

The default workflow records missing validators as `unsupported`, not as
algorithm failures. Synthetic mixed-tree and CCR-style outputs are useful
pre-validation evidence but must not be reported as validator interoperability.

The repository now includes complete RSA and ML-DSA-65 Manifest and ROA
objects. In an isolated local-rsync experiment, Routinator 0.15.2, rpki-client
9.8, and FORT 1.6.8 all produced VRPs from the RSA baseline and rejected the
ML-DSA-65 repository. The result establishes current rejection behavior, not
PQC interoperability.

## Routinator and Krill track

Routinator and Krill are treated as the primary implementation targets for a
production-like interoperability experiment: Routinator for relying-party
validation behavior, and Krill for CA/publication behavior. The public repo
contains only scanners, runners, fixtures, and result summaries. Upstream
checkouts and work-in-progress patches remain local-only.

Use:

```sh
make routinator-krill-scan
make routinator-krill-interop
```

Both commands are safe when no upstream checkout or binary is configured. They
emit `skipped` or `unsupported` results rather than using production TALs,
network fetches, or hidden local state.
