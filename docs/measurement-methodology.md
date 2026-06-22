# Measurement Methodology

Primitive operations use a deterministic 32-byte message and median wall-clock time. The RSA baseline and the required ML-DSA/SLH-DSA comparison rows use one OpenSSL CLI subprocess per timed key generation, signing, or verification operation. These values include process startup, provider initialization, argument parsing, file I/O, and the cryptographic operation. They are end-to-end CLI measurements, not pure algorithm cycle counts. Timing ratios are valid only between rows with the same `comparable_group`; closely grouped verification values primarily characterize the common CLI path.

Optional algorithms use oqs-python/liboqs when available. Those measurements are in-process and belong to a separate comparable group, so they MUST NOT be directly divided by OpenSSL CLI values. A pure per-operation comparison requires all algorithms to use a common in-process API or a benchmark that subtracts and validates harness overhead.

Repository impact applies standardized or candidate parameter sizes to a documented synthetic corpus. Composite rows add component sizes and exclude composite ASN.1 overhead. They are estimates, not measured objects.

VRP-set equality excludes trust-anchor and source attribution. When CCR output is available, compare `ROAPayloadState.hash` and decode `rps` only when hashes differ. The current helper hashes canonical JSON and is explicitly not a CCR DER implementation. Trust-anchor and source attribution are reported separately.

Bulk signing uses `openssl speed`, which keeps provider and process startup outside the timed loop. Its 100,000-manifest and key-roll values are signing-only lower bounds, not complete object-generation measurements. CSV/JSON contain backend, timing scope, comparability group, and status fields and are the primary evidence.

The exact-count benchmark is a separate manual phase. It generates one key pair per algorithm, then performs exactly 100,000 EVP signing operations and 100,000 verification operations. It includes EVP context initialization in each operation but excludes key generation, process startup, RPKI object encoding, file I/O, publication, and HSM latency. The default `run_all.sh` and `make review-evidence` targets MUST NOT invoke this benchmark.

The composite-component benchmark signs the same message with both named components sequentially and accepts a verification only when both component signatures verify. OpenSSL EVP provides RSA, P-256, and ML-DSA; pinned liboqs provides Falcon-512. The measurement excludes composite OIDs, ASN.1 encoding, domain separation, CMS/X.509 processing, and HSM behavior, so it MUST NOT be described as LAMPS composite interoperability.

Current repository-impact data is `estimated`, not proof of global deployability. Before increasing normative language in the Internet-Draft, calibrate the estimator with a local RPKI cache supplied through `PQC_RPKI_CACHE` and produce real-cache projections.
