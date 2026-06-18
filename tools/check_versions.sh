#!/usr/bin/env bash
set -u

PYTHON="${PQC_RPKI_PYTHON:-python3}"
echo "# Tool versions"
"$PYTHON" --version 2>&1 || true
openssl version -a 2>&1 || true
echo "# OpenSSL PQC signature algorithms"
openssl list -signature-algorithms 2>/dev/null | grep -E 'ML-DSA|SLH-DSA|Falcon' || true
"$PYTHON" -c 'import oqs; print("liboqs:", oqs.oqs_version()); print("oqs-python: available")' 2>/dev/null || echo "oqs-python: unavailable"
for tool in krill routinator rpki-client fort bird bgpd; do
  if command -v "$tool" >/dev/null 2>&1; then
    case "$tool" in
      rpki-client|bgpd) "$tool" -V 2>&1 | head -1 ;;
      *) "$tool" --version 2>&1 | head -1 ;;
    esac
  else
    echo "$tool: unavailable"
  fi
done
