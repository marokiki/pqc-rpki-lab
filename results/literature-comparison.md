# Literature Comparison

> EXPERIMENTAL / NOT FOR PRODUCTION

The calibrated model uses the measured object, public-key, and signature counts from the 2025 thesis. Local primitive and published full-RPKI timings are not directly comparable.

| Algorithm | Current synthetic ratio | Calibrated ratio | Published ratio | Synthetic difference | Published validation CPU s |
|---|---|---|---|---|---|
| RSA-2048/SHA-256 | 1.0 | 1.0 | 1.0 | 0.0 | 13.0 |
| ML-DSA-65 | 4.0118 | 4.6628 | 4.6538 | -13.96 | 51.8 |
| ML-DSA-87 | 5.2798 | 6.204 | 6.205 | -14.9 | 80.9 |
| SLH-DSA-SHAKE-128s | 6.845 | 8.0419 | 7.9949 | -14.88 | 1376.3 |
| SLH-DSA-SHAKE-192s | 13.3845 | 15.927 |  | -15.96 |  |
| Falcon-512 | 1.5542 | 1.6794 | 1.6706 | -7.45 | 23.4 |
| Falcon-1024 | 2.3682 | 2.678 | 2.6252 | -11.57 | 46.4 |
| MAYO-1 | 1.584 | 1.7253 | 1.6706 | -8.19 | 44.3 |
| SNOVA-(24,5,4) | 1.2723 | 1.3418 | 1.3126 | -5.18 | 47.3 |
| HAWK-512 | 1.515 | 1.6345 | 1.6706 | -7.31 | 42.8 |
