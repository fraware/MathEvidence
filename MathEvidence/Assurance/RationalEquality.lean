/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Assurance.Level
import MathEvidence.Checkers.RationalEquality.Check
import MathEvidence.Checkers.RationalEquality.Soundness

namespace MathEvidence.Assurance.RationalEquality

open MathEvidence.Checkers.RationalEquality
open MathEvidence.IR.RationalExpr

/-!
# RationalEquality algorithm contract + verified reference

The reference algorithm is the existing checker pipeline:
digest bind → well-formedness → polynomial identity → denominator cover.

Assurance level: `verified_reference_algorithm` (Product 06 §3 item 3), with
checker soundness already established in `Checkers.RationalEquality.Soundness`.
-/

def contract : AlgorithmContract where
  id := "assurance.rational_equality.reference"
  version := "0.1.0"
  assuranceLevel := .verifiedReferenceAlgorithm
  capabilityId := "algebra.rational_equality"
  inputDomain := "RationalExpr over ℚ with explicit divisions; transcendentals rejected"
  outputRelation := "lhs = rhs under explicit nonzero denomFactors (Claim.proposition)"
  soundness := "check_sound / checkBool_sound"
  completeness := none

/-- Verified reference algorithm: coincides with `checkBool`. -/
def referenceCheck (req : Request) (cert : Certificate) : Bool :=
  checkBool req cert

theorem referenceCheck_eq_checkBool (req : Request) (cert : Certificate) :
    referenceCheck req cert = checkBool req cert := rfl

/-- Soundness of the reference algorithm relative to the claim proposition. -/
theorem referenceCheck_sound (req : Request) (cert : Certificate)
    (h : referenceCheck req cert = true) :
    Claim.proposition req.claim cert.denomFactors :=
  checkBool_sound req cert h

/-- Contract does not claim completeness. -/
example : contract.claimsCompleteness = false := by native_decide

example : contract.assuranceLevel = .verifiedReferenceAlgorithm := by native_decide

end MathEvidence.Assurance.RationalEquality
