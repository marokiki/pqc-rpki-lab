# Primitive Benchmark

> EXPERIMENTAL / NOT FOR PRODUCTION

Core comparison timings are end-to-end OpenSSL CLI wall-clock measurements. Each timed operation includes one process launch. Compare timing values only within the same `comparable_group`; they are not pure cryptographic cycle counts.

| Algorithm | Status | Backend | Timing scope | Keygen ms | Sign ms | Verify ms | Measured signature bytes | Notes | Reason |
|---|---|---|---|---|---|---|---|---|---|
| RSA-2048/SHA-256 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 46.094291 | 6.868458 | 6.022708 | 256 | Current RPKI baseline; SPKI size is an approximate DER value. Timed operations each include one OpenSSL process launch. |  |
| ML-DSA-65 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 6.01375 | 6.162125 | 5.569916 | 3309 | Primary balanced PQC candidate. Timed operations each include one OpenSSL process launch. |  |
| ML-DSA-87 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 6.762083 | 8.078625 | 6.420667 | 4627 | High-assurance candidate with larger objects. Timed operations each include one OpenSSL process launch. |  |
| SLH-DSA-SHAKE-128s | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 52.258666 | 349.318167 | 7.476667 | 7856 | Hash-based diversity candidate; signature size is the main concern. Timed operations each include one OpenSSL process launch. |  |
| SLH-DSA-SHAKE-192s | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 73.02875 | 609.270875 | 7.548375 | 16224 | Conservative diversity candidate with very large signatures. Timed operations each include one OpenSSL process launch. |  |
| P-256/SHA-256 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 5.997583 | 5.946292 | 6.661375 | 72 | Compact classical counterfactual; not the current RFC 6488 RPKI profile. Signature size uses the conservative DER maximum. Timed operations each include one OpenSSL process launch. |  |
| Ed25519 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 5.999167 | 5.742042 | 5.811042 | 64 | Compact classical counterfactual; not the current RFC 6488 RPKI profile. Timed operations each include one OpenSSL process launch. |  |
| ML-DSA-44 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 6.035542 | 6.101292 | 5.80225 | 2420 | Measured comparison excluded from the primary profile by the Category 3 policy floor. Timed operations each include one OpenSSL process launch. |  |
| Falcon-512 | confirmed | oqs-python/liboqs | in-process | 6.172583 | 2.112334 | 0.04275 | 658 | Best size/performance candidate in the 2025 RPKI study; no final RPKI-ready X.509/CMS path. In-process timings are not directly comparable with OpenSSL CLI timings. |  |
| Falcon-1024 | confirmed | oqs-python/liboqs | in-process | 22.525667 | 4.647125 | 0.070458 | 1271 | Category-5 Falcon comparison. In-process timings are not directly comparable with OpenSSL CLI timings. |  |
| MAYO-1 | confirmed | oqs-python/liboqs | in-process | 0.113208 | 0.363709 | 0.087542 | 454 | Multivariate candidate with compact signatures; not standardized. In-process timings are not directly comparable with OpenSSL CLI timings. |  |
| SNOVA-(24,5,4) | confirmed | oqs-python/liboqs | in-process | 0.181334 | 0.514375 | 0.360875 | 248 | Multivariate candidate with very compact signatures; not standardized. In-process timings are not directly comparable with OpenSSL CLI timings. |  |
| HAWK-512 | unsupported | oqs-python/liboqs | in-process |  |  |  |  | Promising lattice candidate retained as metadata-only because liboqs 0.15.0 and OpenSSL 3.6.2 do not provide it. | candidate is not enabled by oqs-python/liboqs |
| RSA-2048+ML-DSA-44 | unsupported | size model only | not measured |  |  |  |  | Component-size sum excluding composite ASN.1 overhead; no local X.509/CMS interoperability evidence. | No local composite signature implementation or interoperability profile |
| P-256+ML-DSA-44 | unsupported | size model only | not measured |  |  |  |  | Component-size sum excluding composite ASN.1 overhead; no local X.509/CMS interoperability evidence. | No local composite signature implementation or interoperability profile |
| P-256+Falcon-512 | unsupported | size model only | not measured |  |  |  |  | Component-size sum excluding composite ASN.1 overhead; Falcon/FN-DSA profile is not final. | No local composite signature implementation or interoperability profile |
