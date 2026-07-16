/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.Counterexample.Check
import MathEvidence.IR.FinitePredicate.Soundness

namespace MathEvidence.Checkers.Counterexample

open MathEvidence.IR.FinitePredicate

theorem checkBool_evalOk (req : Request) (cert : Certificate)
    (h : checkBool req cert = true) : evalOk req cert = true := by
  simp [checkBool, Bool.and_eq_true] at h
  exact h.2

theorem checkBool_sound (req : Request) (cert : Certificate)
    (h : checkBool req cert = true) :
    Claim.proposition req.claim cert.witness := by
  simpa [Claim.proposition, evalOk] using checkBool_evalOk req cert h

theorem check_sound (req : Request) (cand : Candidate) (cert : Certificate)
    (h : check req cand cert = .accept) :
    Claim.proposition req.claim cert.witness := by
  exact checkBool_sound req cert ((check_accept_iff req cand cert).1 h)

/-- Accepted counterexample means the predicate is not true at the witness. -/
theorem checkBool_refutes (req : Request) (cert : Certificate)
    (h : checkBool req cert = true) :
    eval cert.witness req.claim.pred = some false := by
  have := checkBool_sound req cert h
  simpa [Claim.proposition, isCounterexample_iff] using this

end MathEvidence.Checkers.Counterexample
