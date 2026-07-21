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
  soundnessDecl := "MathEvidence.Checkers.LinearAlgebra.checkBool_sound"
  checkerDecl := "MathEvidence.Checkers.LinearAlgebra.checkBool"

def referenceCheck (req : Request) (cert : Certificate) : Bool :=
  checkBool req cert

theorem referenceCheck_eq_checkBool (req : Request) (cert : Certificate) :
    referenceCheck req cert = checkBool req cert := rfl

/-- Inverse witness reference coincides with the IR predicate. -/
theorem inverse_reference (A B : Matrix) :
    isInverseWitness A B = (isRightInverse A B && isLeftInverse A B) := rfl

/-- Full contract link: reference check acceptance implies claim proposition. -/
theorem referenceCheck_sound (req : Request) (cert : Certificate)
    (h : referenceCheck req cert = true) :
    Claim.proposition req.claim cert.inverse cert.vector :=
  checkBool_sound req cert h

/-- Inverse operation path: reference check implies evaluated two-sided identity. -/
theorem referenceCheck_inverse_eval (req : Request) (cert : Certificate)
    (h : referenceCheck req cert = true)
    (hop : req.claim.operation = .inverseWitness)
    (B : Matrix) (hi : cert.inverse = some B) :
    (∃ M, req.claim.matrix.mulEval? B = some M ∧ M = identityRats req.claim.matrix.nrows) ∧
      (∃ M, B.mulEval? req.claim.matrix = some M ∧ M = identityRats req.claim.matrix.nrows) :=
  inverse_eval_sound req cert h hop B hi

/-- System-solution path: reference check implies evaluated `A * x = b`. -/
theorem referenceCheck_system_eval (req : Request) (cert : Certificate)
    (h : referenceCheck req cert = true)
    (hop : req.claim.operation = .systemSolution)
    (x : Vector) (hx : cert.vector = some x) :
    ∃ ax bv, req.claim.matrix.mulVecEval? x = some ax ∧
      req.claim.rhs.eval? = some bv ∧ ax = bv :=
  systemSolution_eval_sound req cert h hop x hx

example : contract.claimsCompleteness = false := by native_decide
example : contract.assuranceLevel = .verifiedReferenceAlgorithm := by native_decide
example : contract.linksDecls = true := by native_decide

/-- Contract decls point at the live checker + soundness theorems. -/
theorem contract_decls :
    contract.soundnessDecl = "MathEvidence.Checkers.LinearAlgebra.checkBool_sound" ∧
      contract.checkerDecl = "MathEvidence.Checkers.LinearAlgebra.checkBool" := by
  native_decide

end MathEvidence.Assurance.LinearAlgebra
