#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/local/build"
KRILL="$ROOT/local/upstream/krill"
COUNT="${PQC_RPKI_KRILL_ROA_COUNT:-1000}"
REPETITIONS="${PQC_RPKI_KRILL_RELIABILITY_REPETITIONS:-10}"
BASE="$ROOT/local/krill-scaled/verified-${COUNT}"
OUTPUT="$BASE/repository"
SUITE_FILE="$BASE/suite"
RELIABILITY="$ROOT/local/krill-reliability"
CARGO="$BUILD/cargo-home/bin/cargo"
OPENSSL="$BUILD/openssl-3.6.2-install/bin/openssl"
RPKI_CLIENT="$BUILD/rpki-client-composite/src/rpki-client"
ROUTINATOR="$ROOT/local/upstream/routinator/target/debug/routinator"

case "$COUNT:$REPETITIONS" in
  *[!0-9:]*|0:*|*:0)
    echo "counts must be positive integers" >&2
    exit 2
    ;;
esac

for path in "$CARGO" "$OPENSSL" "$RPKI_CLIENT" "$ROUTINATOR"; do
  test -x "$path" || {
    echo "required executable is missing: $path" >&2
    exit 1
  }
done

python3 - "$BASE" "$RELIABILITY" <<'PY'
import shutil
import sys
from pathlib import Path

for raw in sys.argv[1:]:
    target = Path(raw)
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
PY

for iteration in $(seq 1 "$REPETITIONS"); do
  if env -u PQC_RPKI_KRILL_ROA_COUNT \
      "$ROOT/tools/run_krill_experimental.sh" \
      >"$RELIABILITY/run-${iteration}.log" 2>&1; then
    printf '%s\tpass\n' "$iteration" >>"$RELIABILITY/results.tsv"
  else
    printf '%s\tfail\n' "$iteration" >>"$RELIABILITY/results.tsv"
    exit 1
  fi
done

printf 'rsa\n' >"$SUITE_FILE"
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
  PQC_RPKI_KRILL_ROA_COUNT="$COUNT" \
    /usr/bin/time -v -o "$BASE/generation.time" \
      "$CARGO" +1.88.0 test --no-default-features \
        --test functional_pqc_rollover -- --nocapture
)

LD_LIBRARY_PATH="$BUILD/openssl-3.6.2-install/lib64:${LD_LIBRARY_PATH:-}" \
OPENSSL_CONF="$ROOT/experiments/openssl-composite.cnf" \
PQC_COMPOSITE_PROVIDER_MODULE="$BUILD/composite-provider/composite.so" \
PYTHONPATH="$ROOT/src" \
  /usr/bin/time -v -o "$BASE/validation.time" \
    python3 "$ROOT/tools/krill_experimental_validate.py" \
      --krill-output "$OUTPUT" \
      --rpki-client "$RPKI_CLIENT" \
      --routinator "$ROUTINATOR" \
      --work "$BASE/validation-work" \
      --result "$BASE/validation.json" \
      --expected-vrp-count "$COUNT"

PYTHONPATH="$ROOT/src" python3 "$ROOT/tools/summarize_scaled_krill.py" \
  --scaled-root "$BASE" \
  --reliability "$RELIABILITY/results.tsv" \
  --roa-count "$COUNT"
