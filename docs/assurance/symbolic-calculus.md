# Symbolic calculus — algorithm contract (Product 06)

Independent specification of the owned reference algorithm for
`analysis.symbolic_calculus`. Lean: `MathEvidence.Assurance.Calculus`.

## Assurance level

`verified_reference_algorithm` for the **owned checker** path. Completeness over
symbolic calculus is **not** claimed. Branch/singularity conditions must remain
explicit in certificates.

## Input domain

Restricted calculus IR fragments registered by the capability (differentiation /
selected identities) with explicit side conditions.

## Output relation

Checker acceptance implies the stated claim class under those conditions — never
a silent completeness claim for CAS simplification.

## Reference algorithm

Digest bind → IR well-formedness → checker-specific verification predicates in
`MathEvidence.Checkers.Calculus`. Assurance `referenceCheck` coincides with
`checkBool` where defined.

## Soundness / completeness

Soundness theorems live with the checker package. Completeness: **null** in the
assurance JSON. Candidate validity remains separate from completeness
(Milestone 5 honesty).

## Proprietary backends

Mathematica live generation may be unavailable; offline fixtures and empirical
differential evidence must not be phrased as verified CAS internals.
