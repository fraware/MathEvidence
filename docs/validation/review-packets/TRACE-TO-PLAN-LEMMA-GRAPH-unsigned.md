# Expert judgment — Trace-to-Plan lemma-graph coherence (OPEN)

**Status:** OPEN for human expert review. Do not invent signatures.  
**Product:** 05 Trace-to-Plan — acceptance criterion 5  
**Status tracking:** [`../remaining-spec-matrix.md`](../remaining-spec-matrix.md) · [`../../STATUS.md`](../../STATUS.md)

## How to sign

1. Copy this file to a new name **without** `-unsigned`
   (e.g. `TRACE-TO-PLAN-LEMMA-GRAPH-SIGNED.md` or
   `TRACE-TO-PLAN-LEMMA-GRAPH-<REVIEWER>.md`).
2. Inspect the multi-step demo plan and reconstructions.
3. Fill coherence judgment + Reviewer identity + Signature date.
4. Clear `pending`; check `revise` or `approve lemma graph as coherent`.
5. A signed judgment is **not** capability `stable` promotion.

## Materials for the reviewer

| Artifact | Path |
| --- | --- |
| Product report | [`../products/05_trace_to_plan.md`](../products/05_trace_to_plan.md) |
| Multi-step demo | `benchmarks/trace_to_plan/multistep_rational_demo.json` |
| Demo runner | `scripts/run_trace_to_plan_demo.py` (`just trace-to-plan-demo`) |
| Spec | `docs/products/05_TRACE_TO_PLAN.md` |

## Coherence checklist (human fills)

| Checkpoint | Observed | Pass? |
| --- | --- | --- |
| Step classifications are auditable (direct / reconstructible / hint) | OPEN | OPEN |
| Reconstructible steps do not invent Lean theorems | OPEN | OPEN |
| Search hints never advance theorem status | OPEN | OPEN |
| Lemma graph edges are mathematically natural for the demo | OPEN | OPEN |
| Plan improves comprehension vs final-answer-only (expert view) | OPEN | OPEN |

## Reviewer

| Field | Value |
| --- | --- |
| Name | |
| Affiliation | |
| Area | domain / Trace-to-Plan |
| Consent to list publicly | |
| Signature date | |

## Decision

- [x] pending
- [ ] revise
- [ ] approve lemma graph as coherent (not capability-stable by itself)

## Comments

Human review required. Do not invent a signed coherence judgment.
