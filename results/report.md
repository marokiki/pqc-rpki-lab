# PQC RPKI Evaluation Report

> EXPERIMENTAL / NOT FOR PRODUCTION

## Summary

Draft-00 uses ML-DSA-65 as its primary experiment. Review evidence now includes ML-DSA-44, compact classical references, and small-PQ composite size estimates. OpenSSL generated RFC 6487-oriented CA/EE certificates and CRLs with ML-DSA, but its CMS CLI could not create pure ML-DSA SignedData. Published RPKI measurements and the local size model identify Falcon-512 as the leading size challenger. Pinned liboqs now provides primitive Falcon measurements, but X.509/CMS and validator interoperability remain unsupported.

## RFC-profiled object generation

| Algorithm | Object | Status | Bytes | Classification | Reason |
|---|---|---|---|---|---|
| RSA-2048/SHA-256 | CA certificate | confirmed | 1038 | rfc-profiled-x509-generated |  |
| RSA-2048/SHA-256 | EE certificate | confirmed | 984 | rfc-profiled-x509-generated |  |
| RSA-2048/SHA-256 | CRL | confirmed | 381 | rfc-profiled-crl-generated |  |
| RSA-2048/SHA-256 | CMS SignedData | confirmed | 1492 | generic-cms-generated |  |
| RSA-2048/SHA-256 | MFT | unsupported |  | rpki-payload-generator-unavailable | No existing MFT/ROA payload generator was available; ASN.1 payloads were not reimplemented. |
| RSA-2048/SHA-256 | ROA | unsupported |  | rpki-payload-generator-unavailable | No existing MFT/ROA payload generator was available; ASN.1 payloads were not reimplemented. |
| ML-DSA-65 | CA certificate | confirmed | 5767 | rfc-profiled-x509-generated |  |
| ML-DSA-65 | EE certificate | confirmed | 5713 | rfc-profiled-x509-generated |  |
| ML-DSA-65 | CRL | confirmed | 3430 | rfc-profiled-crl-generated |  |
| ML-DSA-65 | CMS SignedData | unsupported |  | cms-pure-signature-unsupported | 80DE56FB01000000:error:17000080:CMS routines:CMS_add1_signer:no default digest:crypto/cms/cms_sd.c:405:pkey nid=-1 |
| ML-DSA-65 | MFT | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| ML-DSA-65 | ROA | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| ML-DSA-87 | CA certificate | confirmed | 7725 | rfc-profiled-x509-generated |  |
| ML-DSA-87 | EE certificate | confirmed | 7671 | rfc-profiled-x509-generated |  |
| ML-DSA-87 | CRL | confirmed | 4748 | rfc-profiled-crl-generated |  |
| ML-DSA-87 | CMS SignedData | unsupported |  | cms-pure-signature-unsupported | 80DE56FB01000000:error:17000080:CMS routines:CMS_add1_signer:no default digest:crypto/cms/cms_sd.c:405:pkey nid=-1 |
| ML-DSA-87 | MFT | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| ML-DSA-87 | ROA | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| SLH-DSA-SHAKE-128s | CA certificate | confirmed | 8390 | rfc-profiled-x509-generated |  |
| SLH-DSA-SHAKE-128s | EE certificate | confirmed | 8336 | rfc-profiled-x509-generated |  |
| SLH-DSA-SHAKE-128s | CRL | confirmed | 7977 | rfc-profiled-crl-generated |  |
| SLH-DSA-SHAKE-128s | CMS SignedData | unsupported |  | cms-pure-signature-unsupported | 80DE56FB01000000:error:17000080:CMS routines:CMS_add1_signer:no default digest:crypto/cms/cms_sd.c:405:pkey nid=-1 |
| SLH-DSA-SHAKE-128s | MFT | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| SLH-DSA-SHAKE-128s | ROA | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| SLH-DSA-SHAKE-192s | CA certificate | confirmed | 16774 | rfc-profiled-x509-generated |  |
| SLH-DSA-SHAKE-192s | EE certificate | confirmed | 16720 | rfc-profiled-x509-generated |  |
| SLH-DSA-SHAKE-192s | CRL | confirmed | 16345 | rfc-profiled-crl-generated |  |
| SLH-DSA-SHAKE-192s | CMS SignedData | unsupported |  | cms-pure-signature-unsupported | 80DE56FB01000000:error:17000080:CMS routines:CMS_add1_signer:no default digest:crypto/cms/cms_sd.c:405:pkey nid=-1 |
| SLH-DSA-SHAKE-192s | MFT | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| SLH-DSA-SHAKE-192s | ROA | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |

## Primitive benchmark

| Algorithm | Status | Backend | Timing scope | Sign ms | Verify ms | Measured signature bytes | Notes | Reason |
|---|---|---|---|---|---|---|---|---|
| RSA-2048/SHA-256 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 6.868458 | 6.022708 | 256 | Current RPKI baseline; SPKI size is an approximate DER value. Timed operations each include one OpenSSL process launch. |  |
| ML-DSA-65 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 6.162125 | 5.569916 | 3309 | Primary balanced PQC candidate. Timed operations each include one OpenSSL process launch. |  |
| ML-DSA-87 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 8.078625 | 6.420667 | 4627 | High-assurance candidate with larger objects. Timed operations each include one OpenSSL process launch. |  |
| SLH-DSA-SHAKE-128s | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 349.318167 | 7.476667 | 7856 | Hash-based diversity candidate; signature size is the main concern. Timed operations each include one OpenSSL process launch. |  |
| SLH-DSA-SHAKE-192s | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 609.270875 | 7.548375 | 16224 | Conservative diversity candidate with very large signatures. Timed operations each include one OpenSSL process launch. |  |
| P-256/SHA-256 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 5.946292 | 6.661375 | 72 | Compact classical counterfactual; not the current RFC 6488 RPKI profile. Signature size uses the conservative DER maximum. Timed operations each include one OpenSSL process launch. |  |
| Ed25519 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 5.742042 | 5.811042 | 64 | Compact classical counterfactual; not the current RFC 6488 RPKI profile. Timed operations each include one OpenSSL process launch. |  |
| ML-DSA-44 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 6.101292 | 5.80225 | 2420 | Measured comparison excluded from the primary profile by the Category 3 policy floor. Timed operations each include one OpenSSL process launch. |  |
| Falcon-512 | confirmed | oqs-python/liboqs | in-process | 2.112334 | 0.04275 | 658 | Best size/performance candidate in the 2025 RPKI study; no final RPKI-ready X.509/CMS path. In-process timings are not directly comparable with OpenSSL CLI timings. |  |
| Falcon-1024 | confirmed | oqs-python/liboqs | in-process | 4.647125 | 0.070458 | 1271 | Category-5 Falcon comparison. In-process timings are not directly comparable with OpenSSL CLI timings. |  |
| MAYO-1 | confirmed | oqs-python/liboqs | in-process | 0.363709 | 0.087542 | 454 | Multivariate candidate with compact signatures; not standardized. In-process timings are not directly comparable with OpenSSL CLI timings. |  |
| SNOVA-(24,5,4) | confirmed | oqs-python/liboqs | in-process | 0.514375 | 0.360875 | 248 | Multivariate candidate with very compact signatures; not standardized. In-process timings are not directly comparable with OpenSSL CLI timings. |  |
| HAWK-512 | unsupported | oqs-python/liboqs | in-process |  |  |  | Promising lattice candidate retained as metadata-only because liboqs 0.15.0 and OpenSSL 3.6.2 do not provide it. | candidate is not enabled by oqs-python/liboqs |
| RSA-2048+ML-DSA-44 | unsupported | size model only | not measured |  |  |  | Component-size sum excluding composite ASN.1 overhead; no local X.509/CMS interoperability evidence. | No local composite signature implementation or interoperability profile |
| P-256+ML-DSA-44 | unsupported | size model only | not measured |  |  |  | Component-size sum excluding composite ASN.1 overhead; no local X.509/CMS interoperability evidence. | No local composite signature implementation or interoperability profile |
| P-256+Falcon-512 | unsupported | size model only | not measured |  |  |  | Component-size sum excluding composite ASN.1 overhead; Falcon/FN-DSA profile is not final. | No local composite signature implementation or interoperability profile |

## Optional liboqs primitive benchmark

These in-process values are not directly comparable with the OpenSSL CLI table above.

| Algorithm | Status | Keygen ms | Sign ms | Verify ms | Measured signature bytes | Reason |
|---|---|---|---|---|---|---|
| Falcon-512 | confirmed | 6.635791 | 2.124541 | 0.04025 | 658 |  |
| Falcon-1024 | confirmed | 15.45125 | 4.834083 | 0.086167 | 1270 |  |
| MAYO-1 | confirmed | 0.114584 | 0.361583 | 0.086458 | 454 |  |
| SNOVA-(24,5,4) | confirmed | 0.179458 | 0.508959 | 0.350333 | 248 |  |
| HAWK-512 | unsupported |  |  |  |  | candidate is not enabled by oqs-python/liboqs |

## Bulk signing throughput

These OpenSSL `speed` values exclude process startup. The 100,000-Manifest and key-roll columns are signing-only lower bounds, not complete object-generation measurements.

| Algorithm | Status | Sign/s | Verify/s | 100k MFT crypto lower bound s | Key-roll crypto lower bound s |
|---|---|---|---|---|---|
| RSA-2048/SHA-256 | confirmed | 2966.337 | 117652.0 | 2824.18 | 2.883698 |
| P-256/SHA-256 | confirmed | 89466.0 | 30522.0 |  |  |
| Ed25519 | confirmed | 63516.0 | 25427.0 |  |  |
| ML-DSA-44 | confirmed | 4043.0 | 20787.129 | 53.831 | 0.057134 |
| ML-DSA-65 | confirmed | 2499.0 | 11953.0 | 88.274 | 0.09364 |
| ML-DSA-87 | confirmed | 2134.0 | 8232.673 | 105.635 | 0.111966 |

## Exact 100,000-operation benchmark

Each row is a direct loop of 100,000 signing operations followed by 100,000 verification operations. Key generation and complete RPKI object processing are excluded.

| Algorithm | Status | Sign total s | Verify total s | Sign us/op | Verify us/op | Sign time/RSA | Verify time/RSA |
|---|---|---|---|---|---|---|---|
| RSA-2048/SHA-256 | confirmed | 37.242536000 | 0.985560000 | 372.425 | 9.856 | 1.0 | 1.0 |
| P-256/SHA-256 | confirmed | 1.368756000 | 3.579209000 | 13.688 | 35.792 | 0.037 | 3.632 |
| Ed25519 | confirmed | 1.673355000 | 4.037800000 | 16.734 | 40.378 | 0.045 | 4.097 |
| ML-DSA-44 | confirmed | 24.908217000 | 4.792310000 | 249.082 | 47.923 | 0.669 | 4.863 |
| ML-DSA-65 | confirmed | 40.175448000 | 7.352204000 | 401.754 | 73.522 | 1.079 | 7.46 |
| ML-DSA-87 | confirmed | 49.886808000 | 11.545769000 | 498.868 | 115.458 | 1.34 | 11.715 |

## Composite component benchmark

These rows execute both component operations and require both verifications to pass. They do not implement the LAMPS composite ASN.1/OID format.

| Combination | Status | Sign total s | Verify total s | Component bytes | Sign time/ML-DSA-65 | Verify time/ML-DSA-65 | Bytes/ML-DSA-65 |
|---|---|---|---|---|---|---|---|
| RSA-2048+ML-DSA-44 | confirmed | 59.283588000 | 6.398635000 | 2676 | 1.476 | 0.87 | 0.809 |
| P-256+ML-DSA-44 | confirmed | 26.938006000 | 8.463775000 | 2492 | 0.671 | 1.151 | 0.753 |
| RSA-2048+ML-DSA-65 | confirmed | 74.359259000 | 8.351363000 | 3565 | 1.851 | 1.136 | 1.077 |
| P-256+ML-DSA-65 | confirmed | 42.234073000 | 11.275192000 | 3381 | 1.051 | 1.534 | 1.022 |
| RSA-2048+ML-DSA-87 | confirmed | 81.854859000 | 12.620553000 | 4883 | 2.037 | 1.717 | 1.476 |
| P-256+ML-DSA-87 | confirmed | 49.750940000 | 15.382402000 | 4699 | 1.238 | 2.092 | 1.42 |
| P-256+Falcon-512 | confirmed | 215.113181000 | 5.473413000 | 737 | 5.354 | 0.744 | 0.223 |

## Repository impact

| Algorithm | Repository bytes | RSA ratio | RRDP snapshot bytes |
|---|---|---|---|
| RSA-2048/SHA-256 | 294580 | 1.0 | 329930 |
| ML-DSA-65 | 1181790 | 4.0118 | 1323605 |
| ML-DSA-87 | 1555330 | 5.2798 | 1741970 |
| SLH-DSA-SHAKE-128s | 2016400 | 6.845 | 2258368 |
| SLH-DSA-SHAKE-192s | 3942800 | 13.3845 | 4415936 |
| P-256/SHA-256 | 229710 | 0.7798 | 257275 |
| Ed25519 | 224240 | 0.7612 | 251149 |
| ML-DSA-44 | 906920 | 3.0787 | 1015750 |
| Falcon-512 | 457850 | 1.5542 | 512792 |
| Falcon-1024 | 697630 | 2.3682 | 781346 |
| MAYO-1 | 466620 | 1.584 | 522614 |
| SNOVA-(24,5,4) | 374800 | 1.2723 | 419776 |
| HAWK-512 | 446290 | 1.515 | 499845 |
| RSA-2048+ML-DSA-44 | 995500 | 3.3794 | 1114960 |
| P-256+ML-DSA-44 | 930630 | 3.1592 | 1042306 |
| RSA-2048+ML-DSA-65 | 1270370 | 4.3125 | 1422814 |
| P-256+ML-DSA-65 | 1205500 | 4.0923 | 1350160 |
| RSA-2048+ML-DSA-87 | 1643910 | 5.5805 | 1841179 |
| P-256+ML-DSA-87 | 1579040 | 5.3603 | 1768525 |
| P-256+Falcon-512 | 481560 | 1.6347 | 539347 |

## Validator capability

| Validator | Installed | Version | RSA baseline | PQC object | VRP output |
|---|---|---|---|---|---|
| Routinator | False |  | unsupported | unsupported | unsupported |
| rpki-client | False |  | unsupported | unsupported | unsupported |
| FORT | False |  | unsupported | unsupported | unsupported |

## Real repository measurement

| Extension | Status | Count | Total bytes | Median bytes | P95 bytes | Reason |
|---|---|---|---|---|---|---|
| all | skipped | 0 |  |  |  | no --cache argument supplied |

## VRP semantics

Equivalent: `True`.

## Limitations

- Repository values are first-order or literature-calibrated estimates.
- MFT and ROA payloads were not hand-encoded; no existing payload generator was available.
- No RFC-profiled PQC RPKI object has yet been accepted by an independent validator.
- Missing optional dependencies are recorded as unsupported, not suite failures.
- Core primitive timings include one OpenSSL process launch per timed operation; they are end-to-end CLI measurements, not pure cryptographic cycle counts.
- Timing comparisons are valid only within an identical `comparable_group`.
