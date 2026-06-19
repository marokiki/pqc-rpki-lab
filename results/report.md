# PQC RPKI Evaluation Report

> EXPERIMENTAL / NOT FOR PRODUCTION

## Summary

ML-DSA-65 is the standards-ready SIDROPS implementation target. OpenSSL generated RFC 6487-oriented CA/EE certificates and CRLs with ML-DSA, but its CMS CLI could not create pure ML-DSA SignedData. Published RPKI measurements and the local size model identify Falcon-512 as the leading performance challenger, while its local primitive benchmark is unsupported in this evidence snapshot.

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
| RSA-2048/SHA-256 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 6.171625 | 4.784542 | 256 | Current RPKI baseline; SPKI size is an approximate DER value. Timed operations each include one OpenSSL process launch. |  |
| ML-DSA-65 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 5.008583 | 4.452875 | 3309 | Primary balanced PQC candidate. Timed operations each include one OpenSSL process launch. |  |
| ML-DSA-87 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 4.931292 | 4.365125 | 4627 | High-assurance candidate with larger objects. Timed operations each include one OpenSSL process launch. |  |
| SLH-DSA-SHAKE-128s | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 356.297333 | 5.456125 | 7856 | Hash-based diversity candidate; signature size is the main concern. Timed operations each include one OpenSSL process launch. |  |
| SLH-DSA-SHAKE-192s | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 616.289666 | 5.7625 | 16224 | Conservative diversity candidate with very large signatures. Timed operations each include one OpenSSL process launch. |  |
| ML-DSA-44 | confirmed | OpenSSL CLI | end-to-end CLI wall-clock | 5.459542 | 4.591084 | 2420 | Measured comparison excluded from the primary profile by the Category 3 policy floor. Timed operations each include one OpenSSL process launch. |  |
| Falcon-512 | unsupported | oqs-python/liboqs | in-process |  |  |  | Best size/performance candidate in the 2025 RPKI study; no final RPKI-ready X.509/CMS path. | oqs import failed: No module named 'oqs' |
| Falcon-1024 | unsupported | oqs-python/liboqs | in-process |  |  |  | Category-5 Falcon comparison. | oqs import failed: No module named 'oqs' |
| MAYO-1 | unsupported | oqs-python/liboqs | in-process |  |  |  | Multivariate candidate with compact signatures; not standardized. | oqs import failed: No module named 'oqs' |
| SNOVA-(24,5,4) | unsupported | oqs-python/liboqs | in-process |  |  |  | Multivariate candidate with very compact signatures; not standardized. | oqs import failed: No module named 'oqs' |
| HAWK-512 | unsupported | oqs-python/liboqs | in-process |  |  |  | Promising lattice candidate retained as metadata-only because liboqs 0.15.0 and OpenSSL 3.6.2 do not provide it. | oqs import failed: No module named 'oqs' |

## Repository impact

| Algorithm | Repository bytes | RSA ratio | RRDP snapshot bytes |
|---|---|---|---|
| RSA-2048/SHA-256 | 294580 | 1.0 | 329930 |
| ML-DSA-65 | 1181790 | 4.0118 | 1323605 |
| ML-DSA-87 | 1555330 | 5.2798 | 1741970 |
| SLH-DSA-SHAKE-128s | 2016400 | 6.845 | 2258368 |
| SLH-DSA-SHAKE-192s | 3942800 | 13.3845 | 4415936 |
| ML-DSA-44 | 906920 | 3.0787 | 1015750 |
| Falcon-512 | 457850 | 1.5542 | 512792 |
| Falcon-1024 | 697630 | 2.3682 | 781346 |
| MAYO-1 | 466620 | 1.584 | 522614 |
| SNOVA-(24,5,4) | 374800 | 1.2723 | 419776 |
| HAWK-512 | 446290 | 1.515 | 499845 |

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
