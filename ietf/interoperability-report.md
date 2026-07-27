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

An experimental Routinator 0.15.2/rpki-rs 0.19.3 extension independently
processes the repository, certificate path, CRL, CMS, manifest, ROA, and VRP
output. In experimental mode it produces the same two VRPs for the RSA, pure
ML-DSA-65, Composite standalone, and mixed-tree fixtures. In default mode it
continues to reject the experimental suites. Its cryptographic operations use
the same OpenSSL/provider backend as the generator, so this is second-RP
evidence but not independent cryptographic implementation evidence.

Negative tests in both experimental RPs separately reject corrupt component and pure ML-DSA signatures,
component reordering and truncation, unknown OIDs, non-absent parameters,
digest mismatches, certificate and CRL signature failures, invalid
certification paths, and manifest hash mismatches. The Routinator work also
exposed and fixed a long-form DER length bug in rpki-rs signed-attribute
reconstruction when the SHA-512 attributes exceeded 127 octets.

An experimental Krill 0.16.0 extension uses the same patched rpki-rs and
OpenSSL/provider backend to create a Composite child below an RSA testbed
parent. The child publishes its CRL, Manifest, and one ROA. Experimental
rpki-client and Routinator both derive the expected VRP; their default modes
reject that phase. Krill then performs a child key roll back to RSA, after
which both default and experimental RP modes derive the expected VRP. This
demonstrates an isolated CA lifecycle path, but not independent cryptography,
production protocol operation, or repository-scale transport.
