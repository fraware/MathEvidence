# ADR 0002 — The core is solver-independent

## Decision

No core or checker module depends on Mathematica, LeanLink, SageMath, SymPy, or any solver runtime. Backends emit common evidence structures that Lean checks independently.

## Consequence

Mathematica may be the strongest generation backend and Studio environment. It cannot become a replay dependency or theorem authority.
