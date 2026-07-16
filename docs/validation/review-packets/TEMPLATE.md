# Review packet template

**How to use (domain signing — G1-B):**

1. Copy this file to
   `docs/validation/review-packets/YYYY-MM-DD-<short-id>.md`
   (or convert
   [`SAMPLE-rational-equality-unsigned.md`](SAMPLE-rational-equality-unsigned.md)
   by saving under a new name **without** the `-unsigned` suffix).
2. Fill every Metadata field (SAMPLE already has worked values for the classic
   rational identity — prefer those for the v0.1 domain packet).
3. Score every rubric criterion 0–2 using
   [`../expert-review-rubric.md`](../expert-review-rubric.md).
4. Fill Reviewer identity (real name or consented anonymize).
5. Clear `pending` and check `revise` or `approve…` only after scoring.
6. A signed packet is **not** automatic capability `stable` promotion.

Leave Decision as `pending` until a real reviewer signs. Do **not** invent
reviewer identities or scores.

## Metadata

| Field | Value |
| --- | --- |
| Date | YYYY-MM-DD |
| Capability | algebra.rational_equality |
| Statement (Lean) | |
| Informal gloss | |
| Evidence bundle | evidence/... |
| Request digest | sha256:... |
| Assurance mode | kernel_replay |
| Rubric version | docs/validation/expert-review-rubric.md |

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

**Pass bar (must hold for “approve”):** no zeros; total ≥ 9 / 12; semantic
fidelity ≥ 1; claim strength ≥ 1.

## Reviewer

| Field | Value |
| --- | --- |
| Name | |
| Affiliation | |
| Area (domain / trust / other) | domain |
| Consent to list publicly | yes / no / anonymize |
| Signature date | YYYY-MM-DD |

By filling Name + Signature date and clearing `pending` below, the reviewer
attests they personally scored the statement against the rubric.

## Decision

- [ ] pending
- [ ] revise
- [ ] approve for library consideration (not capability-stable by itself)

## Required reviewer notes (from rubric)

1. What would you change before merging into a library?
2. Any pole / branch / totality concern the certificate hides?
3. Is minimality of conditions claimed? (Must be **no** unless proved.)

## Comments

_
