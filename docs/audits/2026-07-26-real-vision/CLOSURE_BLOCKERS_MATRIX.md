# Closure blockers — status matrix (2026-07-26, triple-check refresh)

| Blocker | Status | Evidence |
| --- | --- | --- |
| 1. Local Lake/Mathlib v4.14.0 | **Partial** | Pin `mathlib4@4bbdccd9…`. Core + RationalEquality Bridge/Soundness oleans attested. Ideal Polynomial `Syntax` olean green after Mathlib `Vector` import; Normalize/Interpret/Soundness still compiling. See `MATHLIB_RESOLUTION.md`. |
| 2. Committed `uv.lock` | **Partial** | `uv.lock` present in working tree; workflows require `uv sync --frozen`. **Not git-committed** (needs user commit). |
| 3. Branch protection on `main` | **Fixed** | Required PR + checks + code-owner review. `docs/validation/ci/2026-07-26_closure_ci_truth.json`. |
| 4. Checksum-pinned elan | **Fixed** | `scripts/ci/install-elan-pinned.sh` (elan `v4.2.3`). |
| 5. Signed 0.x release | **Partial** | Provenance/SBOM/cosign hooks in `release.yml`. **No release published.** |
| 6. Real GitHub teams | **Blocked(org)** | Token lacks `admin:org`. CODEOWNERS still `@fraware` stub. |
| 7. `mathevidence-kernel-replay` | **Partial→improved** | Lake target + Linux CI `--self-test` + `--self-test-analytic` (authoritative). Windows: **required** path `scripts/link_exe_via_rsp.py`; `smoke_exe` degrades with `replay_dependency_missing`. See `KERNEL_REPLAY_PLATFORM.md`. |

## Explicitly not claimed

- Stable promotion (still frozen).
- Human adoption / federation interviews.
- Published GitHub Release.
- Full Mathlib-heavy `MathEvidenceCheckers` green as a single attested olean set.
- Rational interactive tactic MET without olean proof that Examples close via Bridge (code path wired; compile attestation pending).
