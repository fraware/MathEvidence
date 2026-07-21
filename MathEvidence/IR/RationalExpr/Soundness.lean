/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring
import MathEvidence.IR.RationalExpr.Eval
import MathEvidence.IR.RationalExpr.Poly
import MathEvidence.IR.RationalExpr.Reify

namespace MathEvidence.IR.RationalExpr

/-!
# Soundness

Specification theorems linking `Defined` / `toFrac` / `polyEqual` / `eval`.
-/

private theorem evalPoly_mul_ne_zero (env : Env ℚ) {p q : Poly}
    (hp : evalPoly env p ≠ 0) (hq : evalPoly env q ≠ 0) :
    evalPoly env (Poly.mul p q) ≠ 0 := by
  simpa [evalPoly, Poly.eval_mul] using mul_ne_zero hp hq

/-- Under definedness, fraction form recovers field evaluation. -/
theorem defined_toFrac_eval (env : Env ℚ) (e : Expr) (h : Defined env e) :
    ∃ n d : Poly,
      toFrac e = some (n, d) ∧
      evalPoly env d ≠ 0 ∧
      eval env e = some (evalPoly env n / evalPoly env d) := by
  induction e with
  | var i =>
    refine ⟨Poly.X i, Poly.one, rfl, ?_, ?_⟩
    · simp [evalPoly, Poly.one, Poly.eval_C]
    · simp [eval, evalPoly, Poly.eval_X, Poly.one, Poly.eval_C]
  | int n =>
    refine ⟨Poly.C n, Poly.one, rfl, ?_, ?_⟩
    · simp [evalPoly, Poly.one, Poly.eval_C]
    · simp [eval, evalPoly, Poly.eval_C, Poly.one]
  | rat n d =>
    have hd : d ≠ 0 := h.1
    have hcast : (d : ℚ) ≠ 0 := h.2
    refine ⟨Poly.C n, Poly.C (Int.ofNat d), ?_, ?_, ?_⟩
    · simp [toFrac, hd]
    · simpa [evalPoly, Poly.eval_C] using hcast
    · simp [eval, evalPoly, Poly.eval_C, hd, hcast]
  | neg e ih =>
    obtain ⟨n, d, ht, hd, he⟩ := ih h
    refine ⟨Poly.neg n, d, ?_, hd, ?_⟩
    · simp [toFrac, ht]
    · simp [eval, he, evalPoly, Poly.eval_neg, neg_div]
  | add a b iha ihb =>
    obtain ⟨n1, d1, ht1, hd1, he1⟩ := iha h.1
    obtain ⟨n2, d2, ht2, hd2, he2⟩ := ihb h.2
    refine ⟨Poly.add (Poly.mul n1 d2) (Poly.mul n2 d1), Poly.mul d1 d2, ?_,
      evalPoly_mul_ne_zero env hd1 hd2, ?_⟩
    · simp [toFrac, ht1, ht2]
    · have heval :
          eval env (.add a b) =
            some (evalPoly env n1 / evalPoly env d1 + evalPoly env n2 / evalPoly env d2) := by
        simp [eval, he1, he2]
      rw [heval]
      congr 1
      -- Goal: n1/d1 + n2/d2 = (n1*d2 + n2*d1)/(d1*d2)
      calc
        evalPoly env n1 / evalPoly env d1 + evalPoly env n2 / evalPoly env d2
            = (evalPoly env n1 * evalPoly env d2 + evalPoly env d1 * evalPoly env n2) /
                (evalPoly env d1 * evalPoly env d2) := by
              rw [← div_add_div _ _ hd1 hd2]
        _ = (evalPoly env n1 * evalPoly env d2 + evalPoly env n2 * evalPoly env d1) /
              (evalPoly env d1 * evalPoly env d2) := by ring
        _ = evalPoly env (Poly.add (Poly.mul n1 d2) (Poly.mul n2 d1)) /
              evalPoly env (Poly.mul d1 d2) := by
              simp only [evalPoly, Poly.eval_add, Poly.eval_mul]
  | sub a b iha ihb =>
    obtain ⟨n1, d1, ht1, hd1, he1⟩ := iha h.1
    obtain ⟨n2, d2, ht2, hd2, he2⟩ := ihb h.2
    refine ⟨Poly.sub (Poly.mul n1 d2) (Poly.mul n2 d1), Poly.mul d1 d2, ?_,
      evalPoly_mul_ne_zero env hd1 hd2, ?_⟩
    · simp [toFrac, ht1, ht2]
    · have heval :
          eval env (.sub a b) =
            some (evalPoly env n1 / evalPoly env d1 - evalPoly env n2 / evalPoly env d2) := by
        simp [eval, he1, he2]
      rw [heval]
      congr 1
      calc
        evalPoly env n1 / evalPoly env d1 - evalPoly env n2 / evalPoly env d2
            = (evalPoly env n1 * evalPoly env d2 - evalPoly env d1 * evalPoly env n2) /
                (evalPoly env d1 * evalPoly env d2) := by
              rw [← div_sub_div _ _ hd1 hd2]
        _ = (evalPoly env n1 * evalPoly env d2 - evalPoly env n2 * evalPoly env d1) /
              (evalPoly env d1 * evalPoly env d2) := by ring
        _ = evalPoly env (Poly.sub (Poly.mul n1 d2) (Poly.mul n2 d1)) /
              evalPoly env (Poly.mul d1 d2) := by
              simp only [evalPoly, Poly.eval_sub, Poly.eval_mul]
  | mul a b iha ihb =>
    obtain ⟨n1, d1, ht1, hd1, he1⟩ := iha h.1
    obtain ⟨n2, d2, ht2, hd2, he2⟩ := ihb h.2
    refine ⟨Poly.mul n1 n2, Poly.mul d1 d2, ?_,
      evalPoly_mul_ne_zero env hd1 hd2, ?_⟩
    · simp [toFrac, ht1, ht2]
    · have heval :
          eval env (.mul a b) =
            some ((evalPoly env n1 / evalPoly env d1) * (evalPoly env n2 / evalPoly env d2)) := by
        simp [eval, he1, he2]
      rw [heval]
      congr 1
      simp only [evalPoly, Poly.eval_mul]
      field_simp
  | pow b k ih =>
    obtain ⟨n, d, ht, hd, he⟩ := ih h
    refine ⟨Poly.pow n k, Poly.pow d k, ?_, ?_, ?_⟩
    · simp [toFrac, ht]
    · simp only [evalPoly, Poly.eval_pow]
      exact pow_ne_zero k hd
    · have heval :
          eval env (.pow b k) = some ((evalPoly env n / evalPoly env d) ^ k) := by
        simp [eval, he]
      rw [heval]
      congr 1
      simp only [evalPoly, Poly.eval_pow]
      field_simp
  | div a b iha ihb =>
    obtain ⟨n1, d1, ht1, hd1, he1⟩ := iha h.1
    obtain ⟨n2, d2, ht2, hd2, he2⟩ := ihb h.2.1
    have hb0 : eval env b ≠ some 0 := h.2.2
    have hn2d2 : evalPoly env n2 / evalPoly env d2 ≠ 0 := by
      intro hz
      exact hb0 (by simp [he2, hz])
    have hn2 : evalPoly env n2 ≠ 0 := by
      intro hz
      exact hn2d2 (by simp [hz])
    refine ⟨Poly.mul n1 d2, Poly.mul d1 n2, ?_,
      evalPoly_mul_ne_zero env hd1 hn2, ?_⟩
    · simp [toFrac, ht1, ht2]
    · have heval :
          eval env (.div a b) =
            some ((evalPoly env n1 / evalPoly env d1) / (evalPoly env n2 / evalPoly env d2)) := by
        simp [eval, he1, he2, hn2d2]
      rw [heval]
      congr 1
      simp only [evalPoly, Poly.eval_mul]
      field_simp

theorem eval_isSome_of_defined (env : Env ℚ) (e : Expr) (h : Defined env e) :
    ∃ v, eval env e = some v := by
  obtain ⟨_, _, _, _, he⟩ := defined_toFrac_eval env e h
  exact ⟨_, he⟩

/-- Polynomial identity + definedness ⇒ equal evaluations. -/
theorem eval_eq_of_polyEqual_defined (lhs rhs : Expr) (env : Env ℚ)
    (hpoly : polyEqual lhs rhs = true)
    (hl : Defined env lhs) (hr : Defined env rhs) :
    eval env lhs = eval env rhs := by
  obtain ⟨nl, dl, htl, hdl, hel⟩ := defined_toFrac_eval env lhs hl
  obtain ⟨nr, dr, htr, hdr, her⟩ := defined_toFrac_eval env rhs hr
  have hdiff : differenceNumerator lhs rhs = some (Poly.sub (Poly.mul nl dr) (Poly.mul nr dl)) := by
    simp [differenceNumerator, htl, htr]
  have hcomb : Poly.combineLike (Poly.sub (Poly.mul nl dr) (Poly.mul nr dl)) = [] := by
    simp only [polyEqual, hdiff, decide_eq_true_eq] at hpoly
    exact hpoly
  have hnum :
      evalPoly env (Poly.sub (Poly.mul nl dr) (Poly.mul nr dl)) = 0 :=
    Poly.eval_eq_zero_of_combineLike_nil env _ hcomb
  have hcross :
      evalPoly env nl * evalPoly env dr = evalPoly env nr * evalPoly env dl := by
    simp only [evalPoly, Poly.eval_sub, Poly.eval_mul] at hnum ⊢
    exact sub_eq_zero.mp hnum
  have : evalPoly env nl / evalPoly env dl = evalPoly env nr / evalPoly env dr :=
    (div_eq_div_iff hdl hdr).2 hcross
  simp [hel, her, this]

theorem acceptReified_wellFormed (r : Reified) (limit : Nat)
    (h : acceptReified r limit = .ok r) :
    r.expr.wellFormed r.varNames.length = true := by
  cases hw : r.expr.wellFormed r.varNames.length
  · simp [acceptReified, hw] at h
  · rfl

end MathEvidence.IR.RationalExpr
