# Exact 100,000-Operation Signature Benchmark

> EXPERIMENTAL / NOT FOR PRODUCTION

Each algorithm uses one generated key pair and performs exactly 100,000 EVP signing operations followed by exactly 100,000 verification operations over the same 32-byte message. The timed loops include EVP context initialization but exclude key generation, process startup, RPKI object construction, file I/O, and HSM latency.

| Algorithm | Status | Operations | Sign total s | Verify total s | Sign us/op | Verify us/op | Sign time/RSA | Verify time/RSA | Last signature bytes | Reason |
|---|---|---|---|---|---|---|---|---|---|---|
| RSA-2048/SHA-256 | confirmed | 100000 | 37.242536000 | 0.985560000 | 372.425 | 9.856 | 1.0 | 1.0 | 256 |  |
| P-256/SHA-256 | confirmed | 100000 | 1.368756000 | 3.579209000 | 13.688 | 35.792 | 0.037 | 3.632 | 72 |  |
| Ed25519 | confirmed | 100000 | 1.673355000 | 4.037800000 | 16.734 | 40.378 | 0.045 | 4.097 | 64 |  |
| ML-DSA-44 | confirmed | 100000 | 24.908217000 | 4.792310000 | 249.082 | 47.923 | 0.669 | 4.863 | 2420 |  |
| ML-DSA-65 | confirmed | 100000 | 40.175448000 | 7.352204000 | 401.754 | 73.522 | 1.079 | 7.46 | 3309 |  |
| ML-DSA-87 | confirmed | 100000 | 49.886808000 | 11.545769000 | 498.868 | 115.458 | 1.34 | 11.715 | 4627 |  |

## Interpretation

The compact classical references have the lowest signing time and signature size, but they do not provide post-quantum security and are not the current RFC 6488 repository profile. ML-DSA-44 has the best measured time and size among the standardized ML-DSA parameter sets. ML-DSA-65 and ML-DSA-87 progressively increase verification time and signature size; this run does not establish an operational reason to select Category 5.

Verification, rather than signing, is the repeated RP-side operation. Absolute verification time for 100,000 operations remains below 12 seconds for all measured algorithms on this host, but repository-wide cost also depends on object count, parallelism, caching, message size, and validator implementation. These primitive values are not complete RPKI validation times.

Composite signatures were not measured because no local composite EVP implementation was available. A sequential composition would at least incur both component operations plus encoding and dispatch overhead; component-time sums are estimates, not composite benchmark results.

This is one run on one host with one key per algorithm and no confidence interval. A publication-grade comparison should repeat the complete run, randomize algorithm order, record thermal and CPU state, and add complete RFC 6488 object and validator measurements.
