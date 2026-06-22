# Bulk Signing Throughput

> EXPERIMENTAL / NOT FOR PRODUCTION

One OpenSSL speed process per algorithm; provider and process startup are outside timed loops.

The signing-only 100,000-manifest value uses two signatures per RFC 6488 object (EE certificate plus CMS signature). Where OpenSSL reports keygen throughput, the crypto lower bound also includes 100,000 one-time EE keys. Both exclude ASN.1/CMS construction, hashing, file I/O, RRDP publication, and HSM latency.

The synthetic key-roll lower bound uses 10 child certificates, 100 RFC 6488 objects, one manifest, and one CRL: 213 signatures and 102 key generations (one CA and 101 EE keys).

Complete PQC RFC 6488 object workload: `unsupported`. No existing generator in this environment can produce complete PQC RFC 6488 Manifest payloads and CMS SignedData; projected crypto work is not object-level throughput.

| Algorithm | Status | Sign/s | Verify/s | 100k signatures s | 100k MFT signing lower bound s | 100k MFT crypto lower bound s | Key-roll signing lower bound s | Key-roll crypto lower bound s | Reason |
|---|---|---|---|---|---|---|---|---|---|
| RSA-2048/SHA-256 | confirmed | 2966.337 | 117652.0 | 33.712 | 67.423 | 2824.18 | 0.071806 | 2.883698 |  |
| P-256/SHA-256 | confirmed | 89466.0 | 30522.0 | 1.118 | 2.235 |  | 0.002381 |  |  |
| Ed25519 | confirmed | 63516.0 | 25427.0 | 1.574 | 3.149 |  | 0.003353 |  |  |
| ML-DSA-44 | confirmed | 4043.0 | 20787.129 | 24.734 | 49.468 | 53.831 | 0.052684 | 0.057134 |  |
| ML-DSA-65 | confirmed | 2499.0 | 11953.0 | 40.016 | 80.032 | 88.274 | 0.085234 | 0.09364 |  |
| ML-DSA-87 | confirmed | 2134.0 | 8232.673 | 46.86 | 93.721 | 105.635 | 0.099813 | 0.111966 |  |
