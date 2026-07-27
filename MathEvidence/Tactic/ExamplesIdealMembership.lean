/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Algebra.MvPolynomial.CommRing
import Mathlib.RingTheory.Ideal.Span
import Mathlib.RingTheory.MvPolynomial.Basic
import MathEvidence.Checkers.IdealMembership.Check
import MathEvidence.Checkers.IdealMembership.Soundness
import MathEvidence.IR.Polynomial.Normalize
import MathEvidence.IR.Polynomial.Soundness
import MathEvidence.Tactic.IdealMembership

/-!
# Ideal membership examples (ME-RV-033/034)

Authority is `checkMembership_sound` / `mem_span_*_of_check` and reifier
congruence lemmas. Independent `ring` is not the theorem authority.
-/

namespace MathEvidence.Tactic.Examples.IdealMembership

open MvPolynomial
open MathEvidence.IR.Polynomial
open MathEvidence.Checkers.IdealMembership

set_option maxHeartbeats 800000

private def fX2m1 : SparsePoly 1 :=
  (SparsePoly.X 1 0).npow 2 |>.sub (SparsePoly.C 1 1)

private def gXm1 : SparsePoly 1 :=
  (SparsePoly.X 1 0).sub (SparsePoly.C 1 1)

private def qXp1 : SparsePoly 1 :=
  (SparsePoly.X 1 0).add (SparsePoly.C 1 1)

/-- IR authority: accepted witness => span membership (no independent ring). -/
theorem ir_x2_minus_1_span :
    fX2m1.eval ∈
      Ideal.span (Set.range fun i : Fin 1 => (#[gXm1][i]).eval) :=
  checkMembership_sound fX2m1 #[gXm1] #[qXp1] (by native_decide)

/-- Reifier congruence lemmas are real interpretation equalities (ME-RV-033). -/
theorem reify_add_mul_X_sample :
    ((SparsePoly.X (m := 2) 0).mul (SparsePoly.X (m := 2) 1)).eval =
      (X (0 : Fin 2) : MvPolynomial (Fin 2) ℤ) * X (1 : Fin 2) :=
  reify_mul_eq _ _ _ _
    (SparsePoly.eval_X 2 0 (by decide))
    (SparsePoly.eval_X 2 1 (by decide))

theorem reify_npow_X_sample :
    ((SparsePoly.X (m := 1) 0).npow 2).eval =
      (X (0 : Fin 1) : MvPolynomial (Fin 1) ℤ) ^ 2 :=
  reify_npow_eq _ 2 _ (SparsePoly.eval_X 1 0 (by decide))

theorem reify_add_eq_sample :
    ((SparsePoly.X (m := 1) 0).add (SparsePoly.C 1 1)).eval =
      (X (0 : Fin 1) : MvPolynomial (Fin 1) ℤ) + MvPolynomial.C 1 :=
  reify_add_eq _ _ _ _
    (SparsePoly.eval_X 1 0 (by decide))
    (SparsePoly.eval_C 1 1)

theorem ir_x2m1_accepts :
    MathEvidence.Checkers.IdealMembership.example_x2_minus_1.check = true :=
  MathEvidence.Checkers.IdealMembership.example_x2_minus_1_accepts

/-- Mathlib singleton span via transport theorem (no independent ring). -/
theorem mathlib_x2_minus_1_span :
    ((SparsePoly.X (m := 1) 0).npow 2 |>.sub (SparsePoly.C 1 1)).eval ∈
      Ideal.span {((SparsePoly.X (m := 1) 0).sub (SparsePoly.C 1 1)).eval} :=
  mem_span_singleton_of_check fX2m1 gXm1 qXp1 _ _
    rfl rfl (by native_decide)

/-- Mathlib two-generator span via transport theorem. -/
theorem mathlib_xy_span :
    ((SparsePoly.X (m := 2) 0).mul (SparsePoly.X (m := 2) 1)).eval ∈
      Ideal.span
        { (SparsePoly.X (m := 2) 0).eval
        , (SparsePoly.X (m := 2) 1).eval } :=
  mem_span_pair_of_check
    ((SparsePoly.X (m := 2) 0).mul (SparsePoly.X (m := 2) 1))
    (SparsePoly.X 2 0) (SparsePoly.X 2 1)
    (SparsePoly.X 2 1) (SparsePoly.zero 2)
    _ _ _
    rfl rfl rfl (by native_decide)

/-- Adversarial: wrong multipliers are rejected by the checker (not by ring). -/
theorem adversarial_wrong_multiplier_rejected :
    checkMembership fX2m1 #[gXm1] #[SparsePoly.C 1 1] = false := by
  native_decide

/-- Adversarial: arity mismatch is rejected. -/
theorem adversarial_arity_mismatch_rejected :
    checkMembership fX2m1 #[gXm1, gXm1] #[qXp1] = false := by
  native_decide

/-- Adversarial: swapped generators without matching multipliers rejected. -/
theorem adversarial_swapped_gens_rejected :
    checkMembership
        ((SparsePoly.X (m := 2) 0).mul (SparsePoly.X (m := 2) 1))
        #[SparsePoly.X 2 0, SparsePoly.X 2 1]
        #[SparsePoly.C 2 0, SparsePoly.C 2 1] = false := by
  native_decide

/-! ## Live Meta matcher (ME-RV-034)

Ordinary Mathlib goals closed by `mathevidence_ideal` via Meta matching +
`checkMembership_sound` / `mem_span_*_of_check` + reifier transport.
-/

/-- Live: `X^2 - 1 ∈ Ideal.span {X - 1}` via Meta + checker authority. -/
theorem live_x2_minus_1_span :
    ((X (0 : Fin 1) : MvPolynomial (Fin 1) ℤ) ^ 2 - 1) ∈
      Ideal.span {(X (0 : Fin 1) : MvPolynomial (Fin 1) ℤ) - 1} := by
  mathevidence_ideal

/-- Live: `X * Y ∈ Ideal.span {X, Y}` via Meta + checker authority. -/
theorem live_xy_span :
    ((X (0 : Fin 2) : MvPolynomial (Fin 2) ℤ) * X (1 : Fin 2)) ∈
      Ideal.span
        { (X (0 : Fin 2) : MvPolynomial (Fin 2) ℤ)
        , (X (1 : Fin 2) : MvPolynomial (Fin 2) ℤ) } := by
  mathevidence_ideal

/-- Live Fin-3: `X*Y*Z ∈ Ideal.span {X, Y, Z}` via Meta + `mem_span_triple_of_check`. -/
theorem live_xyz_span :
    ((X (0 : Fin 3) : MvPolynomial (Fin 3) ℤ) * X (1 : Fin 3) * X (2 : Fin 3)) ∈
      Ideal.span
        { (X (0 : Fin 3) : MvPolynomial (Fin 3) ℤ)
        , (X (1 : Fin 3) : MvPolynomial (Fin 3) ℤ)
        , (X (2 : Fin 3) : MvPolynomial (Fin 3) ℤ) } := by
  mathevidence_ideal

/-- Fin-4 IR authority: product in four-generator `Set.range` span (ME-RV-034). -/
theorem ir_four_var_product_span :
    ((SparsePoly.X (m := 4) 0).mul (SparsePoly.X 4 1) |>.mul (SparsePoly.X 4 2)).eval ∈
      Ideal.span
        (Set.range fun i : Fin 4 =>
          (#[SparsePoly.X 4 0, SparsePoly.X 4 1, SparsePoly.X 4 2, SparsePoly.X 4 3][i]).eval) :=
  checkMembership_sound
    ((SparsePoly.X (m := 4) 0).mul (SparsePoly.X 4 1) |>.mul (SparsePoly.X 4 2))
    #[SparsePoly.X 4 0, SparsePoly.X 4 1, SparsePoly.X 4 2, SparsePoly.X 4 3]
    #[(SparsePoly.X 4 1).mul (SparsePoly.X 4 2), SparsePoly.zero 4, SparsePoly.zero 4,
      SparsePoly.zero 4]
    (by native_decide)

/-- Adversarial: X+1 is not a generator witness for X^2-1 (checker reject). -/
theorem adversarial_x_plus_1_rejected :
    checkMembership fX2m1
      #[(SparsePoly.X (m := 1) 0).add (SparsePoly.C 1 1)]
      #[qXp1] = false := by
  native_decide

/-- Adversarial: oversized / arity-mismatched multiplier list rejected. -/
theorem adversarial_empty_multipliers_rejected :
    checkMembership fX2m1 #[gXm1] (#[] : Array (SparsePoly 1)) = false := by
  native_decide

/-- Adversarial: Fin-3 wrong witness for xyz membership. -/
theorem adversarial_xyz_wrong_mult_rejected :
    checkMembership
        ((SparsePoly.X (m := 3) 0).mul (SparsePoly.X 3 1) |>.mul (SparsePoly.X 3 2))
        #[SparsePoly.X 3 0, SparsePoly.X 3 1, SparsePoly.X 3 2]
        #[SparsePoly.C 3 1, SparsePoly.C 3 1, SparsePoly.C 3 1] = false := by
  native_decide

end MathEvidence.Tactic.Examples.IdealMembership
