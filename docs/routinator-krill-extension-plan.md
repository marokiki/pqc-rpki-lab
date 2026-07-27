# Routinator/Krill Extension Plan

> EXPERIMENTAL / NOT FOR PRODUCTION

This document records the extension plan and its current experimental
implementation. It does not vendor upstream source code or claim upstream
support.

## Local-only upstream checkouts

Use explicit environment variables for local experiments:

```sh
PQC_RPKI_ROUTINATOR_SRC=local/upstream/routinator
PQC_RPKI_KRILL_SRC=local/upstream/krill
PQC_RPKI_ROUTINATOR_BIN=/path/to/routinator
PQC_RPKI_KRILL_BIN=/path/to/krill
```

The pinned checkouts and CA state stay below ignored `local/`. Public,
reviewable patches are stored under `patches/`.

## Routinator extension points

| Area | Experimental status |
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
| CA key abstraction | Implemented for RSA, pure ML-DSA-65, and the selected Composite suite behind an experimental gate. |
| Child CA issuance | Implemented for an RSA parent and Composite child in the fixed testbed scenario. |
| EE certificates | Implemented for the Composite child publication point. |
| CMS signing | Composite Manifest and ROA signing implemented with explicit SHA-512. |
| Publication repository | Composite publication and rollback-to-RSA snapshots are captured below `local/` and summarized publicly. |
| Transport measurement | Still open beyond the isolated fixture. |

## Public evidence

`make routinator-krill-scan` records read-only source-layout evidence when
explicit source paths are configured. `make routinator-krill-interop` records
binary/repository experiment status when explicit binaries and generated
repositories are configured. Missing inputs are recorded as `skipped`, not as
algorithm failure.

`make krill-experimental-e2e` runs the implemented issuance and rollback
scenario and validates both phases with rpki-client and Routinator. The
result is `results/composite-e2e/krill-rollover.json`.
