# Conformance suite for logic.finite_counterexample

Lean offline fixtures: `MathEvidence.Checkers.Counterexample.Tests`.
Python offline bundles under each `requiredCases` name (accept + intentional reject).
SymPy/enumeration live generation backs accept cases; Lean owns accept.
Mathematica/Sage: `live_generator_complete` (bounded enumeration gated by live
runtime availability); public CI without Wolfram/Sage stays fixture/unavailable.
Differential: `scripts/run_differential_backends.py` (CEX accept cases).
