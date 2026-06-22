# Exact 100,000-Operation Composite Component Benchmark

> EXPERIMENTAL / NOT FOR PRODUCTION

Each operation signs the same 32-byte message with both components sequentially. Verification succeeds only when both component signatures verify. The byte count is the sum of the largest component signatures observed and excludes composite ASN.1 encoding. This is not an implementation of the LAMPS composite signature format.

| Combination | Status | Operations | Sign total s | Verify total s | Sign us/op | Verify us/op | Component bytes | Sign time/ML-DSA-65 | Verify time/ML-DSA-65 | Bytes/ML-DSA-65 | Reason |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RSA-2048+ML-DSA-44 | confirmed | 100000 | 58.720045000 | 5.788017000 | 587.2 | 57.88 | 2676 | 1.462 | 0.787 | 0.809 |  |
| P-256+ML-DSA-44 | confirmed | 100000 | 26.253240000 | 8.309788000 | 262.532 | 83.098 | 2492 | 0.653 | 1.13 | 0.753 |  |
| P-256+Falcon-512 | confirmed | 100000 | 207.549013000 | 5.474383000 | 2075.49 | 54.744 | 736 | 5.166 | 0.745 | 0.222 |  |

## Interpretation

P-256+Falcon-512 has the smallest component-signature total, but Falcon signing dominates its runtime. P-256+ML-DSA-44 has the lowest signing time among the measured combinations. RSA-2048+ML-DSA-44 is smaller and verifies faster than pure ML-DSA-65 in this run, but signs more slowly. No measured combination dominates pure ML-DSA-65 in signing time, verification time, and size simultaneously.

The repository estimator remains separate because certificates contain public keys as well as signatures. Its conservative size model uses standardized maximum component sizes and adds no composite ASN.1 overhead.
