# Open Issues for draft-yoshikawa-sidrops-pqc-rpki

> EXPERIMENTAL / NOT FOR PRODUCTION

1. Should ML-DSA-65 be a MUST, SHOULD, or candidate-only next-suite algorithm?
2. Should ML-DSA-87 be mandatory for trust anchors or upper-tier CAs?
3. Should SLH-DSA be included in the profile or only discussed as crypto-diversity future work?
4. Can RPKI CMS signedAttrs requirements be combined with RFC 9882 ML-DSA and RFC 9814 SLH-DSA without profile conflict?
5. How should validators cleanly fail on unsupported PQC algorithms?
6. Should semantic equivalence between RSA and PQC branches be a MUST, SHOULD, or operational recommendation?
7. Should RPKI use parallel publication, composite signatures, or both?
8. Should Null Scheme-like reductions be revived or avoided?
9. Does PQC migration require trust-anchor or TAK procedure updates?
10. Should ASPA, RSC, or BGPsec be included or deferred?
11. Are existing PKIX/CMS OIDs sufficient, or should RPKI define suite identifiers or validator error classes?
