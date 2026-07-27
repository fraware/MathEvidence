# Wave 5 Lean build status (ME-RV-050..054)

Date: 2026-07-26

## Intent

Wave 5 delivers the analytic calculus vertical:

- `Expr.interpret : Expr → ℝ → ℝ` one-variable semantics
- Inductive `DomainObligation` (no caller-trusted domain Booleans)
- Inductive `DerivProof` certificate + `checkDeriv` reconstruction
- `checkDeriv_sound → HasDerivAt` / `checkDerivWithin_sound → HasDerivWithinAt`
- ODE candidate with residual/IC as propositions (`CandidateSolvesFirstOrderODE`)
- Restricted Meta reifier + SymPy proposal adapter + offline fixtures

## Local Lake / Mathlib

**Resolution fixed** (see [`MATHLIB_RESOLUTION.md`](MATHLIB_RESOLUTION.md)).
Core + verify-bundle exes build; analytic/Mathlib-heavy targets may still need
a long first Mathlib compile and are not claimed green here.

Correct Lean sources are committed under:

- `MathEvidence/IR/AnalyticExpr/{Syntax,Domain,Interpret,DerivativeRules}.lean`
- `MathEvidence/Checkers/AnalyticCalculus/{Spec,Certificate,Check,Soundness,Tests,OfflineFixtures,Wire,Basic}.lean`
- `MathEvidence/Tactic/ReifyAnalytic.lean`
- `MathEvidence/Encoding/Analytic.lean`

When Mathlib resolves:

```text
lake build MathEvidenceCheckers
lake env lean MathEvidence/Checkers/AnalyticCalculus/Soundness.lean
```

## Verification without Lean

```text
python -m pytest adapters/common/test_analytic_calculus.py -q
```

Python mirror checks tree shape only; it is not theorem authority.

## GitHub issues

See `docs/audits/2026-07-26-real-vision/issues/WAVE5.md`.

## GitHub issues

- https://github.com/fraware/MathEvidence/issues/29 — ME-RV-050
- https://github.com/fraware/MathEvidence/issues/30 — ME-RV-051
- https://github.com/fraware/MathEvidence/issues/31 — ME-RV-052
- https://github.com/fraware/MathEvidence/issues/32 — ME-RV-053
- https://github.com/fraware/MathEvidence/issues/33 — ME-RV-054
