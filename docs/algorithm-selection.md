# Algorithm Selection

| Algorithm | Track | NIST category | Public key bytes | Signature bytes | Standards |
|---|---|---|---|---|---|
| RSA-2048/SHA-256 | baseline | classical | 270 | 256 | RFC 7935 |
| ML-DSA-65 | primary | 3 | 1952 | 3309 | FIPS 204; RFC 9881; RFC 9882 |
| ML-DSA-87 | high-assurance | 5 | 2592 | 4627 | FIPS 204; RFC 9881; RFC 9882 |
| SLH-DSA-SHAKE-128s | diversity | 1 | 32 | 7856 | FIPS 205; RFC 9909; RFC 9814 |
| SLH-DSA-SHAKE-192s | diversity | 3 | 48 | 16224 | FIPS 205; RFC 9909; RFC 9814 |
| P-256/SHA-256 | classical-reference | classical-128 | 65 | 72 | FIPS 186-5; RFC 8608 for BGPsec |
| Ed25519 | classical-reference | classical-128 | 32 | 64 | RFC 8032 |
| ML-DSA-44 | excluded-policy | 2 | 1312 | 2420 | FIPS 204; RFC 9881; RFC 9882 |
| Falcon-512 | optional | 1 | 897 | 666 | NIST-selected Falcon; FN-DSA final profile pending |
| Falcon-1024 | optional | 5 | 1793 | 1280 | NIST-selected Falcon; FN-DSA final profile pending |
| MAYO-1 | optional | 1 | 1420 | 454 | NIST Additional Signatures Round 3 (2026) |
| SNOVA-(24,5,4) | optional | 1 | 1016 | 248 | NIST Additional Signatures Round 3 (2026) |
| HAWK-512 | optional | 1 | 1024 | 555 | NIST Additional Signatures Round 3 (2026) |
| RSA-2048+ML-DSA-44 | composite-candidate | hybrid | 1582 | 2676 | draft-ietf-lamps-pq-composite-sigs |
| P-256+ML-DSA-44 | composite-candidate | hybrid | 1377 | 2492 | draft-ietf-lamps-pq-composite-sigs |
| P-256+Falcon-512 | composite-candidate | hybrid | 962 | 738 | draft-ietf-lamps-pq-composite-sigs; FN-DSA pending |

P-256 and Ed25519 are compact classical counterfactuals, not current RFC 6488 profile algorithms. ML-DSA-65 is the current primary experiment. ML-DSA-44 remains measured while its profile role is reconsidered alongside small-PQ composite suites. ML-DSA-87 is the high-assurance comparison. SLH-DSA remains a crypto-diversity candidate with significant size and signing-cost concerns. Composite sizes are estimates until RPKI-specific X.509/CMS and validator evidence exists. Falcon, MAYO, SNOVA, and HAWK remain research candidates.
