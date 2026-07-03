# Exact 100,000-Operation Composite Component Benchmark

> EXPERIMENTAL / NOT FOR PRODUCTION

Each combination signs the same 32-byte message with both components sequentially; the standalone FN-DSA-512 row signs it once. Verification of a combination succeeds only when both component signatures verify. The byte count is the sum of the largest component signatures observed and excludes composite ASN.1 encoding. This is not an implementation of the LAMPS composite signature format.

| Combination | Status | Operations | Sign total s | Verify total s | Sign us/op | Verify us/op | Component bytes | Sign time/ML-DSA-65 | Verify time/ML-DSA-65 | Bytes/ML-DSA-65 | Reason |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FN-DSA-512 (Falcon-512) | confirmed | 100000 | 10.547208000 | 1.612536000 | 105.472 | 16.125 | 665 | 0.26 | 0.21 | 0.201 |  |
| RSA-2048+P-256 | confirmed | 100000 | 35.317942000 | 4.473800000 | 353.179 | 44.738 | 328 | 0.871 | 0.584 | 0.099 |  |
| RSA-2048+Ed25519 | confirmed | 100000 | 35.634483000 | 5.057551000 | 356.345 | 50.576 | 320 | 0.879 | 0.66 | 0.097 |  |
| RSA-2048+ML-DSA-44 | confirmed | 100000 | 59.198430000 | 5.784879000 | 591.984 | 57.849 | 2676 | 1.46 | 0.755 | 0.809 |  |
| P-256+ML-DSA-44 | confirmed | 100000 | 26.317486000 | 8.391998000 | 263.175 | 83.92 | 2492 | 0.649 | 1.095 | 0.753 |  |
| RSA-2048+ML-DSA-65 | confirmed | 100000 | 74.396603000 | 8.363908000 | 743.966 | 83.639 | 3565 | 1.835 | 1.091 | 1.077 |  |
| P-256+ML-DSA-65 | confirmed | 100000 | 41.756521000 | 10.879306000 | 417.565 | 108.793 | 3381 | 1.03 | 1.419 | 1.022 |  |
| RSA-2048+ML-DSA-87 | confirmed | 100000 | 81.102208000 | 12.706616000 | 811.022 | 127.066 | 4883 | 2.0 | 1.658 | 1.476 |  |
| RSA-2048+FN-DSA-512 | confirmed | 100000 | 44.606447000 | 2.632527000 | 446.064 | 26.325 | 920 | 1.1 | 0.343 | 0.278 |  |
| P-256+ML-DSA-87 | confirmed | 100000 | 49.977078000 | 15.269535000 | 499.771 | 152.695 | 4699 | 1.233 | 1.992 | 1.42 |  |
| P-256+Falcon-512 | confirmed | 100000 | 12.061653000 | 5.082005000 | 120.617 | 50.82 | 737 | 0.298 | 0.663 | 0.223 |  |

## Interpretation

FN-DSA-512 is reported both alone and with RSA-2048 and P-256. P-256+Falcon-512 has the smallest two-component signature total, but Falcon signing dominates its runtime. Within each ML-DSA parameter set, replacing RSA-2048 with P-256 reduces component key and signature bytes and reduces signing time, while RSA-2048 provides faster verification in this implementation. Larger ML-DSA parameter sets progressively increase both runtime and size. No measured combination dominates all others in signing time, verification time, and size simultaneously.

The repository estimator remains separate because certificates contain public keys as well as signatures. Its conservative size model uses standardized maximum component sizes and adds no composite ASN.1 overhead.
