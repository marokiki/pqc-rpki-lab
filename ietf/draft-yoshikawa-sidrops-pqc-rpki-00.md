---
title: "Post-Quantum Signature Algorithm Profile and Migration Considerations for the Resource Public Key Infrastructure (RPKI)"
abbrev: "PQC for RPKI"
docname: draft-yoshikawa-sidrops-pqc-rpki-00
category: std
ipr: trust200902
area: Routing
wg: SIDROPS
submissiontype: IETF
date: 2026-06-19
keyword:
  - RPKI
  - PQC
  - ML-DSA
  - SLH-DSA
  - SIDROPS
stand_alone: true
author:
  - fullname: "Tomoki Yoshikawa"
    organization: "Graduate School of Informatics, Kyoto University"
    email: "segre@marokiki.net"
--- abstract

This document specifies an initial post-quantum signature algorithm
profile and migration considerations for the Resource Public Key
Infrastructure (RPKI).  It profiles ML-DSA-65 as the primary candidate
for an RPKI next signature algorithm suite by reusing the ML-DSA
algorithm identifiers and CMS conventions defined by LAMPS.  It also
describes how Certification Authorities, repository operators, and
Relying Parties can evaluate and deploy a post-quantum suite while
preserving the existing RPKI architecture and router-facing VRP/RTR
model.

This document profiles candidate post-quantum signature algorithms for
RPKI certificates, CRLs, certification requests, and CMS signed objects.
It is written as input to SIDROPS discussion and does not update RFC 7935
in this revision.  It does not define a new RPKI object format, a new
cryptographic primitive, a new repository synchronization protocol, or a
new router protocol.

--- middle

# Introduction

The RPKI relies on digital signatures in resource certificates, CRLs,
certification requests, and CMS signed objects such as manifests and
Route Origin Authorizations (ROAs).  The deployed RPKI algorithm profile
is based on RSA with SHA-256.  A Cryptographically Relevant Quantum
Computer (CRQC) would invalidate the long-term security assumptions of
RSA signatures.  RPKI therefore needs an algorithm migration path that can
be tested before an emergency transition is required.

The design goal of this document is conservative.  RPKI already has a
well-defined architecture, repository system, validation procedure, and
router interface.  This document keeps those layers intact.  PQC
processing is introduced at the Certification Authority (CA), repository,
CMS signed object, and Relying Party (RP) validation layers.  Routers that
consume Validated ROA Payloads (VRPs) through the RPKI-Router Protocol
(RTR) or local files are not expected to process PQC signatures directly.

This revision is intended as a SIDROPS starting point.  It deliberately
separates the protocol profile from the transition timetable and from the
implementation evidence.  Where this document uses terms such as
"candidate" or "evaluation", the text is identifying open engineering
questions rather than declaring the final global RPKI migration plan.

# Requirements Language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in BCP 14
[BCP14] when, and only when, they appear in all capitals, as
shown here.

# Terminology

This document uses the terminology of the RPKI architecture [RFC6480],
the resource certificate profile [RFC6487], the RPKI signed object
template [RFC6488], the RPKI algorithm agility procedure [RFC6916], and
the RPKI algorithm profile [RFC7935].

Current Suite:  The algorithm suite currently accepted by an RPKI
implementation for production validation.  At the time of writing this is
RSA-2048/SHA-256 as profiled by RFC 7935.

Next Suite:  A candidate algorithm suite that is implemented and tested
before it becomes the Current Suite.

PQC Suite:  A Next Suite whose signature algorithm is intended to remain
secure against a CRQC.

Corresponding Products:  RPKI products issued under different algorithm
suites that assert the same RPKI semantics.  For ROAs, this means the
same set of VRPs, modulo local policy and trust anchor selection.

Semantic Equivalence:  A property of two validated RPKI outputs in which
their routing semantics are identical.  For ROA-derived VRPs, the
comparison keys are prefix, maxLength, origin AS, and validation source or
trust anchor context.

Parallel Publication:  A migration technique in which a CA publishes
corresponding products under both the Current Suite and the Next Suite
for an extended interval.

Composite Signature:  A single signature algorithm construction that
combines a PQC algorithm and a traditional algorithm at the cryptographic
or encoding layer.  This document does not require composite signatures
for the initial RPKI PQC suite.

# Scope

This document applies to RPKI resource certificates, CRLs,
certification requests, manifests [RFC9286], ROAs [RFC9582], and other
CMS signed objects that reuse the RPKI signed object template.

This document does not specify changes to BGPsec path signatures, ASPA,
RSC, router certificates, RTR, TAL formats, RRDP [RFC8182], rsync, or the
RPKI Certificate Policy.  These topics may require companion work after
the basic certificate and CMS profile is interoperable.

# Design Goals

The profile has the following goals.

* Preserve the existing RPKI architecture and repository model.
* Reuse existing LAMPS PKIX and CMS encodings for PQC algorithms.
* Avoid new RPKI object formats unless measurements show that simple
  signature substitution is infeasible.
* Keep routers as consumers of validated payloads, not PQC validators.
* Support a prolonged Current Suite and Next Suite interval.
* Make downgrade, unsupported-algorithm, and semantic-divergence cases
  observable by RPs and operators.
* Keep measurement and interoperability evidence reproducible outside the
  protocol specification.

# Algorithm Profile

## Current Suite

The Current Suite remains RSA PKCS #1 v1.5 with SHA-256 as specified by
RFC 7935 until a separate transition timetable changes production RPKI
policy.

## Primary Next Suite

The primary PQC Next Suite candidate defined by this document is
ML-DSA-65.

This revision defines ML-DSA-65 as the primary candidate implementation
profile.  It does not yet require production acceptance.  An implementation
experiment SHOULD process id-ml-dsa-65 in RPKI certificates and CRLs
according to RFC 9881 and SHOULD report separately whether RFC 9882 CMS
SignedData is supported.

RPKI CAs participating in an isolated experiment MAY use ML-DSA-65 for
CA certificates, EE certificates, and CRLs.  They MUST NOT publish
experimental objects into a production repository or use production keys or
TALs.  CMS signed objects remain an interoperability work item in this
revision.

## Additional Candidate Suites

ML-DSA-87 MAY be implemented as a higher-security candidate, especially
for experiments involving trust anchors or upper-tier CAs.  This document
does not require ML-DSA-87 for basic interoperability because it produces
larger objects than ML-DSA-65.

SLH-DSA-SHAKE-128s and SLH-DSA-SHAKE-192s MAY be implemented for
cryptographic-diversity experiments.  They are not recommended as the
initial default production RPKI suite in this version because their
signature sizes and signing costs are substantially higher than ML-DSA in
the available measurements.

Falcon/FN-DSA, MAYO, SNOVA, and HAWK are outside the mandatory path of
this document.  They may be evaluated as research candidates, but they
MUST NOT be treated as RPKI production algorithm suites by this document
until stable PKIX and CMS profiles exist and are referenced by a future
revision or separate document.

## Algorithm Selection Rationale

ML-DSA-65 is selected as the primary candidate because it has an existing
FIPS signature specification [FIPS204] and corresponding PKIX [RFC9881]
and CMS [RFC9882] algorithm identifier specifications.  It is not
selected because it is always the smallest or fastest possible signature
algorithm.

ML-DSA-44 is retained as a measured comparison but is excluded from the
primary profile because this document uses NIST Category 3 as a conservative
minimum for the primary long-lived RPKI suite.  This is a profile policy
choice, not evidence of an implementation failure, and SIDROPS may revisit it.

ML-DSA-87, SLH-DSA-SHAKE-128s, and SLH-DSA-SHAKE-192s remain useful
comparison points for security level, cryptographic diversity, and
repository stress testing.  The SLH-DSA candidates have corresponding
signature, PKIX, and CMS specifications [FIPS205] [RFC9909] [RFC9814].
Falcon/FN-DSA and other additional-signature candidates may be attractive
for size or performance reasons, but they are outside the mandatory path
of this revision until stable PKIX and CMS profiles and RPKI validator
evidence are available.

The first-order repository estimator gives Falcon-512, using a 666-octet
maximum signature size, a 1.5542 ratio to the RSA baseline and gives
SNOVA-(24,5,4), using a 248-octet signature, a 1.2723 ratio.  Both are much
smaller than the estimated 4.0118 ratio for ML-DSA-65.  These ratios are
synthetic estimates based on static parameter sizes, not local primitive or
full-repository measurements: the corresponding backends were unavailable in
the recorded run.  They are outside the primary profile because stable PKIX
and CMS profiles and validator evidence are absent, not because of repository
size.  They should be reconsidered if their standardization and implementation
maturity changes.

Published RPKI analysis also identifies Falcon-512 as a compact and
performance-oriented candidate [Doesburg2025].  This document treats that
result as literature evidence; the accompanying evidence snapshot does not
contain a confirmed local Falcon primitive benchmark.

Detailed measurements for key sizes, signature sizes, primitive timings,
repository-size estimates, and validator probes are maintained outside
this document by the experimental harness [pqc-rpki-lab].  Those values
are implementation and environment dependent and are not protocol
requirements.

# Resource Certificate and CRL Profile

RPKI resource certificates and CRLs using ML-DSA MUST follow the
certificate and CRL conventions for ML-DSA defined in RFC 9881.  In
particular, AlgorithmIdentifier parameters for ML-DSA MUST be absent.

When id-ml-dsa-65 or id-ml-dsa-87 appears in SubjectPublicKeyInfo, the
subjectPublicKey BIT STRING contains the raw public key encoding defined
by FIPS 204 and profiled by RFC 9881.

For RPKI CA certificates, the keyUsage extension MUST remain consistent
with the resource certificate profile.  A CA certificate that is used to
issue certificates and CRLs requires keyCertSign and cRLSign.  An EE
certificate used for an RPKI signed object requires digitalSignature and
MUST NOT be used as a CA certificate.

This document does not change the RPKI resource extension semantics,
certificate policy OID, certificate path validation procedure, manifest
processing rules, or CRL processing rules.

# CMS Signed Object Profile

RPKI signed objects using ML-DSA MUST follow the CMS conventions for
ML-DSA defined in [RFC9882] and the RPKI signed object template defined in
[RFC6488], as updated by [RFC9589].

The signatureAlgorithm field of SignerInfo MUST contain id-ml-dsa-65 for
the primary Next Suite.  AlgorithmIdentifier parameters MUST be absent.

For ML-DSA-65, the digestAlgorithms field of SignedData and the
digestAlgorithm field of SignerInfo MUST contain id-sha512.  The parameters
field of that AlgorithmIdentifier MUST be absent.  The message-digest signed
attribute MUST contain the SHA-512 digest of the eContent.  SHA-512 is selected
from the algorithms permitted for ML-DSA-65 by [RFC9882] to provide one
mandatory interoperable encoding for this RPKI suite.

The signedAttrs element remains REQUIRED for RPKI signed objects.  In
accordance with [RFC6488] as updated by [RFC9589], it MUST contain exactly one
content-type attribute, one message-digest attribute, and one signing-time
attribute.  The binary-signing-time attribute and all other signed attributes
MUST be absent.  In particular, the CMSAlgorithmProtection attribute suggested
by the general CMS guidance in [RFC9882] MUST NOT be included because the RPKI
signed object profile restricts signedAttrs to those three attributes.

OpenSSL 3.6.2 generated ML-DSA certificates and CRLs but its CMS CLI rejected
ML-DSA signing with `CMS_add1_signer:no default digest`.  The SHA-512 selection
above follows [RFC9882]; the CLI failure remains an implementation and
interoperability gap rather than an unspecified protocol value.

The CMS eContentType and eContent for ROAs, manifests, and other RPKI
signed objects are unchanged.  Validators MUST apply the object-specific
validation rules after CMS signature validation exactly as they do for the
Current Suite.

# Manifests, ROAs, and Repository Processing

## Implementation Evidence

The accompanying implementation harness generated ML-DSA-65, ML-DSA-87,
SLH-DSA-SHAKE-128s, and SLH-DSA-SHAKE-192s CA certificates, EE certificates,
and CRLs using the OpenSSL 3.6.2 default provider.  The certificates included
RFC 3779 IP address and AS resource extensions, RPKI certificate policy,
Subject Information Access, basic constraints, and key usage.  Private keys
were generated only in an automatically deleted temporary directory.

The same OpenSSL installation did not generate ML-DSA CMS SignedData.
Consequently, no RFC 6488 manifest or ROA was generated by the harness.
This is an implementation limitation, not evidence that the RFC profiles are
incompatible.  Routinator, rpki-client, and FORT were not installed in the
measurement environment, so validator acceptance is unconfirmed.

The default run did not receive a real local RPKI cache.  Repository impact
values in this revision remain synthetic or literature-calibrated estimates.

This document does not define new payload encodings for manifests, ROAs,
or CRLs.  Repository operators MAY publish Current Suite and Next Suite
products in parallel during an algorithm transition.  A repository that
publishes parallel products MUST ensure that manifests and CRLs are
internally consistent within each suite.

During parallel publication, operators SHOULD provide a way to identify
corresponding products across suites for measurement and debugging.  This
identification MAY be derived from publication point structure, object
names, CA hierarchy, or an implementation-specific mapping.  It is not a
new on-wire RPKI object in this version.

# Relying Party Behavior

An RP that implements this document MUST be configurable with an accepted
algorithm policy.  The policy MUST be able to represent at least:

* Current Suite only;
* Current Suite plus Next Suite;
* Next Suite preferred with Current Suite fallback;
* Next Suite only.

An RP MUST reject a certificate, CRL, or signed object whose signature
algorithm is not in its configured policy.  The rejection reason SHOULD be
reported distinctly from syntax errors, path validation failures, manifest
failures, and object-specific semantic failures.

An RP that validates both Current Suite and Next Suite products SHOULD
perform semantic-equivalence checks for corresponding products.  For ROAs,
this check compares the resulting VRP set by prefix, maxLength, origin AS,
and trust anchor context.  If the Current Suite and Next Suite produce
different routing semantics, the RP SHOULD emit telemetry and SHOULD NOT
silently merge the divergent outputs.

This document does not require routers to support PQC.  Routers receive
validated payloads through RTR or local export formats.  The RP remains
the cryptographic enforcement point.

# Migration Strategy

The migration strategy follows the planned, multi-year model described in
RFC 6916.  This document does not define an emergency migration.

A deployment that follows this document is expected to proceed through the
following phases.

1. Implementation readiness: CAs and RPs add support for the Next Suite in
   non-production code paths.
2. Test repositories: operators publish PQC test repositories under test
   TALs.
3. Parallel publication: selected CAs publish corresponding products under
   the Current Suite and the Next Suite.
4. RP measurement: RPs validate both suites and report validation time,
   repository size, failure modes, and semantic equivalence.
5. PQC-preferred operation: RPs prefer the Next Suite while retaining the
   Current Suite for a limited period.
6. Classical retirement: a separate transition timetable defines the
   twilight date and withdrawal of the old suite.

This document assumes the top-down migration constraint of RFC 6916 for
production deployment.  Experiments involving partial parent migration,
partial child migration, or mixed unsupported validator deployment are
useful for failure analysis, but they are not declared valid production
transition states by this revision.

# Implementation Status

This section records the status of known implementations of the protocol
defined by this specification at the time of posting of this
Internet-Draft, and is based on a proposal described in [RFC7942].  It is
intended to assist IETF discussion and is to be removed before publication
as an RFC.

An experimental repository, pqc-rpki-lab, was used to evaluate this
proposal.  The implementation status at the time of this draft is:

* Static algorithm metadata: implemented.
* Primitive benchmark using existing libraries: implemented.
* Synthetic repository impact estimator: implemented.
* Local cache size collector: implemented.
* VRP semantic equivalence checker: implemented for CSV/JSON fixtures.
* Validator probes: implemented, but Routinator, rpki-client, and FORT
  were not installed in the test environment.
* RFC-profiled PQC CA certificates, EE certificates, and CRLs: generated
  with OpenSSL 3.6.2 for ML-DSA and SLH-DSA.
* PQC CMS SignedData: unsupported by the tested OpenSSL CMS CLI, which
  returned `CMS_add1_signer:no default digest`.
* Manifest and ROA generation: not completed because PQC CMS signing and an
  existing payload generator were unavailable.
* Multi-validator interoperability using real PQC RPKI objects: future work.

The highest-priority implementation gap is an RFC 9882-capable CMS path and
an existing MFT/ROA payload generator.  The second highest-priority gap is
independent validator behavior for complete objects.

# Security Considerations

The purpose of this document is to reduce the risk that RPKI signatures
become forgeable in the presence of a CRQC.  It does not solve CA
compromise, repository compromise, operational misissuance, BGP policy
mistakes, or route leaks.

Downgrade attacks are a primary concern during a long transition.  An RP
that supports both Current Suite and Next Suite products MUST make its
algorithm acceptance policy explicit.  It MUST NOT silently accept a
Current Suite product as equivalent to a missing or invalid Next Suite
product when local policy requires the Next Suite.

Parallel publication introduces the possibility of semantic divergence.
For example, the RSA branch and the PQC branch might contain different
ROA payloads, stale manifests, or different CRL state.  Validators SHOULD
detect and report these cases rather than silently selecting one branch
without operator visibility.

Larger public keys, signatures, certificates, CRLs, and CMS objects can
increase repository transfer size, local cache size, manifest size, and
validation time.  Implementations SHOULD enforce resource limits and
telemetry for object size, number of objects, validation time, and memory
use.  Operators SHOULD evaluate RRDP snapshot and delta sizes before
large-scale deployment.

ML-DSA uses randomized signing by default.  CA implementations and HSMs
MUST use cryptographically appropriate randomness and SHOULD follow the
operational guidance in RFC 9881 and RFC 9882.  Deterministic signing is
not preferred for platforms where side-channel or fault attacks are a
concern.

Algorithm confusion is possible if AlgorithmIdentifier parameters,
SignerInfo digestAlgorithm, CMS signed attributes, or certificate
SubjectPublicKeyInfo encodings are inconsistently handled.  Implementations
MUST reject malformed AlgorithmIdentifier encodings and MUST follow the
parameter rules of the referenced LAMPS specifications.

Composite signatures may protect against failures in one component
algorithm, but they also introduce additional encoding, policy, and
interoperability complexity.  This document treats composite signatures as
future work until the corresponding LAMPS specifications
[I-D.ietf-lamps-pq-composite-sigs] [I-D.ietf-lamps-cms-composite-sigs] and
RPKI-specific policy questions are stable.

# IANA Considerations

This document requests no new IANA allocations in its current form.  The
ML-DSA and SLH-DSA algorithm identifiers are reused from existing PKIX and
CMS specifications.  If a future revision defines an RPKI-specific
algorithm-suite registry or new telemetry identifiers, this section will
be updated.

# Open Issues

The following issues require additional SIDROPS discussion and
implementation evidence.  In particular, this draft should not strengthen
ML-DSA-65 requirement language until complete RFC 6488 PQC objects are
generated and major validator behavior is measured.

* Whether ML-DSA-65 should be mandatory-to-implement for RPs and CAs.
* Whether ML-DSA-87 is needed for trust anchors or upper-tier CAs.
* Whether SLH-DSA should remain only a diversity experiment.
* Whether composite signatures are needed for RPKI, or whether parallel
  publication is operationally sufficient.
* Whether Null Scheme-like signed-object reductions
  [I-D.doesburg-sidrops-nullscheme] should be considered separately from
  the initial signature-algorithm profile.
* How to define a transition timetable and readiness metrics for RPKI
  deployment.
* Whether semantic-equivalence checking should be mandatory during the
  parallel-publication phase.
* How to handle PQC unsupported validators in mixed deployments.
* Whether TAK, ASPA, RSC, and BGPsec should be covered by this document or
  by separate companion documents.
* How RRDP snapshot and delta limits should be operationally assessed for
  larger objects.
* Whether any RPKI-specific object naming, repository layout, or manifest
  conventions are needed to map corresponding products across suites.

--- back

# Acknowledgements

The author thanks the SIDROPS and LAMPS communities for the specifications
and implementation work that make this experiment possible.

# References

## Normative References

[BCP14] Best Current Practice 14, comprising RFC 2119 and RFC 8174,
https://www.rfc-editor.org/info/bcp14.

[RFC6480] Lepinski, M. and S. Kent, "An Infrastructure to Support Secure
Internet Routing", RFC 6480, DOI 10.17487/RFC6480, February 2012.

[RFC6487] Huston, G., Michaelson, G., and R. Loomans, "A Profile for X.509
PKIX Resource Certificates", RFC 6487, DOI 10.17487/RFC6487, February
2012.

[RFC6488] Lepinski, M., Chi, A., and S. Kent, "Signed Object Template for
the Resource Public Key Infrastructure (RPKI)", RFC 6488, DOI
10.17487/RFC6488, February 2012.

[RFC6916] Gagliano, R., Kent, S., and S. Turner, "Algorithm Agility
Procedure for the Resource Public Key Infrastructure (RPKI)", BCP 182,
RFC 6916, DOI 10.17487/RFC6916, April 2013.

[RFC7935] Huston, G. and G. Michaelson, "The Profile for Algorithms and Key
Sizes for Use in the Resource Public Key Infrastructure", RFC 7935, DOI
10.17487/RFC7935, August 2016.

[RFC8182] Bruijnzeels, T., Muravskiy, O., Weber, B., and R. Austein, "The
RPKI Repository Delta Protocol (RRDP)", RFC 8182, DOI 10.17487/RFC8182,
July 2017.

[RFC9286] Austein, R., Huston, G., Kent, S., and M. Lepinski, "Manifests for
the Resource Public Key Infrastructure (RPKI)", RFC 9286, DOI
10.17487/RFC9286, June 2022.

[RFC9582] Snijders, J., Maddison, B., Lepinski, M., Kong, D., and S. Kent,
"A Profile for Route Origin Authorizations (ROAs)", RFC 9582, DOI
10.17487/RFC9582, May 2024.

[RFC9589] Snijders, J. and T. Harrison, "On the Use of the Cryptographic
Message Syntax (CMS) Signing-Time Attribute in Resource Public Key
Infrastructure (RPKI) Signed Objects", RFC 9589, DOI 10.17487/RFC9589,
May 2024.

[RFC9814] Housley, R., Fluhrer, S., Kampanakis, P., and B. Westerbaan, "Use
of the SLH-DSA Signature Algorithm in the Cryptographic Message Syntax
(CMS)", RFC 9814, DOI 10.17487/RFC9814, July 2025.

[RFC9881] Massimo, J., Kampanakis, P., Turner, S., and B. E. Westerbaan,
"Internet X.509 Public Key Infrastructure -- Algorithm Identifiers for
the Module-Lattice-Based Digital Signature Algorithm (ML-DSA)", RFC 9881,
DOI 10.17487/RFC9881, October 2025.

[RFC9882] Salter, B., Raine, A., and D. Van Geest, "Use of the ML-DSA
Signature Algorithm in the Cryptographic Message Syntax (CMS)", RFC 9882,
DOI 10.17487/RFC9882, October 2025.

[RFC9909] Bashiri, K., Fluhrer, S., Gazdag, S., Van Geest, D., and S.
Kousidis, "Internet X.509 Public Key Infrastructure -- Algorithm Identifiers
for the Stateless Hash-Based Digital Signature Algorithm (SLH-DSA)", RFC
9909, DOI 10.17487/RFC9909, December 2025.

[FIPS204] National Institute of Standards and Technology, "Module-Lattice-
Based Digital Signature Standard", FIPS 204, DOI 10.6028/NIST.FIPS.204,
August 2024.

[FIPS205] National Institute of Standards and Technology, "Stateless Hash-
Based Digital Signature Standard", FIPS 205, DOI 10.6028/NIST.FIPS.205,
August 2024.

## Informative References

[RFC7942] Sheffer, Y. and A. Farrel, "Improving Awareness of Running Code:
The Implementation Status Section", BCP 205, RFC 7942, DOI
10.17487/RFC7942, July 2016.

[I-D.ietf-lamps-pq-composite-sigs] Ounsworth, M., et al., "Composite
Module-Lattice-Based Digital Signature Algorithm (ML-DSA) for use in
X.509 Public Key Infrastructure", Work in Progress.

[I-D.ietf-lamps-cms-composite-sigs] Ounsworth, M., et al., "Composite
Module-Lattice-Based Digital Signature Algorithm (ML-DSA) for use in
Cryptographic Message Syntax (CMS)", Work in Progress.

[I-D.doesburg-sidrops-nullscheme] Doesburg, D., "Null Scheme for Signed
Objects in the Resource Public Key Infrastructure (RPKI)", Work in
Progress, expired.

[Doesburg2025] Doesburg, D., "Post-Quantum Cryptography for the RPKI",
Master's thesis, Radboud University, 27 June 2025,
https://www.sidnlabs.nl/en/news-and-blogs/thesis-pqc-for-the-rpki.

[pqc-rpki-lab] Yoshikawa, T., "pqc-rpki-lab experimental harness",
release for draft-yoshikawa-sidrops-pqc-rpki-00, 2026,
https://github.com/marokiki/pqc-rpki-lab/releases/tag/draft-yoshikawa-sidrops-pqc-rpki-00.
