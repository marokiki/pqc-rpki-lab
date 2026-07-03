# Mixed-Tree Fixture

> EXPERIMENTAL / NOT FOR PRODUCTION

This is a public synthetic model for CA-boundary algorithm transitions. It is not validator interoperability evidence and contains no private keys.

## Certificates

| Name | Issuer | SPKI | Issuer Signature |
|---|---|---|---|
| rsa-ta | self | RSA-2048 | RSA-2048/SHA-256 |
| mldsa-child-ca | rsa-ta | ML-DSA-65 | RSA-2048/SHA-256 |
| roa-ee | mldsa-child-ca | ML-DSA-65 | ML-DSA-65 |

## Products

| Path | Type | Issuer | Signature | Scope Key |
|---|---|---|---|---|
| child/manifest.mft | Manifest | mldsa-child-ca | ML-DSA-65 | mldsa-child-key |
| child/ca.crl | CRL | mldsa-child-ca | ML-DSA-65 | mldsa-child-key |
| child/route.roa | ROA | roa-ee | ML-DSA-65 | mldsa-child-key |

Validation: `True`.
