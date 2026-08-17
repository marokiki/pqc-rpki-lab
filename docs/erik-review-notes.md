# Erik protocol review notes

These notes were produced while adding the PQC repository-transport campaign.
They are review material, not comments already submitted to the Erik authors.

## Proof-of-concept build dependency

The Docker build at APNIC `rpki-erik-demo` commit
`0fc81bb83db00d7434ea444909b0dc42a63c145b` fails while building
`Compress::Raw::Zlib` because `zlib.h` is unavailable.  Installing
`zlib1g-dev` in `docker-prep.sh` made the documented Docker build and all
81 tests pass.  The repository should declare that build dependency.

## Specification-to-implementation version mapping

The proof of concept still exposes the earlier TTQ path, whereas
draft-ietf-sidrops-rpki-erik-protocol-07 specifies snapshot buffers and
segment buffers.  Its README does not identify the implemented draft
revision.  A version or feature matrix would prevent benchmark results from
being attributed to the wrong protocol revision.

## Reproducible transport accounting

Interoperability and performance reports should state whether byte counts
include HTTP headers, TLS, HPACK or QPACK, gzip, and RFC 9842 Compression
Dictionary Transport.  Published transition fixtures for cold, unchanged,
single-publication, and burst-churn states would also make independent
comparisons reproducible.
