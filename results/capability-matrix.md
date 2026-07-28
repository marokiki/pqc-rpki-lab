# Capability Matrix

> EXPERIMENTAL / NOT FOR PRODUCTION

| Component | Status | Backend | Notes |
|---|---|---|---|
| Static algorithm metadata | confirmed | Python standard library | Profile role and comparison scope are recorded separately |
| Primitive benchmark | confirmed | OpenSSL CLI; optional oqs-python | Timing class and comparable group are recorded per row |
| Repository/RRDP/cache estimator | estimated | Python standard library | First-order model |
| Real repository cache adapter | skipped | filesystem | Requires explicit cache path |
| VRP equivalence checker | estimated | CSV/JSON | Synthetic input by default |
| Validator wrappers | confirmed | existing executables | Version-only, no network |
| RFC-profiled PQC X.509/CRL generation | confirmed | OpenSSL 3 | Temporary keys only; RFC 3779 extensions included |
| PQC CMS SignedData generation | unsupported | OpenSSL 3 CMS CLI | Failure reason recorded in object-generation results |
| Experimental PQC RPKI E2E | confirmed | rpki-client and Routinator with OpenSSL provider | Pure ML-DSA-65, Composite, and mixed-tree fixtures; shared cryptographic backend |
| Experimental CA lifecycle | confirmed | Krill with OpenSSL provider | Composite issuance, one-ROA update, and RSA rollback in an isolated testbed |
