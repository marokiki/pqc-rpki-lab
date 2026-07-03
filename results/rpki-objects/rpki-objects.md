# RPKI Object Fixtures

> EXPERIMENTAL / NOT FOR PRODUCTION

Private keys are generated in temporary directories and are not persisted. Public DER artifacts are stored under `testdata/`.

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
