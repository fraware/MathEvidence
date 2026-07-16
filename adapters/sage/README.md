# SageMath adapter

Optional third open backend for `algebra.rational_equality`.

## Modes

| Mode | When | Behavior |
| --- | --- | --- |
| `live` | `sage` / `MATHEVIDENCE_SAGE` found | JSON-RPC `compute` via `sage -python` worker |
| `fixture` | Sage missing or `MATHEVIDENCE_ADAPTER_MODE=fixture` | JSON-RPC up; `compute` → `backend_unavailable` |

Committed evidence under `evidence/` always replays offline without Sage.

## Run

```text
python -m adapters.sage
```

## Contract

Same request/certificate schemas as SymPy and Mathematica. Adapter output is untrusted;
Lean checkers own theorem acceptance.
