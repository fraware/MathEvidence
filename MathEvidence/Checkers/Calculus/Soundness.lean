/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.Calculus.Check
import MathEvidence.IR.CalculusExpr.Soundness

namespace MathEvidence.Checkers.Calculus

theorem checkBool_opOk (req : Request) (cert : Certificate)
    (h : checkBool req cert = true) : opOk req = true := by
  simp [checkBool, Bool.and_eq_true] at h
  exact h.right

theorem checkBool_sound (req : Request) (cert : Certificate)
    (h : checkBool req cert = true) :
    Claim.proposition req.claim := by
  simpa [Claim.proposition, opOk_eq_opHolds] using checkBool_opOk req cert h

theorem check_sound (req : Request) (cand : Candidate) (cert : Certificate)
    (h : check req cand cert = .accept) :
    Claim.proposition req.claim :=
  checkBool_sound req cert ((check_accept_iff req cand cert).1 h)

end MathEvidence.Checkers.Calculus
