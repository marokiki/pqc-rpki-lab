# Primitive Benchmark

> EXPERIMENTAL / NOT FOR PRODUCTION

Core comparison timings are end-to-end OpenSSL CLI wall-clock measurements. Each timed operation includes one process launch. Compare timing values only within the same `comparable_group`; they are not pure cryptographic cycle counts.

| Algorithm | Status | Backend | Timing scope | Keygen ms | Sign ms | Verify ms | Measured signature bytes | Notes | Reason |
|---|---|---|---|---|---|---|---|---|---|
| RSA-2048/SHA-256 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 19.775667 | 6.171625 | 4.784542 | 256 | Current RPKI baseline; SPKI size is an approximate DER value. Timed operations each include one OpenSSL process launch. |  |
| ML-DSA-65 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 5.156125 | 5.008583 | 4.452875 | 3309 | Primary balanced PQC candidate. Timed operations each include one OpenSSL process launch. |  |
| ML-DSA-87 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 4.794208 | 4.931292 | 4.365125 | 4627 | High-assurance candidate with larger objects. Timed operations each include one OpenSSL process launch. |  |
| SLH-DSA-SHAKE-128s | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 50.303875 | 356.297333 | 5.456125 | 7856 | Hash-based diversity candidate; signature size is the main concern. Timed operations each include one OpenSSL process launch. |  |
| SLH-DSA-SHAKE-192s | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 71.943541 | 616.289666 | 5.7625 | 16224 | Conservative diversity candidate with very large signatures. Timed operations each include one OpenSSL process launch. |  |
| ML-DSA-44 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 5.166291 | 5.459542 | 4.591084 | 2420 | Measured comparison excluded from the primary profile by the Category 3 policy floor. Timed operations each include one OpenSSL process launch. |  |
| Falcon-512 | unsupported | oqs-python/liboqs | in-process |  |  |  |  | Best size/performance candidate in the 2025 RPKI study; no final RPKI-ready X.509/CMS path. | oqs import failed: No module named 'oqs' |
| Falcon-1024 | unsupported | oqs-python/liboqs | in-process |  |  |  |  | Category-5 Falcon comparison. | oqs import failed: No module named 'oqs' |
| MAYO-1 | unsupported | oqs-python/liboqs | in-process |  |  |  |  | Multivariate candidate with compact signatures; not standardized. | oqs import failed: No module named 'oqs' |
| SNOVA-(24,5,4) | unsupported | oqs-python/liboqs | in-process |  |  |  |  | Multivariate candidate with very compact signatures; not standardized. | oqs import failed: No module named 'oqs' |
| HAWK-512 | unsupported | oqs-python/liboqs | in-process |  |  |  |  | Promising lattice candidate retained as metadata-only because liboqs 0.15.0 and OpenSSL 3.6.2 do not provide it. | oqs import failed: No module named 'oqs' |
