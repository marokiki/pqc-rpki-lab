# Algorithm candidate matrix

This file records why each candidate is included and what should be measured before taking a recommendation to IETF/SIDROPS.

| Algorithm | Include? | Status to track | Main measurements | Expected RPKI concern |
|---|---:|---|---|---|
| RSA-2048/SHA-256 | Yes | Existing RPKI profile | Baseline object sizes and validator time | Not quantum-safe |
| ML-DSA-44 | Maybe | NIST/IETF standardized | Size/performance | Security category may be too low for long-lived infrastructure policy |
| ML-DSA-65 | Yes | NIST/IETF standardized | cert/CMS size, validation speed, repository growth | Larger than RSA but likely manageable |
| ML-DSA-87 | Yes | NIST/IETF standardized | high-assurance cost delta | Larger keys/signatures; may be excessive for all ROAs |
| SLH-DSA-SHAKE-128s | Yes | NIST/IETF standardized | signature-size impact | Large signatures, repository growth |
| SLH-DSA-SHAKE-192s | Yes | NIST/IETF standardized | category-3 hash-based comparison | Very large signatures |
| FN-DSA/Falcon-derived | Later | NIST additional signature track / standardization status to monitor | implementation maturity, encoding availability | not yet stable enough for v0 normative dependency |
| Composite ML-DSA + RSA/ECDSA | Later/optional | LAMPS draft maturity | migration semantics, object size, parser support | draft dependency and validator complexity |

## Data fields to fill by experiment

The scripts should generate `results/algorithm-matrix.csv` with at least these columns:

```csv
algorithm,nist_category,standards_status,x509_profile,cms_profile,public_key_bytes,secret_key_bytes,signature_bytes,keygen_ms,sign_ms,verify_ms,cert_der_bytes,cms_der_bytes,repository_growth_ratio,validator_runtime_ratio,notes
```
