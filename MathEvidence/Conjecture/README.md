# Conjecture and Falsification (Product 04)

Engine over formally defined object families. Initial domain: finite predicates.

## Modules

| File | Role |
| --- | --- |
| `States.lean` | Conjecture state machine |
| `Family.lean` | Object-family contract → Counterexample claims |
| `Engine.lean` | Observe / candidate / certify refutation / bounded verify |
| `Precision.lean` | Campaign precision accounting; open / formally proved markers |
| `Tests.lean` | Offline fixtures + `campaignDemo` |

## Policy

- Counterexample search before expensive proof (Agent/Python).
- Status becomes `falsified` only after Lean `checkBool`.
- `bounded_verified` ≠ theorem over the unbounded family.
- AI may propose patterns; it does not set proof status.
