# Scope Boundary: TAK, ASPA, RSC, and BGPsec

> EXPERIMENTAL / NOT FOR PRODUCTION

## Initial draft scope

The current draft should focus on the RPKI object and validation path that directly affects ROA-derived VRPs:

- resource certificates,
- CRLs,
- manifests,
- ROAs,
- CMS signed object template,
- validator behavior,
- repository synchronization impact,
- migration behavior for RSA/PQC parallel publication.

## Trust Anchor Key rollover

TAK is related but should remain a separate track unless the PQC transition requires trust anchor changes that cannot be handled by existing TAL/TAK procedures.

Next work:

- describe whether the PQC profile assumes a PQC TA,
- describe whether RSA TA and PQC TA can coexist,
- identify whether RFC 9691 needs updates or only operational guidance,
- decide whether PQC TA transition belongs in this draft or a companion draft.

## ASPA

ASPA is RPKI-signed data but is not required for the first ROA/VRP-focused draft. It should be listed as future work unless the object profile changes are identical and easy to inherit.

Next work:

- determine whether ASPA CMS profile can reuse the same algorithm suite text,
- avoid making ASPA a blocker for ROA-focused PQC migration.

## RSC

RSC is useful for RPKI signed object generality, but it is not required for route origin validation. Keep it deferred unless implementation effort shows signed object behavior is identical.

## BGPsec

BGPsec path signatures are a separate protocol and should not be included in the first RPKI repository/validator draft. BGPsec PQC migration has different performance, message size, and router processing constraints.

## Router protocol

RTR and router VRP consumption should remain unchanged. The validator absorbs PQC signature verification and exports the same semantic VRP data model.
