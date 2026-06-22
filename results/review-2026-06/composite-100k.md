# Exact 100,000-Operation Composite Component Benchmark

> EXPERIMENTAL / NOT FOR PRODUCTION

Each operation signs the same 32-byte message with both components sequentially. Verification succeeds only when both component signatures verify. The byte count is the sum of the largest component signatures observed and excludes composite ASN.1 encoding. This is not an implementation of the LAMPS composite signature format.

| Combination | Status | Operations | Sign total s | Verify total s | Sign us/op | Verify us/op | Component bytes | Sign time/ML-DSA-65 | Verify time/ML-DSA-65 | Bytes/ML-DSA-65 | Reason |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RSA-2048+ML-DSA-44 | confirmed | 100000 | 59.283588000 | 6.398635000 | 592.836 | 63.986 | 2676 | 1.476 | 0.87 | 0.809 |  |
| P-256+ML-DSA-44 | confirmed | 100000 | 26.938006000 | 8.463775000 | 269.38 | 84.638 | 2492 | 0.671 | 1.151 | 0.753 |  |
| RSA-2048+ML-DSA-65 | confirmed | 100000 | 74.359259000 | 8.351363000 | 743.593 | 83.514 | 3565 | 1.851 | 1.136 | 1.077 |  |
| P-256+ML-DSA-65 | confirmed | 100000 | 42.234073000 | 11.275192000 | 422.341 | 112.752 | 3381 | 1.051 | 1.534 | 1.022 |  |
| RSA-2048+ML-DSA-87 | confirmed | 100000 | 81.854859000 | 12.620553000 | 818.549 | 126.206 | 4883 | 2.037 | 1.717 | 1.476 |  |
| P-256+ML-DSA-87 | confirmed | 100000 | 49.750940000 | 15.382402000 | 497.509 | 153.824 | 4699 | 1.238 | 2.092 | 1.42 |  |
| P-256+Falcon-512 | confirmed | 100000 | 215.113181000 | 5.473413000 | 2151.132 | 54.734 | 737 | 5.354 | 0.744 | 0.223 |  |

## Interpretation

P-256+Falcon-512 has the smallest component-signature total, but Falcon signing dominates its runtime. Within each ML-DSA parameter set, replacing RSA-2048 with P-256 reduces component key and signature bytes and reduces signing time, while RSA-2048 provides faster verification in this implementation. Larger ML-DSA parameter sets progressively increase both runtime and size. No measured combination dominates all others in signing time, verification time, and size simultaneously.

The repository estimator remains separate because certificates contain public keys as well as signatures. Its conservative size model uses standardized maximum component sizes and adds no composite ASN.1 overhead.
