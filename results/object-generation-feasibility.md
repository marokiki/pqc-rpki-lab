# RFC-Profiled Object Generation Feasibility

> EXPERIMENTAL / NOT FOR PRODUCTION

All keys and intermediate objects were created under an automatically deleted temporary directory. No private key is persisted or committed.

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
