# Product 03 — Hypothesis Synthesis — acceptance report

**Workstream:** R5  
**Spec:** [docs/products/03_HYPOTHESIS_SYNTHESIS.md](../../products/03_HYPOTHESIS_SYNTHESIS.md)  
**Date:** 2026-07-16

## Acceptance criteria

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Repaired statements are proved in Lean | **PASS** | `isSufficient` / `proveSufficient` = `RationalEquality.checkBool`; `sufficient_implies_proposition`; Tests `sufficient_minimal`, `e2e_propose_lattice_cex` |
| 2 | Removed assumptions have redundancy proof or certified failing variant | **PASS** | `deleteHypothesis` redundancy via checkBool; `buildConditionLatticeWithCex` + `verifyCounterexample` for weaker variants |
| 3 | Minimality language absent unless formally established | **PASS** | `claimsMinimal = false` by default; Agent schema + tests |
| 4 | Expert reviewers judge recommended interfaces appropriate | **OPEN (human)** | Review packet slots (unsigned): `HYPOTHESIS-IFACE-A/B/C-*-unsigned.md` (≥3 interfaces). Do not invent signatures. |
| 5 | Improves autoformalization semantic accuracy on held-out examples | **PARTIAL** | Engineering path + RW12 obligation; measured held-out uplift vs autoformalization baseline still deferred |

## Agent Lean-authoritative ops

| Op | Authority |
| --- | --- |
| `prove_sufficient` | `authorityStatus=lean_checker_mirror` (RationalEquality.checkBool mirror) |
| `delete_hypothesis` | same |
| `verify_counterexample` | Counterexample.checkBool mirror |
| `build_condition_lattice` | sufficiency/deletion/CEX via mirrors; optional `weakerVariantRequest` |

Heuristics may **propose** only; they do not set acceptance status.

## Overall engineering gate

**PASS** for R5 engineering scope. Human expert review (criterion 4) remains OPEN.
