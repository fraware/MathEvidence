# Review packet slot — Hypothesis interface A (OPEN)

**Status:** OPEN for human expert review. Do not invent signatures.

Copy scores/decision from [TEMPLATE.md](TEMPLATE.md) when a real reviewer signs.
Rubric: [expert-review-rubric.md](../expert-review-rubric.md).

## Metadata

| Field | Value |
| --- | --- |
| Date | pending |
| Product | 03 Hypothesis Synthesis |
| Interface id | `recommended_v0` / condition set `{c0}` where `c0 : x - 1 ≠ 0` |
| Statement (Lean gloss) | `(x^2 - 1)/(x - 1) = x + 1` under `x - 1 ≠ 0` |
| Informal gloss | Cancel difference of squares with explicit pole exclusion |
| Evidence / lattice | Lean `MathEvidence.Hypothesis.Tests.e2e_propose_lattice_cex`; Agent lattice via `build_condition_lattice` |
| Assurance mode | kernel_replay / lean_checker_mirror (Agent) |
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
- [ ] approve for library consideration (not capability-stable by itself)

## Comments

Human review required before upstreaming. Minimality is not claimed by the lattice.
