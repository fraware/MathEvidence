/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.MatrixExpr.Ops

namespace MathEvidence.IR.MatrixExpr

/-!
# Soundness

Bool checkers relate to evaluated `ℚ` equalities. Completeness / rank / basis
claims are intentionally absent from this IR.
-/

theorem ratsEqual_eq (A B : List (List ℚ)) :
    ratsEqual A B = true ↔ A = B := by
  simp [ratsEqual, decide_eq_true_eq]

theorem isRightInverse_sound (A B : Matrix) (h : isRightInverse A B = true) :
    ∃ M, A.mulEval? B = some M ∧ M = identityRats A.nrows := by
  revert h
  simp only [isRightInverse]
  split
  · intro h; exact False.elim (Bool.false_ne_true h)
  · next M hm =>
    intro h
    refine ⟨M, hm, (ratsEqual_eq M (identityRats A.nrows)).1 ?_⟩
    simp [Bool.and_eq_true] at h
    exact h.1.1.1

theorem isLeftInverse_sound (A B : Matrix) (h : isLeftInverse A B = true) :
    ∃ M, B.mulEval? A = some M ∧ M = identityRats A.nrows := by
  revert h
  simp only [isLeftInverse]
  split
  · intro h; exact False.elim (Bool.false_ne_true h)
  · next M hm =>
    intro h
    refine ⟨M, hm, (ratsEqual_eq M (identityRats A.nrows)).1 ?_⟩
    simp [Bool.and_eq_true] at h
    exact h.1.1.1

theorem isInverseWitness_sound (A B : Matrix) (h : isInverseWitness A B = true) :
    (∃ M, A.mulEval? B = some M ∧ M = identityRats A.nrows) ∧
      (∃ M, B.mulEval? A = some M ∧ M = identityRats A.nrows) := by
  simp only [isInverseWitness, Bool.and_eq_true] at h
  exact ⟨isRightInverse_sound A B h.1, isLeftInverse_sound A B h.2⟩

theorem isSystemSolution_sound (A : Matrix) (b x : Vector)
    (h : isSystemSolution A b x = true) :
    ∃ ax bv, A.mulVecEval? x = some ax ∧ b.eval? = some bv ∧
      ratsEqual (ax.map fun t => [t]) (bv.map fun t => [t]) = true := by
  revert h
  simp only [isSystemSolution]
  split
  · next ax bv hax hbv =>
    intro h
    refine ⟨ax, bv, hax, hbv, ?_⟩
    simp [Bool.and_eq_true] at h
    exact h.1.1
  · intro h; exact False.elim (Bool.false_ne_true h)

theorem isKernelVector_sound (A : Matrix) (v : Vector)
    (h : isKernelVector A v = true) :
    ∃ av xv, A.mulVecEval? v = some av ∧ v.eval? = some xv ∧
      isZeroRats av = true ∧ isNonzeroRats xv = true := by
  revert h
  simp only [isKernelVector]
  split
  · intro h; exact False.elim (Bool.false_ne_true h)
  · next av hav =>
    intro h
    have hz : isZeroRats av = true := by
      simp [Bool.and_eq_true] at h; exact h.1.1
    have hnz : isNonzeroRats (v.eval?.getD []) = true := by
      simp [Bool.and_eq_true] at h; exact h.1.2
    match hx : v.eval? with
    | none =>
      simp [hx, isNonzeroRats] at hnz
    | some xv =>
      exact ⟨av, xv, hav, rfl, hz, by simpa [hx] using hnz⟩

theorem isDetIdentity_sound (A : Matrix) (d : RatLit)
    (h : isDetIdentity A d = true) :
    ∃ detA dq, A.detEval? = some detA ∧ d.toRat? = some dq ∧ detA = dq := by
  revert h
  simp only [isDetIdentity]
  split
  · next detA dq hd hq =>
    intro h
    refine ⟨detA, dq, hd, hq, ?_⟩
    simp [Bool.and_eq_true, decide_eq_true_eq] at h
    exact h.1
  · intro h; exact False.elim (Bool.false_ne_true h)

end MathEvidence.IR.MatrixExpr
