#!/usr/bin/env bash
# Checksum-pinned elan install for CI (ME-RV-073).
#
# Source of truth for the asset:
#   https://github.com/leanprover/elan/releases/tag/v4.2.3
# Checksum recomputed locally from the release asset bytes (not from master).
# Do NOT curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh
set -euo pipefail

ELAN_VERSION="${ELAN_VERSION:-v4.2.3}"
ELAN_ARCH="${ELAN_ARCH:-x86_64-unknown-linux-gnu}"
ELAN_URL="https://github.com/leanprover/elan/releases/download/${ELAN_VERSION}/elan-${ELAN_ARCH}.tar.gz"
# sha256 of elan-x86_64-unknown-linux-gnu.tar.gz @ v4.2.3
# Verified 2026-07-26 via Get-FileHash / sha256sum against the GitHub release asset.
ELAN_SHA256="${ELAN_SHA256:-df0b2b3a439961ffcbb3985214365ffe40f49bc871df04dff268c7d8e21ca8b2}"

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

archive="$tmpdir/elan.tar.gz"
curl -fsSL "$ELAN_URL" -o "$archive"
echo "${ELAN_SHA256}  ${archive}" | sha256sum -c -

tar -xzf "$archive" -C "$tmpdir"
if [[ -x "${tmpdir}/elan-init" ]]; then
  "${tmpdir}/elan-init" -y --default-toolchain none
elif [[ -x "${tmpdir}/elan" ]]; then
  mkdir -p "${HOME}/.elan/bin"
  cp "${tmpdir}/elan" "${HOME}/.elan/bin/elan"
  "${HOME}/.elan/bin/elan" self install -y --default-toolchain none
else
  echo "elan release archive layout unrecognized" >&2
  ls -la "$tmpdir" >&2
  exit 1
fi

if [[ -n "${GITHUB_PATH:-}" ]]; then
  echo "${HOME}/.elan/bin" >> "${GITHUB_PATH}"
fi
export PATH="${HOME}/.elan/bin:${PATH}"
command -v elan
elan --version
