#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PINS="$ROOT/experiments/composite-dependencies.json"
UPSTREAM="$ROOT/local/upstream"
BUILD="$ROOT/local/build"
JOBS="${PQC_RPKI_BUILD_JOBS:-4}"

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

check_tools() {
  local tool
  for tool in cmake git make perl python3; do
    command -v "$tool" >/dev/null || {
      echo "required tool is missing: $tool" >&2
      exit 1
    }
  done
}

pin_url() {
  json_value "$1" url
}

pin_commit() {
  json_value "$1" commit
}

check_checkout() {
  local name="$1"
  local path="$2"
  local expected
  expected="$(pin_commit "$name")"
  test -d "$path/.git" || {
    echo "missing checkout: $path" >&2
    return 1
  }
  test "$(git -C "$path" rev-parse HEAD)" = "$expected" || {
    echo "wrong commit in $path" >&2
    return 1
  }
  test "$(git -C "$path" remote get-url --push origin)" = "DISABLED" || {
    echo "push is not disabled in $path" >&2
    return 1
  }
}

clone_pin() {
  local name="$1"
  local path="$2"
  local url commit
  url="$(pin_url "$name")"
  commit="$(pin_commit "$name")"
  if [[ -e "$path" ]]; then
    echo "refusing to replace existing path: $path" >&2
    exit 1
  fi
  git clone "$url" "$path"
  git -C "$path" checkout --detach "$commit"
  git -C "$path" remote set-url --push origin DISABLED
}

prepare_rp_source() {
  local portable="$1"
  local apply_experimental="$2"
  clone_pin rpki_client_portable "$portable"
  git clone "$(pin_url rpki_client_openbsd)" "$portable/openbsd"
  git -C "$portable/openbsd" checkout --detach \
    "$(pin_commit rpki_client_openbsd)"
  git -C "$portable/openbsd" remote set-url --push origin DISABLED
  if [[ "$apply_experimental" == "yes" ]]; then
    git -C "$portable/openbsd" apply \
      "$ROOT/patches/rpki-client-composite-experimental.patch"
  fi
  (
    cd "$portable"
    ./autogen.sh "$(pin_commit rpki_client_openbsd)"
  )
}

build_rp() {
  local source="$1"
  local output="$2"
  local prefix="$output/install"
  mkdir -p "$output"
  (
    cd "$output"
    "$source/configure" \
      --with-openssl=openssl \
      --with-openssl-cflags="-I$BUILD/openssl-3.6.2-install/include" \
      --with-openssl-ldflags="-L$BUILD/openssl-3.6.2-install/lib64 -Wl,-rpath,$BUILD/openssl-3.6.2-install/lib64" \
      --prefix="$prefix"
    make -j"$JOBS"
  )
}

check_tools
mkdir -p "$UPSTREAM" "$BUILD"

if [[ "$MODE" == "--check-only" ]]; then
  check_checkout openssl "$UPSTREAM/openssl-3.6.2"
  check_checkout composite_provider "$UPSTREAM/composite-provider"
  check_checkout rpki_client_portable "$UPSTREAM/rpki-client-portable"
  check_checkout rpki_client_openbsd \
    "$UPSTREAM/rpki-client-portable/openbsd"
  check_checkout rpki_client_portable \
    "$UPSTREAM/rpki-client-portable-unmodified"
  check_checkout rpki_client_openbsd \
    "$UPSTREAM/rpki-client-portable-unmodified/openbsd"
  test -x "$BUILD/openssl-3.6.2-install/bin/openssl"
  test -f "$BUILD/composite-provider/composite.so"
  test -x "$BUILD/rpki-client-baseline/src/rpki-client"
  test -x "$BUILD/rpki-client-composite/src/rpki-client"
  echo "pinned Composite E2E dependencies and builds are present"
  exit 0
fi

clone_pin openssl "$UPSTREAM/openssl-3.6.2"
(
  cd "$UPSTREAM/openssl-3.6.2"
  ./Configure \
    --prefix="$BUILD/openssl-3.6.2-install" \
    --openssldir="$BUILD/openssl-3.6.2-install/ssl" \
    shared enable-rfc3779
  make -j"$JOBS"
  make install_sw
)

clone_pin composite_provider "$UPSTREAM/composite-provider"
git -C "$UPSTREAM/composite-provider" apply \
  "$ROOT/patches/composite-provider-private-key-decoder.patch"
cmake -S "$UPSTREAM/composite-provider" \
  -B "$BUILD/composite-provider" \
  -DCMAKE_BUILD_TYPE=Release \
  -DOPENSSL_ROOT_DIR="$BUILD/openssl-3.6.2-install"
cmake --build "$BUILD/composite-provider" --parallel "$JOBS"

prepare_rp_source "$UPSTREAM/rpki-client-portable-unmodified" no
prepare_rp_source "$UPSTREAM/rpki-client-portable" yes
build_rp "$UPSTREAM/rpki-client-portable-unmodified" \
  "$BUILD/rpki-client-baseline"
build_rp "$UPSTREAM/rpki-client-portable" "$BUILD/rpki-client-composite"

"$0" --check-only
make -C "$ROOT" composite-e2e-rp-matrix
