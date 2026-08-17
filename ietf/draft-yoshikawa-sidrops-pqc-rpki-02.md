---
title: "Post-Quantum Signature Experiments and Migration Considerations for the Resource Public Key Infrastructure (RPKI)"
abbrev: "PQC for RPKI"
docname: draft-yoshikawa-sidrops-pqc-rpki-02
category: info
ipr: trust200902
area: Operations and Management
wg: SIDROPS
submissiontype: IETF
consensus: false
date: 2026-07-29
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
    email: "yoshikawa.tomoki.67i@st.kyoto-u.ac.jp"
--- abstract

This document reports experiments with post-quantum signature algorithms
and analyzes migration approaches for the Resource Public Key
Infrastructure (RPKI).  The experiments compare classical,
post-quantum, and composite signature candidates; generate and validate
RPKI-profiled certificate, CRL, manifest, and ROA fixtures; evaluate
parallel publication and Mixed Certification Chains as distinct migration
structures; and evaluate the effect of larger objects on rsync, RRDP, and Erik
Synchronization.  The results identify implementation, interoperability,
repository-distribution, and operational questions that need to be resolved
before a production algorithm profile or transition procedure can be
specified.
This document is informational.  It does not update RFC 7935 or RFC
6916, define a new RPKI algorithm profile, or authorize the use of the
evaluated algorithms or Mixed Certification Chains in the production
RPKI.

--- middle

# Introduction

The RPKI relies on digital signatures in resource certificates, CRLs,
certification requests, and CMS signed objects such as manifests and
Route Origin Authorizations (ROAs).  The deployed RPKI algorithm profile
is based on RSA with SHA-256.  A Cryptographically Relevant Quantum
Computer (CRQC) capable of executing the required quantum algorithms
would undermine the unforgeability of the RSA signatures used by the
deployed RPKI profile.  Preparing for that risk requires measurements
and interoperable implementations before a production transition
procedure can be selected.

This document records that preparatory work.  The cryptographic-object and
migration experiments preserve existing RPKI payload formats and
router-facing validated payload interfaces.  The repository-distribution
experiment separately compares rsync, RRDP, and Erik Synchronization under
the larger object sizes.  Certification Authority (CA) and Relying Party
(RP) implementations require support for the additional signature
algorithms.  The Mixed Certification Chain experiment additionally
evaluates a certificate-path construction that is not permitted by the
migration procedure in RFC 6916.  Routers that consume Validated ROA
Payloads (VRPs) through the RPKI-Router Protocol (RTR) or local files do not
process the evaluated signatures directly.

The descriptions of algorithms, encodings, validation behavior, and
migration steps in this document are experimental assumptions and
observations.  They are not interoperability requirements for production
RPKI implementations.

# Terminology

This document uses the terminology of the RPKI architecture [RFC6480],
the resource certificate profile [RFC6487], the RPKI signed object
template [RFC6488], the RPKI algorithm agility procedure [RFC6916], and
the RPKI algorithm profile [RFC7935].

Current Suite:  The algorithm suite specified by the currently
applicable production RPKI algorithm profile.  At the time of writing,
this is RSA-2048/SHA-256 as profiled by RFC 7935.

Next Suite:  A candidate algorithm suite that is implemented and tested
before it becomes the Current Suite.

PQC Suite:  A Next Suite whose signature algorithm is intended to remain
secure against a CRQC.

Certificate Signature Algorithm:  The algorithm used by the issuer to
sign a certificate or CRL.

Subject Public Key Algorithm:  The algorithm of the key carried in a
certificate's subjectPublicKeyInfo (SPKI).

Mixed Certification Chain:  A certification path in which different
algorithm suites are used above and below a transition certificate.

Corresponding Products:  Products under different algorithm suites that
correspond according to the relationships described in [RFC6916].
Corresponding certificates bind identical Internet Number Resources to
the same entity and are issued by the same CA.  Corresponding signed
objects contain the same encapsulated content and use corresponding EE
certificates.

Semantic Equivalence:  A property of two validation runs in which the
resulting validated routing payloads are identical.  For route-origin
validation, VRPs are compared by address prefix, maximum length, and
origin AS.  Trust-anchor selection, validation time, and input-source
metadata are compared separately.  Semantic equivalence does not imply
that individual input objects are Corresponding Products.

Parallel Publication:  A migration technique in which a CA publishes
corresponding products under both the Current Suite and the Next Suite
for an extended interval.

Composite Signature:  A signature construction that combines multiple
component algorithms into one algorithm identifier and signature value.
In the LAMPS construction evaluated by this document, verification
succeeds only when every component signature validates.

# Scope

The algorithm-profile analysis in this document applies to RPKI resource
certificates, CRLs, certification requests, BGPsec Router Certificates
[RFC8209], and the CMS signed objects that reuse the RPKI signed object
template [RFC6488], including manifests [RFC9286], ROAs [RFC9582], Signed
Checklists (RSC) [RFC9323], ASPA objects
[I-D.ietf-sidrops-aspa-profile], and Trust Anchor Key (TAK) objects
[RFC9691].  The generated signed-object fixtures in this revision cover
manifests and ROAs; additional object types are listed in the Implementation
Status section.  The CMS signed objects are treated as a single
signed-object algorithm profile; see the Signed Object Coverage section.

This document covers the RPKI signatures on BGPsec Router Certificates,
but does not define or change the BGPsec UPDATE signature algorithm
specified by [RFC8608].
For a BGPsec Router Certificate, the experiment applies only to the
certificate signature made by the issuing RPKI CA.  The subject public
key algorithm remains governed by the BGPsec UPDATE algorithm profile
and is not required to match the RPKI certificate-signature suite.

This document does not specify changes to RTR, TAL formats, RRDP
[RFC8182], rsync, the RPKI Certificate Policy, or the BPKI used to
authenticate provisioning and publication relationships established
through [RFC8183].  BPKI algorithm migration is a related operational
problem, but is not evaluated by this document and need not use the same
algorithm or transition schedule as RPKI repository objects.
This document does not modify RRDP or rsync; it separately evaluates their
transport costs, together with Erik Synchronization, under the larger
object sizes used by the experiment.

# Relationship to RFC 6916

RFC 6916 specifies a top-down algorithm transition using parallel
certification hierarchies.  It also states that an RPKI CA does not sign
a CA certificate whose subject key corresponds to an algorithm suite
different from the suite used to sign that certificate.

The Mixed Certification Chain experiment described in this document
deliberately evaluates the X.509 construction excluded by RFC 6916.
Objects produced by this experiment are therefore confined to test TALs
and test repositories.  Production use of this construction would
require separate Standards Track work updating or replacing the
applicable algorithm profile and migration procedure.

# Evaluation Goals

The experiments use the following evaluation goals.

* Preserve the existing RPKI object and validation model when evaluating
  signature-algorithm changes.
* Reuse existing LAMPS PKIX and CMS encodings for PQC algorithms.
* Avoid new RPKI object formats unless measurements show that simple
  signature substitution is infeasible.
* Keep routers as consumers of validated payloads, not PQC validators,
  while acknowledging that RP validation and repository processing
  change.
* Apply one signature algorithm suite uniformly to all RFC 6488 signed
  objects rather than per-object-type algorithm choices.
* Evaluate the EUF-CMA security hedge provided by a composite
  construction when one component remains secure, subject to the
  assumptions of the referenced LAMPS construction.
* Examine the operational effects of a prolonged period in which the
  Current Suite and Next Suite coexist.
* Identify operational measurements needed to detect differences in
  validated outputs during an algorithm transition.
* Keep measurement and interoperability evidence reproducible outside the
  protocol specification.

# Evaluated Algorithm Suites

## Current Suite

The Current Suite baseline used by this experiment is RSA PKCS #1 v1.5
with SHA-256 as specified by RFC 7935.  This document does not set a
production transition timetable.

## Composite Configuration Evaluated in This Revision

The composite signature construction used by this experiment is defined in
revision 19 of [I-D.ietf-lamps-pq-composite-sigs].  The evaluated
configuration is id-MLDSA65-ECDSA-P256-SHA512 (OID
1.3.6.1.5.5.7.6.45), whose identifier and component-algorithm combination
are specified by that document.  It combines ML-DSA-65 with ECDSA P-256 and requires
both component signatures to validate.  The corresponding CMS use is
specified by [I-D.ietf-lamps-cms-composite-sigs].  The choice of this
composite configuration is an experimental input, not a recommendation for
production deployment.

The object experiment applies
[I-D.ietf-lamps-pq-composite-sigs] to composite public keys and
certificate signatures, and [I-D.ietf-lamps-cms-composite-sigs] to
composite CMS SignedData.  The public reference implementation has
generated complete composite X.509 certificates, CRLs, ROAs, and
manifests and has validated an RSA-to-composite mixed tree with
experimental rpki-client and Routinator extensions.  The two RP
processing paths share one OpenSSL and Composite provider backend, so
this is not independent cryptographic interoperability evidence.

Experiments with the composite suite are confined to isolated repositories
under test TALs.  Experimental objects, production repositories,
production keys, and production TALs are deliberately kept separate.

## Additional Candidate Suites

ML-DSA-44 is an additional experimental configuration.  It produces smaller
public keys and signatures and may sign and verify faster, which matters
in a system where RPs repeatedly synchronize repository state and validate
large numbers of objects.  This revision uses ML-DSA-65 in the composite
configuration as an explicit experimental choice, not because the RPKI
requires NIST security Category 3.  The Rationale for the Experimental
Configurations section discusses this choice and its counterarguments.

ML-DSA-87 is included as a higher-security comparison candidate.  It is more
conservative than ML-DSA-65 but carries correspondingly larger size and
performance costs.

SLH-DSA-SHAKE-128s and SLH-DSA-SHAKE-192s are included for
cryptographic-diversity comparison.  Their signature algorithm, PKIX, and CMS
specifications are defined by [FIPS205], [RFC9909], and [RFC9814].  They
are not proposed as the initial suite in this revision because their
signature sizes are substantially larger than those of ML-DSA in the
evaluated configurations.

FN-DSA (Falcon), MAYO, and SNOVA are additional candidates for
future evaluation.  They are outside the present evaluation until stable
PKIX and CMS profiles are available and referenced by a future revision or
separate document.
FN-DSA in particular is discussed further in the Rationale for the
Experimental Configurations section, because its compact signatures make it an attractive
candidate for the RPKI's bulk validation model.

Other Composite ML-DSA combinations specified by LAMPS remain candidates
for comparison.  Changing the component pair would change object sizes and
cryptographic costs, but would not determine whether a deployment uses
parallel publication or a Mixed Certification Chain.  RP support for a
selected suite remains a deployment prerequisite.

## Classical Reference Points

To relativize the cost of PQC candidates, this document uses two compact
classical algorithms as non-normative reference points: ECDSA P-256 with
SHA-256 [FIPS186-5], which is already used for BGPsec UPDATE signatures
[RFC8608], and Ed25519 [RFC8032].  Neither is a CRQC-resistant
algorithm, and neither is proposed here as an RPKI suite.  They provide
compact classical reference points for signature and key sizes in the
non-PQ universe: the deployed RSA-2048 profile is itself several times
larger than these curves, and PQC candidates should be compared against
both baselines rather than against RSA alone.

## Size Model Inputs

The table below records the values supplied to the first-order size
model.  The representations are deliberately mixed: some rows use raw
public keys or fixed-width signatures, while others use representative
DER values or a maximum encoded signature size.  They are therefore
model inputs, not a uniform comparison of SubjectPublicKeyInfo or
signature encodings.

| Algorithm | Cat. | Key representation used by model (B) | Signature representation used by model (B) |
|---|---|---|---|
| RSA-2048/SHA-256 | n/a | 270 | 256 |
| P-256/SHA-256 | n/a | 65 | ~72 |
| Ed25519 | n/a | 32 | 64 |
| ML-DSA-44 | 2 | 1312 | 2420 |
| ML-DSA-65 | 3 | 1952 | 3309 |
| ML-DSA-87 | 5 | 2592 | 4627 |
| FN-DSA-512 (Falcon) | 1 | 897 | <=666 |
| SLH-DSA-SHAKE-128s | 1 | 32 | 7856 |
| SLH-DSA-SHAKE-192s | 3 | 48 | 16224 |

"Cat." is the NIST security category; "n/a" marks classical reference
algorithms.  The RSA-2048 key value is a representative DER RSA
public-key value used by the model.  The P-256 value is an uncompressed
point, and the Ed25519, ML-DSA, FN-DSA, and SLH-DSA values are raw public
keys.  The ECDSA value is a representative DER signature size, while
FN-DSA records a maximum.  These choices are documented so that later
models can replace them with consistently measured RPKI object
encodings.

Beyond static sizes, the evaluation considers the
following dimensions: certificate and CRL size under the RPKI profile;
CMS signed object size; signing and verification cost under the RP
workload; impact on repository size and on distribution via RRDP, rsync,
and Erik;
CA key rollover and publication cycle impact; HSM support; and
standardization and implementation maturity.  The dimensions backed by
measurements in this revision are identified in Appendix A.

Two qualitative observations from the preliminary evidence inform the
rationale in the next section.  First, RP workload is verification
dominated: an RP verifies repository objects but signs nothing as part
of validation, and the deployed RSA profile is exceptionally cheap at
verification, so increases in verification cost are particularly relevant
to RP operation.  Second, first-order size
models place ML-DSA-65 near a fourfold repository size increase over
the RSA baseline, ML-DSA-44 near threefold, and FN-DSA-512 well below
twofold.

Measurements supporting these observations, together with
their conditions, caveats, and the list of dimensions not yet backed by
confirmed measurements, are collected in Appendix A and are maintained
in reproducible form by the experimental harness [pqc-rpki-lab].
Measured values are implementation and environment dependent and are not
protocol requirements.

## Rationale for the Experimental Configurations

This experiment evaluates a composite suite because a global RPKI
migration may benefit from not depending exclusively on a newly deployed
PQC algorithm.  The LAMPS construction accepts a composite signature
only when both component signatures validate.  Under the assumptions
stated by that construction, its EUF-CMA guarantee is retained when at
least one component remains EUF-CMA secure and the prehash remains
collision resistant.

This hedge has a limit.  A CRQC defeats the ECDSA component, so security
against a quantum adversary still depends on ML-DSA-65 remaining secure.
The composite suite also does not protect against failures shared by
both components or by the combiner, encoding, key management, or
validation implementation.  It does not in general preserve strong
unforgeability when only one component has that property.  An
implementation defect in one component can be tolerated only when the
other component, the combiner, encodings, key handling, and the
all-component validation path remain unaffected.

ML-DSA-65 is used as the PQC component of the composite configuration
evaluated in this revision because it has a final FIPS signature
specification [FIPS204], corresponding PKIX [RFC9881] and CMS [RFC9882]
algorithm identifier specifications, and implementations available in
the software environment used by this experiment.  This revision
also chooses Category 3 as an experimental point for examining the cost
of a larger security margin in a system whose re-migration could be a
global, multi-year operation.  This is not an RPKI requirement.  It is not
used because it is the smallest or fastest possible signature
algorithm; it is neither.

The choice between ML-DSA-44 and ML-DSA-65 is genuinely open.  The
argument for ML-DSA-65 is conservatism: the RPKI is a single global
system, algorithm migrations in it are slow and expensive, and a larger
security margin reduces the probability of needing another migration.
The argument for ML-DSA-44 is that a structural cryptanalytic break of
module lattices would likely affect all ML-DSA parameter sets, so the
extra category mainly protects against gradual erosion of concrete
security estimates rather than against a qualitative break; under that
view, the roughly 25-35% smaller keys and signatures of ML-DSA-44, or a
small-PQ composite built on it, may be a better use of the size budget
[Doesburg2025].  This document uses ML-DSA-65 in the composite
configuration measured in this revision, keeps ML-DSA-44 in the comparison,
and records the parameter-set choice as a question for further work.

ML-DSA-87 provides a higher-security comparison point, but its size and
performance costs make it less attractive in the evaluated repository
model.

FN-DSA (Falcon) is an attractive candidate on size and performance
grounds: its signatures are roughly one fifth the size of ML-DSA-65
signatures, and both published RPKI analysis [Doesburg2025] and
repository-scale redesign work [pqRPKI] identify Falcon as the compact
lattice option.  This document nevertheless treats FN-DSA as an
additional configuration for future evaluation rather than one measured
in the composite experiment, for the following reasons:

* This document does not profile FN-DSA because it does not reference a
  final FN-DSA standard together with stable PKIX and CMS profiles.

* Side-channel-resistant FN-DSA implementations and HSM support require
  separate implementation and deployment evaluation.

* Availability of FN-DSA in the platforms that RPKI CAs, RIRs, HSM
  vendors, and validator implementations actually use is a separate
  question from the algorithm's intrinsic merits.  This experiment does
  not evaluate production RPKI CA or RP support for FN-DSA.

These are reasons to sequence the evaluation, not to dismiss the
algorithm.  FN-DSA remains in the comparison set as the compact
signature candidate, and the conditions under which it should be
examined further are recorded as questions for further work.

Algorithm selection for the RPKI cannot be based on software benchmarks
alone.  HSM support for a candidate algorithm is also a deployment
prerequisite for CAs that protect their signing keys in HSMs.

# Experimental Certificate and CRL Encoding

The composite certificate and CRL experiment follows the encodings in
[I-D.ietf-lamps-pq-composite-sigs].  Under that assumption, a composite
subject carries id-MLDSA65-ECDSA-P256-SHA512 in the SPKI
AlgorithmIdentifier with absent parameters.  A certificate or CRL signed
by the composite issuer uses that identifier in its signatureAlgorithm
field.  A transition certificate signed by a Current Suite issuer instead
retains the issuer's Current Suite signatureAlgorithm while carrying the
composite identifier in the subject SPKI.

The same composite SPKI and signature encodings are assumed for resource
certificate requests and their proof-of-possession signatures.  Pure
ML-DSA certificates and CRLs used for component measurements follow
[RFC9881]; they provide component-level evidence and are not proposed as
a production Next Suite.  These request and proof-of-possession encodings
are not exercised by the implementation in this revision.

The generated RPKI fixtures preserve the existing keyUsage constraints.
CA certificates carry keyCertSign and cRLSign, while EE certificates for
signed objects carry digitalSignature and are not used as CA
certificates.  The experiment does not change resource extension
semantics, the certificate policy OID, certificate path validation,
manifest processing, or CRL processing.

# Experimental CMS Signed Object Encoding

The composite CMS experiment combines
[I-D.ietf-lamps-cms-composite-sigs] with the RPKI signed object template
in [RFC6488], as updated by [RFC9589].  The assumed SignerInfo
signatureAlgorithm is id-MLDSA65-ECDSA-P256-SHA512 with absent
parameters.  The SignedData digestAlgorithms set includes id-sha512,
and the SignerInfo digestAlgorithm is id-sha512.  The parameters are absent in
both AlgorithmIdentifiers, and the message-digest signed attribute
contains the SHA-512 digest of the eContent.

The experiment retains the signedAttrs restrictions from the existing
RPKI signed object profile: one content-type attribute, one
message-digest attribute, and one signing-time attribute, with no
binary-signing-time or other signed attributes.  The eContentType,
eContent, and object-specific validation rules remain unchanged.

The implementation generated and validated complete Composite ROA and
manifest SignedData using these encodings, together with the certificates
and CRLs required for repository validation.  Experimental rpki-client and
Routinator extensions processed the resulting repository.  Interoperability
with a cryptographic implementation independent of the shared OpenSSL and
Composite provider remains open work.

# Signed Object Coverage

Manifests [RFC9286], ROAs [RFC9582], Signed Checklists [RFC9323], ASPA
objects [I-D.ietf-sidrops-aspa-profile], TAK objects [RFC9691], and any
future object types built on the RFC 6488 template share one CMS structure,
one EE certificate model, one certification infrastructure, and one
repository.  The evaluation model therefore treats them as one
signed-object algorithm profile.  Migrating, for example, ROAs to a PQC
suite while leaving ASPA objects on RSA would introduce per-object-type
algorithm diversity, leaving part of the RPKI signed-object set dependent
on the Current Suite.

Changing only the CMS signature algorithm does not change an object's
eContentType or object-specific payload syntax.  Some objects, notably
TAK objects, may nevertheless carry public keys whose algorithms change
as part of a wider trust-anchor migration and therefore require separate
object-specific interoperability testing.  A future standards-track
profile that selects a new mandatory RPKI algorithm suite would update
[RFC7935].  An object-specific RFC needs an update
only if that object's payload or validation semantics also change; this
document makes no such change.

BGPsec UPDATE signatures are not RFC 6488 signed objects and are outside
this experiment.  BGPsec Router Certificates and their covering CRLs and
manifests are repository products and remain part of the evaluation
scope.

# Related Experimental Designs

The cryptographic-object and mixed-chain experiments preserve the existing
X.509 resource-certificate and CMS signed-object model while changing
signature algorithms and, in the mixed-chain case, the certification path.
The Null Scheme [I-D.doesburg-sidrops-nullscheme] preserves the signed-object
structure but replaces the one-time-use EE key pair and CMS signature
with a public key derived from the message digest and an empty signature,
reducing redundant cryptographic cost.

pqRPKI [pqRPKI] instead introduces a Merkle Tree Ladder and restructures
manifest, delegation, and bulk-verification processing.  It is an
alternative repository architecture rather than a direct algorithm
substitution.  Comparing these object-design alternatives requires separate
measurements; the cryptographic-object experiments in this document cover
only the structure-preserving approach.

# Repository Distribution Considerations

## Impact of Larger Objects

Changing the signature suite affects more than cryptographic processing.
Larger certificates, CRLs, manifests, and signed objects increase the bytes
transferred during cold repository synchronization and in updates that
contain those objects.  The captured 1,000-ROA Composite repository
occupied 9,797,552 object bytes, compared with 1,768,736 bytes for its RSA
rollback state, a 5.54-fold increase.  Transport scalability is therefore a
deployment constraint that needs evaluation independently of algorithm
correctness and RP validation time.

## RRDP, rsync, and Erik Synchronization

RRDP [RFC8182] distributes snapshots and a journal of deltas.  An RP obtains
a complete snapshot when the notification file no longer offers a
contiguous delta chain from the RP's serial, or when the session identifier
changes.  A polling RP can receive intermediate publication states that it
does not ultimately use.
An rsync synchronization first exchanges repository metadata and then
transfers changed files; even an unchanged repository therefore has a cost
that grows with the file list.

Erik Synchronization [I-D.ietf-sidrops-rpki-erik-protocol] is an RPKI-
specific replication protocol using Merkle trees, content-addressable
naming, and HTTP.  An RP compares ErikIndex and ErikPartition objects and
fetches selected objects by hash.  Snapshot and segment prefetching can
reduce the request cost of cache bootstrap and catch-up.  This document
does not specify Erik or require it for PQC deployment; it evaluates Erik
alongside RRDP and rsync as a candidate response to repository expansion.

## Transport Experiment Boundary

Appendix A compares cold synchronization, an unchanged repository, one ROA
replacement, and 10% ROA churn for RSA-2048, pure ML-DSA-65, and the
evaluated Composite suite.  It combines an actual local rsync run with
RRDP-shaped and Erik-shaped response-body accounting over the same
deterministic, size-calibrated corpus.  The transformed corpus preserves
measured object counts and repository sizes but is not a cryptographically
valid RPKI repository.  The comparison is consequently evidence about byte
growth and request shape, not a production-network throughput result.

# Manifests and Repository Processing

## Manifest Scope During Migration

A manifest covers the products of one CA instance at one publication
point, as specified by [RFC9286] and updated by [RFC9981].  The manifest is
signed with a one-time-use EE certificate issued by that CA.  Its fileList contains
the certificates issued and published by that CA, the CA's current CRL,
and signed objects whose embedded EE certificates were issued by that
CA.

The relevant RP check is therefore issuer and publication-scope
consistency, not equality between the manifest signing key and product
keys.  An RP validates the manifest EE certificate under the associated
CA, verifies each listed certificate, CRL, or signed object under that
same CA instance as required by its object profile, and checks the
publication point, file name, and file hash according to [RFC9286].  A
shared publication point can contain products from multiple CA instances
during key rollover, but each manifest covers only its associated CA
instance.

Mixed Certification Chains and composite signatures do not change these
checks.  This document therefore introduces no additional requirement
for the manifest EE key to equal a key used by a listed product, and it
does not weaken the existing RP checks that bind every listed product to
the manifest's CA scope.

## Parallel Publication Mechanics

The parallel-publication experiment does not define new payload
encodings for manifests, ROAs, or CRLs.  It publishes Current Suite and
Next Suite products in separate, internally consistent branches.

The experimental harness needs a mapping between corresponding products
for measurement and debugging.  Such a mapping can be derived from the
publication point structure, object names, CA hierarchy, or an
implementation-specific record.  It is not proposed as a new on-wire
RPKI object.

# Experimental Results Summary

OpenSSL 3.6.2 and the evaluated Composite provider generated complete
certificate, CRL, manifest, and ROA sets for pure ML-DSA-65, Composite
ML-DSA, and an RSA-to-Composite mixed tree.  Experimental rpki-client and
Routinator extensions validated each repository and produced the same two
VRPs as the RSA baseline.  An experimental Krill extension then created a
Composite child below an RSA parent, published and replaced ROAs, and rolled
the child back to RSA.  Both experimental RPs derived the expected VRPs at
each stage.

The primary repeated cryptographic-operation benchmarks measure key
generation, signing, and verification without X.509, CMS, repository
transfer, or RP processing.  Those rows use ten independent runs and give
the median and sample standard deviation.  Additional Composite ML-DSA
operation measurements and their conditions are identified separately in
Appendix A.  Repository ratios are separate synthetic estimates derived
from explicit object counts and measured key and signature sizes.  Appendix
A records the complete methods, results, and limitations.

The two RP extensions use the same OpenSSL and Composite provider backend.
The experiment therefore demonstrates two RP processing paths, but not
independent cryptographic interoperability or production readiness.

# Relying Party Evaluation

The experiment extended rpki-client and Routinator to recognize the
id-ml-dsa-65 and id-MLDSA65-ECDSA-P256-SHA512 identifiers and to delegate
their cryptographic operations to OpenSSL providers.  Each RP processed
four complete repositories: the RSA baseline, pure ML-DSA-65, Composite
ML-DSA, and an RSA-to-Composite mixed tree.  For every repository, the
test covered certificate-path and CRL validation, manifest and CMS
validation, ROA processing, and VRP production.

The mixed-tree test additionally verified that the issuer signature
algorithm and subject SPKI algorithm are processed independently.  The RSA
parent's public key verifies the signature on the transition certificate,
while the Next Suite public key carried in the transition certificate's
SPKI is used to validate signatures issued by the child.

Fifteen negative cases for cryptographic and profile processing exercised algorithm
identifiers and parameters, digest and signature corruption, component
order and truncation, certificate-path failure, and manifest hash failure.
Seven repository-operation cases exercised expired, revoked, stale, and
missing objects.  Both experimental RPs rejected every negative case.

When an experiment validates both Current Suite and Next Suite products,
it separately compares their semantic outputs.  For ROAs, semantic
equivalence means equality of the canonical VRP sets by prefix,
maxLength, and origin AS.  When both runs use the same CCR version and
hash algorithm, equal ROAPayloadState hashes establish equality of
those canonical VRP sets [I-D.ietf-sidrops-rpki-ccr].  The experiment
parsed actual rpki-client CCR DER for the RSA, pure ML-DSA-65,
Composite, and mixed-tree repositories and recomputed every embedded
collection hash.  All four ROAPayloadState hashes were equal, while
ManifestState differed as expected.  TrustAnchorState is compared
separately and also differed.  This result uses one CCR-producing RP.
ROAPayloadState does not preserve per-VRP
certificate-chain or publication provenance, so provenance equivalence
requires additional experiment records.  Divergent outputs are
recorded as an experimental result rather than silently merged.

This document does not require routers to support PQC.  Routers receive
validated payloads through RTR or local export formats, and the semantic
content of that output is intended to be unchanged by the algorithm
migration.

# Experimental Migration Observations

This section compares two migration structures: the planned, top-down
transition specified by RFC 6916 and the Mixed Certification Chain
evaluated in this experiment.  The choice of signature suite is orthogonal
to this comparison.

RFC 6916 specifies a top-down transition in which a parent CA adopts
support for the Next Suite before its children.  During phases 2 and 3,
corresponding Current Suite and Next Suite product sets are maintained in
parallel.  RFC 6916 deliberately avoids mixed-suite CA certificates: a CA
certificate signed using one suite does not carry a subject key associated
with another suite.

The Mixed Certification Chain evaluated here relaxes that restriction.  A
parent using the Current Suite signs a transition certificate whose subject
public key belongs to the Next Suite.  The child then issues its
certificates, CRLs, and signed objects using the Next Suite without first
requiring the parent to migrate its own CA key and product set.  Production
issuance would still require the parent to process the child's Next Suite
certificate request and proof of possession.  This experiment constructs
the transition certificate directly; it has not implemented that
provisioning exchange.

| Migration model | Migration ordering | Legacy RP compatibility | Parallel products | Principal limitation |
|---|---|---|---|---|
| RFC 6916 parallel hierarchy | Top-down | Current Suite hierarchy remains available | Required during transition | Repository and operational duplication |
| Mixed-tree subtree cutover | Per subtree after required support is available | Unsupported RPs lose the switched subtree | Not required within the switched subtree | The path still depends on Current Suite ancestors |

The experiment uses test repositories and test TALs.  It does not define or
authorize a production transition procedure.

## Parallel Publication and Semantic Divergence

Parallel Publication is useful in test repositories for comparing a
Current Suite branch with a candidate branch.  Its use as a production
transition would need to account for divergence caused by
publication failures, timing skew, software defects, or configuration
drift.  The experiment compares the resulting VRP sets.  CCR
[I-D.ietf-sidrops-rpki-ccr] is a candidate common representation for
that comparison.

## Mixed Certification Chains and Mixed-Tree Migration

The parent signs the transition certificate using the Current Suite, while
the child SPKI carries a Next Suite key.  Below that boundary, the child
uses the Next Suite to sign the certificates and CRLs that it issues, as
well as the CMS signed objects associated with the child CA.
The evaluated fixture instantiates the Next Suite with the Composite ML-DSA
configuration described above, but the mixed-chain construction itself is
algorithm-agnostic.  The model processes the two algorithm fields
independently and verifies each certificate or CRL signatureAlgorithm with
the issuer's public key.

This construction is not permitted by the RFC 6916 transition procedure.
It is evaluated only as an experimental alternative under test TALs.

Unlike the parallel-hierarchy procedure, a switched subtree does not
maintain corresponding Current Suite and Next Suite products.  This avoids
duplicate repository content and the publication, configuration, and
rollover work needed to keep two product sets aligned.  It also permits
subtrees to move independently after the necessary parent and RP support is
available, rather than waiting for every ancestor to migrate its own CA key
and product set.

The trade-off is compatibility.  Once a subtree switches, an RP that does
not support the Next Suite cannot validate it through the mixed
certification path.  Mixed-tree deployment therefore replaces the parallel
legacy hierarchy with a requirement for sufficient RP support before each
subtree cutover.

A Mixed Certification Chain rooted in a Current Suite trust anchor is not
quantum resistant as a complete certification path.  Validation of the
certification path depends on every certificate signature along it,
including signatures made under the Current Suite.  If an
adversary can forge a Current Suite certificate signature above the
transition boundary, the adversary can substitute a different Next Suite
child key and construct a forged subtree.

Mixed-tree migration is therefore a pre-compromise deployment mechanism,
not a post-compromise recovery mechanism or a complete way to establish a
quantum-resistant trust anchor.  Achieving end-to-end post-quantum security
ultimately requires removing dependence on the Current Suite from the
complete certification path.  Trust-anchor migration and establishment of
such a path are separate concerns from the mixed-tree mechanism evaluated
here.

# Implementation Status

This section records the status of the experiments at the time of posting
this Internet-Draft, using the reporting pattern described in [RFC7942].  It is
intended to assist IETF discussion and is to be removed before publication
as an RFC.

pqc-rpki-lab is a research prototype used for the experiments described in
this document.  The lists below distinguish the implemented experimental
coverage from remaining work.

Implemented:

* Generation of complete pure ML-DSA-65 and Composite certificates, CRLs,
  manifests, and ROAs, including an RSA-to-Composite mixed-tree repository.
* Experimental rpki-client and Routinator extensions that validate the RSA,
  pure ML-DSA-65, Composite, and mixed-tree repositories and produce the
  expected VRPs.
* Experimental Krill issuance, publication, one-ROA replacement, and RSA
  rollback for a Composite child below an RSA parent.
* Object generation and validation, repository-size and scale experiments,
  RP-cache experiments, and rsync/RRDP/Erik transport accounting described
  in Appendix A.
* Negative tests for cryptographic, profile, and repository failures,
  together with sibling-isolation cases and CCR output comparisons.

Not yet implemented or incomplete:

* Composite certificate requests and proof of possession, BGPsec Router
  Certificates, and Composite ASPA, RSC, and TAK objects.
* Independent cryptographic interoperability and a second CCR-producing RP.
* Public-like multi-CA re-signing and production-network RRDP, rsync, and
  Erik measurements.
* HSM support, long-running RP resource use, and additional candidate suites.

The highest-priority gaps are independent cryptographic interoperability
and validation over a public-like, re-signable multi-CA corpus.

# Security Considerations

This document addresses forgery of RPKI signatures in the presence of a
CRQC.  Existing considerations for CA compromise, repository compromise,
operational misissuance, BGP policy mistakes, and route leaks are
unchanged.

A rollback to the Current Suite is a recovery mechanism only while that
suite remains trustworthy and policy permits its use.  After the Current
Suite becomes forgeable, or after a deployment adopts a Next-Suite-only
policy, such a rollback is a downgrade rather than recovery.

Divergent algorithm policies and downgrade behavior are primary concerns
during a long transition.  Divergent suite-selection policies across the RP
population can cause different RPs to derive different VRP sets from the
same repository; this is a systemic risk of the transition period itself,
and it persists for as long as classical and PQC suites coexist.

Parallel publication introduces the possibility of semantic divergence.
For example, the RSA branch and the PQC branch might contain different
ROA payloads, stale manifests, or different CRL state.  The experiment
detects and reports these cases rather than silently selecting one branch;
see the Experimental Migration Observations section.

Mixed Certification Chains introduce the risk of confusing the
Certificate Signature Algorithm with the Subject Public Key Algorithm.
An implementation that assumes the two are equal may accept invalid
chains or reject valid ones.  The experimental model processes each
certificate or CRL signatureAlgorithm independently, verifies the
signature with the issuer's public key, and processes the subject SPKI
algorithm as a separate field.

Larger public keys, signatures, certificates, CRLs, and CMS objects
enlarge the repository fetch and validation attack surface.  A hostile
or misbehaving publication point can impose disproportionate transfer
and CPU cost on RPs, and PQC object sizes raise the ceiling of that
cost.  Resource limits and operational measurements of object size,
object count, validation time, and memory use therefore belong in a
production readiness evaluation.  Production-network measurements of
RRDP, rsync, and Erik Synchronization under projected repository sizes
and churn rates are needed before large-scale deployment.

HSM implementations of PQC algorithms are newer than their software
counterparts and may lag in side-channel hardening, fault-attack
resistance, and certification.  A CA key that is protected against
extraction but signs with a leaky implementation does not receive the intended level of protection.
Side-channel resistance is algorithm- and implementation-dependent and
requires separate evaluation for each candidate and platform.

ML-DSA supports both deterministic and randomized signing.  Signatures
generated using either mode are interoperable.  The experiment uses the
signing mode selected by the implementation and does not compare the two
modes.  Randomized signing can make implementations easier to harden against
fault and hardware side-channel attacks [RFC9881].

Algorithm confusion is possible if AlgorithmIdentifier parameters,
SignerInfo digestAlgorithm, CMS signed attributes, or certificate
SubjectPublicKeyInfo encodings are inconsistently handled.  The
experimental validation criteria reject malformed AlgorithmIdentifier
encodings and follow the parameter rules of the referenced LAMPS
specifications.

The LAMPS composite construction provides a conditional EUF-CMA
guarantee only when every component is verified, at least one component
remains EUF-CMA secure, and the prehash remains collision resistant.  It
does not generally preserve SUF-CMA from only one strongly unforgeable
component.  The experiment follows the
component-key separation rules in
[I-D.ietf-lamps-pq-composite-sigs]; reuse as standalone keys or in other
composite combinations can enable
stripping and cross-protocol attacks.  A defect in one component is
tolerated only if the other component and the combiner, parser,
encoding, key management, and all-component validation path are
unaffected.  A shared implementation defect or compromise of both
component keys is not mitigated by the composite construction.  After a
CRQC breaks ECDSA, the composite suite's unforgeability depends on
ML-DSA-65.

# IANA Considerations

This document requests no IANA actions.  It reuses algorithm identifiers
defined by the referenced LAMPS specifications and defines no new RPKI
object type, file extension, or content type.

# Questions for Further Work

The following questions require additional SIDROPS discussion and
implementation evidence.  The results reported here do not select a
production suite or transition procedure.

## Algorithm Configurations

* Whether ML-DSA-44, ML-DSA-65, or another candidate provides an appropriate
  balance of object size, signing and validation cost, security margin, and
  implementation availability for a future standards-track profile.
* Under what conditions FN-DSA should be promoted from a future
  evaluation candidate: completion of the FN-DSA standard, stable
  PKIX/CMS conventions, evidence of side-channel-resistant
  implementations, and HSM availability.

## Migration Design

* Under what operational and compatibility conditions parallel publication
  or a Mixed Certification Chain provides an acceptable migration path.
* How RP readiness can be measured reliably before a production mixed-tree
  subtree cutover.
* How to define a transition timetable and readiness metrics, and
  whether that work should update or replace RFC 6916.
* How the EE subject public-key algorithm, the CA signature on the EE
  certificate, and the CMS signature algorithm should be related under a
  future Next Suite, including whether a null-signature construction should
  replace the current one-time-use EE model.
* How provisioning and publication software will roll the BPKI trust
  anchors and EE certificates used for existing relationships, including
  relationships established through [RFC8183], before those protocols
  depend on a PQC algorithm.  The procedure needs overlap, rollback, and
  recovery behavior and can be prepared independently of the final RPKI
  object-signature algorithm choice.

## Repository Distribution

* Whether RRDP and rsync remain operationally sufficient at projected PQC
  repository sizes, topology, polling intervals, and churn rates, or whether
  deployment requires a more selective mechanism such as Erik
  Synchronization.
* How RRDP journal replay, rsync file-list exchange, Erik tree traversal,
  snapshot and segment prefetch, HTTP multiplexing, gzip, and compression
  dictionaries should be accounted for under the same network conditions.

## Operational Readiness

* Which PQC signature algorithms RIR CA teams and their HSM vendors plan
  to support, on what firmware, API, certification, and deployment
  timelines.
* Whether claimed HSM support uses a general-purpose CPU implementation
  within the HSM boundary or native hardware or FPGA acceleration, and
  how those implementation choices affect key generation, signing
  latency, throughput, side-channel properties, and operational capacity.

--- back

# Measurement Details

This appendix records measurements referenced by the Size Model Inputs,
Experimental Results Summary, and Implementation Status sections.  All values
were produced by the experimental harness [pqc-rpki-lab], which
contains the corresponding scripts, raw outputs, and environment
metadata.  The harness remains the durable record.

## Reproducibility Metadata

The evidence snapshot cited by this revision is Git commit
bbbc401336b0c917b7bb89a9e8f5b783c81012db.  The cryptographic-operation
measurements cover key generation, signing, and verification without
X.509, CMS, or repository processing.  They were run on macOS 26.5.2 arm64
on an Apple M4 using
OpenSSL 3.6.2 and a C harness compiled with
`cc -O2 -Wall -Wextra -Werror`.  The recorded environment also identifies
Python 3.14.4 and liboqs 0.15.0.  The Composite ML-DSA operation benchmark,
implementing revision 19 of the LAMPS construction, used
`cc -O3 -Wall -Wextra -Werror` with OpenSSL 3.6.2.  The small-scale E2E
and controlled-scale measurements below were run separately on the stated
12-vCPU x86-64 host.  The Composite provider used for the X.509, CMS, and RP
experiments was CompositeCrypto/composite-provider commit
2263161f6b058fe0195a98b6fad088c2d4a2595f, with the repository's private-key
decoder patch applied.

## Small-Scale E2E Measurement

A 12-vCPU x86-64 host used OpenSSL 3.6.2, the evaluated Composite
provider, and rpki-client 9.8.  Each scenario used 100 complete generation
repetitions and 1000 local RP-validation repetitions.  Standalone validation fixtures were
generated in the same benchmark run, and the mixed-tree fixture was
generated immediately before it.  Each standalone generation sample
creates one CA key and two one-time-use EE keys.  The table reports the
median and sample standard deviation in separate fields, together with
the minimum and maximum.  Wall time uses a monotonic nanosecond clock, CPU
time uses child-resource usage deltas, and maximum RSS is in KiB.

| Phase | Scenario | Metric | Median | Sample stdev | Min | Max |
|---|---|---|---:|---:|---:|---:|
| Generation | RSA baseline | Wall (s) | 0.606 | 0.094 | 0.427 | 0.893 |
| Generation | RSA baseline | CPU (s) | 0.635 | 0.102 | 0.444 | 0.947 |
| Generation | RSA baseline | RSS (KiB) | 22400 | 58 | 22268 | 22528 |
| Generation | Pure ML-DSA-65 | Wall (s) | 0.335 | 0.010 | 0.314 | 0.361 |
| Generation | Pure ML-DSA-65 | CPU (s) | 0.339 | 0.010 | 0.318 | 0.365 |
| Generation | Pure ML-DSA-65 | RSS (KiB) | 22396 | 25 | 22268 | 22400 |
| Generation | Composite standalone | Wall (s) | 0.355 | 0.011 | 0.339 | 0.388 |
| Generation | Composite standalone | CPU (s) | 0.359 | 0.011 | 0.342 | 0.392 |
| Generation | Composite standalone | RSS (KiB) | 22396 | 37 | 22268 | 22400 |
| Generation | RSA-to-Composite mixed tree | Wall (s) | 0.619 | 0.072 | 0.514 | 0.839 |
| Generation | RSA-to-Composite mixed tree | CPU (s) | 0.638 | 0.078 | 0.526 | 0.874 |
| Generation | RSA-to-Composite mixed tree | RSS (KiB) | 21248 | 80 | 21120 | 21504 |
| Validation | RSA baseline | Wall (s) | 0.0136 | 0.0010 | 0.0116 | 0.0190 |
| Validation | RSA baseline | CPU (s) | 0.0138 | 0.0010 | 0.0118 | 0.0191 |
| Validation | RSA baseline | RSS (KiB) | 7424 | 25 | 7168 | 7424 |
| Validation | Pure ML-DSA-65 | Wall (s) | 0.0158 | 0.0011 | 0.0134 | 0.0220 |
| Validation | Pure ML-DSA-65 | CPU (s) | 0.0160 | 0.0011 | 0.0135 | 0.0223 |
| Validation | Pure ML-DSA-65 | RSS (KiB) | 7424 | 17 | 7296 | 7424 |
| Validation | Composite standalone | Wall (s) | 0.0189 | 0.0013 | 0.0162 | 0.0285 |
| Validation | Composite standalone | CPU (s) | 0.0190 | 0.0013 | 0.0164 | 0.0288 |
| Validation | Composite standalone | RSS (KiB) | 7424 | 22 | 7296 | 7516 |
| Validation | RSA-to-Composite mixed tree | Wall (s) | 0.0200 | 0.0014 | 0.0167 | 0.0269 |
| Validation | RSA-to-Composite mixed tree | CPU (s) | 0.0200 | 0.0014 | 0.0168 | 0.0269 |
| Validation | RSA-to-Composite mixed tree | RSS (KiB) | 7424 | 29 | 7296 | 7584 |

All four validation scenarios produced the expected two VRPs with the
experimental rpki-client extension.
The four required repository products had a median of 4843 bytes for
RSA and occupied 28247 bytes for pure ML-DSA-65 in every repetition.
Composite standalone had a median of 28855 bytes and range of
[28851, 28859].  The seven products across both mixed-tree publication
points had a median of 29095 bytes and range of [29092, 29098].

These very small validation runs measure complete local RP processes,
but must not be extrapolated to global RPKI validation.  They exclude
network transfer and do not measure a real repository, RRDP, rsync,
cold-cache behavior, or incremental validation.  The Composite ML-DSA
100,000-operation measurements elsewhere in this appendix are cryptographic
signing and verification loops, not 100,000 complete E2E validations.

## Public-Cache Profile and Controlled Scale Measurements

One Routinator 0.15.2 RRDP-only cache snapshot was reduced to aggregate
counts and byte distributions.  It contained 550,210 public-cache objects
across 54,960 publication points and the validation run produced 980,019
VRPs.  The ARIN trust anchor was unavailable during collection.  No source
objects, keys, repository URIs, or local paths are included in the public
result.  This is one incomplete snapshot rather than a measurement of the
entire global RPKI, update churn, or incremental validation.

A separate Krill campaign used one RSA parent and one child publication
point.  For 1, 10, and 100 ROAs, complete generation was repeated 30
times; the 1,000-ROA case was repeated 10 times.  At every size, a
fresh-validator-cache validation matrix was repeated 100 times.  The
experimental rpki-client and Routinator modes produced the expected VRPs in
every repetition.

| ROAs | Generation samples | Generation wall median (s) | Generation wall sample stdev (s) |
|---:|---:|---:|---:|
| 1 | 30 | 6.990 | 0.244 |
| 10 | 30 | 7.675 | 0.348 |
| 100 | 30 | 19.360 | 0.519 |
| 1000 | 10 | 141.530 | 2.436 |

The captured 1,000-ROA Composite state contained 1008 rsync files
occupying 9,797,596 bytes.  Its RRDP snapshot was 13,145,809 bytes
uncompressed and 9,190,012 bytes with deterministic gzip.  The captured
delta for the bulk Composite publication state was 13,133,093 bytes
uncompressed and 9,182,046 bytes with deterministic gzip.  It is not the
delta produced by the later one-ROA cache-regime update.  These are
generated-state sizes, not network-throughput measurements.

The same 1,000-ROA repository was used to compare three validation cache
regimes, with 30 repetitions per RP and regime.  One ROA was replaced;
the ROA, manifest, and CRL were the three changed files.  Their combined
size was 73,160 bytes before the update and 73,204 bytes afterward.  This
cache-regime harness did not capture the corresponding RRDP delta.
rpki-client does not retain a parsed validation cache between these processes, and
its wall medians were 0.86 seconds for a fresh cache, 0.86 seconds for
an unchanged repository, and 0.85 seconds after the one-ROA update.
Routinator's corresponding medians were 2.26, 1.99, and 2.30 seconds.
The OS page cache was uncontrolled.  These values therefore characterize
this harness, not a general incremental-validation speedup.

A separate synthetic topology pilot generated one RSA parent and 100
Composite child CAs, each with one publication point and one ROA.  Its
403 objects occupied 2,598,482 bytes.  Both experimental RPs produced
100 VRPs.  After the complete publication point for one child was
removed, each produced the 99 sibling VRPs.  This test exercises branch isolation, but it
does not use Krill or reproduce public-RPKI topology.

For each captured Krill state, the harness waits for the published
object count to converge, adds a two-second quiescence interval, and
overlays the publication API's current objects at canonical
rsync-module paths before validation.

The public cache profile supplies topology and object-size inputs for a future
re-signed synthetic corpus.  The controlled campaign adds repeated
single-child scale, cache-regime, and multi-publication-point evidence.
However, full re-signing of the evaluated configurations over a public-like
topology remains future work, as do production measurements of RRDP, rsync,
and Erik.

## Repository Transport Measurements

The transport campaign reused the measured 1,000-ROA object count and the
captured RSA and Composite repository totals.  The pure ML-DSA-65 total was
size-calibrated from measured certificate, CRL, manifest, and ROA files.
Each state contained 1008 files: two certificates, three CRLs, three
manifests, and 1,000 ROAs.  These counts reproduce the captured 1,000-ROA
Krill state.  For each transition, five local rsync repetitions using
checksum comparison started from the same cache state.  RRDP values are the uncompressed
notification plus snapshot or delta response bodies.  Erik values use a
deliberately simplified single-partition accounting model: one ErikIndex,
one ErikPartition, and only the required objects fetched by hash.  This is a
lower-bound response-body model, not a complete simulation of AKI-based
partitioning or segment-prefetch behavior.  Request and response headers,
TLS, HPACK or QPACK, connection setup, and Compression Dictionary Transport
[RFC9842] are excluded.

| Algorithm | State | Local rsync exchanged (B) | RRDP response bodies (B) | Erik tree-fetch bodies (B) |
|---|---|---:|---:|---:|
| RSA-2048 | Cold | 1,897,870 | 2,444,873 | 1,769,082 |
| RSA-2048 | Unchanged | 60,562 | 184 | 113 |
| RSA-2048 | One ROA update | 203,695 | 191,067 | 143,259 |
| RSA-2048 | 10% ROA churn | 370,906 | 413,520 | 303,738 |
| ML-DSA-65 | Cold | 9,752,914 | 12,916,933 | 9,624,126 |
| ML-DSA-65 | Unchanged | 60,562 | 184 | 113 |
| ML-DSA-65 | One ROA update | 222,370 | 215,967 | 161,934 |
| ML-DSA-65 | 10% ROA churn | 1,163,068 | 1,469,604 | 1,095,900 |
| Composite | Cold | 9,926,678 | 13,147,301 | 9,797,898 |
| Composite | Unchanged | 60,562 | 184 | 113 |
| Composite | One ROA update | 169,476 | 145,451 | 109,048 |
| Composite | 10% ROA churn | 1,133,142 | 1,429,580 | 1,065,982 |

The request shape was one rsync session per state.  RRDP used two response
bodies for cold or changed states and one notification for the unchanged
state.  The simplified Erik tree-fetch model counts 1,010 requests when
cold, one when unchanged, five for a one-ROA update, and 104 for 10% churn.
The Erik snapshot-prefetch model reduced the cold object body to one bulk response of 1,768,736 bytes
for RSA, 9,623,780 bytes for ML-DSA-65, and 9,797,552 bytes for Composite;
a tree comparison still follows the prefetch as specified by the protocol.

These models show that larger signatures amplify cold and churn traffic,
while selective synchronization can avoid retransmitting most unchanged
object bodies under the modeled conditions.  They do not establish that
Erik is a prerequisite for deployment:
the rsync run was local, RRDP and Erik were response-body models rather than
production servers, and the deterministic payloads do not reproduce real
compression ratios.  Experiments measuring obsolete intermediate-state
retrieval under realistic polling intervals remain future work.

## Measured Certificate and CRL Sizes

RFC 6487-profiled certificates (including RFC 3779 resource
extensions) and CRLs generated with OpenSSL 3.6.2 are shown below.  The
RSA, P-256, Ed25519, ML-DSA, and SLH-DSA rows use the OpenSSL default
provider.  The FN-DSA-512 row uses the experimental provider described
below.

| Algorithm | CA cert (B) | EE cert (B) | CRL (B) |
|---|---|---|---|
| RSA-2048/SHA-256 | 1038 | 984 | 381 |
| P-256/SHA-256 | 641 | 587 | 187 |
| Ed25519 | 578 | 524 | 170 |
| ML-DSA-44 | 4238 | 4184 | 2541 |
| ML-DSA-65 | 5767 | 5713 | 3430 |
| ML-DSA-87 | 7725 | 7671 | 4748 |
| SLH-DSA-SHAKE-128s | 8390 | 8336 | 7977 |
| SLH-DSA-SHAKE-192s | 16774 | 16720 | 16345 |
| FN-DSA-512 (Falcon-512) | 2048 | 1991 | 764 |

The P-256 and Ed25519 rows use the same RFC 6487 structure and resource
extensions as the other rows, but are classical comparison algorithms
rather than RFC 7935 suites.  The FN-DSA-512 row uses the experimental
Falcon-512 OID and encoding from oqs-provider 0.11.0-rc1 with liboqs
0.15.0; it is a measured experimental encoding, not a final FN-DSA PKIX
profile.  Falcon signatures are variable length, so its certificate and
CRL sizes can vary between runs.

## Synthetic Repository Size Model

First-order repository size ratios relative to the RSA-2048 baseline,
computed by applying the key and signature inputs above to an explicit
synthetic corpus.  The corpus contains 10 CA certificates, 100 EE
certificates, 10 CRLs, 10 manifests, and 100 ROAs.  Its base payload
assumptions are respectively 1500, 1500, 600, 1500, and 200 bytes.

For certificates, the model adds both a public-key input and a signature
input to the base payload.  For CRLs, manifests, and ROAs, it adds the
signature input.  It multiplies each resulting size by the corresponding
object count and sums the products.  The reported repository ratio is the sum of the
modeled object sizes, normalized to the RSA-2048 baseline.  Transport
encoding and cache overhead are not included in the reported ratio.  No
real repository snapshot or snapshot date was used.  These are synthetic
model outputs, not full-repository measurements:

| Algorithm | Repository ratio |
|---|---|
| Ed25519 | 0.76 |
| P-256 | 0.78 |
| RSA-2048 | 1.00 |
| FN-DSA-512 | 1.55 |
| ML-DSA-44 | 3.08 |
| ML-DSA-65 | 4.01 |
| ML-DSA-65 + P-256 Composite | 4.09 |
| ML-DSA-87 | 5.28 |
| SLH-DSA-SHAKE-128s | 6.85 |
| SLH-DSA-SHAKE-192s | 13.38 |

As a check on the model, the same formula was applied to the standalone
fixture counts: one CA certificate, two EE certificates, one CRL, one
manifest, and one ROA.  The error below is (predicted - measured) divided
by measured.

| Suite | Model prediction (B) | Measured median (B) | Model error |
|---|---:|---:|---:|
| RSA-2048 | 9146 | 4843 | +88.8% |
| ML-DSA-65 + P-256 Composite | 33131 | 28855 | +14.8% |

For these counts, the model predicts a Composite-to-RSA ratio of 3.62,
whereas the measured ratio is 5.96.  The difference results primarily
from fixed base-payload assumptions that overestimate the small RSA
fixture.  The 4.09 ratio above is therefore specific to the stated
synthetic corpus and must not be treated as a measured repository-wide
ratio.

## Repeated Cryptographic Operation Timing

The primary timing summary below reports the median and sample standard
deviation across ten repetitions of 1000 operations on a fixed 32-byte
message.  Values are wall-clock seconds per 1000 operations.

| Algorithm | Sign median | Sign stdev | Verify median | Verify stdev |
|---|---|---|---|---|
| RSA-2048/SHA-256 | 0.340326 | 0.002114 | 0.009792 | 0.000057 |
| P-256/SHA-256 | 0.012660 | 0.000332 | 0.034535 | 0.005361 |
| Ed25519 | 0.016657 | 0.006613 | 0.040442 | 0.018694 |
| ML-DSA-44 | 0.249238 | 0.029970 | 0.047798 | 0.002460 |
| ML-DSA-65 | 0.405729 | 0.017570 | 0.073411 | 0.014139 |
| ML-DSA-87 | 0.477243 | 0.012468 | 0.115963 | 0.001536 |

The sweep also covers 512-byte, 2-KiB, and 8-KiB messages and records
key-generation timing, variance, and process peak RSS.  Those raw
results remain in the evidence snapshot rather than being duplicated
here.

## Composite ML-DSA Operation Measurements

The following single-run measurements execute 100,000 signing operations
and 100,000 verification operations for each Composite ML-DSA configuration.
They implement the message representative, ML-DSA context binding, both
component operations, raw key and signature concatenation, and all-component
verification in [I-D.ietf-lamps-pq-composite-sigs].  The ML-DSA-87 combination uses
P-384 because revision 19 does not define ML-DSA-87 with P-256.

| Composite | Sign (s/100k) | Verify (s/100k) | PubKey (B) | Mean sig (B) | Repository ratio |
|---|---|---|---|---|---|
| ML-DSA-44 + P-256 | 26.0 | 8.3 | 1377 | 2491 | 3.16 |
| ML-DSA-65 + P-256 | 45.6 | 11.9 | 2017 | 3380 | 4.09 |
| ML-DSA-87 + P-384 | 59.4 | 32.8 | 2689 | 4730 | 5.40 |

The timing includes message-representative construction and raw
signature concatenation.  It excludes key generation, file I/O, X.509,
CMS, validator processing, and HSM latency.  The repository ratios are
synthetic model outputs derived from the measured raw key and mean
signature sizes; they are not complete-repository measurements.

## Open Measurement Tasks

The following dimensions are not yet backed by confirmed measurements
and are deliberately recorded as open tasks rather than numbers:

* CA key rollover, publication cycle, and full validation across the
  evaluated configurations over a public-like, re-signable multi-CA
  topology.  The controlled
  single-child and synthetic 100-child results do not reproduce public
  RPKI topology.
* Production RRDP, rsync, and Erik transfer, churn, polling-interval, and
  cache behavior.  The generated bodies and local runs do not measure WAN
  behavior or obsolete intermediate-state transfer.
* Long-running validator memory and cache growth.  The current results
  record process peak RSS for bounded executions only.
* HSM performance and support.


# Changes from -01

This section is to be removed before publication as an RFC.

* Changed the intended status from Standards Track to Informational and
  reframed the document as an experiment report rather than an RPKI
  algorithm profile.
* Replaced interoperability requirements with experimental assumptions,
  observed behavior, and production-readiness questions.
* Added an explicit relationship to RFC 6916 and confined the
  non-RFC-6916 mixed-chain construction to test TALs and repositories.
* Separated RFC 6916 Corresponding Products from semantic equivalence
  and separated CCR ROAPayloadState comparison from TrustAnchorState and
  provenance comparison.
* Clarified the conditional EUF-CMA guarantee and SUF-CMA limitation of
  the evaluated composite construction.
* Treated composite signatures, mixed certification chains, and parallel
  publication as independent design axes.
* Added repeated-run statistics, explicit synthetic-corpus inputs and
  formulas, tool versions, and compiler flags.
* Added Composite ML-DSA operation measurements, based on revision 19,
  for ML-DSA-44 with P-256,
  ML-DSA-65 with P-256, and ML-DSA-87 with P-384.
* Added experimental Krill Composite-child issuance, publication,
  one-ROA update, and rollback evidence validated by both experimental
  RPs.
* Added 15 cryptographic/profile and seven operational negative cases.
* Added a public-cache aggregate profile, repeated Krill measurements
  through 1,000 ROAs, a 1,000-ROA cache-regime comparison, and a
  100-publication-point branch-isolation pilot.
* Added actual rpki-client CCR DER parsing and verified equal
  ROAPayloadState hashes while keeping ManifestState, TrustAnchorState,
  and provenance separate.
* Added an rsync, RRDP, and Erik repository-transport comparison, with
  measured and modeled results explicitly distinguished.
* Kept a future production algorithm profile and transition procedure as
  separate standards work informed by these results.

# Acknowledgements

The author thanks Job Snijders, Dirk Doesburg, Loganaden Velvindron, and
Ties de Kock for their reviews and comments.  The author also thanks the
SIDROPS and LAMPS communities for the specifications and implementation
work that make this experiment possible.

# References

## Informative References

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

[RFC8209] Reynolds, M., Turner, S., and S. Kent, "A Profile for BGPsec
Router Certificates, Certificate Revocation Lists, and Certification
Requests", RFC 8209, DOI 10.17487/RFC8209, September 2017.

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

[RFC9691] Martinez, C., Michaelson, G., Harrison, T., Bruijnzeels, T., and
R. Austein, "A Profile for Resource Public Key Infrastructure (RPKI)
Trust Anchor Keys (TAKs)", RFC 9691, DOI 10.17487/RFC9691, December 2024.

[RFC9881] Massimo, J., Kampanakis, P., Turner, S., and B. E. Westerbaan,
"Internet X.509 Public Key Infrastructure -- Algorithm Identifiers for
the Module-Lattice-Based Digital Signature Algorithm (ML-DSA)", RFC 9881,
DOI 10.17487/RFC9881, October 2025.

[RFC9882] Salter, B., Raine, A., and D. Van Geest, "Use of the ML-DSA
Signature Algorithm in the Cryptographic Message Syntax (CMS)", RFC 9882,
DOI 10.17487/RFC9882, October 2025.

[RFC9981] Harrison, T., Michaelson, G., and J. Snijders, "Resource Public
Key Infrastructure (RPKI) Manifest Number Handling", RFC 9981, DOI
10.17487/RFC9981, May 2026.

[FIPS204] National Institute of Standards and Technology, "Module-Lattice-
Based Digital Signature Standard", FIPS 204, DOI 10.6028/NIST.FIPS.204,
August 2024.

[I-D.ietf-lamps-pq-composite-sigs] Ounsworth, M., et al., "Composite
Module-Lattice-Based Digital Signature Algorithm (ML-DSA) for use in
X.509 Public Key Infrastructure", draft-ietf-lamps-pq-composite-sigs-19,
Work in Progress, 21 April 2026.

[I-D.ietf-lamps-cms-composite-sigs] Ounsworth, M., et al., "Composite
Module-Lattice-Based Digital Signature Algorithm (ML-DSA) for use in
Cryptographic Message Syntax (CMS)",
draft-ietf-lamps-cms-composite-sigs-05, Work in Progress, 22 May 2026.

## Additional Informative References

[RFC7942] Sheffer, Y. and A. Farrel, "Improving Awareness of Running Code:
The Implementation Status Section", BCP 205, RFC 7942, DOI
10.17487/RFC7942, July 2016.

[RFC8032] Josefsson, S. and I. Liusvaara, "Edwards-Curve Digital Signature
Algorithm (EdDSA)", RFC 8032, DOI 10.17487/RFC8032, January 2017.

[RFC8183] Austein, R., "An Out-of-Band Setup Protocol for Resource Public
Key Infrastructure (RPKI) Production Services", RFC 8183, DOI
10.17487/RFC8183, July 2017.

[RFC8608] Turner, S. and O. Borchert, "BGPsec Algorithms, Key Formats, and
Signature Formats", RFC 8608, DOI 10.17487/RFC8608, June 2019.

[RFC9323] Snijders, J., Harrison, T., and B. Maddison, "A Profile for RPKI
Signed Checklists (RSCs)", RFC 9323, DOI 10.17487/RFC9323, November 2022.

[RFC9814] Housley, R., Fluhrer, S., Kampanakis, P., and B. Westerbaan, "Use
of the SLH-DSA Signature Algorithm in the Cryptographic Message Syntax
(CMS)", RFC 9814, DOI 10.17487/RFC9814, July 2025.

[RFC9909] Bashiri, K., Fluhrer, S., Gazdag, S., Van Geest, D., and S.
Kousidis, "Internet X.509 Public Key Infrastructure -- Algorithm Identifiers
for the Stateless Hash-Based Digital Signature Algorithm (SLH-DSA)", RFC
9909, DOI 10.17487/RFC9909, December 2025.

[FIPS186-5] National Institute of Standards and Technology, "Digital
Signature Standard (DSS)", FIPS 186-5, DOI 10.6028/NIST.FIPS.186-5,
February 2023.

[FIPS205] National Institute of Standards and Technology, "Stateless Hash-
Based Digital Signature Standard", FIPS 205, DOI 10.6028/NIST.FIPS.205,
August 2024.

[RFC9842] Meenan, P., Ed. and Y. Weiss, Ed., "Compression Dictionary
Transport", RFC 9842, DOI 10.17487/RFC9842, September 2025.

[I-D.ietf-sidrops-rpki-ccr] Snijders, J., Bakker, B., Bruijnzeels, T., and
T. Buehler, "A Profile for Resource Public Key Infrastructure (RPKI)
Canonical Cache Representation (CCR)", draft-ietf-sidrops-rpki-ccr-11,
Work in Progress, 1 July 2026.

[I-D.ietf-sidrops-aspa-profile] Azimov, A., Uskov, E., Bush, R., Snijders,
J., Housley, R., and B. Maddison, "A Profile for Autonomous System
Provider Authorization", draft-ietf-sidrops-aspa-profile-29,
Work in Progress, 29 July 2026.

[I-D.ietf-sidrops-rpki-erik-protocol] Snijders, J., Bruijnzeels, T.,
Harrison, T., and W. Ohgai, "The Erik Synchronization Protocol for use
with the Resource Public Key Infrastructure (RPKI)",
draft-ietf-sidrops-rpki-erik-protocol-07, Work in Progress,
16 August 2026.

[I-D.doesburg-sidrops-nullscheme] Doesburg, D., "Null Scheme for Signed
Objects in the Resource Public Key Infrastructure (RPKI)",
draft-doesburg-sidrops-nullscheme-00, expired and archived,
5 October 2025.

[Doesburg2025] Doesburg, D., "Post-Quantum Cryptography for the RPKI",
Master's thesis, Radboud University, 27 June 2025,
https://www.sidnlabs.nl/en/news-and-blogs/thesis-pqc-for-the-rpki.

[pqRPKI] Li, W., Li, Y., and T. Chung, "pqRPKI: A Practical RPKI
Architecture for the Post-Quantum Era", arXiv:2603.06968, March 2026,
https://arxiv.org/abs/2603.06968.

[pqc-rpki-lab] Yoshikawa, T., "pqc-rpki-lab experimental evidence
snapshot", Git commit bbbc401336b0c917b7bb89a9e8f5b783c81012db,
28 July 2026,
https://github.com/marokiki/pqc-rpki-lab/tree/bbbc401336b0c917b7bb89a9e8f5b783c81012db.
