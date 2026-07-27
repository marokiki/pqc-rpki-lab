#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PINS="$ROOT/experiments/composite-dependencies.json"
UPSTREAM="$ROOT/local/upstream"
BUILD="$ROOT/local/build"
RUSTUP_HOME="$BUILD/rustup-home"
CARGO_HOME="$BUILD/cargo-home"
KRILL="$UPSTREAM/krill"

usage() {
  echo "usage: $0 --allow-network | --check-only" >&2
  exit 2
}

[[ $# -eq 1 ]] || usage
MODE="$1"
[[ "$MODE" == "--allow-network" || "$MODE" == "--check-only" ]] || usage

json_value() {
  python3 - "$PINS" "$1" "$2" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
print(data[sys.argv[2]][sys.argv[3]])
PY
}

check_all() {
  test -d "$KRILL/.git"
  test "$(git -C "$KRILL" rev-parse HEAD)" = "$(json_value krill commit)"
  test "$(git -C "$KRILL" remote get-url --push origin)" = "DISABLED"
  git -C "$KRILL" apply --reverse --check \
    "$ROOT/patches/krill-experimental-pqc.patch"
  git -C "$UPSTREAM/rpki-rs" apply --reverse --check \
    "$ROOT/patches/rpki-rs-experimental-pqc.patch"
  test -x "$CARGO_HOME/bin/cargo"
  test -x "$KRILL/target/debug/krill"
  echo "pinned experimental Krill source, patches, and build are present"
}

if [[ "$MODE" == "--check-only" ]]; then
  check_all
  exit 0
fi

for tool in git python3; do
  command -v "$tool" >/dev/null || {
    echo "required tool is missing: $tool" >&2
    exit 1
  }
done

test -d "$UPSTREAM/rpki-rs/.git" || {
  echo "run make routinator-experimental-bootstrap first" >&2
  exit 1
}
git -C "$UPSTREAM/rpki-rs" apply --reverse --check \
  "$ROOT/patches/rpki-rs-experimental-pqc.patch"
test -x "$CARGO_HOME/bin/rustup" || {
  echo "run make routinator-experimental-bootstrap first" >&2
  exit 1
}

if [[ -e "$KRILL" ]]; then
  echo "refusing to replace existing path: $KRILL" >&2
  exit 1
fi
git clone "$(json_value krill url)" "$KRILL"
git -C "$KRILL" checkout --detach "$(json_value krill commit)"
git -C "$KRILL" remote set-url --push origin DISABLED
git -C "$KRILL" apply "$ROOT/patches/krill-experimental-pqc.patch"

RUSTUP_HOME="$RUSTUP_HOME" CARGO_HOME="$CARGO_HOME" \
  "$CARGO_HOME/bin/rustup" toolchain install 1.88.0 --profile minimal

(
  cd "$KRILL"
  RUSTUP_HOME="$RUSTUP_HOME" \
  CARGO_HOME="$CARGO_HOME" \
  OPENSSL_DIR="$BUILD/openssl-3.6.2-install" \
  LD_LIBRARY_PATH="$BUILD/openssl-3.6.2-install/lib64:${LD_LIBRARY_PATH:-}" \
    "$CARGO_HOME/bin/cargo" +1.88.0 build --no-default-features
)

check_all
"$ROOT/tools/run_krill_experimental.sh"
