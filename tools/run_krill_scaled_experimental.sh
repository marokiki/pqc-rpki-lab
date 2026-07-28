#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/local/build"
KRILL="$ROOT/local/upstream/krill"
COUNT="${PQC_RPKI_KRILL_ROA_COUNT:-1000}"
REPETITIONS="${PQC_RPKI_KRILL_RELIABILITY_REPETITIONS:-10}"
RUN_ID="${PQC_RPKI_KRILL_RUN_ID:-verified-${COUNT}}"
RUN_RELIABILITY="${PQC_RPKI_KRILL_RUN_RELIABILITY:-1}"
BASE="$ROOT/local/krill-scaled/$RUN_ID"
OUTPUT="$BASE/repository"
SUITE_FILE="$BASE/suite"
RELIABILITY="$ROOT/local/krill-reliability"
SUMMARY_OUTPUT="${PQC_RPKI_KRILL_SUMMARY_OUTPUT:-$ROOT/results/scaled-corpus/krill-scaled-summary.json}"
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
case "$RUN_RELIABILITY" in
  0|1) ;;
  *)
    echo "PQC_RPKI_KRILL_RUN_RELIABILITY must be 0 or 1" >&2
    exit 2
    ;;
esac
case "$RUN_ID" in
  ""|*[!A-Za-z0-9._-]*)
    echo "PQC_RPKI_KRILL_RUN_ID contains unsafe characters" >&2
    exit 2
    ;;
esac

for path in "$CARGO" "$OPENSSL" "$RPKI_CLIENT" "$ROUTINATOR"; do
  test -x "$path" || {
    echo "required executable is missing: $path" >&2
    exit 1
  }
done

python3 - "$BASE" <<'PY'
import shutil
import sys
from pathlib import Path

for raw in sys.argv[1:]:
    target = Path(raw)
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
PY

if test "$RUN_RELIABILITY" = 1; then
  python3 - "$RELIABILITY" <<'PY'
import shutil
import sys
from pathlib import Path

target = Path(sys.argv[1])
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
else
  test -s "$RELIABILITY/results.tsv" || {
    echo "reliability evidence missing: $RELIABILITY/results.tsv" >&2
    exit 1
  }
fi

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
  --roa-count "$COUNT" \
  --output "$SUMMARY_OUTPUT"
