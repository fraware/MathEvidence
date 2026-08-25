# SPEC-00 delta — handoff 2026-08-25 vs live workspace

Handoff pin: `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b` (PR #53,
`fix/exact-certification-binding`, assessed 2026-08-25).

This file records whether implementation began from that pin, what changed in
CI, and the reproduced Lean exact-replay diagnostic. It does not rewrite dated
audit evidence.

## Workspace vs pin

| Item | Value |
| --- | --- |
| Working branch (Phase 0 start) | `phase0/exact-certification-baseline` (from `origin/fix/exact-certification-binding`) |
| Current working branch | `phase4/exact-certification-handoff` (Phases 0–4 + E2E; do **not** rebase onto `main`) |
| HEAD at Phase 0 start / pin | `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b` |
| Pin | `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b` |
| SHA delta vs pin | none — HEAD **is** the pin; Phases 0–4 work is largely **uncommitted** on top |
| Current `main` | `6d87c4d` (fixture substitution still present; **not** used) |

The PR conversation mentioned synchronize SHA `7665010699728319eae48329550e63e31923c9cb`.
That commit is an **ancestor** of the pin (`Build declaration identity authority in Lean CI`),
not a later head. `git ls-remote` for `refs/heads/fix/exact-certification-binding`
and `refs/pull/53/head` both resolve to `30522d70`.

## PR #53 vs current main

PR #53 already contains (do not rebuild): exact ideal-membership Lean inlining,
`mathevidence-declaration-identity`, generic `assurance_mode_unavailable` for
rational / LA / CEX / analytic, stricter `verify_certification_record`, and
substitution forensic tests. Current `main` still uses fixture substitution in
`adapters/common/kernel_replay.py` and `scripts/generate_replay_module.py`.

## Local toolchain (reproduction host)

| Item | Value |
| --- | --- |
| OS | Windows NT 10.0.26200 (PowerShell) |
| `lean --version` | Lean 4.14.0, `x86_64-w64-windows-gnu`, commit `410fab728470` |
| Lake | 5.0.0-410fab7 (Lean 4.14.0) |
| elan | 4.2.3 |
| `lean-toolchain` | `leanprover/lean4:v4.14.0` |
| lake-manifest mathlib SHA | `4bbdccd9c5f862bf90ff12f0a9e2c8be032b9a84` |

CI image for the failing jobs is GitHub `ubuntu-latest` with the same pinned
elan installer (`scripts/ci/install-elan-pinned.sh`) and the same toolchain
file / mathlib revision.

## CI delta at the pin (GitHub Actions on `fix/exact-certification-binding`)

Observed on run family starting 2026-08-25T06:56:07Z (example lean run
[32819174319](https://github.com/fraware/MathEvidence/actions/runs/32819174319)):

| Workflow | Pin / PR head status | Interpretation |
| --- | --- | --- |
| `security` | PASS | Must stay green |
| `adapter-conformance` | PASS | Must stay green |
| `supply-chain` | PASS | Must stay green |
| `adversarial` | PASS | Must stay green |
| `lean` | FAIL at `lake build` of verification + declaration-identity + audit drivers | Shared ExprSerialize parse error |
| `offline-replay` | FAIL at Lean leg (`lake build` OfflineFixtures / Tactic.Examples) | Same ExprSerialize parse error; Python leg passed |
| `benchmarks` | `benchmarks` job PASS; `ideal-release-grade` FAIL at `lake build MathEvidenceCheckers mathevidence-declaration-identity` | Same ExprSerialize required-build failure |

## Reproduced `lake build` diagnostic

Do not treat the following as speculation. It was reproduced locally on the pin
and matches the GitHub Actions logs.

Local:

```text
lake build MathEvidence.Core.ExprSerialize
✖ [9/9] Building MathEvidence.Core.ExprSerialize
error: .\.\.\.\MathEvidence\Core\ExprSerialize.lean:49:8: unexpected token 'prefix'; expected '=>'
error: .\.\.\.\MathEvidence\Core\ExprSerialize.lean:49:15: unexpected identifier; expected ':'
error: .\.\.\.\MathEvidence\Core\ExprSerialize.lean:51:15: unexpected identifier; expected ':'
error: Lean exited with code 1
Some required builds logged failures:
- MathEvidence.Core.ExprSerialize
error: build failed
```

CI (`lean` job 32819174319, step "Lake build (verification + declaration identity + audit drivers)"):

```text
error: ././././MathEvidence/Core/ExprSerialize.lean:49:8: unexpected token 'prefix'; expected '=>'
error: ././././MathEvidence/Core/ExprSerialize.lean:49:15: unexpected identifier; expected ':'
error: ././././MathEvidence/Core/ExprSerialize.lean:51:15: unexpected identifier; expected ':'
error: Lean exited with code 1
Some required builds logged failures:
- MathEvidence.Core.ExprSerialize
error: build failed
```

Root cause: Lean 4 reserved word `prefix` (notation commands) used as a pattern
binder in `serializeName` (`| .str prefix value =>` / `| .num prefix value =>`).
`mathevidence-declaration-identity` imports this module, so every exact-replay
CI target that requires declaration identity fails the same way.

After that parse error was fixed, `lake build MathEvidenceCheckers` (the
`ideal-release-grade` prerequisite) still failed on three imported test modules.
Those errors were also present in the pin CI log; they are independent of
ExprSerialize:

- `WireTests.lean`: `native_decide` could not synthesize `Decidable` for
  `Except String RequestDigest` equality. Wrapped the vectors in a `Bool`
  matcher (`digestMatches`).
- `Encoding/Examples.lean`: theorems cited missing `InterpretsAt` /
  `interprets_sparseC1_add_X` identifiers. Restated against the existing
  `MvPolynomial` eval bridges (`eval_add_bridge` / `eval_mul_bridge` /
  `SparsePoly.eval_X`).
- `AnalyticCalculus/Tests.lean`: unnamed `example` + `native_decide` hit a
  Lean 4.14.0 `ofReduceBool` typing bug on `quotientCert`; `HasDerivAt.pow`
  did not match `(fun y => y ^ 2)` / `2 * x`. Named the theorems, used `#eval`
  for the quotient positive vector, and `simpa` for `hasDerivAt_sq`.

Forbidden non-fixes were not used: generated modules were not skipped, theorems
were not weakened, sorry/axiom/import/declaration audits were not disabled, and
exact replay was not converted back to fixture replay.

## Local verification (Phase 0)

| Command | Result |
| --- | --- |
| `python scripts/validate_schemas.py` | ok (36 files, including maturity-inventory) |
| `python scripts/validate_registry.py` | ok (9 capabilities; maturity inventory agrees with STATUS.md) |
| `python scripts/validate_maturity_inventory.py` | ok |
| `python -m pytest tests/forensic/test_maturity_inventory.py -q` | 10 passed |
| `lake build MathEvidence.Core.ExprSerialize MathEvidence.Core.ExprSerializeTests mathevidence-declaration-identity` | success |
| `lake build mathevidence-verify-bundle mathevidence-kernel-replay mathevidence-declaration-identity mathevidence-import-graph mathevidence-axiom-report` | success (lean.yml targets) |
| `lake build MathEvidence.Checkers.RationalEquality.OfflineFixtures MathEvidence.Tactic.Examples` | success (offline-replay Lean leg) |
| `lake build MathEvidenceCheckers mathevidence-declaration-identity` | success (ideal-release-grade prerequisite) |

## Post Phase-4 Lake E2E repair (release ladder)

Additional root causes found and fixed on the same pin (uncommitted program work):

1. **Windows `Lean.olean` shadow:** `kernel_replay._compile_and_inspect` wrote oleans under
   `.lake/build/lib/lean/...`. On case-insensitive Windows that directory shadows the
   toolchain `Lean` module in `LEAN_PATH`. Fixed to `.lake/build/lib/<Module>/...`.
2. **DeclarationIdentity argv:** `lake exe mathevidence-declaration-identity -- --module ...`
   forwards a bare `--` into the exe (exit 2). Fixed to pass flags without `--`.
3. **Ideal / rational (and sibling) generators:** theorem type must be
   `Claim.proposition req.claim ...` via named `def`s (OfflineFixtures pattern).
   Literal claim copies + accidental `{{` brace doubling broke elaboration / introduced
   `sorryAx`.

After those fixes, local ladders green for **ideal**, **rational equality**,
**linear algebra** (inverse/system/kernel/det), **finite counterexample**
(`refuted`), **formal rational calculus** (derivative/antiderivative/recurrence/ODE
with `soundResult`), and **analytic calculus** (Deriv / DerivWithin / Antideriv /
ODE empty-obligation single-IC) → `crEligible=true` in registry + maturity
inventory. Federated logic remains `crEligible=false`. Offline exact driver
defaults to `theorem_pending`; with `MATHEVIDENCE_OFFLINE_LEAN=1` /
`require_lean=True` and Lake available it can reach `theorem_proved` after
declaration-identity inspect (still not a CR mint). Online `kernel_replay`
remains the primary promotion path.

## Final polish pass (post Phase-4)

Additional fail-closed / honesty hardening on the same pin (still uncommitted):

- Receipt polarity hard-equals claim mapping; registry `allowedOutcomes` enforced
  for `proved`/`refuted`
- Inventory validator syncs `cr_eligible` / exact binding to live capability JSON
- Analytic exact parse aligned with sibling plugins (required fields, kind match,
  pow bounds); formal univariate `dependentVar` defaults to independent
- Offline Lean inspect uses real `environment_lock_digest` + type/proof identity
  checks; docs distinguish offline `theorem_proved` from CR promotion
- Kernel profile no longer remaps unknown capabilities to rational equality
- STATUS / HANDOFF / ADR 0005 / this delta aligned on CR v0.4 and eligibility

## Phase 0 code delta relative to the pin

Phase 0 adds the SPEC-00 inventory/ADR/status rebaseline and the Lean compile
fixes required for SPEC-01. Generated replay remains argv-only `lake env lean`
(SPEC-11 slice unchanged). Later phases + the E2E repair above extend exact
generators and enable CR only where ladders are green.
