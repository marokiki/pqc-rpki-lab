# Composite Signatures, Parallel Publication, and Null Scheme Decision Notes

> EXPERIMENTAL / NOT FOR PRODUCTION

## Current recommendation

Parallel publication, Composite signatures, and Mixed Certification Chains
remain independent migration choices. Draft-02 reports Composite and
Mixed-tree feasibility without selecting a production transition model.
Null Scheme-like designs remain a separate analysis track.

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

Composite ML-DSA raw signing and verification are implemented against `draft-ietf-lamps-pq-composite-sigs-19`. The implementation covers the message representative defined by revision 19, ML-DSA context binding, both component operations, raw public-key and signature concatenation, and all-component verification. The measured variants are ML-DSA-44 with P-256, ML-DSA-65 with P-256, and ML-DSA-87 with P-384. Revision 19 does not define ML-DSA-87 with P-256.

The repository now defines an experimental RPKI X.509/CMS profile for
id-MLDSA65-ECDSA-P256-SHA512 and demonstrates one controlled E2E path through
experimental rpki-client and Routinator patches. Krill also exercises
RSA-parent to Composite-child issuance, publication, and RSA rollback in an
isolated testbed. These implementations share one OpenSSL/provider backend,
so they are not independent cryptographic interoperability.
Composite may reduce branch consistency problems, but it introduces RPKI
questions:

- Can legacy RPs parse or cleanly reject composite objects?
- Does composite reduce or increase total repository size compared with parallel publication?
- Should RPKI require non-separability properties?
- Is a composite signature profile stable enough for RPKI Standards Track dependency?
- Does composite complicate CA key management and rollover?

Raw measurements are in `results/draft-composite-2026-07/`; complete object,
RP, negative-test, and E2E results are in `results/composite-e2e/`. Decision
status remains `experimental`. Controlled evidence now includes repeated
1,000-ROA issuance/validation, a 100-publication-point topology pilot, and a
one-ROA update. Independent cryptographic implementation, public-topology
re-signing, production RRDP/rsync behavior, and longitudinal repository-scale
operation remain future work.

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
| Composite | likely unsupported by legacy RPs | hybrid | 3.16x, 4.09x, or 5.40x in the first-order raw-size model | lower branch risk | LAMPS composite + RPKI profile |
| Null Scheme-like | unknown | depends on design | potentially lower | unknown | new SIDROPS work |
