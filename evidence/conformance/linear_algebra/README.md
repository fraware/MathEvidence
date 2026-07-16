# Conformance suite for algebra.linear_algebra

Lean offline fixtures: `MathEvidence.Checkers.LinearAlgebra.Tests`.
Python offline bundles under each `requiredCases` name (accept + intentional reject).
SymPy live generation backs accept cases; Lean owns theorem acceptance.
Mathematica/Sage: `live_generator_complete` when respective live runtimes are
available; public CI without Wolfram/Sage stays fixture/unavailable.
Differential: `scripts/run_differential_backends.py` (LA accept cases).
