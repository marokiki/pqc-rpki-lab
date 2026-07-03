# IANA and RPKI Profile Questions

> EXPERIMENTAL / NOT FOR PRODUCTION

## Current position

The draft currently assumes no new IANA registry is needed because ML-DSA and SLH-DSA object identifiers are already defined by the relevant PKIX/CMS RFCs. RPKI would profile the allowed subset rather than allocate new cryptographic identifiers.

OpenSSL 3.6.2 recognizes the standardized ML-DSA and SLH-DSA OIDs directly,
including `id-ml-dsa-65`. The observed CMS failure is not an unknown-OID
failure; it occurs because the CMS signer path cannot select a default digest
for the pure ML-DSA key. No new OID would fix that implementation gap.

## Questions to resolve

1. Should RPKI define its own algorithm-suite name, such as `rpki-mldsa65-2026`, even if no new OID is allocated?
2. Should the RPKI algorithm profile registry be expanded to track current, next, deprecated, and forbidden suites?
3. Should validator error classes for unsupported algorithms be standardized?
4. Should manifest or repository metadata indicate branch equivalence between RSA and PQC publication points?
5. Should a future version update RFC 7935, RFC 6487, RFC 6488, or RFC 6916 after complete object-generation and validator evidence exists?

## Draft guidance

For the initial draft, keep IANA minimal and include a clear table:

| Item | New IANA action? | Reason |
|---|---:|---|
| ML-DSA-65 OID | no | inherited from PKIX/CMS RFCs |
| ML-DSA-87 OID | no | inherited from PKIX/CMS RFCs |
| SLH-DSA OIDs | no | inherited from PKIX/CMS RFCs |
| RPKI algorithm suite name | TBD | may help operational clarity |
| Validator error classes | TBD | may be useful but not strictly required |

The current draft revision intentionally does not declare an `Updates:` relationship.
That relationship should be added only after the profile moves from experimental
evidence gathering to a concrete replacement or extension of the RFC 7935 RPKI
algorithm profile.
