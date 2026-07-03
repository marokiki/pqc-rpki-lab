# Existing Implementations

| Layer | Preferred implementation | Current use |
|---|---|---|
| PQC primitives | liboqs / oqs-python | Conditional benchmark |
| Provider/PKIX/CMS | OpenSSL 3 default provider | ML-DSA certificates, CRLs, CMS API signing, and local verification |
| CA/publication | Krill | Future isolated repository |
| Validation | Routinator, rpki-client, FORT | Pinned unmodified container repository probes |
| Router consumers | BIRD/OpenBGPD | VRP consumers only |

The default run performs no network access and never uses production TALs or
credentials. Cryptographic primitives and X.509 generation/verification stay
in OpenSSL. The small CMS DER assembler is an encoding reference and
cross-check, not a replacement cryptographic or path-validation implementation.
RRDP, rsync, RTR, and validator logic are not reimplemented.

Routinator and Krill experiments are opt-in through explicit environment
variables. Suggested local upstream checkouts live under ignored
`local/upstream/`; upstream source and work-in-progress patches are not copied
into this public repository.
