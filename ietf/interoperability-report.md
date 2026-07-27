# Interoperability Report

> EXPERIMENTAL / NOT FOR PRODUCTION

OpenSSL 3.6.2 generated ML-DSA resource-profile CA certificates, EE
certificates, and CRLs. The generic CMS CLI still reports
`CMS_add1_signer:no default digest`, while the CMS API succeeds when SHA-512
is supplied explicitly. Complete pure ML-DSA-65 manifests and ROAs are
therefore generated through the explicit API path and cross-checked against an
independent DER assembler.

Pinned unmodified Routinator, rpki-client, and FORT accept the RSA baseline and
reject pure ML-DSA-65 as unsupported. The experimental rpki-client extension
keeps the same Current Suite-only default. With its explicit experimental
option, it validates pure ML-DSA-65, Composite standalone, and an
RSA-to-Composite mixed tree; each successful fixture produces the same two
VRPs as the RSA baseline.

Negative tests separately reject corrupt component and pure ML-DSA signatures,
component reordering and truncation, unknown OIDs, non-absent parameters,
digest mismatches, certificate and CRL signature failures, invalid
certification paths, and manifest hash mismatches. Independent RP
interoperability and production-scale repository transport remain open.
