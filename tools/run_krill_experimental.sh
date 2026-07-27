#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/local/build"
KRILL="$ROOT/local/upstream/krill"
OUTPUT="$ROOT/local/krill-experimental/repository"
SUITE_FILE="$ROOT/local/krill-experimental/suite"
CARGO="$BUILD/cargo-home/bin/cargo"
OPENSSL="$BUILD/openssl-3.6.2-install/bin/openssl"
RPKI_CLIENT="$BUILD/rpki-client-composite/src/rpki-client"
ROUTINATOR="$ROOT/local/upstream/routinator/target/debug/routinator"

for path in "$CARGO" "$OPENSSL" "$RPKI_CLIENT" "$ROUTINATOR"; do
  test -x "$path" || {
    echo "required executable is missing: $path" >&2
    exit 1
  }
done

python3 - "$OUTPUT" <<'PY'
import shutil
import sys
from pathlib import Path

target = Path(sys.argv[1])
if target.exists():
    shutil.rmtree(target)
target.mkdir(parents=True)
PY
printf 'rsa\n' > "$SUITE_FILE"

(
  cd "$KRILL"
  RUSTUP_HOME="$BUILD/rustup-home" \
  CARGO_HOME="$BUILD/cargo-home" \
  OPENSSL_DIR="$BUILD/openssl-3.6.2-install" \
  LD_LIBRARY_PATH="$BUILD/openssl-3.6.2-install/lib64:${LD_LIBRARY_PATH:-}" \
  OPENSSL_CONF="$ROOT/experiments/openssl-composite.cnf" \
  PQC_COMPOSITE_PROVIDER_MODULE="$BUILD/composite-provider/composite.so" \
  PQC_RPKI_OPENSSL="$OPENSSL" \
  PQC_RPKI_EXPERIMENTAL=1 \
  PQC_RPKI_KRILL_SUITE_FILE="$SUITE_FILE" \
  PQC_RPKI_KRILL_OUTPUT="$OUTPUT" \
    "$CARGO" +1.88.0 test --no-default-features \
      --test functional_pqc_rollover -- --nocapture
)

LD_LIBRARY_PATH="$BUILD/openssl-3.6.2-install/lib64:${LD_LIBRARY_PATH:-}" \
OPENSSL_CONF="$ROOT/experiments/openssl-composite.cnf" \
PQC_COMPOSITE_PROVIDER_MODULE="$BUILD/composite-provider/composite.so" \
PYTHONPATH="$ROOT/src" \
  python3 "$ROOT/tools/krill_experimental_validate.py" \
    --krill-output "$OUTPUT" \
    --rpki-client "$RPKI_CLIENT" \
    --routinator "$ROUTINATOR"
