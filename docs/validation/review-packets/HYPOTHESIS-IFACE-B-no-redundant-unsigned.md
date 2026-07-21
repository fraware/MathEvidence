# Review packet slot — Hypothesis interface B (OPEN)

**Status:** OPEN for human expert review. Do not invent signatures.  
**Status tracking:** [`../remaining-spec-matrix.md`](../remaining-spec-matrix.md) · [`../../STATUS.md`](../../STATUS.md)

## How to sign

1. Copy this file to a new name **without** `-unsigned`
   (e.g. `HYPOTHESIS-IFACE-B-no-redundant-SIGNED.md`).
2. Score every rubric criterion 0–2 using
   [`../expert-review-rubric.md`](../expert-review-rubric.md).
3. Fill Reviewer Name / Affiliation / Area / Consent / Signature date.
4. Clear `pending`; check `revise` or `approve for library consideration`.
5. Pass bar: no zeros; total ≥ 9/12; semantic fidelity ≥ 1; claim strength ≥ 1.
6. Signed packet ≠ capability `stable` promotion.

## Metadata

| Field | Value |
| --- | --- |
| Date | pending |
| Product | 03 Hypothesis Synthesis |
| Interface id | `iface_b_redundant_stripped` |
| Statement (Lean gloss) | Same identity as A, after deleting unused assumption `y` |
| Informal gloss | Recommended interface must not retain irrelevant hypotheses |
| Evidence / lattice | Deletion marks `y_unused` redundant via Lean `deleteHypothesis` / checkBool |
| Assurance mode | kernel_replay |
| Rubric version | docs/validation/expert-review-rubric.md |
| Signature date | |

## Scores

| Criterion | Score (0–2) | Notes |
| --- | --- | --- |
| Semantic fidelity | | |
| Side conditions | | |
| Claim strength | | |
| Checker fit | | |
| Replay | | |
| Library interface | | |
| **Total** | / 12 | |

## Reviewer

| Field | Value |
| --- | --- |
| Name | |
| Affiliation | |
| Area | domain / Semantic IR |
| Consent to list publicly | |

## Decision

- [x] pending
- [ ] revise
- [ ] approve for library consideration

## Comments

OPEN — expert judges whether the recommended interface is mathematically natural.
