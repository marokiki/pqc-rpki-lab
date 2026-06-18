# Interoperability Report

> EXPERIMENTAL / NOT FOR PRODUCTION

OpenSSL generated ML-DSA resource-profile CA certificates, EE certificates, and CRLs. OpenSSL CMS rejected ML-DSA signing with `CMS_add1_signer:no default digest`; therefore MFT and ROA generation did not proceed. Existing validator executables are probed without network access.

Required next phases:

1. RSA baseline fixture accepted by Routinator, rpki-client, and FORT.
2. ML-DSA-65 fixture generated with RFC 9881/RFC 9882 encodings.
3. Validator behavior recorded for unknown/unsupported PQC algorithms.
4. VRP equivalence checked between RSA and PQC-equivalent branches.
5. Negative tests for inconsistent ROA, stale manifest, expired EE certificate, missing CRL, and invalid signedAttrs.
