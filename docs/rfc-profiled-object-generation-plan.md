# RFC-Profiled PQC RPKI Object Generation Plan

> EXPERIMENTAL / NOT FOR PRODUCTION

## Confirmed feasibility result

OpenSSL 3.6.2 default provider generated ML-DSA-65, ML-DSA-87,
SLH-DSA-SHAKE-128s, and SLH-DSA-SHAKE-192s CA certificates, EE certificates,
and CRLs. The generated certificates include RFC 3779 IP/AS resource
extensions, RPKI certificate policy, SIA, key usage, and basic constraints.
Keys and objects are generated in an automatically deleted temporary directory.

OpenSSL CMS did not generate pure ML-DSA SignedData. It returned
`CMS_add1_signer:no default digest`. Consequently MFT and ROA generation is
blocked before payload integration. This is classified as
`cms-pure-signature-unsupported`, not an RPKI profile rejection.

## Standards boundary

RPKI-side requirements:

- RFC 6487 for resource certificates.
- RFC 6488 for RPKI signed objects.
- RFC 9286 for manifests.
- RFC 9582 for ROAs.
- RFC 7935 for the current RSA baseline.
- RFC 6916 for algorithm migration procedure.

PQC-side requirements:

- RFC 9881 for ML-DSA in X.509 certificates and CRLs.
- RFC 9882 for ML-DSA in CMS.
- RFC 9909 for SLH-DSA in X.509 certificates and CRLs.
- RFC 9814 for SLH-DSA in CMS.

## Remaining fixtures

Do not persist private keys. A future fixture exporter may write only public
certificates, CRLs, CMS objects, and metadata after an RFC 9882-capable CMS
backend is available.

Required output:

```text
artifacts/test-repo/
  rsa/
    ta.cer
    ca.cer
    ca.crl
    manifest.mft
    route.roa
  mldsa65/
    ta.cer
    ca.cer
    ca.crl
    manifest.mft
    route.roa
  metadata/
    object-generation.json
    object-sizes.csv
    tool-versions.txt
```

Optional output:

```text
artifacts/test-repo/mldsa87/
artifacts/test-repo/slhdsa-shake-128s/
```

## Implementation rule

Do not hand-code cryptographic algorithms. Do not invent OIDs. Do not create non-standard CMS or X.509 encodings merely to make a test pass.

Permitted implementation approaches:

1. OpenSSL 3 with oqs-provider if it can emit required certs and signatures.
2. Existing LAMPS-compatible libraries if they implement RFC 9881/9882/9909/9814 behavior.
3. Existing RPKI tooling such as Krill, with minimal patches or wrappers.
4. asn1crypto/cryptography only for assembly when cryptographic operations are delegated to standard libraries.

## Key checks

For each generated object, record:

- object type,
- algorithm identifier OID,
- public key size,
- signature size,
- total DER size,
- signedAttrs presence,
- digest algorithm used for signedAttrs,
- whether the object can be parsed by generic ASN.1 tools,
- whether the object can be parsed by RPKI validators,
- generation command,
- tool versions.

## Known risk area

The most important compatibility check is the interaction between RPKI signed object requirements and ML-DSA/SLH-DSA CMS rules. RPKI signed objects require CMS signed attributes. The implementation must verify whether RFC 9882 and RFC 9814 handling of signed attributes is compatible with the existing RPKI signed object template.

## Deliverables

- `tools/object_generation_feasibility.py`
- `results/generated-object-sizes.csv`
- `results/object-generation-feasibility.md`
- `results/object-generation-feasibility.json`
- draft text update in `ietf/draft-yoshikawa-sidrops-pqc-rpki-00.md`
