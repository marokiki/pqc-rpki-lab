# Existing Implementations

| Layer | Preferred implementation | Current use |
|---|---|---|
| PQC primitives | liboqs / oqs-python | Conditional benchmark |
| Provider/PKIX/CMS | OpenSSL 3 / oqs-provider | Future object experiments |
| CA/publication | Krill | Future isolated repository |
| Validation | Routinator, rpki-client, FORT | Version/capability probes |
| Router consumers | BIRD/OpenBGPD | VRP consumers only |

The default run performs no network access and never uses production TALs or credentials. Do not reimplement ML-DSA, SLH-DSA, ASN.1 DER, X.509 path validation, CMS SignedData, RRDP, rsync, or RTR from scratch.
