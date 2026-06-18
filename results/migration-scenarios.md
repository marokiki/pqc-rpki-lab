# Migration Scenarios

> EXPERIMENTAL / NOT FOR PRODUCTION

| Scenario Id | Scenario | Validator Population | Expected Vrp Relation | Status | Observation |
|---|---|---|---|---|---|
| rsa-only | RSA only | all | equivalent | confirmed | Baseline deployment |
| parallel-ml-dsa-65 | RSA + ML-DSA-65 parallel | mixed | equivalent | estimated | Preferred first transition experiment |
| parallel-ml-dsa-87 | RSA + ML-DSA-87 parallel | mixed | equivalent | estimated | High-assurance transition |
| parallel-slh-128s | RSA + SLH-DSA-SHAKE-128s parallel | mixed | equivalent | estimated | Large repository and transfer impact |
| pqc-only | PQC only | PQC-capable only | equivalent | future work | Legacy validators reject or ignore branch |
| partial-hierarchy | Partial parent/child migration | policy-dependent | blocked | estimated | Algorithm suite mismatch can break path validation |
| inconsistent-roa | Inconsistent parallel ROA | mixed | different | confirmed | Must raise semantic divergence telemetry |
| stale-manifest | Stale manifest in one branch | mixed | different | confirmed | Freshness rules remain independently enforced |
| mixed-validators | Unsupported validator mixed deployment | mixed | policy-dependent | estimated | Avoid silent downgrade and split VRP views |
