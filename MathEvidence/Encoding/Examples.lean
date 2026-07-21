/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Data.Matrix.Basic
import MathEvidence.Encoding.Finite
import MathEvidence.Encoding.Matrix
import MathEvidence.Encoding.Polynomial
import MathEvidence.IR.MatrixExpr.Eval
import MathEvidence.IR.Polynomial.Syntax

/-!
# Encoding examples

Compile-time regression theorems for Mathlib quotation bridges.
If densify/quote or Fin/Bool/sparse evaluation identities break, this module
fails to build.
-/

namespace MathEvidence.Encoding.Examples

open MathEvidence.Encoding.Matrix
open MathEvidence.Encoding.Finite
open MathEvidence.Encoding.Polynomial
open MathEvidence.IR.MatrixExpr (evalMatrix? evalVector?)
open MathEvidence.IR.Polynomial (SparsePoly)

/-- densify ∘ interpret ∘ quote = id on a concrete 2×2 matrix. -/
theorem matrix_quote_roundtrip_2x2 :
    let A : _root_.Matrix (Fin 2) (Fin 2) ℚ := fun
      | ⟨0, _⟩, ⟨0, _⟩ => 1
      | ⟨0, _⟩, ⟨1, _⟩ => (1 : ℚ) / 2
      | ⟨1, _⟩, ⟨0, _⟩ => -3
      | ⟨1, _⟩, ⟨1, _⟩ => 4
    densifyMatrix ((evalMatrix? (quoteMatrix A)).getD []) = A :=
  densify_interpret_quote _

/-- Vector densify ∘ interpret ∘ quote. -/
theorem vector_quote_roundtrip :
    let v : Fin 3 → ℚ := fun
      | ⟨0, _⟩ => 1
      | ⟨1, _⟩ => -1
      | ⟨2, _⟩ => (2 : ℚ) / 3
    densifyVector ((evalVector? (quoteVector v)).getD []) = v :=
  densifyVector_interpret_quote _

/-- Bool CEX Meta body equals Lean predicate. -/
theorem bool_pred_matches (b : Bool) :
    InterpretsPred (.eq (.var 0) (.lit (.bool true))) (envBool b) (b == true) :=
  interprets_bool_eq_true b

/-- Fin CEX Meta body equals Lean predicate. -/
theorem fin_pred_matches (x : Fin 3) :
    InterpretsPred (.eq (.var 0) (.lit (.nat 0))) (envFin x) (decide (x.val = 0)) :=
  interprets_fin3_eq_zero x

/-- Bounded-Nat implication body equals Lean implication. -/
theorem nat_bound_pred_matches (x : Nat) :
    InterpretsPred
      (impliesPred (.le (.var 0) (.lit (.nat 3))) (.eq (.var 0) (.lit (.nat 0))))
      (envNat x)
      (decide (x ≤ 3 → x = 0)) :=
  interprets_nat_le_imp_eq x 3 0

/-- Univariate sparse IR matches `Polynomial.eval`. -/
theorem poly_C_add_X_matches (c x : Int) :
    InterpretsAt (SparsePoly.add (sparseC1 c) sparseX) [x]
      ((_root_.Polynomial.eval x) ((_root_.Polynomial.C c) + _root_.Polynomial.X)) :=
  interprets_sparseC1_add_X c x

/-- MvPolynomial Fin-2 product matches sparse IR. -/
theorem mv_X0_mul_X1_matches (a b : Int) :
    InterpretsAt (SparsePoly.mul sparseX0 sparseX1) [a, b]
      (MvPolynomial.eval (fun i : Fin 2 => if i = 0 then a else b)
        ((MvPolynomial.X (0 : Fin 2) : MvPolynomial (Fin 2) ℤ) *
          MvPolynomial.X (1 : Fin 2))) :=
  interprets_sparseX0_mul_X1 a b

end MathEvidence.Encoding.Examples
