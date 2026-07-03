# Routinator/Krill Extension Plan

> EXPERIMENTAL / NOT FOR PRODUCTION

This public plan describes how Routinator and Krill should be used for
draft-01 interoperability work. It does not vendor upstream source code and
does not claim upstream support exists.

## Local-only upstream checkouts

Use explicit environment variables for local experiments:

```sh
PQC_RPKI_ROUTINATOR_SRC=local/upstream/routinator
PQC_RPKI_KRILL_SRC=local/upstream/krill
PQC_RPKI_ROUTINATOR_BIN=/path/to/routinator
PQC_RPKI_KRILL_BIN=/path/to/krill
```

The suggested checkout location is under ignored `local/upstream/`. Work-in-
progress upstream patches should stay in their own worktrees or branches, not
inside this public repository.

## Routinator extension points

| Area | Required work |
|---|---|
| Algorithm registry | Register ML-DSA and standards-track composite AlgorithmIdentifiers. |
| X.509 verification | Accept or reject certificate SPKI/signature algorithm combinations according to the selected profile. |
| CMS verification | Verify RFC 6488 SignedData with PQC signature algorithms. |
| Manifest consistency | Detect publication-scope gaps, wrong signer context, and mixed products inside one CA scope. |
| Mixed-tree validation | Permit algorithm transitions at CA boundaries without arbitrary per-object mixing. |
| VRP/CCR output | Export VRPs, and later CCR `ROAPayloadState`, for semantic comparison. |

## Krill extension points

| Area | Required work |
|---|---|
| CA key abstraction | Support CA keys beyond RSA while preserving current RSA behavior. |
| Child CA issuance | Allow issuer signature algorithm and child SPKI algorithm to differ at CA boundaries. |
| EE certificates | Generate RFC 6488 EE certificates for selected object-signing algorithms. |
| CMS signing | Produce Manifest and ROA CMS SignedData with the selected algorithm suite. |
| Publication repository | Publish RSA baseline, PQC branch, and mixed-tree repositories reproducibly. |
| Transport measurement | Measure RRDP snapshot, RRDP delta, and rsync output size. |

## Public evidence

`make routinator-krill-scan` records read-only source-layout evidence when
explicit source paths are configured. `make routinator-krill-interop` records
binary/repository experiment status when explicit binaries and generated
repositories are configured. Missing inputs are recorded as `skipped`, not as
algorithm failure.

