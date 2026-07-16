# Finite counterexample — algorithm contract (Product 06)

Independent specification of the owned reference algorithm for
`logic.finite_counterexample`. Lean: `MathEvidence.Assurance.Counterexample`.

## Assurance level

`verified_reference_algorithm`. Completeness / exhaustive search: **not claimed**.

## Input domain

Typed finite predicates (`FinitePredicate`) over finite domains (nat/int/bool
with explicit bounds).

## Output relation

The witness assignment is admissible and falsifies the claimed universal
predicate (`Claim.proposition` / `isCounterexample`).

## Reference algorithm

1. Digest bind.
2. Witness well-formedness against domain bounds.
3. Evaluate the predicate at the witness.
4. Accept iff evaluation shows a counterexample.

Entry: `MathEvidence.Checkers.Counterexample.checkBool` =
`MathEvidence.Assurance.Counterexample.referenceCheck`.

## Soundness / completeness

`checkBool_sound` / `referenceCheck_sound`. Absence of a found witness is **not**
evidence of truth; exhaustive completeness is out of scope.

## Proprietary backends

Untrusted enumeration/search; status advances only after this checker accepts.
