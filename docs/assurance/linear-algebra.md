# Linear algebra — algorithm contract (Product 06)

Independent specification of the owned reference algorithm for
`algebra.linear_algebra`. Lean: `MathEvidence.Assurance.LinearAlgebra`.

## Assurance level

`verified_reference_algorithm`. Completeness: **not claimed**.

## Input domain

Finite matrices/vectors over `ℚ` with nonzero entry denominators, operations:
`inverse_witness`, `system_solution`, `kernel_vector`, `det_identity` (as
registered).

## Output relation

Witness relations checked by exact arithmetic predicates
(`isInverseWitness`, `isSystemSolution`, …) behind `checkBool`.

## Reference algorithm

1. Digest bind + operation agreement.
2. Decode matrices/vectors over `ℚ`.
3. Evaluate the operation-specific witness predicate (matrix multiply / det).
4. Reject singular/out-of-domain witnesses.

Entry: `MathEvidence.Checkers.LinearAlgebra.checkBool` =
`MathEvidence.Assurance.LinearAlgebra.referenceCheck`.

## Soundness / completeness

Soundness via checker soundness theorems. Completeness over all matrices is
**not** claimed; singular cases are expected rejects.

Practical matrix scale is bounded by `IR/MatrixExpr.defaultSizeLimit` (64
entries) and factorial Laplace cost for `det_identity`. That limit is an
**intentional resource policy**, not a missing proof: general-n det Bridge is
MET within the accepted size.

## Proprietary backends

Empirical only unless a higher assurance level is separately evidenced.
