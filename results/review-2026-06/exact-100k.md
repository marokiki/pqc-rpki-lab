# Exact 100,000-Operation Signature Benchmark

> EXPERIMENTAL / NOT FOR PRODUCTION

Each algorithm uses one generated key pair and performs exactly 100,000 EVP signing operations followed by exactly 100,000 verification operations over the same 32-byte message. The timed loops include EVP context initialization but exclude key generation, process startup, RPKI object construction, file I/O, and HSM latency.

| Algorithm | Status | Operations | Sign total s | Verify total s | Sign us/op | Verify us/op | Sign time/RSA | Verify time/RSA | Last signature bytes | Reason |
|---|---|---|---|---|---|---|---|---|---|---|
| RSA-2048/SHA-256 | confirmed | 100000 | 34.327696000 | 0.986373000 | 343.277 | 9.864 | 1.0 | 1.0 | 256 |  |
| P-256/SHA-256 | confirmed | 100000 | 1.268314000 | 3.477508000 | 12.683 | 34.775 | 0.037 | 3.526 | 71 |  |
| Ed25519 | confirmed | 100000 | 1.663721000 | 4.046193000 | 16.637 | 40.462 | 0.048 | 4.102 | 64 |  |
| ML-DSA-44 | confirmed | 100000 | 25.081317000 | 4.958273000 | 250.813 | 49.583 | 0.731 | 5.027 | 2420 |  |
| ML-DSA-65 | confirmed | 100000 | 40.543142000 | 7.665719000 | 405.431 | 76.657 | 1.181 | 7.772 | 3309 |  |
| ML-DSA-87 | confirmed | 100000 | 47.943284000 | 11.742680000 | 479.433 | 117.427 | 1.397 | 11.905 | 4627 |  |

## Interpretation

The compact classical references have the lowest signing time and signature size, but they do not provide post-quantum security and are not the current RFC 6488 repository profile. ML-DSA-44 has the best measured time and size among the standardized ML-DSA parameter sets. ML-DSA-65 and ML-DSA-87 progressively increase verification time and signature size; this run does not establish an operational reason to select Category 5.

Verification, rather than signing, is the repeated RP-side operation. Absolute verification time for 100,000 operations remains below 12 seconds for all measured algorithms on this host, but repository-wide cost also depends on object count, parallelism, caching, message size, and validator implementation. These primitive values are not complete RPKI validation times.

Composite signatures were not measured because no local composite EVP implementation was available. A sequential composition would at least incur both component operations plus encoding and dispatch overhead; component-time sums are estimates, not composite benchmark results.

This is one run on one host with one key per algorithm and no confidence interval. A publication-grade comparison should repeat the complete run, randomize algorithm order, record thermal and CPU state, and add complete RFC 6488 object and validator measurements.
