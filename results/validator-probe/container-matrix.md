# Unmodified Validator Container Probe

> EXPERIMENTAL / NOT FOR PRODUCTION

| Validator | Repository | Status | Parser | Certificate path | Manifest | ROA | VRP output | Hard error |
|---|---|---|---|---|---|---|---|---|
| Routinator | rsa | accepted | accepted | accepted | accepted | accepted | present |  |
| rpki-client | rsa | accepted | accepted | accepted | accepted | accepted | present |  |
| FORT | rsa | accepted | accepted | accepted | accepted | accepted | present |  |
| Routinator | ml-dsa-65 | rejected | rejected | rejected-or-not-reached | rejected-or-not-reached | rejected-or-not-reached | absent | [ERROR] Failed to read TAL /tals/test.tal: bad key info: invalid public key format (at position 6). |
| rpki-client | ml-dsa-65 | rejected | rejected | rejected-or-not-reached | rejected-or-not-reached | rejected-or-not-reached | absent | Certificates: 1 (1 invalid, 0 non-functional) |
| FORT | ml-dsa-65 | rejected | rejected | rejected-or-not-reached | rejected-or-not-reached | rejected-or-not-reached | absent | Jul  3 04:00:26 WRN: Validation from TAL '/tals/test.tal' yielded error -22 (Invalid argument); discarding all validation results. |
