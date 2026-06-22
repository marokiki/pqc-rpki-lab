# Draft Revision Recommendations

For a revision after `draft-00`:

1. Treat ROA, Manifest, ASPA, RSC, and TAK as one RFC 6488 algorithm profile.
2. Exclude BGPsec UPDATE signatures; BGPsec router certificates remain part of the RPKI certificate system.
3. Replace the independent VRP-equivalence definition with CCR `ROAPayloadState.hash` comparison and decoded `rps` diagnostics.
4. Present P-256 or Ed25519 as compact classical references and retain ML-DSA-44 in the measured comparison.
5. Evaluate small-PQ composite suites; do not describe them as compatible with RSA-only validators.
6. Describe parallel publication as an experimental comparison method, not the preferred operational migration.
7. Evaluate mixed-tree migration, including migration toward a composite suite.
8. Move the complete migration procedure to a document that updates or replaces RFC 6916.
9. Keep the Null Scheme optional; if selected, coordinate it with the PQC migration rather than requiring a second repository-wide rollover.
