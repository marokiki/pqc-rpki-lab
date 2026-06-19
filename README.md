# pqc-rpki-lab

PQC for RPKI Internet-Draft / SIDROPS submission support repository.

This repository is a research and engineering scaffold for evaluating how post-quantum digital signatures can be introduced into the Resource Public Key Infrastructure (RPKI) without redesigning the entire RPKI architecture.

The main goal is not to invent a new cryptographic primitive. The goal is to compare standardized or actively standardized post-quantum signature algorithms in an RPKI workflow, reuse existing implementations as much as possible, and produce reproducible evidence that can be used for an Internet-Draft, paper, or conference presentation.

## Core hypothesis

RPKI should keep its existing X.509 / CMS / repository / validator / RTR architecture. PQC migration should be evaluated primarily at the CA, publication server, signed object, and validator layers. Routers should continue to consume validated payloads such as VRPs via RTR or local files.

## Target WG

The intended IETF venue is SIDROPS. The work should be framed as an RPKI algorithm profile and migration/evaluation document, with dependencies on LAMPS documents for X.509 and CMS algorithm encodings.

## Initial algorithm candidates

The initial candidates are intentionally narrow:

| Candidate | Role in experiment | Reason |
|---|---|---|
| RSA-2048/SHA-256 | Baseline | Current RPKI algorithm profile baseline |
| ML-DSA-44 | Excluded-policy comparison | Measured for completeness; below the Category 3 floor selected for the primary profile |
| ML-DSA-65 | Primary PQC candidate | NIST-standardized signature algorithm; balanced security/size/performance candidate |
| ML-DSA-87 | High-assurance candidate | Higher NIST category; useful for trust anchor or CA-oriented discussion |
| SLH-DSA-SHAKE-128s | Diversity candidate | Hash-based alternative; useful for crypto-diversity and size-cost comparison |
| SLH-DSA-SHAKE-192s | Conservative diversity candidate | Higher category hash-based alternative; expected to be costly for RPKI signed objects |
| Composite ML-DSA + classical | Optional future track | Relevant to transition, but should not be the default baseline until LAMPS composite drafts stabilize |

KEM algorithms such as ML-KEM are out of scope for the first version because RPKI object validation is signature-centric.

The optional research track adds Falcon-512/1024, MAYO-1,
SNOVA-(24,5,4), and HAWK-512. These candidates remain separate from the
mandatory path. Falcon is NIST-selected but its final RPKI-ready profile is not
validated here; MAYO, SNOVA, and HAWK are NIST Additional Signatures Round 3
candidates as of May 14, 2026.

## Repository layout

```text
.
├── README.md
├── docs/                          # Design notes, algorithm matrix, report template
├── experiments/                   # Experiment definitions and scenario manifests
├── benchmarks/                    # Benchmark runner placeholders
├── src/pqc_rpki_lab/              # Python harness for metadata, result collection, reporting
├── tools/                         # Shell wrappers for existing tools/providers
├── ietf/                          # Internet-Draft source and submission artifacts
├── results/                       # Generated benchmark outputs and reports
└── third_party/                   # Pointers only; do not vendor large upstream projects by default
```


## Current draft and supporting evidence

The current Internet-Draft source is
`ietf/draft-yoshikawa-sidrops-pqc-rpki-00.md`. Submission renderings are under
`ietf/submission/`. Detailed evidence and remaining interoperability work are
documented in:

- `docs/rfc-profiled-object-generation-plan.md`
- `docs/validator-interoperability-plan.md`
- `docs/real-world-repository-measurement-plan.md`
- `docs/composite-and-nullscheme-decision.md`
- `docs/scope-boundary-tak-aspa-rsc-bgpsec.md`
- `docs/iana-and-profile-questions.md`
- `ietf/interoperability-report.md`
- `results/report.md`

The highest-priority gap is generating actual RFC-profiled PQC RPKI objects. Primitive benchmarks and synthetic size projections are not enough for SIDROPS discussion. The next revision should prove, or precisely document why it cannot yet prove, that ML-DSA certificates, CRLs, and CMS signed objects can satisfy the RPKI object profiles without ad-hoc encodings.

## Existing implementations to reuse

The implementation should prefer wrappers around existing projects:

- Krill for RPKI CA / publication workflows.
- Routinator, rpki-client, and FORT for validator/cache comparison.
- BIRD or OpenBGPD for router-side VRP consumption checks.
- OpenSSL 3 provider model, oqs-provider, liboqs, and oqs-python for PQC primitive experiments where upstream RPKI tools do not yet expose the required algorithms.
- LAMPS RFC-defined encodings for ML-DSA/SLH-DSA in X.509 and CMS.

Do not reimplement ML-DSA, SLH-DSA, ASN.1 DER, X.509 path validation, CMS SignedData, RRDP, rsync, or RTR from scratch.

## Minimal first milestone

1. Generate or import comparable RPKI-like object corpora for RSA baseline and PQC candidates.
2. Measure key size, signature size, certificate size, CMS object size, manifest/ROA total repository size, validation time, and VRP output equivalence.
3. Produce machine-readable CSV/JSON results and a Markdown report.
4. Produce Internet-Draft evidence tables: algorithm profile, migration risks, validator impact, repository size impact, and downgrade considerations.

## Non-goals for v0

- Production deployment in a public RPKI repository.
- Router changes beyond consuming VRPs from existing validators.
- New cryptographic primitive design.
- BGPsec path signature migration.
- ASPA/RSC/TAK full coverage, except as future-work discussion.

## Reproducibility principle

Every experiment should produce:

- input corpus metadata,
- tool and commit versions,
- algorithm parameters,
- machine-readable result files,
- a human-readable report fragment,
- known limitations.

## Quick start

The default execution performs no network access and requires only Python 3.11
or later. Optional tools are detected and recorded as unsupported when absent.

```sh
make
```

Equivalent direct commands:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
tools/run_all.sh
```

Optional inputs:

```sh
make install-optional-pqc
PQC_RPKI_CACHE=/path/to/local/rpki-cache tools/run_all.sh
PQC_RPKI_ITERATIONS=100 tools/run_all.sh  # increase benchmark iterations for publication-quality timing
python3 tools/vrp_equivalence.py --baseline rsa.csv --candidate pqc.json
```

`make install-optional-pqc` is the only installation path that uses the
network. It installs pinned liboqs/liboqs-python sources under `.local/oqs` and
`.venv`, then enables Falcon, MAYO, and SNOVA primitive measurements. HAWK is
recorded as unsupported because liboqs 0.15.0 does not provide it.

The default primitive benchmark uses a small iteration count so that offline CI and Codex runs finish quickly. Set `PQC_RPKI_ITERATIONS` to a larger value for paper-quality measurements.

The RSA, ML-DSA, and SLH-DSA comparison rows use end-to-end OpenSSL CLI
wall-clock measurements. Each timed operation includes one process launch, so
the values are not pure cryptographic cycle counts. Compare timings only when
the `comparable_group` field is identical. Optional oqs-python measurements
are in-process and belong to a separate comparison group.

`PQC_RPKI_CACHE` reads local `.cer`, `.roa`, `.mft`, and `.crl` file metadata
only. Network use is not part of the default harness. Use isolated test TALs
and repositories for future validator interoperability work; never use or
commit production credentials, private keys, or TALs.

## RFC-profiled object feasibility

`tools/run_all.sh` uses OpenSSL in a temporary directory to test resource
certificate, EE certificate, CRL, and CMS generation. No private key or
generated test object is persisted. Current evidence is written to:

- `results/object-generation-feasibility.md`
- `results/object-generation-feasibility.json`
- `results/generated-object-sizes.csv`

OpenSSL 3.6.2 generates ML-DSA and SLH-DSA resource-profile certificates and
CRLs. Its CMS CLI currently rejects pure PQC signing with
`CMS_add1_signer:no default digest`; MFT and ROA generation are therefore
recorded as unsupported rather than implemented.

## Result preservation

`results/` contains the evidence snapshot associated with the current release.
It is regenerated by `tools/run_all.sh` and may differ depending on optional
PQC backends and validator executables installed in the current environment.

## Result status vocabulary

- `confirmed`: executed or directly observed.
- `estimated`: generated by a documented synthetic/model path.
- `unsupported`: an implementation or algorithm is unavailable.
- `skipped`: optional input or dependency was not requested.
- `blocked`: the attempted path cannot proceed with the supplied inputs.
- `future work`: intentionally outside the mandatory implementation path.
