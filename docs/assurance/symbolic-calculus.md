# Formal rational calculus — algorithm contract (Product 06)

Independent specification of the owned reference algorithm for
`algebra.formal_rational_calculus`, the transitional registry ID for the planned
`algebra.formal_rational_calculus` rename. Lean checker:
`MathEvidence.Assurance.Calculus`.

## Assurance level

`verified_reference_algorithm` for the **owned checker** path. Completeness over
formal rational calculus is **not** claimed. Branch/singularity conditions must
remain explicit in certificates.

## Input domain

Restricted rational-expression IR fragments registered by the capability
(syntactic differentiation / selected substitution identities) with explicit
side conditions.

This is not Mathlib analytic calculus: checker acceptance does not establish
`HasDerivAt`, `HasDerivWithinAt`, continuity, ODE existence/uniqueness, or
identity at poles.

## Output relation

Checker acceptance implies the stated claim class under those conditions — never
a silent completeness claim for CAS simplification.

## Reference algorithm

Digest bind → IR well-formedness → checker-specific verification predicates in
`MathEvidence.Checkers.Calculus`. Assurance `referenceCheck` coincides with
`checkBool` where defined.

New Lean imports may use the additive alias barrel
`MathEvidence.IR.FormalRationalCalculus`; the underlying implementation remains
`MathEvidence.IR.CalculusExpr` until a coordinated filesystem rename is safe.

## Soundness / completeness

Soundness theorems live with the checker package. Completeness: **null** in the
assurance JSON. Candidate validity remains separate from completeness
(Milestone 5 honesty).

## Proprietary backends

Mathematica live generation may be unavailable; offline fixtures and empirical
differential evidence must not be phrased as verified CAS internals.
