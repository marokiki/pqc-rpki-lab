# Research Questions

1. Which standardized PQC signature is practical for RPKI?
2. How do candidates affect certificates, CRLs, manifests, ROAs, repositories, RRDP, and caches?
3. Can RFC 6487/6488 objects be generated using RFC 9881/9882/9909/9814 encodings without ad-hoc profiles?
4. Which existing validators can parse, reject, or validate generated PQC RPKI objects?
5. Do RSA and PQC validation runs produce the same CCR `ROAPayloadState.hash`?
6. Which combination of mixed-tree migration and pure or composite signatures is operationally viable?
7. Are Null Scheme-like reductions useful enough to justify new SIDROPS work?
8. Which downgrade and mixed-validator failures require normative handling?

The protocol-level issue list is maintained in the Open Issues section of `ietf/draft-yoshikawa-sidrops-pqc-rpki-00.md`.
