# Algorithm Selection

| Algorithm | Track | NIST category | Public key bytes | Signature bytes | Standards |
|---|---|---|---|---|---|
| RSA-2048/SHA-256 | baseline | classical | 270 | 256 | RFC 7935 |
| ML-DSA-65 | primary | 3 | 1952 | 3309 | FIPS 204; RFC 9881; RFC 9882 |
| ML-DSA-87 | high-assurance | 5 | 2592 | 4627 | FIPS 204; RFC 9881; RFC 9882 |
| SLH-DSA-SHAKE-128s | diversity | 1 | 32 | 7856 | FIPS 205; RFC 9909; RFC 9814 |
| SLH-DSA-SHAKE-192s | diversity | 3 | 48 | 16224 | FIPS 205; RFC 9909; RFC 9814 |
| Falcon-512 | optional | 1 | 897 | 666 | NIST-selected Falcon; FN-DSA final profile pending |
| Falcon-1024 | optional | 5 | 1793 | 1280 | NIST-selected Falcon; FN-DSA final profile pending |
| MAYO-1 | optional | 1 | 1420 | 454 | NIST Additional Signatures Round 3 (2026) |
| SNOVA-(24,5,4) | optional | 1 | 1016 | 248 | NIST Additional Signatures Round 3 (2026) |
| HAWK-512 | optional | 1 | 1024 | 555 | NIST Additional Signatures Round 3 (2026) |

ML-DSA-65 is the standards-ready primary experiment. ML-DSA-87 is the high-assurance candidate. SLH-DSA remains a crypto-diversity candidate with significant size and signing-cost concerns. Composite signatures, Falcon, MAYO, SNOVA, and HAWK remain outside the mandatory path until RPKI-specific profile and interoperability evidence exists.
