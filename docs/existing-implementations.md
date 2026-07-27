# Existing Implementations

| Layer | Preferred implementation | Current use |
|---|---|---|
| PQC primitives | liboqs / oqs-python | Conditional benchmark |
| Provider/PKIX/CMS | OpenSSL 3 default and Composite providers | ML-DSA and Composite certificates, CRLs, CMS signing, and local verification |
| CA/publication | Experimental Krill 0.16.0 patch | Isolated RSA-parent to Composite-child issuance, publication, and RSA rollback |
| Validation | Routinator, rpki-client, FORT | Unmodified rejection probes plus experimental rpki-client and Routinator E2E paths |
| Router consumers | BIRD/OpenBGPD | VRP consumers only |

The default run performs no network access and never uses production TALs or
credentials. Cryptographic primitives and X.509 generation/verification stay
in OpenSSL. The small CMS DER assembler is an encoding reference and
cross-check, not a replacement cryptographic or path-validation implementation.
RRDP, rsync, and RTR are not reimplemented. The experimental rpki-client
patch changes algorithm policy and delegates cryptography to OpenSSL; it is not
a new validator implementation.

Routinator and Krill experiments are opt-in. Suggested local upstream
checkouts live under ignored `local/upstream/`; upstream source and CA state
stay local while reproducible, public-safe experimental patches and sanitized
results are stored in tracked paths.
