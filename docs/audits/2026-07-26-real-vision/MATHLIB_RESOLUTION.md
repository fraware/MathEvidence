# Lake / Mathlib local resolution (2026-07-26 closure)

## Root cause (previous "revision not found 'v4.14.0'")

`.lake/packages/mathlib` was a **corrupted git checkout** whose `origin`
pointed at `fraware/MathEvidence` (this repository), not Mathlib. Lake then
looked for tag `v4.14.0` in the wrong repo and reported "revision not found".

The upstream tag **does exist**:

```text
leanprover-community/mathlib4 tag v4.14.0
  -> 4bbdccd9c5f862bf90ff12f0a9e2c8be032b9a84
  lean-toolchain: leanprover/lean4:v4.14.0
```

## Fix applied

1. Deleted the corrupted `.lake/packages/mathlib`.
2. Pinned Mathlib in `lakefile.toml` to the explicit git URL + commit SHA
   (still matching Lean `v4.14.0`).
3. Wrote `lake-manifest.json` with Mathlib + transitive deps from Mathlib's
   own `v4.14.0` manifest.
4. Shallow/full cloned packages under `.lake/packages/`.
5. Fixed Lean name-resolution bugs in `EnvironmentLock` / `ReplayTarget` /
   `TheoremIdentity` (`digest` was recursively resolving to itself) and a
   `check_accept_iff` proof in RationalEquality.

## Verified locally

```text
lake build MathEvidenceCore
# Build completed successfully.

lake build mathevidence-verify-bundle mathevidence-import-graph mathevidence-axiom-report
# Build completed successfully.
```

## Residual

- Ideal `IR/Polynomial/Soundness.lean` still fails compile (missing eval lemmas /
  Mathlib Ideal API mismatches); Interpret is `noncomputable` and builds.
- Full LA/CEX/Analytic Checkers oleans not universally attested.
- `mathevidence-kernel-replay` is a Lake target; Linux CI runs `--self-test`.
  Windows may fail `leanc` link (error 87) while the fixture `.olean` succeeds —
  see `KERNEL_REPLAY_PLATFORM.md`.
- Stable promotion remains frozen.
- `uv.lock` must still be git-committed by a human for ME-RV-070.