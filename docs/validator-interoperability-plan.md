# Validator Interoperability Plan

> EXPERIMENTAL / NOT FOR PRODUCTION

## Purpose

The draft cannot make strong deployment claims until existing relying-party software behavior is measured. The next phase must test how major validators behave with RSA baseline fixtures and PQC-profiled fixtures.

## Current result

Pinned unmodified Routinator 0.15.2, rpki-client 9.8, and FORT 1.6.8 containers
were tested against isolated local rsync repositories. All three accepted the
RSA baseline and emitted its VRP. All three rejected ML-DSA-65 at the TAL or
certificate layer before signed-object validation. No production TAL or
operational repository was used.

## Validators

Minimum target set:

- Routinator
- rpki-client
- FORT

Optional:

- OctoRPKI if available
- Krill internal validation paths if useful

## Test matrix

| Case | Input | Expected legacy behavior | Expected PQC-aware behavior |
|---|---|---|---|
| RSA baseline | RSA fixture repository | valid | valid |
| ML-DSA-65 valid | PQC fixture repository | clean reject or unsupported | valid |
| ML-DSA-87 valid | PQC fixture repository | clean reject or unsupported | valid or unsupported |
| SLH-DSA valid | PQC fixture repository | clean reject or unsupported | valid or unsupported |
| inconsistent ROA | RSA/PQC branch mismatch | detect divergence by external checker | detect divergence by external checker |
| stale manifest | PQC branch stale | invalid or warning depending fixture | invalid or warning depending fixture |
| unknown algorithm | intentionally unknown OID | clean reject | clean reject |

## Output format

Produce:

- `results/validator-capability.csv`
- `results/validator-errors.json`
- `results/validator-interoperability.md`
- `results/vrp-equivalence.csv`
- `results/vrp-equivalence.md`

For every validator run, record:

- command,
- version,
- input repository,
- TAL used,
- exit code,
- stderr summary,
- parsed VRP output if available,
- failure class.

Failure classes:

- `valid`
- `unsupported_algorithm`
- `parse_error`
- `profile_error`
- `path_validation_error`
- `manifest_error`
- `crl_error`
- `repository_error`
- `tool_missing`
- `blocked`

## Semantic equivalence

The core migration safety property is that RSA and PQC branches produce the same validated routing semantics during parallel publication.

Compare at least:

- prefix,
- maxLength,
- origin AS,
- trust anchor/source,
- object URI if available,
- validity interval if available.

A difference in signature algorithm alone must not change the VRP set. A difference in ROA content, validity, or resource set must be detected and reported.

## Draft impact

Interoperability results should feed directly into:

- Implementation Status,
- Operational Considerations,
- Security Considerations,
- downgrade behavior,
- unsupported validator behavior,
- semantic equivalence requirement language.
