#!/usr/bin/env bash
# Exact Lean 4.14.0 CI bootstrap from the official leanprover/lean4 release asset.
#
# This transport path avoids releases.lean-lang.org, whose TLS endpoint has
# repeatedly failed before project code can run. The source is pinned by:
#   tag:        v4.14.0
#   tag commit: 410fab7284703f41660ca2454218dcca9b2ec896
#   asset id:   210336963
#   asset name: lean-4.14.0-linux.tar.zst
#   byte size:  249860945
#   sha256:     320f18e7d58271d95fced740522b5a5ed41b85b2af5bf0e8ab9a8dbc380e450a
#
# The SHA-256 was observed from the exact official GitHub release asset after
# independently checking asset id/name/size, archive integrity, extracted Lean
# version, and the upstream v4.14.0 tag commit. CI fails closed on any mismatch.
set -euo pipefail

LEAN_VERSION="4.14.0"
LEAN_TOOLCHAIN="leanprover/lean4:v${LEAN_VERSION}"
LEAN_TAG_COMMIT="410fab7284703f41660ca2454218dcca9b2ec896"
LEAN_ASSET_ID="210336963"
LEAN_ASSET_NAME="lean-${LEAN_VERSION}-linux.tar.zst"
LEAN_ASSET_SIZE="249860945"
LEAN_ASSET_URL="https://api.github.com/repos/leanprover/lean4/releases/assets/${LEAN_ASSET_ID}"
LEAN_SHA256="320f18e7d58271d95fced740522b5a5ed41b85b2af5bf0e8ab9a8dbc380e450a"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
actual_toolchain="$(tr -d '\r\n' < "${repo_root}/lean-toolchain")"
if [[ "$actual_toolchain" != "$LEAN_TOOLCHAIN" ]]; then
  echo "lean-toolchain mismatch: got '$actual_toolchain', expected '$LEAN_TOOLCHAIN'" >&2
  exit 1
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
archive="${tmpdir}/${LEAN_ASSET_NAME}"
extract_root="${tmpdir}/extract"
mkdir -p "$extract_root"

retry_download() {
  local attempt
  for attempt in 1 2 3; do
    if curl \
      --fail \
      --location \
      --silent \
      --show-error \
      --connect-timeout 20 \
      --max-time 900 \
      -H 'Accept: application/octet-stream' \
      -H 'X-GitHub-Api-Version: 2022-11-28' \
      "$LEAN_ASSET_URL" \
      -o "$archive"; then
      return 0
    fi
    rm -f "$archive"
    if [[ "$attempt" -eq 3 ]]; then
      echo "official Lean release asset download failed after ${attempt} attempts" >&2
      return 1
    fi
    sleep_seconds=$((5 * (2 ** (attempt - 1))))
    echo "Lean asset download attempt ${attempt} failed; retrying in ${sleep_seconds}s" >&2
    sleep "$sleep_seconds"
  done
}

retry_download

actual_size="$(stat -c '%s' "$archive")"
if [[ "$actual_size" != "$LEAN_ASSET_SIZE" ]]; then
  echo "Lean asset size mismatch: got ${actual_size}, expected ${LEAN_ASSET_SIZE}" >&2
  exit 1
fi

observed_sha256="$(sha256sum "$archive" | awk '{print $1}')"
echo "MATHEVIDENCE_LEAN_ASSET_ID=${LEAN_ASSET_ID}"
echo "MATHEVIDENCE_LEAN_ASSET_SIZE=${actual_size}"
echo "MATHEVIDENCE_LEAN_ASSET_SHA256=${observed_sha256}"
if [[ "$observed_sha256" != "$LEAN_SHA256" ]]; then
  echo "Lean asset SHA-256 mismatch: got ${observed_sha256}, expected ${LEAN_SHA256}" >&2
  exit 1
fi

# Verify compressed-stream integrity before extraction.
zstd --test "$archive" >/dev/null

tar --zstd -xf "$archive" -C "$extract_root"
toolchain_dir="${extract_root}/lean-${LEAN_VERSION}-linux"
if [[ ! -x "${toolchain_dir}/bin/lean" || ! -x "${toolchain_dir}/bin/lake" ]]; then
  echo "official Lean release archive layout is not the expected linux distribution" >&2
  find "$extract_root" -maxdepth 2 \( -type f -o -type d \) >&2 || true
  exit 1
fi

lean_version="$(${toolchain_dir}/bin/lean --version)"
lake_version="$(${toolchain_dir}/bin/lake --version)"
printf '%s\n' "$lean_version"
printf '%s\n' "$lake_version"
if [[ "$lean_version" != *"version ${LEAN_VERSION}"* ]]; then
  echo "extracted Lean version mismatch: $lean_version" >&2
  exit 1
fi

install_root="${HOME}/.local/share/mathevidence/lean-${LEAN_VERSION}-linux"
rm -rf "$install_root"
mkdir -p "$(dirname "$install_root")"
mv "$toolchain_dir" "$install_root"

if [[ -n "${GITHUB_PATH:-}" ]]; then
  echo "${install_root}/bin" >> "$GITHUB_PATH"
fi

echo "MATHEVIDENCE_LEAN_TAG_COMMIT=${LEAN_TAG_COMMIT}"
echo "MATHEVIDENCE_LEAN_BIN=${install_root}/bin/lean"
