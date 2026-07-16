/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.RationalEquality.Check
import MathEvidence.IR.RationalExpr.Soundness

namespace MathEvidence.Checkers.RationalEquality

open MathEvidence.IR.RationalExpr

theorem checkBool_polyOk (req : Request) (cert : Certificate)
    (h : checkBool req cert = true) : polyOk req = true := by
  simp [checkBool, Bool.and_eq_true] at h
  -- ((digestOk ∧ wellFormedOk) ∧ polyOk) ∧ coverOk
  exact h.1.2

theorem checkBool_sound (req : Request) (cert : Certificate)
    (h : checkBool req cert = true) :
    Claim.proposition req.claim cert.denomFactors := by
  intro env _ hl hr
  have hp : polyEqual req.claim.lhs req.claim.rhs = true := checkBool_polyOk req cert h
  exact eval_eq_of_polyEqual_defined req.claim.lhs req.claim.rhs env hp hl hr

theorem check_sound (req : Request) (cand : Candidate) (cert : Certificate)
    (h : check req cand cert = .accept) :
    Claim.proposition req.claim cert.denomFactors := by
  exact checkBool_sound req cert ((check_accept_iff req cand cert).1 h)

end MathEvidence.Checkers.RationalEquality
