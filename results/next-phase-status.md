# Next Phase Status

> EXPERIMENTAL / NOT FOR PRODUCTION

This file records the status of tasks needed before a stronger SIDROPS Internet-Draft revision.

| Area | Current status | Next action |
|---|---|---|
| RFC-profiled PQC certificates/CRLs | confirmed | retain reproducible OpenSSL evidence |
| PQC CMS/MFT/ROA | unsupported | find RFC 9882-capable CMS and existing payload generator |
| Validator interoperability | unsupported/not measured | probe Routinator, rpki-client, FORT |
| Real cache measurement | input-dependent | run with `PQC_RPKI_CACHE=/path` |
| Repository impact | synthetic estimate | calibrate with real cache |
| Composite signatures | future work | compare against parallel publication |
| Null Scheme-like reduction | research question | analyze size benefit without normative dependency |
| TAK/ASPA/RSC/BGPsec | deferred | keep out of first ROA-focused profile unless needed |
| IANA action | no new crypto OID indicated | revisit suite names/error classes |
