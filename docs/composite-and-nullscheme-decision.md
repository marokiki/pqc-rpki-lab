# Composite Signatures, Parallel Publication, and Null Scheme Decision Notes

> EXPERIMENTAL / NOT FOR PRODUCTION

## Current recommendation

For draft-00 and the next implementation phase, keep the mainline transition model as parallel RSA/PQC publication. Keep composite signatures and Null Scheme-like designs as separate analysis tracks.

## Why parallel publication first

Parallel publication aligns with the RPKI algorithm agility model and allows legacy relying parties to continue validating RSA objects while PQC-aware relying parties validate the PQC branch. It also allows semantic equivalence checks between branches before router-facing VRP output changes.

Operational concerns:

- branch inconsistency,
- downgrade behavior,
- repository size growth,
- manifest and CRL duplication,
- parent/child transition order,
- stale branch handling.

## Composite signature track

Composite ML-DSA for X.509 and CMS is relevant because it can bind classical and PQC signatures inside one object. This may reduce branch consistency problems, but it introduces new RPKI questions:

- Can legacy RPs parse or cleanly reject composite objects?
- Does composite reduce or increase total repository size compared with parallel publication?
- Should RPKI require non-separability properties?
- Is a composite signature profile stable enough for RPKI Standards Track dependency?
- Does composite complicate CA key management and rollover?

Decision status: `future work`, not mainline for draft-00.

## Null Scheme track

Null Scheme-like ideas may reduce the cost of one-time EE certificates and signed objects. This could be important because RPKI uses EE certificates for signed objects, and PQC public keys and signatures substantially increase object size.

However, the known Null Scheme draft is expired and should not be a normative dependency. The correct next action is to analyze the idea as a size-reduction design pattern, not to depend on the expired draft.

Decision status: `research question`, not mainline for draft-00.

## Required comparison table

The next draft revision should include a non-normative decision matrix comparing:

| Model | Legacy RP behavior | PQC security | Size impact | Consistency risk | Standardization dependency |
|---|---|---|---|---|---|
| RSA only | works | none | baseline | none | existing RFCs |
| Parallel RSA/PQC | works for RSA branch | yes for PQC-aware RPs | high | high unless equivalence checked | RPKI PQC profile |
| PQC only | fails for legacy RPs | yes | medium/high | low | full migration required |
| Composite | likely unsupported by legacy RPs | hybrid | unknown | lower branch risk | LAMPS composite + RPKI profile |
| Null Scheme-like | unknown | depends on design | potentially lower | unknown | new SIDROPS work |
