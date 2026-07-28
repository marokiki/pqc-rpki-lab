#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

from pqc_rpki_lab.algorithms import algorithm_rows
from pqc_rpki_lab.result_io import markdown_table

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def write(name: str, text: str) -> None:
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n")


def read_csv(name: str) -> list[dict[str, str]]:
    path = RESULTS / name
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    algorithms = algorithm_rows()
    primitive = read_csv("primitive-bench.csv")
    validators = read_csv("validator-capability.csv")
    objects = read_csv("generated-object-sizes.csv")
    real_repository = read_csv("real-repository-summary.csv")
    object_status = "confirmed" if any(
        row.get("algorithm") == "ML-DSA-65"
        and row.get("object_type") == "CA certificate"
        and row.get("status") == "confirmed"
        for row in objects
    ) else "unsupported"
    cms_status = "confirmed" if any(
        row.get("algorithm") == "ML-DSA-65"
        and row.get("object_type") == "CMS SignedData"
        and row.get("status") == "confirmed"
        for row in objects
    ) else "unsupported"
    real_status = real_repository[0].get("status", "skipped") if real_repository else "skipped"
    composite_result = RESULTS / "composite-e2e" / "rp-validation-matrix.json"
    routinator_result = RESULTS / "composite-e2e" / "routinator-matrix.json"
    krill_result = RESULTS / "composite-e2e" / "krill-rollover.json"
    ccr_result = RESULTS / "ccr-comparison" / "rp-produced-state-hashes.json"

    capability = [
        {"component": "Static algorithm metadata", "status": "confirmed", "backend": "Python standard library", "notes": "Profile role and comparison scope are recorded separately"},
        {"component": "Primitive benchmark", "status": "confirmed" if any(row.get("benchmark_status") == "confirmed" for row in primitive) else "unsupported", "backend": "OpenSSL CLI; optional oqs-python", "notes": "Timing class and comparable group are recorded per row"},
        {"component": "Repository/RRDP/cache estimator", "status": "estimated", "backend": "Python standard library", "notes": "First-order model"},
        {"component": "Real repository cache adapter", "status": real_status, "backend": "filesystem", "notes": "Requires explicit cache path"},
        {"component": "VRP equivalence checker", "status": "estimated", "backend": "CSV/JSON", "notes": "Synthetic input by default"},
        {"component": "Validator wrappers", "status": "confirmed", "backend": "existing executables", "notes": "Version-only, no network"},
        {"component": "RFC-profiled PQC X.509/CRL generation", "status": object_status, "backend": "OpenSSL 3", "notes": "Temporary keys only; RFC 3779 extensions included"},
        {"component": "PQC CMS SignedData generation", "status": cms_status, "backend": "OpenSSL 3 CMS CLI", "notes": "Failure reason recorded in object-generation results"},
        {"component": "Experimental PQC RPKI E2E", "status": "confirmed" if composite_result.exists() else "future work", "backend": "rpki-client and Routinator with OpenSSL provider", "notes": "Pure ML-DSA-65, Composite, and mixed-tree fixtures; shared cryptographic backend"},
        {"component": "Experimental CA lifecycle", "status": "confirmed" if krill_result.exists() else "future work", "backend": "Krill with OpenSSL provider", "notes": "Composite issuance, one-ROA update, and RSA rollback in an isolated testbed"},
    ]
    write("results/capability-matrix.md", "# Capability Matrix\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\n" +
          markdown_table(capability, [("component", "Component"), ("status", "Status"), ("backend", "Backend"), ("notes", "Notes")]))

    write("docs/algorithm-selection.md", "# Algorithm Selection\n\n" +
          markdown_table(algorithms, [
              ("name", "Algorithm"), ("track", "Track"), ("nist_category", "NIST category"),
              ("public_key_bytes", "Public key bytes"), ("signature_bytes", "Signature bytes"),
              ("specification", "Standards"),
          ]) +
          "\n\nP-256 and Ed25519 are compact classical counterfactuals, not current RFC 6488 profile algorithms. "
          "ML-DSA-65 is the current primary experiment. ML-DSA-44 remains measured while its profile role is reconsidered alongside small-PQ composite suites. ML-DSA-87 is the high-assurance comparison. "
          "SLH-DSA remains a crypto-diversity candidate with significant size and signing-cost concerns. "
          "The selected ML-DSA-65 + P-256 Composite suite has measured X.509/CMS and experimental two-RP evidence; other Composite combinations remain estimates. Falcon, MAYO, SNOVA, and HAWK remain research candidates.")

    write("docs/existing-implementations.md", """# Existing Implementations

| Layer | Preferred implementation | Current use |
|---|---|---|
| PQC primitives | liboqs / oqs-python | Conditional benchmark |
| Provider/PKIX/CMS | OpenSSL 3 default and Composite providers | ML-DSA and Composite certificates, CRLs, CMS signing, and local verification |
| CA/publication | Experimental Krill 0.16.0 patch | Isolated RSA-parent to Composite-child issuance, publication, one-ROA update, and RSA rollback |
| Validation | Routinator, rpki-client, FORT | Unmodified rejection probes plus experimental rpki-client and Routinator E2E paths |
| Router consumers | BIRD/OpenBGPD | VRP consumers only |

The default run performs no network access and never uses production TALs or
credentials. Cryptographic primitives and X.509 generation/verification stay
in OpenSSL. The small CMS DER assembler is an encoding reference and
cross-check, not a replacement cryptographic or path-validation implementation.
RRDP, rsync, and RTR are not reimplemented. The experimental RP patches change
algorithm policy and delegate cryptography to OpenSSL; they are not new
validator implementations.

Routinator and Krill experiments are opt-in. Suggested local upstream
checkouts live under ignored `local/upstream/`; upstream source, keys, raw
measurements, and CA state stay local while reproducible public-safe patches
and sanitized results are stored in tracked paths.""")

    write("docs/measurement-methodology.md", """# Measurement Methodology

Primitive operations use a deterministic 32-byte message and median wall-clock time. The RSA baseline and the required ML-DSA/SLH-DSA comparison rows use one OpenSSL CLI subprocess per timed key generation, signing, or verification operation. These values include process startup, provider initialization, argument parsing, file I/O, and the cryptographic operation. They are end-to-end CLI measurements, not pure algorithm cycle counts. Timing ratios are valid only between rows with the same `comparable_group`; closely grouped verification values primarily characterize the common CLI path.

Optional algorithms use oqs-python/liboqs when available. Those measurements are in-process and belong to a separate comparable group, so they MUST NOT be directly divided by OpenSSL CLI values. A pure per-operation comparison requires all algorithms to use a common in-process API or a benchmark that subtracts and validates harness overhead.

Repository impact applies standardized or candidate parameter sizes to a documented synthetic corpus. Composite rows add component sizes and exclude composite ASN.1 overhead. They are estimates, not measured objects.

VRP-set equality excludes trust-anchor and source attribution. The original helper hashes canonical JSON and is explicitly not a CCR DER implementation. A separate rpki-client CCR workflow parses real DER, recomputes `ROAPayloadState`, `ManifestState`, and `TrustAnchorState`, and reports them separately. It does not provide a second independent CCR-producing RP.

Bulk signing uses `openssl speed`, which keeps provider and process startup outside the timed loop. Its 100,000-manifest and key-roll values are signing-only lower bounds, not complete object-generation measurements. CSV/JSON contain backend, timing scope, comparability group, and status fields and are the primary evidence.

The exact-count benchmark is a separate manual phase. It generates one key pair per algorithm, then performs exactly 100,000 EVP signing operations and 100,000 verification operations. It includes EVP context initialization in each operation but excludes key generation, process startup, RPKI object encoding, file I/O, publication, and HSM latency. The default `run_all.sh` and `make review-evidence` targets MUST NOT invoke this benchmark.

The composite-component benchmark signs the same message with both named components sequentially and accepts a verification only when both component signatures verify. OpenSSL EVP provides RSA, P-256, and ML-DSA; pinned liboqs provides Falcon-512. The measurement excludes composite OIDs, ASN.1 encoding, domain separation, CMS/X.509 processing, and HSM behavior, so it MUST NOT be described as LAMPS composite interoperability.

Current repository-impact data is `estimated`, not proof of global
deployability. A 2026-07-27 aggregate profile covers one Routinator RRDP-only
cache: 550,210 current objects, 54,960 publication points, and 980,019
validated VRPs. ARIN was unavailable. No source objects or local paths are
published, and the single snapshot does not measure churn.

The controlled Krill campaign measures one child publication point at 1, 10,
100, and 1,000 ROAs. Generation is repeated 30 times through 100 ROAs and 10
times at 1,000; the eight-mode fresh-cache validation matrix is repeated 100
times per size. A separate 1,000-ROA run measures fresh, unchanged, and
one-ROA-update states 30 times per RP. A synthetic topology pilot validates
100 child CAs and publication points. These are local-rsync experiments with
uncontrolled OS page cache, not global-repository or network benchmarks.""")

    write("docs/research-questions.md", """# Research Questions

1. Which standardized PQC signature is practical for RPKI?
2. How do candidates affect certificates, CRLs, manifests, ROAs, repositories, RRDP, and caches?
3. Can RFC 6487/6488 objects be generated using RFC 9881/9882/9909/9814 encodings without ad-hoc profiles?
4. Which existing validators can parse, reject, or validate generated PQC RPKI objects?
5. Do RSA and PQC validation runs produce the same CCR `ROAPayloadState.hash`?
6. Which combination of mixed-tree migration and pure or composite signatures is operationally viable?
7. Are Null Scheme-like reductions useful enough to justify new SIDROPS work?
8. Which downgrade and mixed-validator failures require normative handling?

The protocol-level issue list is maintained in the Open Issues section of `ietf/draft-yoshikawa-sidrops-pqc-rpki-00.md`.""")

    write("docs/references.md", """# References

Normative and standards references:

- RFC 6480, 6487, 6488, 6916, 7935, 8182, 9286, 9582, 9589
- RFC 9881 and RFC 9882 for ML-DSA in X.509 and CMS
- RFC 9909 and RFC 9814 for SLH-DSA in X.509 and CMS
- NIST FIPS 204 and FIPS 205

Internet-Drafts and research references:

- draft-ietf-lamps-pq-composite-sigs
- draft-ietf-lamps-cms-composite-sigs
- draft-ietf-sidrops-rpki-ccr
- draft-ietf-pquip-hybrid-signature-spectrums
- draft-doesburg-sidrops-nullscheme, expired individual draft
- Dirk Doesburg, *Post-Quantum Cryptography for the RPKI*, Master's thesis, Radboud University, 27 June 2025, https://www.sidnlabs.nl/en/news-and-blogs/thesis-pqc-for-the-rpki

Use the Datatracker before submission because active Internet-Draft status can change.""")

    installed = [row["validator"] for row in validators if row.get("installed") == "True"]
    unsupported = [row["validator"] for row in validators if row.get("installed") != "True"]
    write("ietf/implementation-status.md", f"""# Implementation Status

> EXPERIMENTAL / NOT FOR PRODUCTION

This note is maintained in the style of an RFC 7942 implementation-status section, but it is not yet ready for direct publication.

| Component | Status | Evidence |
|---|---|---|
| Algorithm metadata | implemented | `src/pqc_rpki_lab/algorithms.py` |
| Primitive benchmark | implemented | `results/primitive-bench.*` |
| Synthetic repository estimator | implemented | `results/repository-impact.*` |
| Migration scenario scaffold | implemented | `results/migration-scenarios.*` |
| VRP equivalence fixture checker | implemented | `tools/vrp_equivalence.py`, tests |
| Validator probing | implemented baseline | `results/validator-probe/` |
| Real cache profile | one aggregate snapshot | 550,210 objects across 54,960 publication points; ARIN unavailable; no source objects published |
| RFC-profiled PQC CA/EE certificates and CRLs | {object_status} | `results/object-generation-feasibility.*` |
| Pure ML-DSA-65 CMS SignedData, MFT, and ROA | implemented | `testdata/ml-dsa-65/`, `results/rpki-objects/` |
| Composite CMS SignedData, MFT, and ROA | implemented | `testdata/composite-mldsa65-p256/`, `results/composite-e2e/` |
| Experimental rpki-client validation | {"implemented" if composite_result.exists() else "not implemented"} | pure ML-DSA-65, Composite standalone, and mixed-tree fixtures |
| Experimental Routinator validation | {"implemented" if routinator_result.exists() else "not implemented"} | second RP processing path; all four scenarios and 15 negative cases |
| Operational negative validation | implemented | seven expired, revoked, stale, and missing-publication cases in both RPs |
| Experimental Krill lifecycle | {"implemented" if krill_result.exists() else "not implemented"} | Composite issuance, publication, one-ROA update, and RSA rollback |
| Repeated scaled Krill validation | implemented through 1,000 ROAs | `results/scaled-corpus/krill-repeated-summary.json` |
| Multi-publication-point topology | implemented at 100 child CAs | `results/scaled-corpus/topology-pilot-summary.json` |
| RP cache regimes | implemented at 1,000 ROAs | 30 fresh, unchanged, and one-ROA-update repetitions per RP |
| RP-produced CCR state comparison | {"implemented" if ccr_result.exists() else "not implemented"} | actual DER hashes from rpki-client CCR output |
| Independent cryptographic implementation | not implemented | generator, both RPs, and Krill share one OpenSSL/Composite provider |

Public-cache topology is aggregate-only, and controlled scale runs do not
represent production repository or network performance. Complete pure
ML-DSA-65 and selected Composite objects are accepted by experimental
rpki-client and Routinator paths. Krill exercises issuance, update,
publication, and rollback. Both RPs and Krill share the same OpenSSL/provider
backend, so the result is not independent cryptographic interoperability
evidence.""")

    write("ietf/interoperability-report.md", """# Interoperability Report

> EXPERIMENTAL / NOT FOR PRODUCTION

OpenSSL 3.6.2 generated ML-DSA resource-profile CA certificates, EE
certificates, and CRLs. The generic CMS CLI still reports
`CMS_add1_signer:no default digest`, while the CMS API succeeds when SHA-512
is supplied explicitly. Complete pure ML-DSA-65 Manifests and ROAs are
generated through that explicit API path and cross-checked against a small DER
encoding reference. The selected ML-DSA-65 + P-256 Composite suite also
produces complete CA/EE certificates, CRLs, Manifests, and ROAs.

Pinned unmodified Routinator, rpki-client, and FORT accept RSA and reject the
experimental suites. Experimental rpki-client and Routinator paths accept
RSA, pure ML-DSA-65, Composite standalone, and RSA-to-Composite mixed trees
with equal VRP sets. The RP processing paths are distinct, but their
cryptographic operations share the same OpenSSL/provider backend.

Both RPs reject 15 cryptographic/profile negative cases and seven operational
repository failures. The latter cover expired or revoked objects, stale
CRL/Manifest state, and missing publication objects. A 100-child topology
pilot retains 99 VRPs after one publication branch is removed.

Experimental Krill issues a Composite child, publishes its CRL, Manifest, and
ROAs, replaces one ROA, and rolls the child back to RSA. Repeated controlled
measurements extend through 1,000 ROAs and compare fresh, unchanged, and
one-ROA-update RP states. These local-rsync results do not establish
independent cryptographic interoperability, production protocol operation,
or global-repository performance.""")


if __name__ == "__main__":
    main()
