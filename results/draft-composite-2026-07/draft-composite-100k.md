# Composite ML-DSA Benchmark (draft revision 19)

> EXPERIMENTAL / NOT FOR PRODUCTION

This benchmark implements `draft-ietf-lamps-pq-composite-sigs-19`. It constructs `M'` from the fixed Prefix, per-variant Label, one-byte application-context length, empty application context, and the specified message pre-hash. The ML-DSA component signs in pure mode with the Label supplied as its ML-DSA context. The traditional component signs the same `M'`. Verification succeeds only when both components verify. The signature value is the raw concatenation `mldsaSig || tradSig`.

`ML-DSA-87 + ECDSA P-256` is not defined by revision 19, so the Category-5 row uses ECDSA P-384.

| Composite variant | Operations | Sign total s | Verify total s | Raw public key bytes | Mean signature bytes | Repository/RSA | Status |
|---|---|---|---|---|---|---|---|
| ML-DSA-44 + ECDSA P-256 | 100000 | 26.049569 | 8.300573 | 1377 | 2491.000 | 3.1584 | confirmed |
| ML-DSA-65 + ECDSA P-256 | 100000 | 45.611158 | 11.933963 | 2017 | 3379.994 | 4.0915 | confirmed |
| ML-DSA-87 + ECDSA P-384 | 100000 | 59.410493 | 32.772383 | 2689 | 4729.998 | 5.3965 | confirmed |

## Scope and limitations

The timing includes construction of the message representative, both component operations, and raw signature concatenation. It excludes key generation, file I/O, X.509, CMS, validator processing, and HSM latency. Public-key and signature sizes are the raw concatenations defined by revision 19. ECDSA signatures use variable-length DER encoding, so the result records minimum, maximum, and mean signature lengths.

Repository ratios are first-order model outputs using the measured raw key and mean signature lengths. They are not full-repository measurements and do not include any future RPKI-specific X.509 or CMS profile overhead.
