# pqc-rpki-lab

Experimental harness and evidence for
`draft-yoshikawa-sidrops-pqc-rpki`.

> EXPERIMENTAL / NOT FOR PRODUCTION

The repository evaluates post-quantum signature migration in RPKI while
reusing existing cryptographic and RPKI implementations. It does not implement
cryptographic algorithms, RRDP, rsync, or a production RPKI validator. It
provides fixture generation and experimental patches that delegate X.509/CMS
cryptography to OpenSSL providers and validation policy to existing RP code.

Public repository contents are limited to reproducible implementation,
measurements, public fixtures, public draft-support evidence, and explicit
limitations. Local-only notes, review context, scratch work, and private inputs
belong under ignored `local/`.

## Scope

The comparison covers:

- RSA-2048/SHA-256
- P-256/SHA-256 and Ed25519 as compact classical references
- ML-DSA-44, ML-DSA-65, and ML-DSA-87
- SLH-DSA-SHAKE-128s and SLH-DSA-SHAKE-192s

Small-PQ composite suites remain experimental. The repository contains
raw-construction and size-model results, complete Composite X.509/CMS fixture
generation, and a patch for one experimentally extended RP. This is a public
reference experiment, not independent interoperability evidence.
Falcon, MAYO, SNOVA, and HAWK remain research candidates.

## Run

Python 3.11 or later is required. The default run performs no network access.

```sh
make
```

This runs the benchmarks, estimators, validators' presence checks, VRP
equivalence checks, CCR-style interim comparison, object payload benchmarks,
mixed-tree fixture generation, report generation, tests, and public-boundary
checks. Missing optional software is recorded as `unsupported` or `skipped`.

Optional inputs:

```sh
PQC_RPKI_CACHE=/path/to/local/rpki-cache tools/run_all.sh
PQC_RPKI_ITERATIONS=100 tools/run_all.sh
python3 tools/vrp_equivalence.py --baseline rsa.csv --candidate pqc.json
make object-benchmarks
make rpki-objects
make key-roll
make local-validation
make cms-api-probe
make message-sweep
make validator-container-probe
make mixed-tree
make ccr-comparison
make routinator-krill-scan
make routinator-krill-interop
make pre-publication
make review-evidence
```

`make install-optional-pqc` is the only network-enabled installation path. It
installs pinned liboqs and oqs-python versions and builds a pinned oqs-provider
under repository-local ignored directories.

## Evidence

Machine-readable results are under `results/` as CSV and JSON. Markdown files
in the same directory are generated views. The principal outputs are:

- `results/primitive-bench.json`
- `results/repository-impact.json`
- `results/object-generation-feasibility.json`
- `results/validator-errors.json`
- `results/vrp-equivalence.json`
- `results/object-benchmarks/object-benchmarks.json`
- `results/rpki-objects/rpki-objects.json`
- `results/key-roll/key-roll.json`
- `results/local-validation/local-validation.json`
- `results/cms-probe/cms-api-probe.json`
- `results/cms-generation/cms-generation.json`
- `results/message-sweep/message-sweep.json`
- `results/validator-probe/container-matrix.json`
- `results/mixed-tree/mixed-tree.json`
- `results/ccr-comparison/ccr-comparison.json`
- `results/routinator-krill/extension-map.json`
- `results/routinator-krill/interop-matrix.json`
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

Run the Draft-19 raw Composite ML-DSA benchmark separately with:

```sh
make draft-composite-100k
```

This implements the message representative, ML-DSA context binding, raw key
and signature concatenation, and all-component verification from
`draft-ietf-lamps-pq-composite-sigs-19`. It does not implement an RPKI-specific
X.509/CMS profile or validator interoperability.

The Composite E2E workflow requires the pinned OpenSSL, Composite provider,
and rpki-client builds below ignored `local/`. Generator, validation, negative
test, and measurement code is public. Private keys, external checkouts, build
trees, raw measurements, generated negative fixtures, host configuration, and
AI working notes stay below `local/`:

`Makefile` defaults to the documented `local/build/` layout and uses the
public, relocatable `experiments/openssl-composite.cnf`. Override
`COMPOSITE_OPENSSL`, `COMPOSITE_OPENSSL_LIBDIR`, and
`COMPOSITE_PROVIDER_MODULE` when using another build layout.

```sh
make composite-e2e
make composite-e2e-rp-matrix
make composite-e2e-negative
make composite-e2e-benchmark
make composite-keygen-benchmark
```

The E2E benchmark performs 100 complete generation repetitions and 1,000 RP
validation repetitions per scenario. The separate primitive Composite
benchmarks use 100,000 sign and verify operations; those counts describe
different workloads and are not compared as if they were interchangeable.
The key-generation target uses 1,000 fresh `openssl genpkey` subprocesses per
algorithm and records raw samples only below `local/`.

The E2E targets use pure ML-DSA-65 and
id-MLDSA65-ECDSA-P256-SHA512, OID `1.3.6.1.5.5.7.6.45`. The
mixed-tree transition certificate has an RSA signature and Composite SPKI. The
child publication point contains a Composite CRL, manifest, and ROA. The
rpki-client development patch remains Current Suite-only by default and
enables both experimental suites only with its existing experimental option.

The experiment pins OpenSSL 3.6.2 at
`fe686e15d84334b284f883118ed92f64b409b3aa`, the Composite provider at
`2263161f6b058fe0195a98b6fad088c2d4a2595f`, rpki-client-portable at
`b7d6e2fc4522751515444b45f07ce68cc0b3497b`, and its OpenBSD source at
`577166e3dda1990fd9c54679b5d74ffc0ec5dec5`. The second-RP experiment pins
Routinator 0.15.2 at `0cf9104efa730ebc2de6bbd880e9bcee50de10d9`
and rpki-rs 0.19.3 at `56d3811d3ee44a7b93eab33e5b1853cbcd4dee70`.
The CA experiment pins Krill 0.16.0 at
`b2a26cd9f44a385d8a62a0199b082f44e5062039` and builds it with Rust
1.88.0.
The machine-readable source of these pins is
`experiments/composite-dependencies.json`.

Build the complete ignored dependency tree and run the RP matrix with:

```sh
make composite-bootstrap
```

This is the only network-enabled Composite bootstrap target. It refuses to
replace existing checkout paths and disables their push URLs. Validate an
existing build without network access with `make composite-bootstrap-check`.
The bootstrap applies the provider integration fix and public RP reference
patch before building:

```sh
git -C local/upstream/composite-provider apply \
  ../../../patches/composite-provider-private-key-decoder.patch
git -C local/upstream/rpki-client-portable/openbsd apply \
  ../../../../patches/rpki-client-composite-experimental.patch
```

Build the second experimental RP and run its four-scenario and 15-case
negative matrices with:

```sh
make routinator-experimental-bootstrap
make routinator-experimental-negative
```

The bootstrap applies public patches to pinned Routinator and rpki-rs
checkouts below `local/upstream/`. It uses the same OpenSSL 3.6.2 and
Composite provider as the generator and rpki-client experiment, but
Routinator/rpki-rs provide an independently implemented repository, resource
certificate, CRL, CMS, manifest, and ROA processing path. This is evidence
from a second RP implementation, not an independent cryptographic
implementation. The experimental path is enabled only by
`PQC_RPKI_EXPERIMENTAL=1`.

Build the experimental Krill CA, run RSA-parent to Composite-child issuance,
publish a ROA, and roll the child back to RSA with:

```sh
make krill-experimental-bootstrap
# For an existing checkout and build:
make krill-experimental-e2e
make krill-experimental-bootstrap-check
```

Run `make composite-bootstrap` and
`make routinator-experimental-bootstrap` first on a new machine. The Krill
bootstrap applies the public patch to the pinned checkout, disables its push
URL, builds with the sibling patched rpki-rs, runs the fixed rollover
scenario, and validates both publication phases with experimental rpki-client
and Routinator. The suite selector and captured CA state remain below
`local/`; only the patch and sanitized acceptance matrix are public.

Generate the certificate and CRL size evidence, including experimental
Falcon-512 X.509 encodings, with:

```sh
make certificate-sizes
```

OpenSSL 3.6.2 generated resource-profile ML-DSA certificates and CRLs. Its CMS
CLI still fails to select a default digest for ML-DSA, while the CMS API
succeeds when SHA-512 is supplied explicitly. The repository therefore
contains complete ML-DSA-65 Manifest and ROA fixtures plus an independent
manual DER reference. Pinned unmodified Routinator, rpki-client, and FORT
containers accept the RSA baseline and reject the ML-DSA-65 repository at
unsupported trust-anchor or algorithm checks.
The patched rpki-client retains that rejection in default mode and validates
the complete pure ML-DSA-65 repository only in experimental mode.

`results/object-benchmarks/` is an object-payload benchmark. It measures
deterministic synthetic Manifest file-list construction and hashing, not
complete RFC 6488 CMS generation. `results/mixed-tree/` is a public synthetic
model for CA-boundary algorithm transition. `results/ccr-comparison/` is a
local canonical-hash interim workflow and is not CCR `ROAPayloadState.hash`.
`results/rpki-objects/` records public DER fixtures: RSA and ML-DSA-65 `.mft`
and `.roa` CMS objects, ML-DSA-44/65/87 certificates and CRLs, and ML-DSA
eContent. `results/local-validation/` records OpenSSL DER/CMS round trips, EE
profile checks, and Manifest hash checks. `results/validator-probe/` records
the isolated unmodified-validator experiment. `results/key-roll/` is a
synthetic configurable key-roll model.
`results/composite-e2e/routinator-matrix.json` and
`routinator-negative-summary.json` record the second-RP E2E result.
`results/composite-e2e/krill-rollover.json` records the Krill-issued
Composite publication and RSA rollback result. This is a small, isolated
local-rsync CA experiment, not a production deployment or repository-scale
measurement. `results/routinator-krill/` retains the earlier extension map
and source scan. Configure external inputs with
`PQC_RPKI_ROUTINATOR_SRC`, `PQC_RPKI_KRILL_SRC`,
`PQC_RPKI_ROUTINATOR_BIN`, and `PQC_RPKI_KRILL_BIN`; suggested checkouts live
under ignored `local/upstream/`.

## Draft

The current published revision is
`ietf/draft-yoshikawa-sidrops-pqc-rpki-01.md`.  The working revision is
the Informational experiment report
`ietf/draft-yoshikawa-sidrops-pqc-rpki-02.md`.  Its generated artifacts are:

- `ietf/submission/draft-yoshikawa-sidrops-pqc-rpki-02.xml`
- `ietf/submission/draft-yoshikawa-sidrops-pqc-rpki-02.txt`

Generate the standalone XML with:

```sh
python3 tools/render_draft_submission.py
xml2rfc --text ietf/submission/draft-yoshikawa-sidrops-pqc-rpki-02.xml
```

## Safety

Do not commit private keys, credentials, production TALs, external checkouts,
raw E2E measurements, generated negative fixtures, AI working notes, or
operational RPKI objects. Public reference patches, generators, tests,
non-secret fixtures, and summarized results are intended to be reviewable.
Object-generation tests use temporary directories or ignored `local/`.

Before publishing or committing:

```sh
make pre-publication
git status --short --ignored
```

`local/` is ignored and is the only intended place for non-public notes or
scratch inputs.
