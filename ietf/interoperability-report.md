# Interoperability Report

> EXPERIMENTAL / NOT FOR PRODUCTION

OpenSSL 3.6.2 generated ML-DSA resource-profile CA certificates, EE
certificates, and CRLs. The generic CMS CLI still reports
`CMS_add1_signer:no default digest`, while the CMS API succeeds when SHA-512
is supplied explicitly. Complete pure ML-DSA-65 Manifests and ROAs are
generated through that explicit API path and cross-checked against a small DER
encoding reference. The selected ML-DSA-65 + P-256 Composite suite also
produces complete CA/EE certificates, CRLs, Manifests, and ROAs.

Pinned unmodified Routinator, rpki-client, and FORT accept RSA and reject the
experimental suites. Experimental rpki-client and Routinator paths accept
RSA, pure ML-DSA-65, Composite standalone, and RSA-to-Composite mixed trees
with equal VRP sets. The RP processing paths are distinct, but their
cryptographic operations share the same OpenSSL/provider backend.

Both RPs reject 15 cryptographic/profile negative cases and seven operational
repository failures. The latter cover expired or revoked objects, stale
CRL/Manifest state, and missing publication objects. A 100-child topology
pilot retains 99 VRPs after one publication branch is removed.

Experimental Krill issues a Composite child, publishes its CRL, Manifest, and
ROAs, replaces one ROA, and rolls the child back to RSA. Repeated controlled
measurements extend through 1,000 ROAs and compare fresh, unchanged, and
one-ROA-update RP states. These local-rsync results do not establish
independent cryptographic interoperability, production protocol operation,
or global-repository performance.
