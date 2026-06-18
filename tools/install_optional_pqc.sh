#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LIBOQS_TAG="0.15.0"
LIBOQS_COMMIT="97f6b86b1b6d109cfd43cf276ae39c2e776aed80"
LIBOQS_PYTHON_COMMIT="35eceb69d2b363cb0421085cf1ae1c682dee1acc"

if [[ "${1:-}" != "--allow-network" && "${PQC_RPKI_ALLOW_NETWORK:-0}" != "1" ]]; then
  echo "network access is disabled; pass --allow-network or set PQC_RPKI_ALLOW_NETWORK=1" >&2
  exit 2
fi

python3 -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/pip" install cmake==4.3.2 ninja==1.13.0 cryptography==48.0.1
WORK="$(mktemp -d "${TMPDIR:-/tmp}/pqc-rpki-oqs.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
git clone --depth 1 --branch "$LIBOQS_TAG" https://github.com/open-quantum-safe/liboqs.git "$WORK/liboqs"
test "$(git -C "$WORK/liboqs" rev-parse HEAD)" = "$LIBOQS_COMMIT"
"$ROOT/.venv/bin/cmake" -S "$WORK/liboqs" -B "$WORK/build" -GNinja \
  -DCMAKE_MAKE_PROGRAM="$ROOT/.venv/bin/ninja" -DBUILD_SHARED_LIBS=ON \
  -DCMAKE_INSTALL_PREFIX="$ROOT/.local/oqs"
"$ROOT/.venv/bin/cmake" --build "$WORK/build" --parallel "${PQC_RPKI_BUILD_JOBS:-4}"
"$ROOT/.venv/bin/cmake" --install "$WORK/build"
git clone https://github.com/open-quantum-safe/liboqs-python.git "$WORK/liboqs-python"
git -C "$WORK/liboqs-python" checkout "$LIBOQS_PYTHON_COMMIT"
OQS_INSTALL_PATH="$ROOT/.local/oqs" "$ROOT/.venv/bin/pip" install "$WORK/liboqs-python"
echo "installed pinned liboqs and liboqs-python"
