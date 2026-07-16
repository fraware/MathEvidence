/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Assurance.Level
import MathEvidence.Checkers.Counterexample.Check
import MathEvidence.Checkers.Counterexample.Soundness
import MathEvidence.IR.FinitePredicate.Eval

namespace MathEvidence.Assurance.Counterexample

open MathEvidence.Checkers.Counterexample
open MathEvidence.IR.FinitePredicate

/-!
# Finite counterexample algorithm contract + verified reference

Reference algorithm: evaluate the original finite predicate at the typed witness.
Exhaustive absence / completeness is explicitly out of scope.
-/

def contract : AlgorithmContract where
  id := "assurance.finite_counterexample.reference"
  version := "0.1.0"
  assuranceLevel := .verifiedReferenceAlgorithm
  capabilityId := "logic.finite_counterexample"
  inputDomain := "FinitePredicate over typed finite domains"
  outputRelation := "Witness assignment falsifies the claimed universal predicate"
  soundness := "check_sound / checkBool implies isCounterexample"
  completeness := none

def referenceCheck (req : Request) (cert : Certificate) : Bool :=
  checkBool req cert

theorem referenceCheck_eq_checkBool (req : Request) (cert : Certificate) :
    referenceCheck req cert = checkBool req cert := rfl

theorem reference_eval (req : Request) (cert : Certificate)
    (h : referenceCheck req cert = true) :
    evalOk req cert = true :=
  checkBool_evalOk req cert h

theorem referenceCheck_sound (req : Request) (cert : Certificate)
    (h : referenceCheck req cert = true) :
    Claim.proposition req.claim cert.witness :=
  checkBool_sound req cert h

example : contract.claimsCompleteness = false := by native_decide
example : contract.assuranceLevel = .verifiedReferenceAlgorithm := by native_decide

end MathEvidence.Assurance.Counterexample
