# Migration Analysis

> EXPERIMENTAL / NOT FOR PRODUCTION

| Method | Duplicate product trees | Legacy RSA-only RP | Main issue | Current status |
|---|---:|---:|---|---|
| RFC 6916 parallel suites | yes | can use Suite A | branches can diverge | specified, not operationally demonstrated |
| Mixed tree | no | fails on an unsupported algorithm | requires RP-first deployment and RFC 6916 changes | research implementation reported |
| Composite suite | no | cannot verify composite objects | larger objects and new X.509/CMS support | LAMPS work in progress |
| Mixed tree to composite | no | cannot verify migrated branches | combines both implementation requirements | selected -01 design; implementation incomplete |

Parallel publication remains useful for controlled experiments because it permits direct comparison of validation results. CCR can detect divergent VRP sets but cannot keep the two product trees synchronized or choose an authoritative branch.

A mixed tree permits an issuer signature algorithm and subject public-key algorithm to differ. It removes the requirement to maintain two complete product trees, but a CA is not fully protected against a quantum attack while an RSA ancestor remains able to issue an alternative certificate for its resources.

A composite signature combines traditional and PQ signatures in one algorithm
and one signed object. It prevents payload divergence between two signature
branches and retains classical unforgeability if either component remains
secure, because both component signatures must validate. It is not backward
compatible with deployed RSA-only validators, and after a CRQC breaks the
classical component its security depends on the PQ component. Draft-01 selects
the composite plus mixed-tree combination.

The algorithm and RFC 6488 profile can remain in the PQC profile document. A deployable RP-readiness, TAL, rollover, rollback, and classical-retirement procedure should be specified in a document that updates or replaces RFC 6916.

## Public implementation status

The repository includes a synthetic mixed-tree fixture under
`results/mixed-tree/` and `testdata/mixed-tree/`. It models the CA-boundary
transition from an RSA-signed child CA certificate to an ML-DSA child SPKI and
ML-DSA child products. It is component-level evidence for consistency checks,
not an implementation of the selected composite suite or validator
interoperability evidence.
