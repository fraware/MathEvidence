/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.LinearAlgebra.Check
import MathEvidence.IR.MatrixExpr.Soundness

namespace MathEvidence.Checkers.LinearAlgebra

open MathEvidence.IR.MatrixExpr

theorem checkBool_opOk (req : Request) (cert : Certificate)
    (h : checkBool req cert = true) : opOk req cert = true := by
  simp [checkBool, Bool.and_eq_true] at h
  exact h.2

theorem checkBool_sound (req : Request) (cert : Certificate)
    (h : checkBool req cert = true) :
    Claim.proposition req.claim cert.inverse cert.vector := by
  simpa [Claim.proposition, opOk] using checkBool_opOk req cert h

theorem check_sound (req : Request) (cand : Candidate) (cert : Certificate)
    (h : check req cand cert = .accept) :
    Claim.proposition req.claim cert.inverse cert.vector := by
  exact checkBool_sound req cert ((check_accept_iff req cand cert).1 h)

/-- Inverse witness additionally implies evaluated two-sided identity. -/
theorem inverse_eval_sound (req : Request) (cert : Certificate)
    (h : checkBool req cert = true)
    (hop : req.claim.operation = .inverseWitness)
    (B : Matrix) (hi : cert.inverse = some B) :
    (∃ M, req.claim.matrix.mulEval? B = some M ∧ M = identityRats req.claim.matrix.nrows) ∧
      (∃ M, B.mulEval? req.claim.matrix = some M ∧ M = identityRats req.claim.matrix.nrows) := by
  have hp := checkBool_sound req cert h
  have hbool : isInverseWitness req.claim.matrix B = true := by
    simpa [Claim.proposition, payloadOk, hop, hi] using hp
  exact isInverseWitness_sound req.claim.matrix B hbool

end MathEvidence.Checkers.LinearAlgebra
