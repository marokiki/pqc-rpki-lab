# VRP Set Equality

> EXPERIMENTAL / NOT FOR PRODUCTION

The default hash is a local canonical JSON approximation, not the DER-encoded CCR `ROAPayloadState.hash`. When validator CCR output is available, that hash is the comparison target; decoded `rps` values identify individual VRP differences. Trust-anchor and source attribution are reported separately.

| Baseline Count | Candidate Count | Equivalent | Only Baseline Count | Only Candidate Count | Provenance Difference Count | Baseline Local Hash | Candidate Local Hash | Status |
|---|---|---|---|---|---|---|---|---|
| 2 | 2 | True | 0 | 0 | 0 | 0db17e0be0b26181fc3857665671e3035cdbaabe9b69046939e313b4d6c8be4a | 0db17e0be0b26181fc3857665671e3035cdbaabe9b69046939e313b4d6c8be4a | estimated |
