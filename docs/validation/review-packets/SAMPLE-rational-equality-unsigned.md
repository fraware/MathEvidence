# Sample review packet (unsigned)

Illustrative packet for the classic rational identity used in Milestone 1
fixtures. **Not an approval.** Reviewer fields intentionally blank.

## Metadata

| Field | Value |
| --- | --- |
| Date | 2026-07-16 |
| Capability | algebra.rational_equality |
| Statement (Lean) | `(x : ℚ) → (x - 1 ≠ 0) → (x^2 - 1)/(x - 1) = x + 1` |
| Informal gloss | Cancel `x-1` on the difference of squares over ℚ away from the pole |
| Evidence bundle | evidence/examples/rational_equality_basic |
| Request digest | sha256:354adca7a9f55584f929033ae67b739c3543ca3defcc47e7ee862a3aaca77423 |
| Assurance mode | kernel_replay |
| Rubric version | docs/validation/expert-review-rubric.md |

## Scores

| Criterion | Score (0–2) | Notes |
| --- | --- | --- |
| Semantic fidelity | _ | Awaiting reviewer |
| Side conditions | _ | Denominator factor `x-1` expected |
| Claim strength | _ | Must not claim value at `x=1` |
| Checker fit | _ | RFC 0001 path |
| Replay | _ | CI offline replay |
| Library interface | _ | |
| **Total** | _ / 12 | |

## Reviewer

| Field | Value |
| --- | --- |
| Name | _(open — do not invent)_ |
| Affiliation | |
| Area (domain / trust / other) | domain |
| Consent to list publicly | |

## Decision

- [x] pending
- [ ] revise
- [ ] approve for library consideration (not capability-stable by itself)

## Comments

Prepared as a worked example of packet shape for expert outreach. Fill scores
only after a real domain review.
