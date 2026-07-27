# Elan checksum pin (ME-RV-073)

## Policy

CI MUST NOT download `https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh`.

Use `scripts/ci/install-elan-pinned.sh`, which fetches a **release asset** and
verifies SHA-256 before install.

## Current pin

| Field | Value |
| --- | --- |
| Version | `v4.2.3` |
| Asset | `elan-x86_64-unknown-linux-gnu.tar.gz` |
| URL | https://github.com/leanprover/elan/releases/download/v4.2.3/elan-x86_64-unknown-linux-gnu.tar.gz |
| SHA-256 | `df0b2b3a439961ffcbb3985214365ffe40f49bc871df04dff268c7d8e21ca8b2` |
| Checksum source | Computed 2026-07-26 from the GitHub release asset bytes (`Get-FileHash -Algorithm SHA256` / `sha256sum`) |
| Release page | https://github.com/leanprover/elan/releases/tag/v4.2.3 |

Upstream does not currently publish a `SHA256SUMS` file on the release; the
checksum above is the project-recorded digest of the official asset. Recompute
and update this file + the install script when bumping elan.
