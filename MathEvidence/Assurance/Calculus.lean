/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Assurance.Level
import MathEvidence.Checkers.Calculus.Check
import MathEvidence.Checkers.Calculus.Soundness

namespace MathEvidence.Assurance.Calculus

open MathEvidence.Checkers.Calculus

/-!
# Symbolic calculus algorithm contract + verified reference

Reference algorithm: formal differentiation / substitution + `polyEqual`.
Completeness / uniqueness claims are explicitly out of scope.
-/

def contract : AlgorithmContract where
  id := "assurance.symbolic_calculus.reference"
  version := "0.1.0"
  assuranceLevel := .verifiedReferenceAlgorithm
  capabilityId := "analysis.symbolic_calculus"
  inputDomain := "CalculusExpr over RationalExpr with explicit domainConditions"
  outputRelation := "Formal candidate identity (deriv / antideriv / recurrence / ODE+IC)"
  soundness := "check_sound / checkBool implies Claim.proposition (opHolds)"
  completeness := none

def referenceCheck (req : Request) (cert : Certificate) : Bool :=
  checkBool req cert

theorem referenceCheck_eq_checkBool (req : Request) (cert : Certificate) :
    referenceCheck req cert = checkBool req cert := rfl

theorem referenceCheck_sound (req : Request) (cert : Certificate)
    (h : referenceCheck req cert = true) :
    Claim.proposition req.claim :=
  checkBool_sound req cert h

example : contract.claimsCompleteness = false := by native_decide
example : contract.assuranceLevel = .verifiedReferenceAlgorithm := by native_decide

end MathEvidence.Assurance.Calculus
