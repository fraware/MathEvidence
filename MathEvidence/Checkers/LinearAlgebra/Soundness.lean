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

private theorem singletonColumns_eq {xs ys : List ℚ}
    (h : xs.map (fun t => [t]) = ys.map (fun t => [t])) : xs = ys := by
  revert ys
  induction xs with
  | nil =>
    intro ys h
    cases ys <;> simp at h ⊢
  | cons x xs ih =>
    intro ys h
    cases ys with
    | nil => simp at h
    | cons y ys =>
      simp at h
      rw [h.1, ih h.2]

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

/-- Accepted system-solution witnesses imply evaluated `A * x = b` over `ℚ`. -/
theorem systemSolution_eval_sound (req : Request) (cert : Certificate)
    (h : checkBool req cert = true)
    (hop : req.claim.operation = .systemSolution)
    (x : Vector) (hx : cert.vector = some x) :
    ∃ ax bv, req.claim.matrix.mulVecEval? x = some ax ∧
      req.claim.rhs.eval? = some bv ∧ ax = bv := by
  have hp := checkBool_sound req cert h
  have hbool : isSystemSolution req.claim.matrix req.claim.rhs x = true := by
    simpa [Claim.proposition, payloadOk, hop, hx] using hp
  obtain ⟨ax, bv, hax, hbv, heq⟩ :=
    isSystemSolution_sound req.claim.matrix req.claim.rhs x hbool
  refine ⟨ax, bv, hax, hbv, ?_⟩
  exact singletonColumns_eq ((ratsEqual_eq _ _).1 heq)

/-- Accepted kernel-vector witnesses imply evaluated nonzero `v` with `A * v = 0`. -/
theorem kernelVector_eval_sound (req : Request) (cert : Certificate)
    (h : checkBool req cert = true)
    (hop : req.claim.operation = .kernelVector)
    (v : Vector) (hv : cert.vector = some v) :
    ∃ av xv, req.claim.matrix.mulVecEval? v = some av ∧
      v.eval? = some xv ∧ isZeroRats av = true ∧ isNonzeroRats xv = true := by
  have hp := checkBool_sound req cert h
  have hbool : isKernelVector req.claim.matrix v = true := by
    simpa [Claim.proposition, payloadOk, hop, hv] using hp
  exact isKernelVector_sound req.claim.matrix v hbool

/-- Accepted determinant identities imply the evaluated determinant equals the claim. -/
theorem detIdentity_eval_sound (req : Request) (cert : Certificate)
    (h : checkBool req cert = true)
    (hop : req.claim.operation = .detIdentity)
    (d : RatLit) (hd : req.claim.claimedDet = some d) :
    ∃ detA dq, req.claim.matrix.detEval? = some detA ∧
      d.toRat? = some dq ∧ detA = dq := by
  have hp := checkBool_sound req cert h
  have hbool : isDetIdentity req.claim.matrix d = true := by
    simpa [Claim.proposition, payloadOk, hop, hd] using hp
  exact isDetIdentity_sound req.claim.matrix d hbool

end MathEvidence.Checkers.LinearAlgebra
