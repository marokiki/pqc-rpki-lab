# pqc-rpki-lab

Experimental harness and evidence for
`draft-yoshikawa-sidrops-pqc-rpki-00`.

> EXPERIMENTAL / NOT FOR PRODUCTION

The repository evaluates post-quantum signature migration in RPKI while
reusing existing cryptographic and RPKI implementations. It does not implement
cryptographic algorithms, X.509/CMS validation, RRDP, rsync, or an RPKI
validator.

## Scope

The comparison covers:

- RSA-2048/SHA-256
- P-256/SHA-256 and Ed25519 as compact classical references
- ML-DSA-44, ML-DSA-65, and ML-DSA-87
- SLH-DSA-SHAKE-128s and SLH-DSA-SHAKE-192s

Small-PQ composite suites are size-model candidates, not confirmed
interoperable algorithms. Falcon, MAYO, SNOVA, and HAWK remain research
candidates.

## Run

Python 3.11 or later is required. The default run performs no network access.

```sh
make
```

This runs the benchmarks, estimators, validators' presence checks, VRP
equivalence checks, report generation, and tests. Missing optional software is
recorded as `unsupported` or `skipped`.

Optional inputs:

```sh
PQC_RPKI_CACHE=/path/to/local/rpki-cache tools/run_all.sh
PQC_RPKI_ITERATIONS=100 tools/run_all.sh
python3 tools/vrp_equivalence.py --baseline rsa.csv --candidate pqc.json
make review-evidence
```

`make install-optional-pqc` is the only network-enabled installation path. It
installs pinned liboqs and oqs-python versions into repository-local ignored
directories.

## Evidence

Machine-readable results are under `results/` as CSV and JSON. Markdown files
in the same directory are generated views. The principal outputs are:

- `results/primitive-bench.json`
- `results/repository-impact.json`
- `results/object-generation-feasibility.json`
- `results/validator-errors.json`
- `results/vrp-equivalence.json`
- `results/report.json`

Core primitive timings are end-to-end OpenSSL CLI wall-clock measurements.
Each operation includes process startup and file I/O. Compare timing values
only when `comparable_group` is identical; these values are not pure algorithm
cycle counts. Repository-impact results are synthetic estimates.

`make review-evidence` writes OpenSSL in-process throughput and signing-only
100,000-object/key-roll projections under `results/review-2026-06/`. These
values do not claim complete Manifest generation. The published `draft-00`
snapshot remains available at the Git tag and Release of the same name.

The exact 100,000-operation benchmark is intentionally separate from the
default and review targets because it can take several minutes:

```sh
make exact-100k
```

It compiles `benchmarks/exact_100k.c` in a temporary directory and writes
results to `results/review-2026-06/exact-100k.*`. It performs 100,000 signing
and 100,000 verification operations per algorithm; it is not a complete RPKI
Manifest-generation benchmark.

After `make install-optional-pqc`, run the sequential composite-component
benchmark with:

```sh
make composite-100k
```

This requires both component signatures to verify, but does not implement
the LAMPS composite ASN.1/OID format.

OpenSSL generated resource-profile ML-DSA and SLH-DSA certificates and CRLs in
the recorded environment. Pure-PQC CMS SignedData, complete MFT/ROA fixtures,
and validator interoperability remain unsupported or unconfirmed as recorded
in the result files.

## Draft

The authoring source is
`ietf/draft-yoshikawa-sidrops-pqc-rpki-00.md`. Submission artifacts are:

- `ietf/submission/draft-yoshikawa-sidrops-pqc-rpki-00.xml`
- `ietf/submission/draft-yoshikawa-sidrops-pqc-rpki-00.txt`

Generate the standalone XML with:

```sh
python3 tools/render_draft_submission.py
xml2rfc --text ietf/submission/draft-yoshikawa-sidrops-pqc-rpki-00.xml
```

## Safety

Do not commit private keys, credentials, production TALs, or operational RPKI
objects. Object-generation tests use temporary directories and delete their
keys and generated objects after measurement.
