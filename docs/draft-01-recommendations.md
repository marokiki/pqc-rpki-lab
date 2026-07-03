# Draft-01 Recommendations

> EXPERIMENTAL / NOT FOR PRODUCTION

Recommended draft posture:

- Keep normative strength conservative until the selected Composite ML-DSA
  repository is accepted by a modified validator and equivalent VRPs are
  demonstrated.
- Include the RSA and ML-DSA-65 `.mft` and `.roa` fixture evidence. State that
  the OpenSSL CMS API works with explicit SHA-512 while the default-digest CLI
  path fails.
- Distinguish primitive cryptographic timing, object-generation timing,
  repository-size modeling, parser compatibility, validator interoperability,
  and VRP semantic equivalence.
- Use ML-DSA-44/65/87 and compact classical references in all comparison
  tables. Include Falcon-512 only where library support or literature evidence
  is clearly labeled.
- Use `id-MLDSA65-ECDSA-P256-SHA512` as the primary experimental Next Suite.
  Require both component signatures to validate and prohibit component-key
  reuse.
- Use composite plus mixed-tree as the selected migration design: the parent
  signs a transition certificate whose child SPKI carries the composite key,
  and the child publication scope uses the composite suite.
- Add a Routinator/Krill interoperability track. Krill is the preferred
  production-like publication path to investigate, and Routinator is the
  preferred validator path to test parser, signature, certification-path,
  Manifest, CRL, and VRP behavior.
- Record the unmodified-validator baseline: Routinator 0.15.2, rpki-client 9.8,
  and FORT 1.6.8 accept RSA and reject ML-DSA-65 before VRP output.
- Treat the local VRP hash as an interim semantic-equivalence tool. Replace it
  with CCR `ROAPayloadState.hash` when real CCR output is available.
- Keep null-scheme discussion optional and non-blocking.
