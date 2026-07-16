# Sample review packet (unsigned)

Illustrative packet for the classic rational identity used in Milestone 1
fixtures. **Not an approval. Not a signature.**

**G1-B conversion (human only):**

1. Copy this file to a new path such as
   `docs/validation/review-packets/2026-rational-equality-<REVIEWER>.md`
   — the new filename must **not** contain `-unsigned`.
2. Fill every **Scores** cell (replace `_` / “Awaiting reviewer”).
3. Fill **Reviewer** Name, Affiliation, Consent, Signature date.
4. Meet pass bar: no zeros; total ≥ 9 / 12; semantic fidelity ≥ 1; claim
   strength ≥ 1 (see [`../expert-review-rubric.md`](../expert-review-rubric.md)).
5. Uncheck `pending`; check `revise` or `approve…`.
6. Answer the three required reviewer notes.

Until those steps happen, this SAMPLE must stay unsigned. Do **not** invent a
reviewer.

Blank template without SAMPLE metadata:
[`TEMPLATE.md`](TEMPLATE.md).

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

**Pass bar:** no zeros; total ≥ 9 / 12; semantic fidelity ≥ 1; claim strength ≥ 1.

## Reviewer

| Field | Value |
| --- | --- |
| Name | _(open — do not invent)_ |
| Affiliation | |
| Area (domain / trust / other) | domain |
| Consent to list publicly | |
| Signature date | _(blank until real signature)_ |

## Decision

- [x] pending
- [ ] revise
- [ ] approve for library consideration (not capability-stable by itself)

## Required reviewer notes (from rubric)

1. What would you change before merging into a library?
2. Any pole / branch / totality concern the certificate hides?
3. Is minimality of conditions claimed? (Must be **no** unless proved.)

## Comments

Prepared as a worked example of packet shape for expert outreach. Fill scores
and signature only after a real domain review.
