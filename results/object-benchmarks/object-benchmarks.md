# Object-Level Payload Benchmark

> EXPERIMENTAL / NOT FOR PRODUCTION

Build deterministic synthetic ROA-like payload records, hash each payload, and encode a deterministic Manifest file list. Complete CMS SignedData, certificate generation, DER object serialization, publication, and validator processing are outside this benchmark.

| Workload | Objects | Payload Construction Ms | File Hashing Ms | Manifest Payload Encoding Ms | Manifest Payload Bytes | Cms Assembly Status | Signing Status | Der Serialization Status | Classification |
|---|---|---|---|---|---|---|---|---|---|
| synthetic-manifest-payloads | 100000 | 61.617 | 26.734416 | 79.470667 | 10900001 | blocked | not-measured-here | payload-only | object-payload benchmark, not complete RFC 6488 CMS generation |
