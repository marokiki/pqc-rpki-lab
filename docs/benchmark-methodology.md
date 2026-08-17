# Benchmark Methodology

> EXPERIMENTAL / NOT FOR PRODUCTION

The repository keeps separate measurement classes:

| Class | Command | Measures | Does not measure |
|---|---|---|---|
| Primitive benchmark | `make` | Key generation, signing, verification, and sizes for configured algorithms | Complete RPKI object processing |
| Exact 100k benchmark | `make exact-100k` | Exactly 100,000 sign operations and 100,000 verify operations over a 32-byte message | Key roll, CMS, publication, validator work |
| Composite component benchmark | `make composite-100k` | Sequential component signatures where both components must verify | LAMPS composite encoding or interoperability |
| Composite ML-DSA benchmark (draft revision 19) | `make draft-composite-100k` | Revision-19 message representative, context binding, raw signature concatenation, and two-component verification | X.509/CMS/RPKI profile encoding or validator interoperability |
| Object payload benchmark | `make object-benchmarks` | Synthetic Manifest file-list construction, payload hashing, and deterministic payload encoding | CMS SignedData, DER RPKI object serialization, validator work |
| RPKI object fixtures | `make rpki-objects` | Public DER certificates, CRLs, eContent, and RSA/ML-DSA-65 CMS `.mft`/`.roa` | Independent validator acceptance |
| Local object validation | `make local-validation` | DER, CMS, EE profile, content, and Manifest hash checks | Full RPKI validation |
| Repeated message sweep | `make message-sweep` | 32 B, 512 B, 2 KiB, and 8 KiB EVP operations with 10 repetitions, variance, key generation, and process peak RSS | Complete object or validator processing |
| Validator containers | `make validator-container-probe` | Isolated rsync fetch and validation by pinned Routinator, rpki-client, and FORT images | Modified-validator interoperability |
| Key-roll model | `make key-roll` | Configurable file counts and transport-size estimates using measured fixture sizes where available | Production CA/HSM/RRDP behavior |
| Repository model | `make` | Estimated repository, RRDP snapshot, RRDP delta, and local-cache bytes | Production cache behavior |

All public results must record the command scope, iteration count, tool versions
where practical, and whether the result is confirmed, estimated, unsupported,
skipped, or blocked.

Historical raw measurements under `results/review-2026-06/` are preserved. New
public measurements use separate result directories so draft-00 evidence is not
overwritten accidentally.
