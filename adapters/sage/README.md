# SageMath adapter

Optional third open backend for `algebra.rational_equality` (scaffold),
`algebra.linear_algebra`, and `logic.finite_counterexample`.

## Modes

| Mode | When | Behavior |
| --- | --- | --- |
| `live` | `sage` / `MATHEVIDENCE_SAGE` found | JSON-RPC `compute` via `sage -python` worker (LA) or gated enumeration (CEX) |
| `fixture` | Sage missing or `MATHEVIDENCE_ADAPTER_MODE=fixture` | JSON-RPC up; `compute` → `backend_unavailable` |

Committed evidence under `evidence/` always replays offline without Sage.

## Support levels

| Capability | Level |
| --- | --- |
| `algebra.rational_equality` | `placeholder` (scaffold / best-effort zero-numerator path) |
| `algebra.linear_algebra` | `live_generator_complete` when sage is available |
| `logic.finite_counterexample` | `live_generator_complete` when sage is available |

## Run

```text
python -m adapters.sage
```

## Contract

Same request/certificate schemas as SymPy and Mathematica. Adapter output is untrusted;
Lean checkers own theorem acceptance.
