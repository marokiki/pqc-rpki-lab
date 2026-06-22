# Primitive Benchmark

> EXPERIMENTAL / NOT FOR PRODUCTION

Core comparison timings are end-to-end OpenSSL CLI wall-clock measurements. Each timed operation includes one process launch. Compare timing values only within the same `comparable_group`; they are not pure cryptographic cycle counts.

| Algorithm | Status | Backend | Timing scope | Keygen ms | Sign ms | Verify ms | Measured signature bytes | Notes | Reason |
|---|---|---|---|---|---|---|---|---|---|
| RSA-2048/SHA-256 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 17.483958 | 7.757875 | 6.901916 | 256 | Current RPKI baseline; SPKI size is an approximate DER value. Timed operations each include one OpenSSL process launch. |  |
| ML-DSA-65 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 6.514084 | 6.887041 | 6.933208 | 3309 | Primary balanced PQC candidate. Timed operations each include one OpenSSL process launch. |  |
| ML-DSA-87 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 6.348625 | 6.552125 | 5.71175 | 4627 | High-assurance candidate with larger objects. Timed operations each include one OpenSSL process launch. |  |
| SLH-DSA-SHAKE-128s | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 51.242084 | 354.469209 | 7.586125 | 7856 | Hash-based diversity candidate; signature size is the main concern. Timed operations each include one OpenSSL process launch. |  |
| SLH-DSA-SHAKE-192s | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 73.726667 | 607.893375 | 7.696959 | 16224 | Conservative diversity candidate with very large signatures. Timed operations each include one OpenSSL process launch. |  |
| P-256/SHA-256 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 6.010125 | 5.970834 | 5.676791 | 71 | Compact classical counterfactual; not the current RFC 6488 RPKI profile. Signature size uses the conservative DER maximum. Timed operations each include one OpenSSL process launch. |  |
| Ed25519 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 6.303667 | 5.693125 | 5.842666 | 64 | Compact classical counterfactual; not the current RFC 6488 RPKI profile. Timed operations each include one OpenSSL process launch. |  |
| ML-DSA-44 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 5.878083 | 6.046667 | 5.746167 | 2420 | Measured comparison excluded from the primary profile by the Category 3 policy floor. Timed operations each include one OpenSSL process launch. |  |
| Falcon-512 | confirmed | oqs-python/liboqs | in-process | 6.635791 | 2.124541 | 0.04025 | 658 | Best size/performance candidate in the 2025 RPKI study; no final RPKI-ready X.509/CMS path. In-process timings are not directly comparable with OpenSSL CLI timings. |  |
| Falcon-1024 | confirmed | oqs-python/liboqs | in-process | 15.45125 | 4.834083 | 0.086167 | 1270 | Category-5 Falcon comparison. In-process timings are not directly comparable with OpenSSL CLI timings. |  |
| MAYO-1 | confirmed | oqs-python/liboqs | in-process | 0.114584 | 0.361583 | 0.086458 | 454 | Multivariate candidate with compact signatures; not standardized. In-process timings are not directly comparable with OpenSSL CLI timings. |  |
| SNOVA-(24,5,4) | confirmed | oqs-python/liboqs | in-process | 0.179458 | 0.508959 | 0.350333 | 248 | Multivariate candidate with very compact signatures; not standardized. In-process timings are not directly comparable with OpenSSL CLI timings. |  |
| HAWK-512 | unsupported | oqs-python/liboqs | in-process |  |  |  |  | Promising lattice candidate retained as metadata-only because liboqs 0.15.0 and OpenSSL 3.6.2 do not provide it. | candidate is not enabled by oqs-python/liboqs |
| RSA-2048+ML-DSA-44 | unsupported | size model only | not measured |  |  |  |  | Component-size sum excluding composite ASN.1 overhead; no local X.509/CMS interoperability evidence. | No local composite signature implementation or interoperability profile |
| P-256+ML-DSA-44 | unsupported | size model only | not measured |  |  |  |  | Component-size sum excluding composite ASN.1 overhead; no local X.509/CMS interoperability evidence. | No local composite signature implementation or interoperability profile |
| P-256+Falcon-512 | unsupported | size model only | not measured |  |  |  |  | Component-size sum excluding composite ASN.1 overhead; Falcon/FN-DSA profile is not final. | No local composite signature implementation or interoperability profile |
