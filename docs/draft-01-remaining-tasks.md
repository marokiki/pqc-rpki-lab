# Draft-01 Remaining Tasks

> EXPERIMENTAL / NOT FOR PRODUCTION

## Required before posting -01

1. Confirm the current ASPA, CCR, and LAMPS composite draft revisions against
   their public datatracker records.
2. Create an immutable evidence commit or release and replace the provisional
   draft-01 repository reference.
3. Render the final RFCXML and run `xml2rfc` and datatracker submission checks.
4. Regenerate public reports, run `make test`, `make verify-artifacts`, and
   `make pre-publication` against the exact submission commit.

## Highest-priority implementation track

1. Generate standards-conformant `id-MLDSA65-ECDSA-P256-SHA512`
   certificates, CRLs, manifests, and ROAs, and verify that failure of either
   component rejects the object.
2. Extend Routinator or another RP to recognize the composite SPKI and
   signature identifiers, then validate the complete composite repository.
3. Extend Krill or an equivalent CA implementation for mixed issuer/subject
   algorithms, composite EE issuance, CMS signing, and publication.
4. Generate a complete RSA-to-composite mixed-tree repository and measure
   whether unsupported RPs drop only the child subtree.

## Additional evidence after -01

1. Add complete ML-DSA-44/87 and SLH-DSA CMS fixtures where provider support
   permits.
2. Measure real RRDP snapshots/deltas, rsync transfer, full-validator memory,
   and HSM support.
3. Compare real CCR `ROAPayloadState.hash` output across suites.
4. Measure complete composite encodings rather than sequential component
   lower bounds.

The first section is a posting gate. The implementation and additional
evidence sections are not prerequisites for accurately publishing the current
experimental -01 status, provided the draft does not claim interoperability.
