# Experimental 0.x signed prerelease (ME-RV-074)

This documents the **pipeline** for an experimental 0.x prerelease. It does
**not** claim a published release occurred. Tier B prepares this runbook only;
**do not** push tags or run `gh release create` until an explicit maintainer
"publish" ask.

## Preconditions

- Closure commit on `main` (or the intended release SHA) with committed `uv.lock`.
- Branch protection on `main` enabled; required checks green for that SHA
  (see [`POST_PUSH_CI_ATTESTATION_TEMPLATE.json`](POST_PUSH_CI_ATTESTATION_TEMPLATE.json)).
- Registry capabilities remain **non-stable** (experimental / incubation only).

## What CI produces (`.github/workflows/release.yml`)

On `workflow_dispatch` or `v*` tag push:

1. Frozen `uv sync --frozen` (requires committed `uv.lock`).
2. Schema/registry/import/axiom audits + environment audits.
3. `lake build mathevidence-verify-bundle mathevidence-kernel-replay mathevidence-import-graph mathevidence-axiom-report`.
4. Offline replay + exe smoke + ideal-membership smoke.
5. Provenance manifest (`scripts/generate_release_provenance.py`).
6. SBOM (`scripts/generate_sbom.py`).
7. SHA-256 digests (`dist/provenance/artifact-digests.sha256`).
8. Cosign keyless `sign-blob` attempt for digests (+ SBOM when present). Soft-fail
   is recorded under `dist/signed/STATUS.txt` if identity signing is unavailable.
9. Artifact upload: `release-provenance`.

Auto-publish is intentionally **not** wired. `PUBLISH_EXPERIMENTAL_PRERELEASE`
only warns; it never creates a GitHub Release.

## Manual maintainer steps (required — human gate)

1. Ensure `main` required checks are green for the release commit.
2. Tag only an experimental commit (push tag only after explicit publish approval):
   ```bash
   git tag v0.1.0-experimental.<sha7>
   git push origin v0.1.0-experimental.<sha7>
   ```
   or run `workflow_dispatch` on `release.yml` for the same SHA.
3. Download the `release-provenance` artifact from the workflow run:
   ```bash
   gh run download <run_id> --name release-provenance --dir dist
   ```
4. Verify provenance completeness:
   - `dist/provenance/provenance-manifest.json` has `leanToolchain`, `gitCommit`
     (not `"workspace"`), and lake package pins.
   - `dist/provenance/artifact-digests.sha256` present and non-empty.
   - `dist/sbom/` present (`sbom.json` or equivalent).
   - `dist/signed/STATUS.txt` is `cosign_attempted` (or document soft-fail).
5. Verify cosign bundle (keyless) **or** re-sign with the org Ed25519 release key
   when that key is provisioned:
   ```bash
   cosign verify-blob --bundle dist/signed/artifact-digests.cosign.bundle \
     dist/provenance/artifact-digests.sha256
   ```
6. Create a GitHub **prerelease** only after human review:
   ```bash
   gh release create <tag> --prerelease --title "0.x experimental" \
     dist/provenance/* dist/sbom/* dist/signed/*
   ```
7. Do **not** set registry capabilities to `stable`. Experimental only.

## Verification checklist (fill after publish ask)

| Step | Command / evidence | Pass? |
| --- | --- | --- |
| Required checks green | Actions run IDs in CI truth JSON | |
| Tag points at intended SHA | `git rev-parse <tag>` | |
| Provenance manifest | `gitCommit` + toolchain pins | |
| Digests file | `artifact-digests.sha256` | |
| SBOM | `dist/sbom/` | |
| Cosign verify | `cosign verify-blob ...` | |
| Prerelease (not release) | `gh release view <tag> --json isPrerelease` | |
| Registry still non-stable | capability rows | |

## Remaining gaps (honest)

- Org Ed25519 / hardware release key not yet provisioned as a long-term
  signing identity (cosign keyless is the current CI hook).
- Auto-publish is intentionally **not** wired.
- No published 0.x release is claimed by this documentation.
- Tag push and `gh release create` are **out of scope** for Tier B preparation.
