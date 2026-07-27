# Real-World Repository Measurement Plan

> EXPERIMENTAL / NOT FOR PRODUCTION

## Purpose

The current repository impact numbers are synthetic estimates. The next phase must calibrate them against real local RPKI caches before proposing ML-DSA-65 as a MUST or SHOULD-level RPKI next-suite algorithm.

## Current result

One operator-supplied Routinator snapshot has now been reduced to a public-safe
aggregate profile. The result is explicitly
`skipped` in `results/real-repository-summary.csv/json/md`. The adapter records
count, total, min, median, p95, max, object age, and objects changed within 24
hours when `PQC_RPKI_CACHE` is supplied.

## Inputs

The measurement must run only on local cache paths supplied explicitly by the operator.

Supported inputs:

- Routinator cache directory
- rpki-client cache/output directory
- FORT cache directory
- rsync/RRDP mirror directory

No network fetching should occur by default.

## Metrics

Collect:

- object count by extension: `.cer`, `.roa`, `.mft`, `.crl`, others,
- total size by object type,
- min/median/p95/max size by object type,
- per-publication-point size,
- per-trust-anchor size if derivable,
- estimated RSA baseline bytes,
- projected ML-DSA-65 bytes,
- projected ML-DSA-87 bytes,
- projected SLH-DSA-SHAKE-128s bytes,
- projected SLH-DSA-SHAKE-192s bytes,
- RRDP snapshot projection,
- RRDP delta projection under configurable update ratios,
- local cache growth ratio.

## Sampling method

Use at least three snapshots if available:

1. current local cache,
2. cache after normal refresh interval,
3. cache after a manifest/CRL-heavy update if available.

The current result is marked `single_snapshot`: 550,210 objects across 54,960
publication points, producing 980,019 VRPs while ARIN was unavailable. If only
one cache is available, retain that classification.

The profile is an input distribution, not yet a complete re-signed synthetic
corpus. A 1,000-ROA single-child Krill run established that object generation
and RSA rollback scale to that count; both experimental RPs also produced the
expected 1,000 VRPs from the Composite state. Full RSA, pure ML-DSA-65,
Composite, and mixed-tree measurements over a topology-shaped corpus remain
open.

## Output

- `results/real-repository-summary.csv`
- `results/real-repository-summary.json`
- `results/real-repository-summary.md`
- `results/real-cache-projection.csv`
- `results/real-cache-projection.md`
- `results/figures/real-cache-size-by-object-type.png`
- `results/figures/projected-repository-growth.png`

## Draft impact

The resulting data should determine whether the draft says:

- ML-DSA-65 MUST be implemented,
- ML-DSA-65 SHOULD be implemented,
- ML-DSA-65 is a candidate pending operational data,
- SLH-DSA is only optional/future,
- RRDP operational guidance is required in the same document.
