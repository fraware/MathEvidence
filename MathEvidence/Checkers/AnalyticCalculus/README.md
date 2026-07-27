# AnalyticCalculus checker (ME-RV-050..054)

Experimental Mathlib analytic vertical. Checker acceptance plus explicit domain
hypotheses yields `HasDerivAt`, `HasDerivWithinAt`, or
`CandidateSolvesFirstOrderODE`. Completeness / uniqueness / maximal interval
claims are rejected.

## Modules

| File | Role |
| --- | --- |
| `Spec.lean` | Claim / request / ODE proposition |
| `Certificate.lean` | Inductive `DerivProof`, deriv / ODE certificates |
| `Check.lean` | `reconstructDeriv`, `checkDeriv`, `checkODE` |
| `Soundness.lean` | `checkDeriv_sound`, `checkODE_sound` |
| `Tests.lean` | Native-decide shape tests |
| `OfflineFixtures.lean` | Backend-free replay fixtures |
| `Wire.lean` | Adapter tag helpers |
| `Basic.lean` | Barrel import |

IR interpretation: `MathEvidence.IR.AnalyticExpr.{Syntax,Domain,Interpret}`.

Restricted Meta reifier: `MathEvidence.Tactic.ReifyAnalytic`.

Python proposal mirror: `adapters/common/analytic_calculus.py` (never theorem authority).

## Required theorem shapes

```lean
theorem checkDeriv_sound
    (hcheck : checkDeriv cert = true)
    (hdom : SatisfiesObligations cert.obligations x) :
    HasDerivAt cert.source.interpret (cert.derivative.interpret x) x

theorem checkODE_sound ... :
    CandidateSolvesFirstOrderODE solution.interpret rhs.interpret domain ics
```

Domain obligations are inductive (`nonzero` / `positive` / `member`). Caller
Booleans are never trusted as domain evidence.
