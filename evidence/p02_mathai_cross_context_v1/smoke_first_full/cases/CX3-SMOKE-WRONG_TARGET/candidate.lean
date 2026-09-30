import MathEvidence.Assurance.LinearAlgebra
open MathEvidence.Checkers.LinearAlgebra
open MathEvidence.IR.MatrixExpr

namespace P02CrossContext.LinearAlgebra

theorem p02Native (A B : Matrix) : isInverseWitness A B = isInverseWitness A B := by
  rfl

end P02CrossContext.LinearAlgebra
