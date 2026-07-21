# Product 03 — Hypothesis Synthesis — acceptance report

**Workstream:** R5  
**Spec:** [docs/products/03_HYPOTHESIS_SYNTHESIS.md](../../products/03_HYPOTHESIS_SYNTHESIS.md)  
**Date:** 2026-07-16

## Acceptance criteria

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Repaired statements are proved in Lean | **PASS** | `isSufficient` / `proveSufficient` = `RationalEquality.checkBool`; three-way `proved`/`failed`/`unknown` with typed `SufficiencyEvidence` (theoremDecl/checkerDecl/receiptId/axiomReportId); `sufficient_implies_proposition`; Tests `sufficient_minimal`, `prove_sufficient_proved_shape`, `denom_coverage_alone_not_sufficient`, `e2e_propose_lattice_cex` |
| 2 | Removed assumptions have redundancy proof or certified failing variant | **PASS** | `deleteHypothesis` redundancy via checkBool; `buildConditionLatticeWithCex` + `verifyCounterexample` for weaker variants |
| 3 | Minimality language absent unless formally established | **PASS** | `claimsMinimal = false` by default; Agent schema + tests |
| 4 | Expert reviewers judge recommended interfaces appropriate | **OPEN (human)** | Unsigned packets + signing steps: `HYPOTHESIS-IFACE-A/B/C-*-unsigned.md`. Board: [`p2-blocker-status.md`](../p2-blocker-status.md). Do not invent signatures. |
| 5 | Improves autoformalization semantic accuracy on held-out examples | **PARTIAL** | Engineering path + RW12 obligation; measured held-out uplift vs autoformalization baseline still deferred |

## Agent Lean-authoritative ops

| Op | Authority |
| --- | --- |
| `prove_sufficient` | `outcome ∈ {proved,failed,unknown}`; `authorityStatus=lean_checker_mirror`; typed `evidence` cites Lean theorem/checker/receipt/axiom-report; **refuses** sufficiency from denom-coverage alone |
| `delete_hypothesis` | same mirror |
| `verify_counterexample` | Counterexample.checkBool mirror |
| `build_condition_lattice` | sufficiency/deletion/CEX via mirrors; optional `weakerVariantRequest`; optional `sufficiencyPreview` |

Heuristics may **propose** only; they do not set acceptance status. Denominator coverage without poly identity is never marked sufficient.

## Overall engineering gate

**PASS** for R5 engineering scope. Human expert review (criterion 4) remains OPEN.
