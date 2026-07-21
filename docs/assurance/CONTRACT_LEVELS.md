# Assurance contract scaffold (ME-305)

Machine-checkable contracts link Lean decls to assurance levels. Registry
rejects unsupported claim levels.

## Levels

1. `declared` — documentation only
2. `tested` — conformance fixtures
3. `verified_reference_algorithm` — Lean reference with soundness theorem
4. `kernel_replay` — checker receipt + offline replay
5. `dual_backend` — two generators, one checker
6. `externally_reviewed` — signed domain + trust packets (human)

Contracts live under `registry/assurance/` and `MathEvidence/Assurance/`.
This file is the packaging checklist; do not invent signed reviews.
