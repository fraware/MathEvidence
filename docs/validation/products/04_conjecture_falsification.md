# Product 04 — Conjecture / Falsification — acceptance report

**Workstream:** R5  
**Spec:** [docs/products/04_CONJECTURE_FALSIFICATION.md](../../products/04_CONJECTURE_FALSIFICATION.md)  
**Date:** 2026-07-16

## Acceptance criteria

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | ≥1 domain family with verified executable encoding | **PASS** | `FinitePredicateFamily` `finite.nat_le_3` → Counterexample claims |
| 2 | Certified counterexamples refute false candidates | **PASS** | `certifyRefutation` only after `checkBool`; Tests `falsify_eq0` |
| 3 | Clear separation of bounded evidence vs proof | **PASS** | States + `isTheoremGrade`; `bounded_verified` notes |
| 4 | Expert review finds useful precision rate | **OPEN (human)** | Engineering precision accounting in Lean `campaign_precision_accounting` / Agent `precisionAccounting`; expert sign-off not invented |
| 5 | Surviving conjecture → reusable theorem **or** meaningful open problem | **PASS** | Theorem: `eq_refl_on_nat3`; Open problem artifact: `artifacts/conjecture-open-problem-nat-le-family.md` |

## Campaign demo

`MathEvidence.Conjecture.Tests.campaignDemo`: proposed=3, falsified=1, formallyProved=1, openProblems=1.

## Overall engineering gate

**PASS** for R5 engineering scope. Criterion 4 expert precision judgment remains OPEN.
