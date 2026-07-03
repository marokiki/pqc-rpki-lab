# ML-DSA-65 CMS Generation

> EXPERIMENTAL / NOT FOR PRODUCTION

OpenSSL 3.6.2 succeeds through `CMS_add1_signer` when SHA-512 is supplied explicitly. The generated objects pass the internal profile, raw-signature, OpenSSL parser, and OpenSSL CMS verification checks.

| Artifact | Status | Backend | Bytes | Public path |
|---|---|---|---|---|
| ROA CMS | confirmed | rfc6488-openssl-api-cms-generated | 9434 | testdata/ml-dsa-65/route.roa |
| Manifest CMS | confirmed | rfc6488-openssl-api-cms-generated | 9556 | testdata/ml-dsa-65/manifest.mft |
