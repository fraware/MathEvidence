# Hypothesis Synthesis (Product 03)

Lean-side sufficiency / deletion / lattice for repairing incomplete statements.

## Modules

| File | Role |
| --- | --- |
| `Lattice.lean` | Condition lattice artifact (primary output) |
| `Sufficiency.lean` | `proveSufficient` three-way + typed `SufficiencyEvidence` via `RationalEquality` checker |
| `Deletion.lean` | `delete_hypothesis` with redundancy justification |
| `CounterexampleBridge.lean` | Weaker-variant CEX via `Counterexample` checker |
| `Build.lean` | Bounded lattice construction policy |
| `Tests.lean` | Offline fixtures (`native_decide`); denom-coverage-alone refusal |

## Invariants

- Proposed conditions are never silently inserted into theorems.
- Sufficiency is checker acceptance (`checkBool` = poly identity **and** denom coverage) + soundness theorem.
- Denominator coverage alone is never sufficiency.
- `proveSufficient` outcomes are distinct: `proved` / `failed` / `unknown`, with theoremDecl / checkerDecl / receiptId / axiomReportId citations.
- Necessity / minimality require explicit `NecessityProof` entries.
- Absence of a counterexample is not necessity.

## Agent operations

See Agent API: `propose_conditions`, `prove_sufficient`, `delete_hypothesis`,
`find_counterexample`, `verify_counterexample`, `build_condition_lattice`.
