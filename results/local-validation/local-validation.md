# Local Object Validation

> EXPERIMENTAL / NOT FOR PRODUCTION

This verifies DER parseability, CMS signature/content round-trips, object-specific EE certificate constraints, and Manifest product hashes with OpenSSL and the internal parser. It is not independent multi-validator interoperability.

| Algorithm | Layer | Artifact | Status | Reason |
|---|---|---|---|---|
| rsa | DER parse | ca.cer | confirmed |  |
| rsa | DER parse | route.ee.cer | confirmed |  |
| rsa | DER parse | manifest.ee.cer | confirmed |  |
| rsa | DER parse | ca.crl | confirmed |  |
| rsa | DER parse | route.roa.econtent | confirmed |  |
| rsa | DER parse | manifest.mft.econtent | confirmed |  |
| rsa | CMS verify | route.roa | confirmed |  |
| rsa | CMS verify | manifest.mft | confirmed |  |
| rsa | EE profile | route.ee.cer | confirmed |  |
| rsa | EE profile | manifest.ee.cer | confirmed |  |
| rsa | Manifest hash | manifest.mft.econtent | confirmed |  |
| ml-dsa-44 | DER parse | ca.cer | confirmed |  |
| ml-dsa-44 | DER parse | route.ee.cer | confirmed |  |
| ml-dsa-44 | DER parse | manifest.ee.cer | confirmed |  |
| ml-dsa-44 | DER parse | ca.crl | confirmed |  |
| ml-dsa-44 | DER parse | route.roa.econtent | confirmed |  |
| ml-dsa-44 | DER parse | manifest.mft.econtent | confirmed |  |
| ml-dsa-44 | CMS verify | route.roa | skipped | CMS artifact unavailable |
| ml-dsa-44 | CMS verify | manifest.mft | skipped | CMS artifact unavailable |
| ml-dsa-44 | EE profile | route.ee.cer | confirmed |  |
| ml-dsa-44 | EE profile | manifest.ee.cer | confirmed |  |
| ml-dsa-65 | DER parse | ca.cer | confirmed |  |
| ml-dsa-65 | DER parse | route.ee.cer | confirmed |  |
| ml-dsa-65 | DER parse | manifest.ee.cer | confirmed |  |
| ml-dsa-65 | DER parse | ca.crl | confirmed |  |
| ml-dsa-65 | DER parse | route.roa.econtent | confirmed |  |
| ml-dsa-65 | DER parse | manifest.mft.econtent | confirmed |  |
| ml-dsa-65 | CMS verify | route.roa | confirmed |  |
| ml-dsa-65 | CMS verify | manifest.mft | confirmed |  |
| ml-dsa-65 | EE profile | route.ee.cer | confirmed |  |
| ml-dsa-65 | EE profile | manifest.ee.cer | confirmed |  |
| ml-dsa-65 | Manifest hash | manifest.mft.econtent | confirmed |  |
| ml-dsa-87 | DER parse | ca.cer | confirmed |  |
| ml-dsa-87 | DER parse | route.ee.cer | confirmed |  |
| ml-dsa-87 | DER parse | manifest.ee.cer | confirmed |  |
| ml-dsa-87 | DER parse | ca.crl | confirmed |  |
| ml-dsa-87 | DER parse | route.roa.econtent | confirmed |  |
| ml-dsa-87 | DER parse | manifest.mft.econtent | confirmed |  |
| ml-dsa-87 | CMS verify | route.roa | skipped | CMS artifact unavailable |
| ml-dsa-87 | CMS verify | manifest.mft | skipped | CMS artifact unavailable |
| ml-dsa-87 | EE profile | route.ee.cer | confirmed |  |
| ml-dsa-87 | EE profile | manifest.ee.cer | confirmed |  |
