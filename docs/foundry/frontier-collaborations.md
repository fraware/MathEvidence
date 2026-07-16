# Frontier mathematics collaborations (Milestone 6 scaffolding)

Status: **engineering scaffolding and collaboration notes**. This document does
**not** claim that any frontier program has been materially accelerated.

See also: `docs/architecture/collaboration-cslib-lean-auto-smt.md`,
`docs/foundry/library-contribution-template.md`,
`docs/foundry/exit-gate-status.md`.

## Purpose

Record selected frontier formalization programs where MathEvidence-certified
computation could reduce computational bottlenecks, and define how contributions
are measured when human collaborations begin.

## Selection criteria

A frontier collaboration candidate SHOULD:

1. have recurring computational proof obligations (not one-off tactics);
2. benefit from offline-replayable evidence rather than opaque CAS notebooks;
3. accept explicit side conditions / claim-class discipline;
4. allow measured library contributions (PRs, lemmas, certificates) to be tracked.

## Candidate programs (notes only)

| Program / area | Computational bottleneck | MathEvidence posture | Status |
| --- | --- | --- | --- |
| Large Mathlib algebra / linear algebra refactors | Exact matrix witnesses, rational identities | Offer `algebra.linear_algebra` / `algebra.rational_equality` replay bundles | Outreach not started |
| Analytic / formal calculus libraries | Derivative / antiderivative / ODE candidates with domains | `analysis.symbolic_calculus` with candidate ≠ completeness | Outreach not started |
| Finite combinatorial falsification | Bounded counterexamples | `logic.finite_counterexample` typed witnesses | Outreach not started |
| SMT-backed developments | Reconstruction authority elsewhere | Federated `logic.smt` metadata only | Align with Lean-SMT maintainers |
| Gröbner / ideal membership stacks | Specialized checkers | Federated `algebra.groebner_membership` metadata | Align with external owners |

## Collaboration protocol

1. Open a GitHub issue labeled `frontier/<program>` with bottleneck inventory links.
2. Agree claim classes and which checker is authoritative.
3. Exchange offline evidence bundles before any live process adapter.
4. Log library contributions using `docs/foundry/library-contribution-template.md`.
5. Never feed Foundry episodes into theorem acceptance.

## Measured contribution fields (required when claiming progress)

- repository / PR URL;
- lemma or declaration names;
- capability + request digest;
- assurance mode;
- whether the result is library-merged;
- human reviewer;
- hours saved estimate (optional, labeled estimate).

## Explicit non-claims

- No live frontier acceleration is asserted by this repository state.
- Sample Foundry corpus episodes are fixtures, not collaboration outcomes.
- Exit criterion "≥1 frontier program materially accelerated" remains **human / external**.
