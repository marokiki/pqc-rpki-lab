# Routinator/Krill Patch Plan

> EXPERIMENTAL / NOT FOR PRODUCTION

No patch files are stored in this public repository. When patches are created, they should live in the relevant upstream worktree or PR branch.

| Project | Area | Patch Unit | Upstream Source | Status |
|---|---|---|---|---|
| Routinator | algorithm-registry | Register ML-DSA and candidate composite AlgorithmIdentifiers. | external checkout; not vendored | planned |
| Routinator | x509-verification | Verify certificate SPKI and signature algorithms across CA boundaries. | external checkout; not vendored | planned |
| Routinator | cms-verification | Verify RFC 6488 SignedData with PQC signature algorithms. | external checkout; not vendored | planned |
| Routinator | manifest-consistency | Reject products outside the Manifest signer issuing context. | external checkout; not vendored | planned |
| Routinator | mixed-tree | Allow algorithm transition at CA boundaries without per-object mixing. | external checkout; not vendored | planned |
| Routinator | vrp-ccr-export | Export VRPs or CCR-compatible ROAPayloadState for semantic comparison. | external checkout; not vendored | planned |
| Krill | ca-key-algorithm | Abstract CA key algorithms beyond RSA. | external checkout; not vendored | planned |
| Krill | child-ca-issuance | Issue child certificates whose SPKI algorithm differs from issuer signature algorithm. | external checkout; not vendored | planned |
| Krill | ee-certificate | Generate RFC 6488 EE certificates for PQC object signers. | external checkout; not vendored | planned |
| Krill | cms-signing | Sign Manifest and ROA CMS objects with selected algorithm suite. | external checkout; not vendored | planned |
| Krill | publication | Publish RSA baseline, PQC branch, and mixed-tree repositories reproducibly. | external checkout; not vendored | planned |
| Krill | transport-size | Measure RRDP snapshot, RRDP delta, and rsync output growth. | external checkout; not vendored | planned |
