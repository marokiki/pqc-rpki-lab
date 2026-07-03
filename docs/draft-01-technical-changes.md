# Draft-01 Technical Changes

> EXPERIMENTAL / NOT FOR PRODUCTION

This public note lists technical changes needed for `draft-01` without
including private review-thread history.

- Treat the signature profile as applying to RFC 6488 signed objects generally,
  with ROA and Manifest as the first complete payload targets.
- Keep certificates and CRLs in scope because they determine certification-path
  and publication-state behavior.
- Separate BGPsec Router Certificate processing from BGPsec UPDATE signature
  algorithms. The RPKI certificate side is in scope; router UPDATE signing is
  not.
- Compare RSA-2048, P-256, Ed25519, ML-DSA-44, ML-DSA-65, ML-DSA-87,
  Falcon-512 where supported, and standards-track composite candidates.
- Reduce dependence on a single fixed ML-DSA-65 recommendation until object
  generation, repository impact, and validator interoperability are measured.
- Present parallel publication as an experimental comparison tool, not a
  complete operational migration strategy.
- Add mixed-tree migration at CA boundaries and reject arbitrary per-object
  algorithm mixing inside one publication scope.
- Add Manifest/product key-consistency checks using RFC 6488 EE-certificate
  semantics.
- State that composite signatures are not legacy-validator-compatible and that
  component benchmarks are not LAMPS composite interoperability.
- Preserve open issues and blockers explicitly.

