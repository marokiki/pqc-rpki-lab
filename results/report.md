# PQC RPKI Evaluation Report

> EXPERIMENTAL / NOT FOR PRODUCTION

## Summary

Draft-01 uses ML-DSA-65 as its primary experiment. Evidence includes ML-DSA-44, compact classical references, and small-PQ composite size estimates. OpenSSL 3.6.2 generated ML-DSA-65 RFC 6488 ROA and Manifest objects through the CMS API when SHA-512 was supplied explicitly; the default-digest CLI path still fails. Routinator, rpki-client, and FORT accepted the RSA baseline repository and rejected the ML-DSA-65 repository at unsupported trust-anchor or algorithm checks. Published RPKI measurements and the local size model identify Falcon-512 as the leading size challenger. Pinned liboqs now provides primitive Falcon measurements, but Falcon X.509/CMS interoperability remains unsupported.

## RFC-profiled object generation

| Algorithm | Object | Status | Bytes | Classification | Reason |
|---|---|---|---|---|---|
| RSA-2048/SHA-256 | CA certificate | confirmed | 1038 | rfc-profiled-x509-generated |  |
| RSA-2048/SHA-256 | EE certificate | confirmed | 984 | rfc-profiled-x509-generated |  |
| RSA-2048/SHA-256 | CRL | confirmed | 381 | rfc-profiled-crl-generated |  |
| RSA-2048/SHA-256 | CMS SignedData | confirmed | 1492 | generic-cms-generated |  |
| RSA-2048/SHA-256 | MFT | unsupported |  | rpki-payload-generator-unavailable | No existing MFT/ROA payload generator was available; ASN.1 payloads were not reimplemented. |
| RSA-2048/SHA-256 | ROA | unsupported |  | rpki-payload-generator-unavailable | No existing MFT/ROA payload generator was available; ASN.1 payloads were not reimplemented. |
| P-256/SHA-256 | CA certificate | confirmed | 641 | rfc-profiled-x509-generated |  |
| P-256/SHA-256 | EE certificate | confirmed | 587 | rfc-profiled-x509-generated |  |
| P-256/SHA-256 | CRL | confirmed | 187 | rfc-profiled-crl-generated |  |
| P-256/SHA-256 | CMS SignedData | confirmed | 903 | generic-cms-generated |  |
| P-256/SHA-256 | MFT | unsupported |  | rpki-payload-generator-unavailable | No existing MFT/ROA payload generator was available; ASN.1 payloads were not reimplemented. |
| P-256/SHA-256 | ROA | unsupported |  | rpki-payload-generator-unavailable | No existing MFT/ROA payload generator was available; ASN.1 payloads were not reimplemented. |
| Ed25519 | CA certificate | confirmed | 578 | rfc-profiled-x509-generated |  |
| Ed25519 | EE certificate | confirmed | 524 | rfc-profiled-x509-generated |  |
| Ed25519 | CRL | confirmed | 170 | rfc-profiled-crl-generated |  |
| Ed25519 | CMS SignedData | unsupported |  | cms-pure-signature-unsupported | 805D41F101000000:error:17000080:CMS routines:CMS_add1_signer:no default digest:crypto/cms/cms_sd.c:405:pkey nid=1087 |
| Ed25519 | MFT | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| Ed25519 | ROA | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| ML-DSA-44 | CA certificate | confirmed | 4238 | rfc-profiled-x509-generated |  |
| ML-DSA-44 | EE certificate | confirmed | 4184 | rfc-profiled-x509-generated |  |
| ML-DSA-44 | CRL | confirmed | 2541 | rfc-profiled-crl-generated |  |
| ML-DSA-44 | CMS SignedData | unsupported |  | cms-pure-signature-unsupported | 805D41F101000000:error:17000080:CMS routines:CMS_add1_signer:no default digest:crypto/cms/cms_sd.c:405:pkey nid=-1 |
| ML-DSA-44 | MFT | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| ML-DSA-44 | ROA | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| ML-DSA-65 | CA certificate | confirmed | 5767 | rfc-profiled-x509-generated |  |
| ML-DSA-65 | EE certificate | confirmed | 5713 | rfc-profiled-x509-generated |  |
| ML-DSA-65 | CRL | confirmed | 3430 | rfc-profiled-crl-generated |  |
| ML-DSA-65 | CMS SignedData | unsupported |  | cms-pure-signature-unsupported | 805D41F101000000:error:17000080:CMS routines:CMS_add1_signer:no default digest:crypto/cms/cms_sd.c:405:pkey nid=-1 |
| ML-DSA-65 | MFT | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| ML-DSA-65 | ROA | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| ML-DSA-87 | CA certificate | confirmed | 7725 | rfc-profiled-x509-generated |  |
| ML-DSA-87 | EE certificate | confirmed | 7671 | rfc-profiled-x509-generated |  |
| ML-DSA-87 | CRL | confirmed | 4748 | rfc-profiled-crl-generated |  |
| ML-DSA-87 | CMS SignedData | unsupported |  | cms-pure-signature-unsupported | 805D41F101000000:error:17000080:CMS routines:CMS_add1_signer:no default digest:crypto/cms/cms_sd.c:405:pkey nid=-1 |
| ML-DSA-87 | MFT | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| ML-DSA-87 | ROA | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| SLH-DSA-SHAKE-128s | CA certificate | confirmed | 8390 | rfc-profiled-x509-generated |  |
| SLH-DSA-SHAKE-128s | EE certificate | confirmed | 8336 | rfc-profiled-x509-generated |  |
| SLH-DSA-SHAKE-128s | CRL | confirmed | 7977 | rfc-profiled-crl-generated |  |
| SLH-DSA-SHAKE-128s | CMS SignedData | unsupported |  | cms-pure-signature-unsupported | 805D41F101000000:error:17000080:CMS routines:CMS_add1_signer:no default digest:crypto/cms/cms_sd.c:405:pkey nid=-1 |
| SLH-DSA-SHAKE-128s | MFT | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| SLH-DSA-SHAKE-128s | ROA | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| SLH-DSA-SHAKE-192s | CA certificate | confirmed | 16774 | rfc-profiled-x509-generated |  |
| SLH-DSA-SHAKE-192s | EE certificate | confirmed | 16720 | rfc-profiled-x509-generated |  |
| SLH-DSA-SHAKE-192s | CRL | confirmed | 16345 | rfc-profiled-crl-generated |  |
| SLH-DSA-SHAKE-192s | CMS SignedData | unsupported |  | cms-pure-signature-unsupported | 805D41F101000000:error:17000080:CMS routines:CMS_add1_signer:no default digest:crypto/cms/cms_sd.c:405:pkey nid=-1 |
| SLH-DSA-SHAKE-192s | MFT | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| SLH-DSA-SHAKE-192s | ROA | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| FN-DSA-512 (Falcon-512) | CA certificate | confirmed | 2048 | rfc-profiled-x509-generated |  |
| FN-DSA-512 (Falcon-512) | EE certificate | confirmed | 1991 | rfc-profiled-x509-generated |  |
| FN-DSA-512 (Falcon-512) | CRL | confirmed | 764 | rfc-profiled-crl-generated |  |
| FN-DSA-512 (Falcon-512) | CMS SignedData | unsupported |  | cms-pure-signature-unsupported | 805D41F101000000:error:17000080:CMS routines:CMS_add1_signer:no default digest:crypto/cms/cms_sd.c:405:pkey nid=-1 |
| FN-DSA-512 (Falcon-512) | MFT | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |
| FN-DSA-512 (Falcon-512) | ROA | unsupported |  | cms-signing-unavailable | RFC 6488 object generation cannot proceed because CMS signing failed. |

## RPKI object fixtures

RSA and ML-DSA-65 `.mft` and `.roa` fixtures are generated. ML-DSA-65 uses the OpenSSL CMS API with explicit SHA-512 and is cross-checked against an independent manual DER assembly path.

| Algorithm | Artifact | Status | Classification | Bytes | Public Path | Reason |
|---|---|---|---|---|---|---|
| RSA-2048/SHA-256 | CA certificate | confirmed | public-der-fixture | 1064 | testdata/rsa/ca.cer |  |
| RSA-2048/SHA-256 | ROA EE certificate | confirmed | public-der-fixture | 1082 | testdata/rsa/route.ee.cer |  |
| RSA-2048/SHA-256 | Manifest EE certificate | confirmed | public-der-fixture | 1100 | testdata/rsa/manifest.ee.cer |  |
| RSA-2048/SHA-256 | CRL | confirmed | public-der-fixture | 415 | testdata/rsa/ca.crl |  |
| RSA-2048/SHA-256 | ROA eContent | confirmed | rpki-econtent-der | 45 | testdata/rsa/route.roa.econtent |  |
| RSA-2048/SHA-256 | Manifest eContent | confirmed | rpki-econtent-der | 146 | testdata/rsa/manifest.mft.econtent |  |
| RSA-2048/SHA-256 | ROA CMS | confirmed | rfc6488-cms-generated | 1621 | testdata/rsa/route.roa |  |
| RSA-2048/SHA-256 | Manifest CMS | confirmed | rfc6488-cms-generated | 1743 | testdata/rsa/manifest.mft |  |
| ML-DSA-44 | CA certificate | confirmed | public-der-fixture | 4264 | testdata/ml-dsa-44/ca.cer |  |
| ML-DSA-44 | ROA EE certificate | confirmed | public-der-fixture | 4282 | testdata/ml-dsa-44/route.ee.cer |  |
| ML-DSA-44 | Manifest EE certificate | confirmed | public-der-fixture | 4300 | testdata/ml-dsa-44/manifest.ee.cer |  |
| ML-DSA-44 | CRL | confirmed | public-der-fixture | 2575 | testdata/ml-dsa-44/ca.crl |  |
| ML-DSA-44 | ROA eContent | confirmed | rpki-econtent-der | 45 | testdata/ml-dsa-44/route.roa.econtent |  |
| ML-DSA-44 | Manifest eContent | confirmed | rpki-econtent-der | 146 | testdata/ml-dsa-44/manifest.mft.econtent |  |
| ML-DSA-44 | ROA CMS | blocked | cms-signing-unavailable |  | results/rpki-objects/ml-dsa-44/route.roa.cms-error.txt | 805D41F101000000:error:17000080:CMS routines:CMS_add1_signer:no default digest:crypto/cms/cms_sd.c:405:pkey nid=-1 |
| ML-DSA-44 | Manifest CMS | blocked | cms-signing-unavailable |  | results/rpki-objects/ml-dsa-44/manifest.mft.cms-error.txt | 805D41F101000000:error:17000080:CMS routines:CMS_add1_signer:no default digest:crypto/cms/cms_sd.c:405:pkey nid=-1 |
| ML-DSA-65 | CA certificate | confirmed | public-der-fixture | 5793 | testdata/ml-dsa-65/ca.cer |  |
| ML-DSA-65 | ROA EE certificate | confirmed | public-der-fixture | 5811 | testdata/ml-dsa-65/route.ee.cer |  |
| ML-DSA-65 | Manifest EE certificate | confirmed | public-der-fixture | 5829 | testdata/ml-dsa-65/manifest.ee.cer |  |
| ML-DSA-65 | CRL | confirmed | public-der-fixture | 3464 | testdata/ml-dsa-65/ca.crl |  |
| ML-DSA-65 | ROA eContent | confirmed | rpki-econtent-der | 45 | testdata/ml-dsa-65/route.roa.econtent |  |
| ML-DSA-65 | Manifest eContent | confirmed | rpki-econtent-der | 146 | testdata/ml-dsa-65/manifest.mft.econtent |  |
| ML-DSA-65 | ROA CMS | confirmed | rfc6488-openssl-api-cms-generated | 9434 | testdata/ml-dsa-65/route.roa |  |
| ML-DSA-65 | Manifest CMS | confirmed | rfc6488-openssl-api-cms-generated | 9556 | testdata/ml-dsa-65/manifest.mft |  |
| ML-DSA-87 | CA certificate | confirmed | public-der-fixture | 7751 | testdata/ml-dsa-87/ca.cer |  |
| ML-DSA-87 | ROA EE certificate | confirmed | public-der-fixture | 7769 | testdata/ml-dsa-87/route.ee.cer |  |
| ML-DSA-87 | Manifest EE certificate | confirmed | public-der-fixture | 7787 | testdata/ml-dsa-87/manifest.ee.cer |  |
| ML-DSA-87 | CRL | confirmed | public-der-fixture | 4782 | testdata/ml-dsa-87/ca.crl |  |
| ML-DSA-87 | ROA eContent | confirmed | rpki-econtent-der | 45 | testdata/ml-dsa-87/route.roa.econtent |  |
| ML-DSA-87 | Manifest eContent | confirmed | rpki-econtent-der | 146 | testdata/ml-dsa-87/manifest.mft.econtent |  |
| ML-DSA-87 | ROA CMS | blocked | cms-signing-unavailable |  | results/rpki-objects/ml-dsa-87/route.roa.cms-error.txt | 805D41F101000000:error:17000080:CMS routines:CMS_add1_signer:no default digest:crypto/cms/cms_sd.c:405:pkey nid=-1 |
| ML-DSA-87 | Manifest CMS | blocked | cms-signing-unavailable |  | results/rpki-objects/ml-dsa-87/manifest.mft.cms-error.txt | 805D41F101000000:error:17000080:CMS routines:CMS_add1_signer:no default digest:crypto/cms/cms_sd.c:405:pkey nid=-1 |

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

## Synthetic key-roll model

| Algorithm | Status | Files | Output bytes | RRDP snapshot | RRDP delta | rsync bytes |
|---|---|---|---|---|---|---|
| ML-DSA-44 | estimated | 112 | 49861 | 55844 | 5584 | 49861 |
| ML-DSA-65 | estimated | 112 | 1014350 | 1136072 | 113607 | 1014350 |
| ML-DSA-87 | estimated | 112 | 86938 | 97371 | 9737 | 86938 |
| RSA-2048/SHA-256 | estimated | 112 | 174898 | 195886 | 19589 | 174898 |

## Local object validation

Local validation records DER parseability, RSA and ML-DSA-65 CMS round-trips, EE profile checks, and Manifest product hashes. Independent validator results are reported separately.

| Algorithm | Layer | Artifact | Status | Reason |
|---|---|---|---|---|
| rsa | DER parse | ca.cer | confirmed |  |
| rsa | DER parse | route.ee.cer | confirmed |  |
| rsa | DER parse | manifest.ee.cer | confirmed |  |
| rsa | DER parse | ca.crl | confirmed |  |
| rsa | DER parse | route.roa.econtent | confirmed |  |
| rsa | DER parse | manifest.mft.econtent | confirmed |  |
| rsa | CMS verify | route.roa | confirmed |  |
| rsa | CMS verify | manifest.mft | confirmed |  |
| rsa | EE profile | route.ee.cer | confirmed |  |
| rsa | EE profile | manifest.ee.cer | confirmed |  |
| rsa | Manifest hash | manifest.mft.econtent | confirmed |  |
| ml-dsa-44 | DER parse | ca.cer | confirmed |  |
| ml-dsa-44 | DER parse | route.ee.cer | confirmed |  |
| ml-dsa-44 | DER parse | manifest.ee.cer | confirmed |  |
| ml-dsa-44 | DER parse | ca.crl | confirmed |  |
| ml-dsa-44 | DER parse | route.roa.econtent | confirmed |  |
| ml-dsa-44 | DER parse | manifest.mft.econtent | confirmed |  |
| ml-dsa-44 | CMS verify | route.roa | skipped | CMS artifact unavailable |
| ml-dsa-44 | CMS verify | manifest.mft | skipped | CMS artifact unavailable |
| ml-dsa-44 | EE profile | route.ee.cer | confirmed |  |
| ml-dsa-44 | EE profile | manifest.ee.cer | confirmed |  |
| ml-dsa-65 | DER parse | ca.cer | confirmed |  |
| ml-dsa-65 | DER parse | route.ee.cer | confirmed |  |
| ml-dsa-65 | DER parse | manifest.ee.cer | confirmed |  |
| ml-dsa-65 | DER parse | ca.crl | confirmed |  |
| ml-dsa-65 | DER parse | route.roa.econtent | confirmed |  |
| ml-dsa-65 | DER parse | manifest.mft.econtent | confirmed |  |
| ml-dsa-65 | CMS verify | route.roa | confirmed |  |
| ml-dsa-65 | CMS verify | manifest.mft | confirmed |  |
| ml-dsa-65 | EE profile | route.ee.cer | confirmed |  |
| ml-dsa-65 | EE profile | manifest.ee.cer | confirmed |  |
| ml-dsa-65 | Manifest hash | manifest.mft.econtent | confirmed |  |
| ml-dsa-87 | DER parse | ca.cer | confirmed |  |
| ml-dsa-87 | DER parse | route.ee.cer | confirmed |  |
| ml-dsa-87 | DER parse | manifest.ee.cer | confirmed |  |
| ml-dsa-87 | DER parse | ca.crl | confirmed |  |
| ml-dsa-87 | DER parse | route.roa.econtent | confirmed |  |
| ml-dsa-87 | DER parse | manifest.mft.econtent | confirmed |  |
| ml-dsa-87 | CMS verify | route.roa | skipped | CMS artifact unavailable |
| ml-dsa-87 | CMS verify | manifest.mft | skipped | CMS artifact unavailable |
| ml-dsa-87 | EE profile | route.ee.cer | confirmed |  |
| ml-dsa-87 | EE profile | manifest.ee.cer | confirmed |  |

## Exact 100,000-operation benchmark

Each row is a direct loop of 100,000 signing operations followed by 100,000 verification operations. Key generation and complete RPKI object processing are excluded.

| Algorithm | Status | Sign total s | Verify total s | Sign us/op | Verify us/op | Sign time/RSA | Verify time/RSA |
|---|---|---|---|---|---|---|---|
| RSA-2048/SHA-256 | confirmed | 34.327696000 | 0.986373000 | 343.277 | 9.864 | 1.0 | 1.0 |
| P-256/SHA-256 | confirmed | 1.268314000 | 3.477508000 | 12.683 | 34.775 | 0.037 | 3.526 |
| Ed25519 | confirmed | 1.663721000 | 4.046193000 | 16.637 | 40.462 | 0.048 | 4.102 |
| ML-DSA-44 | confirmed | 25.081317000 | 4.958273000 | 250.813 | 49.583 | 0.731 | 5.027 |
| ML-DSA-65 | confirmed | 40.543142000 | 7.665719000 | 405.431 | 76.657 | 1.181 | 7.772 |
| ML-DSA-87 | confirmed | 47.943284000 | 11.742680000 | 479.433 | 117.427 | 1.397 | 11.905 |

## Composite component benchmark

These rows execute both component operations and require both verifications to pass. They do not implement the LAMPS composite ASN.1/OID format.

| Combination | Status | Sign total s | Verify total s | Component bytes | Sign time/ML-DSA-65 | Verify time/ML-DSA-65 | Bytes/ML-DSA-65 |
|---|---|---|---|---|---|---|---|
| FN-DSA-512 (Falcon-512) | confirmed | 10.547208000 | 1.612536000 | 665 | 0.26 | 0.21 | 0.201 |
| RSA-2048+P-256 | confirmed | 35.317942000 | 4.473800000 | 328 | 0.871 | 0.584 | 0.099 |
| RSA-2048+Ed25519 | confirmed | 35.634483000 | 5.057551000 | 320 | 0.879 | 0.66 | 0.097 |
| RSA-2048+ML-DSA-44 | confirmed | 59.198430000 | 5.784879000 | 2676 | 1.46 | 0.755 | 0.809 |
| P-256+ML-DSA-44 | confirmed | 26.317486000 | 8.391998000 | 2492 | 0.649 | 1.095 | 0.753 |
| RSA-2048+ML-DSA-65 | confirmed | 74.396603000 | 8.363908000 | 3565 | 1.835 | 1.091 | 1.077 |
| P-256+ML-DSA-65 | confirmed | 41.756521000 | 10.879306000 | 3381 | 1.03 | 1.419 | 1.022 |
| RSA-2048+ML-DSA-87 | confirmed | 81.102208000 | 12.706616000 | 4883 | 2.0 | 1.658 | 1.476 |
| RSA-2048+FN-DSA-512 | confirmed | 44.606447000 | 2.632527000 | 920 | 1.1 | 0.343 | 0.278 |
| P-256+ML-DSA-87 | confirmed | 49.977078000 | 15.269535000 | 4699 | 1.233 | 1.992 | 1.42 |
| P-256+Falcon-512 | confirmed | 12.061653000 | 5.082005000 | 737 | 0.298 | 0.663 | 0.223 |

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

## Unmodified validator repository probe

Pinned unmodified validator containers fetched isolated repositories from a local rsync daemon. No production TAL or Internet repository was used.

| Validator | Repository | Status | Parser | Certificate path | Manifest | ROA | VRP output | Hard error |
|---|---|---|---|---|---|---|---|---|
| Routinator | rsa | accepted | accepted | accepted | accepted | accepted | present |  |
| rpki-client | rsa | accepted | accepted | accepted | accepted | accepted | present |  |
| FORT | rsa | accepted | accepted | accepted | accepted | accepted | present |  |
| Routinator | ml-dsa-65 | rejected | rejected | rejected-or-not-reached | rejected-or-not-reached | rejected-or-not-reached | absent | [ERROR] Failed to read TAL /tals/test.tal: bad key info: invalid public key format (at position 6). |
| rpki-client | ml-dsa-65 | rejected | rejected | rejected-or-not-reached | rejected-or-not-reached | rejected-or-not-reached | absent | Certificates: 1 (1 invalid, 0 non-functional) |
| FORT | ml-dsa-65 | rejected | rejected | rejected-or-not-reached | rejected-or-not-reached | rejected-or-not-reached | absent | Jul  3 04:00:26 WRN: Validation from TAL '/tals/test.tal' yielded error -22 (Invalid argument); discarding all validation results. |

## CMS API and object generation

| CMS API digest mode | Status | Return code | Output bytes | Error |
|---|---|---|---|---|
| default | blocked | 1 | 0 | 805D41F101000000:error:17000080:CMS routines:CMS_add1_signer:no default digest:crypto/cms/cms_sd.c:405:pkey nid=-1 |
| sha512 | confirmed | 0 | 9116 |  |

| Artifact | Status | Backend | Bytes | Public path |
|---|---|---|---|---|
| ROA CMS | confirmed | rfc6488-openssl-api-cms-generated | 9434 | testdata/ml-dsa-65/route.roa |
| Manifest CMS | confirmed | rfc6488-openssl-api-cms-generated | 9556 | testdata/ml-dsa-65/manifest.mft |

## Repeated message-size sweep

| Algorithm | Message bytes | Repetitions | Status | Sign median s | Sign stdev s | Verify median s | Verify stdev s | Peak RSS median bytes |
|---|---|---|---|---|---|---|---|---|
| Ed25519 | 32 | 10 | confirmed | 0.0166565 | 0.0066131999852147546 | 0.040441500000000005 | 0.018693730986022502 | 5341184.0 |
| Ed25519 | 512 | 10 | confirmed | 0.017145 | 0.0002296828973461744 | 0.040886500000000006 | 0.0026813871948841864 | 5341184.0 |
| Ed25519 | 2048 | 10 | confirmed | 0.019014 | 0.0005195823215707875 | 0.041787000000000005 | 0.000378169582771187 | 5341184.0 |
| Ed25519 | 8192 | 10 | confirmed | 0.026115 | 0.0005241822096264705 | 0.045107499999999995 | 0.0006635259016965526 | 5357568.0 |
| ML-DSA-44 | 32 | 10 | confirmed | 0.2492375 | 0.02996983994766887 | 0.0477975 | 0.0024596575665007604 | 5603328.0 |
| ML-DSA-44 | 512 | 10 | confirmed | 0.24926700000000002 | 0.007512190732402896 | 0.048516500000000004 | 0.006986570324558394 | 5529600.0 |
| ML-DSA-44 | 2048 | 10 | confirmed | 0.24800650000000002 | 0.008460611838264286 | 0.049780000000000005 | 0.00026971005007435443 | 5537792.0 |
| ML-DSA-44 | 8192 | 10 | confirmed | 0.2530775 | 0.014824931489067859 | 0.0555355 | 0.009765382771698083 | 5570560.0 |
| ML-DSA-65 | 32 | 10 | confirmed | 0.405729 | 0.017569537192412197 | 0.0734105 | 0.01413849605549017 | 5652480.0 |
| ML-DSA-65 | 512 | 10 | confirmed | 0.4008925 | 0.007362091638175182 | 0.0739315 | 0.0010952076616889718 | 5619712.0 |
| ML-DSA-65 | 2048 | 10 | confirmed | 0.401352 | 0.007778928724445286 | 0.0752735 | 0.0006939509748934388 | 5619712.0 |
| ML-DSA-65 | 8192 | 10 | confirmed | 0.413362 | 0.007357251679654417 | 0.08101749999999999 | 0.0034889943489015075 | 5644288.0 |
| ML-DSA-87 | 32 | 10 | confirmed | 0.477243 | 0.012467642439976822 | 0.11596300000000001 | 0.0015355287507710317 | 5758976.0 |
| ML-DSA-87 | 512 | 10 | confirmed | 0.46777749999999996 | 0.011902649789484318 | 0.116371 | 0.0008233567135681708 | 5775360.0 |
| ML-DSA-87 | 2048 | 10 | confirmed | 0.478189 | 0.010645353649467086 | 0.1179915 | 0.0026760257534884325 | 5783552.0 |
| ML-DSA-87 | 8192 | 10 | confirmed | 0.481751 | 0.011612352274386282 | 0.123285 | 0.0007850812342964535 | 5758976.0 |
| P-256/SHA-256 | 32 | 10 | confirmed | 0.012660000000000001 | 0.0003322606239418422 | 0.034534499999999996 | 0.005360799754804419 | 5242880.0 |
| P-256/SHA-256 | 512 | 10 | confirmed | 0.0128995 | 6.664633023155385e-05 | 0.034547499999999995 | 0.00011922136273895505 | 5242880.0 |
| P-256/SHA-256 | 2048 | 10 | confirmed | 0.013333000000000001 | 0.00015186470586969438 | 0.035047499999999995 | 0.0004672434649682704 | 5234688.0 |
| P-256/SHA-256 | 8192 | 10 | confirmed | 0.01533 | 0.0002886204735942652 | 0.037066 | 0.0006184714490850269 | 5259264.0 |
| RSA-2048/SHA-256 | 32 | 10 | confirmed | 0.340326 | 0.002114198519008517 | 0.0097915 | 5.6513125319109134e-05 | 4898816.0 |
| RSA-2048/SHA-256 | 512 | 10 | confirmed | 0.33947000000000005 | 0.00995606636065558 | 0.009933500000000001 | 4.8242903911122394e-05 | 4898816.0 |
| RSA-2048/SHA-256 | 2048 | 10 | confirmed | 0.340194 | 0.0020684014466356513 | 0.010469 | 0.00010795163526114613 | 4890624.0 |
| RSA-2048/SHA-256 | 8192 | 10 | confirmed | 0.341387 | 0.008301982882955663 | 0.012399 | 0.0004012827210611268 | 4915200.0 |

## Real repository measurement

| Extension | Status | Count | Total bytes | Median bytes | P95 bytes | Reason |
|---|---|---|---|---|---|---|
| all | skipped | 0 |  |  |  | no --cache argument supplied |

## VRP semantics

Equivalent: `True`.

## CCR-style interim comparison

The local CCR-style workflow uses canonical JSON and is not CCR `ROAPayloadState.hash` output.

Equivalent: `True`.

## Object payload benchmark

| Workload | Objects | Payload construction ms | Hashing ms | Manifest encoding ms | CMS status | Classification |
|---|---|---|---|---|---|---|
| synthetic-manifest-payloads | 100000 | 61.617 | 26.734416 | 79.470667 | blocked | object-payload benchmark, not complete RFC 6488 CMS generation |

## Mixed-tree model

Valid synthetic model: `True`. This is not validator interoperability evidence.

## Routinator/Krill extension track

Routinator/Krill scan and interop runners are optional, read-only, and configured with explicit environment variables. External checkouts must remain under ignored `local/` or separate upstream worktrees.

| Project | Role | Status | Source Env | Reason |
|---|---|---|---|---|
| Routinator | validator | skipped | PQC_RPKI_ROUTINATOR_SRC | PQC_RPKI_ROUTINATOR_SRC is not set |
| Krill | ca-publication | skipped | PQC_RPKI_KRILL_SRC | PQC_RPKI_KRILL_SRC is not set |

## Limitations

- Repository values are first-order or literature-calibrated estimates.
- ML-DSA-44/87 and SLH-DSA complete CMS fixtures remain unimplemented.
- No unmodified validator accepted the ML-DSA-65 repository; rejection is expected until algorithm support is added.
- The mixed-tree fixture is still structural rather than a complete validator repository.
- Missing optional dependencies are recorded as unsupported, not suite failures.
- Core primitive timings include one OpenSSL process launch per timed operation; they are end-to-end CLI measurements, not pure cryptographic cycle counts.
- Timing comparisons are valid only within an identical `comparable_group`.
