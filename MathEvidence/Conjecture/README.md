# Conjecture and Falsification (Product 04)

Engine over formally defined object families.

## Primary domain scaffold

| File | Role |
| --- | --- |
| `Domains/FiniteGraph.lean` | Formal `Object n` (upper-triangle simple graphs) + Lean-certified falsification of "every Fin-3 graph has an edge" via empty-graph witness |
| Python `agent/conjecture/finite_graph.py` | Atlas load (≥1000 noniso n≤7), ≥5 invariants, calibrated + scaled falsification, Foundry artifacts |

Executable campaign artifacts: `evidence/conjecture/finite_graph/` (generator
`finite_graph.v0.2.0`). Nat-bounded fixtures in `Tests.lean` remain regression
coverage only — they are **not** the product vertical.

## Modules

| File | Role |
| --- | --- |
| `States.lean` | Conjecture state machine |
| `Family.lean` | Object-family contract → Counterexample claims |
| `Engine.lean` | Observe / candidate / certify refutation / bounded verify |
| `Precision.lean` | Campaign precision accounting; open / formally proved markers |
| `Domains/` | Domain plugins (finite graphs first) |
| `Tests.lean` | Nat fixture campaign + precision accounting |

## Policy

- Counterexample search before expensive proof (Agent/Python).
- Status becomes `falsified` only after Lean `checkBool`.
- `bounded_verified` ≠ theorem over the unbounded family.
- AI may propose patterns; it does not set proof status.
