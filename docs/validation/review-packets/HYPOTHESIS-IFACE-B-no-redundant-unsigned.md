# Review packet slot — Hypothesis interface B (OPEN)

**Status:** OPEN for human expert review. Do not invent signatures.

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
