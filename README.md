# pqc-rpki-lab

Experimental harness and evidence for
`draft-yoshikawa-sidrops-pqc-rpki-00`.

> EXPERIMENTAL / NOT FOR PRODUCTION

The repository evaluates post-quantum signature migration in RPKI while
reusing existing cryptographic and RPKI implementations. It does not implement
cryptographic algorithms, X.509/CMS validation, RRDP, rsync, or an RPKI
validator.

## Scope

The required comparison covers:

- RSA-2048/SHA-256
- ML-DSA-65 and ML-DSA-87
- SLH-DSA-SHAKE-128s and SLH-DSA-SHAKE-192s

ML-DSA-44 is retained as an excluded-policy comparison. Falcon, MAYO, SNOVA,
and HAWK are optional candidates and remain outside the proposed profile.

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
