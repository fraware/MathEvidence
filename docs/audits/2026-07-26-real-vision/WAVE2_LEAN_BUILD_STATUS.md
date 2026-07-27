# Wave 2 Lean build status (ME-RV-020..024)

Date: 2026-07-26 (updated closure pass)

## Intent

Wave 2 adds theorem identity / environment lock / replay target modules,
`Request.ofClaim : Except`, Lean resource policy in `checkBool`, `replaySound`,
tactic certification digests, `mathevidence-verify-bundle` error taxonomy,
and the Python `kernel_replay` driver (`adapters/common/kernel_replay.py` +
`scripts/generate_replay_module.py`).

## Local Lake / Mathlib

**Resolved.** See
[`MATHLIB_RESOLUTION.md`](MATHLIB_RESOLUTION.md).

Previous failure (`revision not found 'v4.14.0'`) was a corrupted
`.lake/packages/mathlib` pointing at this repository. Mathlib tag `v4.14.0`
exists upstream at `4bbdccd9c5f862bf90ff12f0a9e2c8be032b9a84`.

Verified:

```text
lake build MathEvidenceCore
lake build mathevidence-verify-bundle mathevidence-kernel-replay mathevidence-import-graph mathevidence-axiom-report
```

`mathevidence-kernel-replay` is now a Lake target (`MathEvidence/Exe/KernelReplay.lean`)
carrying fixture `replaySound`. First local builds may still grind Mathlib.
Python `kernel_replay` refuses `soundness_verified` without Lean success.

## Verification without Lean

```text
python -m pytest tests/forensic/test_theorem_identity_digests.py \
  tests/forensic/test_wave2_kernel_replay.py \
  studio/test_epistemic_receipt.py \
  adapters/common/test_epistemic_studio.py -q
```

## GitHub issues

- https://github.com/fraware/MathEvidence/issues/10 — ME-RV-020
- https://github.com/fraware/MathEvidence/issues/11 — ME-RV-021
- https://github.com/fraware/MathEvidence/issues/12 — ME-RV-022
- https://github.com/fraware/MathEvidence/issues/13 — ME-RV-023
- https://github.com/fraware/MathEvidence/issues/14 — ME-RV-024
