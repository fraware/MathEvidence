# Review packet slot — Hypothesis interface C (OPEN)

**Status:** OPEN for human expert review. Do not invent signatures.  
**Board:** [`../p2-blocker-status.md`](../p2-blocker-status.md)

## How to sign

1. Copy this file to a new name **without** `-unsigned`
   (e.g. `HYPOTHESIS-IFACE-C-weaker-cex-SIGNED.md`).
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
| Interface id | `iface_c_weaker_falsified` |
| Statement (Lean gloss) | Weaker finite claim `∀ x ≤ 3, x = 0` rejected with certified CEX |
| Informal gloss | Necessity language only after certified failing weaker variant |
| Evidence / lattice | `verifyCounterexample` + `recordCertifiedCounterexample` / Agent weakerVariantRequest |
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

OPEN — confirms certified CEX path is the right necessity interface for this domain.
