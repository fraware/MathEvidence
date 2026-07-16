# Rational equality — algorithm contract (Product 06)

Independent specification of the **owned reference algorithm** for
`algebra.rational_equality`. This document is normative for assurance claims;
the Lean module `MathEvidence.Assurance.RationalEquality` exports the executable
contract metadata and soundness bridge.

## Assurance level

`verified_reference_algorithm` (Product 06 §3 item 3).

Not claimed: restricted completeness, open-implementation correspondence, or
verification of SymPy/Mathematica internals.

## Input domain

- Rational expressions over `ℚ` in the `RationalExpr` IR.
- Explicit division nodes; transcendentals and unsupported ops rejected upstream.
- Side conditions appear as explicit denominator factors (never silent).

## Output relation

Under the certificate's `denomFactors`, establish
`Claim.proposition` — i.e. `lhs = rhs` as rational functions where those
denominators are nonzero.

## Reference algorithm (checker = reference)

1. Bind `requestDigest` (reject mismatch).
2. Well-formedness of request/certificate IR.
3. Sparse polynomial identity of the cleared difference numerator.
4. Denominator-factor cover of every division in `lhs`/`rhs`.

Executable entry point: `MathEvidence.Checkers.RationalEquality.checkBool`.
Assurance alias: `MathEvidence.Assurance.RationalEquality.referenceCheck`
(definitionally equal to `checkBool`).

## Soundness

`checkBool_sound` / `referenceCheck_sound`: acceptance implies the claim
proposition under the stated factors.

## Completeness

**None.** Completeness is explicitly `null` in the JSON contract. Finite
conformance suites do not imply completeness over all rational identities.

## Termination / complexity assumptions

Finite expression size; integer digit and nesting bounds from the capability
resource policy. Performance is reported separately from correctness
(`performanceNotes` in the registry assurance JSON).

## Proprietary backends

Mathematica/SymPy may generate candidate certificates. Every accepted result
must pass this reference checker. Differential/conformance evidence for
proprietary backends is empirical (`proprietary_differential` level) and is
**not** implied by this contract.

## Reuse

Domain checkers and external projects may import
`MathEvidence.Checkers.RationalEquality` / Assurance without pulling adapters.
