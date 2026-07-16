/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Assurance.Level
import MathEvidence.Checkers.LinearAlgebra.Check
import MathEvidence.Checkers.LinearAlgebra.Soundness
import MathEvidence.IR.MatrixExpr.Ops

namespace MathEvidence.Assurance.LinearAlgebra

open MathEvidence.Checkers.LinearAlgebra
open MathEvidence.IR.MatrixExpr

/-!
# LinearAlgebra algorithm contract + verified reference

Reference algorithm: witness checks via matrix multiplication / det evaluation
(`isInverseWitness`, `isSystemSolution`, …) behind `checkBool`.
-/

def contract : AlgorithmContract where
  id := "assurance.linear_algebra.reference"
  version := "0.1.0"
  assuranceLevel := .verifiedReferenceAlgorithm
  capabilityId := "algebra.linear_algebra"
  inputDomain := "Finite matrices / vectors over ℚ with nonzero denominators"
  outputRelation := "Witness relations (inverse, system solution, kernel, det identity)"
  soundness := "check_sound / checkBool implies payloadOk"
  completeness := none

def referenceCheck (req : Request) (cert : Certificate) : Bool :=
  checkBool req cert

theorem referenceCheck_eq_checkBool (req : Request) (cert : Certificate) :
    referenceCheck req cert = checkBool req cert := rfl

/-- Inverse witness reference coincides with the IR predicate. -/
theorem inverse_reference (A B : Matrix) :
    isInverseWitness A B = (isRightInverse A B && isLeftInverse A B) := rfl

example : contract.claimsCompleteness = false := by native_decide
example : contract.assuranceLevel = .verifiedReferenceAlgorithm := by native_decide

end MathEvidence.Assurance.LinearAlgebra
