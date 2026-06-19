# Third-party policy

Do not vendor upstream projects by default. Use this directory only for small patches, commit pointers, or reproducible build notes.

Preferred upstreams to reuse:

- liboqs / oqs-python / oqs-provider
- OpenSSL 3 provider model
- Krill
- Routinator
- rpki-client
- FORT validator
- BIRD
- OpenBGPD

## Reproducible optional PQC backend

Run `make install-optional-pqc` only when network access is explicitly allowed.
The installer builds into ignored repository-local paths and currently pins:

- liboqs 0.15.0, commit `97f6b86b1b6d109cfd43cf276ae39c2e776aed80`
- liboqs-python commit `35eceb69d2b363cb0421085cf1ae1c682dee1acc`

The PyPI project named `oqs` is intentionally not declared as a dependency.
The official Open Quantum Safe Python wrapper is installed from its pinned
upstream Git commit by `tools/install_optional_pqc.sh`.

This backend enables primitive measurements for Falcon-512/1024, MAYO-1, and
SNOVA-(24,5,4). HAWK-512 remains metadata-only because it is not provided by
the pinned liboqs or OpenSSL versions.
