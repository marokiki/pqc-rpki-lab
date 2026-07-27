#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PINS="$ROOT/experiments/composite-dependencies.json"
UPSTREAM="$ROOT/local/upstream"
BUILD="$ROOT/local/build"
RUSTUP_HOME="$BUILD/rustup-home"
CARGO_HOME="$BUILD/cargo-home"

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

check_checkout() {
  local name="$1"
  local path="$2"
  test -d "$path/.git"
  test "$(git -C "$path" rev-parse HEAD)" = \
    "$(json_value "$name" commit)"
  test "$(git -C "$path" remote get-url --push origin)" = "DISABLED"
}

clone_pin() {
  local name="$1"
  local path="$2"
  if [[ -e "$path" ]]; then
    echo "refusing to replace existing path: $path" >&2
    exit 1
  fi
  git clone "$(json_value "$name" url)" "$path"
  git -C "$path" checkout --detach "$(json_value "$name" commit)"
  git -C "$path" remote set-url --push origin DISABLED
}

check_all() {
  check_checkout rpki_rs "$UPSTREAM/rpki-rs"
  check_checkout routinator "$UPSTREAM/routinator"
  git -C "$UPSTREAM/rpki-rs" apply --reverse --check \
    "$ROOT/patches/rpki-rs-experimental-pqc.patch"
  git -C "$UPSTREAM/routinator" apply --reverse --check \
    "$ROOT/patches/routinator-experimental-pqc.patch"
  test -x "$CARGO_HOME/bin/cargo"
  test -x "$UPSTREAM/routinator/target/debug/routinator"
  echo "pinned experimental Routinator source, patches, and build are present"
}

if [[ "$MODE" == "--check-only" ]]; then
  check_all
  exit 0
fi

for tool in curl git make python3; do
  command -v "$tool" >/dev/null || {
    echo "required tool is missing: $tool" >&2
    exit 1
  }
done

mkdir -p "$UPSTREAM" "$BUILD" "$RUSTUP_HOME" "$CARGO_HOME"
curl --proto '=https' --tlsv1.2 -fsSLo "$BUILD/rustup-init" \
  https://static.rust-lang.org/rustup/dist/x86_64-unknown-linux-gnu/rustup-init
chmod 700 "$BUILD/rustup-init"
RUSTUP_HOME="$RUSTUP_HOME" CARGO_HOME="$CARGO_HOME" \
  "$BUILD/rustup-init" -y --no-modify-path --profile minimal \
  --default-toolchain 1.86.0

clone_pin rpki_rs "$UPSTREAM/rpki-rs"
clone_pin routinator "$UPSTREAM/routinator"
git -C "$UPSTREAM/rpki-rs" apply \
  "$ROOT/patches/rpki-rs-experimental-pqc.patch"
git -C "$UPSTREAM/routinator" apply \
  "$ROOT/patches/routinator-experimental-pqc.patch"

(
  cd "$UPSTREAM/routinator"
  RUSTUP_HOME="$RUSTUP_HOME" \
  CARGO_HOME="$CARGO_HOME" \
  OPENSSL_DIR="$BUILD/openssl-3.6.2-install" \
  LD_LIBRARY_PATH="$BUILD/openssl-3.6.2-install/lib64:${LD_LIBRARY_PATH:-}" \
    "$CARGO_HOME/bin/cargo" build --no-default-features
)

check_all
