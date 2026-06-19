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

    capability = [
        {"component": "Static algorithm metadata", "status": "confirmed", "backend": "Python standard library", "notes": "Profile role and comparison scope are recorded separately"},
        {"component": "Primitive benchmark", "status": "confirmed" if any(row.get("benchmark_status") == "confirmed" for row in primitive) else "unsupported", "backend": "OpenSSL CLI; optional oqs-python", "notes": "Timing class and comparable group are recorded per row"},
        {"component": "Repository/RRDP/cache estimator", "status": "estimated", "backend": "Python standard library", "notes": "First-order model"},
        {"component": "Real repository cache adapter", "status": real_status, "backend": "filesystem", "notes": "Requires explicit cache path"},
        {"component": "VRP equivalence checker", "status": "estimated", "backend": "CSV/JSON", "notes": "Synthetic input by default"},
        {"component": "Validator wrappers", "status": "confirmed", "backend": "existing executables", "notes": "Version-only, no network"},
        {"component": "RFC-profiled PQC X.509/CRL generation", "status": object_status, "backend": "OpenSSL 3", "notes": "Temporary keys only; RFC 3779 extensions included"},
        {"component": "PQC CMS SignedData generation", "status": cms_status, "backend": "OpenSSL 3 CMS CLI", "notes": "Failure reason recorded in object-generation results"},
        {"component": "PQC RPKI interoperability", "status": "future work", "backend": "existing validators", "notes": "No complete RFC 6488 PQC object tested"},
    ]
    write("results/capability-matrix.md", "# Capability Matrix\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\n" +
          markdown_table(capability, [("component", "Component"), ("status", "Status"), ("backend", "Backend"), ("notes", "Notes")]))

    write("docs/algorithm-selection.md", "# Algorithm Selection\n\n" +
          markdown_table(algorithms, [
              ("name", "Algorithm"), ("track", "Track"), ("nist_category", "NIST category"),
              ("public_key_bytes", "Public key bytes"), ("signature_bytes", "Signature bytes"),
              ("specification", "Standards"),
          ]) +
          "\n\nML-DSA-65 is the standards-ready primary experiment. ML-DSA-44 is measured but excluded from the profile by the Category 3 policy floor. ML-DSA-87 is the high-assurance candidate. "
          "SLH-DSA remains a crypto-diversity candidate with significant size and signing-cost concerns. "
          "Composite signatures, Falcon, MAYO, SNOVA, and HAWK remain outside the mandatory path until RPKI-specific profile and interoperability evidence exists.")

    write("docs/existing-implementations.md", """# Existing Implementations

| Layer | Preferred implementation | Current use |
|---|---|---|
| PQC primitives | liboqs / oqs-python | Conditional benchmark |
| Provider/PKIX/CMS | OpenSSL 3 / oqs-provider | Future object experiments |
| CA/publication | Krill | Future isolated repository |
| Validation | Routinator, rpki-client, FORT | Version/capability probes |
| Router consumers | BIRD/OpenBGPD | VRP consumers only |

The default run performs no network access and never uses production TALs or credentials. Do not reimplement ML-DSA, SLH-DSA, ASN.1 DER, X.509 path validation, CMS SignedData, RRDP, rsync, or RTR from scratch.""")

    write("docs/measurement-methodology.md", """# Measurement Methodology

Primitive operations use a deterministic 32-byte message and median wall-clock time. The RSA baseline and the required ML-DSA/SLH-DSA comparison rows use one OpenSSL CLI subprocess per timed key generation, signing, or verification operation. These values include process startup, provider initialization, argument parsing, file I/O, and the cryptographic operation. They are end-to-end CLI measurements, not pure algorithm cycle counts. Timing ratios are valid only between rows with the same `comparable_group`; closely grouped verification values primarily characterize the common CLI path.

Optional algorithms use oqs-python/liboqs when available. Those measurements are in-process and belong to a separate comparable group, so they MUST NOT be directly divided by OpenSSL CLI values. A pure per-operation comparison requires all algorithms to use a common in-process API or a benchmark that subtracts and validates harness overhead.

Repository impact applies standardized or candidate parameter sizes to a documented synthetic corpus. It does not require a locally executable primitive backend and is classified as `estimated`. VRP comparison normalizes prefix, maxLength, origin AS, and TA/source. CSV/JSON contain backend, timing scope, comparability group, and status fields and are the primary evidence; Markdown views retain those limitations.

Current repository-impact data is `estimated`, not proof of global deployability. Before increasing normative language in the Internet-Draft, calibrate the estimator with a local RPKI cache supplied through `PQC_RPKI_CACHE` and produce real-cache projections.""")

    write("docs/research-questions.md", """# Research Questions

1. Which standardized PQC signature is practical for RPKI?
2. How do candidates affect certificates, CRLs, manifests, ROAs, repositories, RRDP, and caches?
3. Can RFC 6487/6488 objects be generated using RFC 9881/9882/9909/9814 encodings without ad-hoc profiles?
4. Which existing validators can parse, reject, or validate generated PQC RPKI objects?
5. Can parallel RSA/PQC publication preserve identical VRP semantics?
6. Is composite signature support needed, or is parallel publication sufficient?
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
| Validator probing | partial | installed validators: {", ".join(installed) or "none"}; unavailable: {", ".join(unsupported) or "none"} |
| Real cache measurement | input-dependent | requires `PQC_RPKI_CACHE` |
| RFC-profiled PQC CA/EE certificates and CRLs | {object_status} | `results/object-generation-feasibility.*` |
| PQC CMS SignedData, MFT, and ROA | {cms_status} | OpenSSL CMS failure and dependency classification recorded |
| Multi-validator PQC object validation | not implemented | depends on generated objects |

Current repository-size results are synthetic or literature-calibrated estimates. ML-DSA certificates and CRLs were generated with OpenSSL, but MFT/ROA generation remains blocked at the CMS/payload-generator layer. No independent validator has accepted a PQC RPKI object in this repository.""")

    write("ietf/open-issues.md", """# Open Issues for draft-yoshikawa-sidrops-pqc-rpki

> EXPERIMENTAL / NOT FOR PRODUCTION

The authoritative protocol issue list is the Open Issues section of
`draft-yoshikawa-sidrops-pqc-rpki-00`. Research execution questions are
maintained separately in `docs/research-questions.md`.""")

    write("ietf/security-considerations-notes.md", """# Security Considerations Notes

Avoid silent downgrade, split VRP views, algorithm confusion, oversized-object resource exhaustion, stale manifest masking, and accidental use of experimental private keys or production TALs. The protocol text explicitly handles unsupported validators, stale RSA/PQC branches, and semantic divergence between parallel publication branches.""")

    write("ietf/iana-considerations-notes.md", """# IANA Considerations Notes

The current assumption is no new IANA registry action because ML-DSA and SLH-DSA OIDs are inherited from PKIX/CMS specifications. An RPKI-specific algorithm-suite name, suite registry, or validator error registry remains an open design question.""")

    write("ietf/interoperability-report.md", """# Interoperability Report

> EXPERIMENTAL / NOT FOR PRODUCTION

OpenSSL generated ML-DSA resource-profile CA certificates, EE certificates, and CRLs. OpenSSL CMS rejected ML-DSA signing with `CMS_add1_signer:no default digest`; therefore MFT and ROA generation did not proceed. Existing validator executables are probed without network access.

Required next phases:

1. RSA baseline fixture accepted by Routinator, rpki-client, and FORT.
2. ML-DSA-65 fixture generated with RFC 9881/RFC 9882 encodings.
3. Validator behavior recorded for unknown/unsupported PQC algorithms.
4. VRP equivalence checked between RSA and PQC-equivalent branches.
5. Negative tests for inconsistent ROA, stale manifest, expired EE certificate, missing CRL, and invalid signedAttrs.""")


if __name__ == "__main__":
    main()
