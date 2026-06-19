# Measurement Methodology

Primitive operations use a deterministic 32-byte message and median wall-clock time. The RSA baseline and the required ML-DSA/SLH-DSA comparison rows use one OpenSSL CLI subprocess per timed key generation, signing, or verification operation. These values include process startup, provider initialization, argument parsing, file I/O, and the cryptographic operation. They are end-to-end CLI measurements, not pure algorithm cycle counts. Timing ratios are valid only between rows with the same `comparable_group`; closely grouped verification values primarily characterize the common CLI path.

Optional algorithms use oqs-python/liboqs when available. Those measurements are in-process and belong to a separate comparable group, so they MUST NOT be directly divided by OpenSSL CLI values. A pure per-operation comparison requires all algorithms to use a common in-process API or a benchmark that subtracts and validates harness overhead.

Repository impact applies standardized or candidate parameter sizes to a documented synthetic corpus. It does not require a locally executable primitive backend and is classified as `estimated`. VRP comparison normalizes prefix, maxLength, origin AS, and TA/source. CSV/JSON contain backend, timing scope, comparability group, and status fields and are the primary evidence; Markdown views retain those limitations.

Current repository-impact data is `estimated`, not proof of global deployability. Before increasing normative language in the Internet-Draft, calibrate the estimator with a local RPKI cache supplied through `PQC_RPKI_CACHE` and produce real-cache projections.
