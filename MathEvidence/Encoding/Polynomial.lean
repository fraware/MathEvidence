/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Algebra.Polynomial.Basic
import Mathlib.RingTheory.MvPolynomial.Basic
import MathEvidence.IR.Polynomial.Syntax
import MathEvidence.IR.Polynomial.Normalize
import MathEvidence.IR.Polynomial.Interpret
import MathEvidence.IR.Polynomial.Soundness

/-!
# Encoding — sparse polynomials (fixed-arity)

Structural quotation lemmas and Mathlib evaluation bridges for ideal membership.
-/

namespace MathEvidence.Encoding.Polynomial

open MathEvidence.IR.Polynomial
open MvPolynomial

/-- Quotation is the typed sparse poly itself (arity fixed by `m`). -/
def WellFormedQuote {m : Nat} (_p : SparsePoly m) : Prop := True

theorem zero_wellFormed (m : Nat) : WellFormedQuote (SparsePoly.zero m) := trivial

theorem eval_zero_bridge (m : Nat) : (SparsePoly.zero m).eval = 0 :=
  SparsePoly.eval_zero m

theorem eval_C_bridge (m : Nat) (c : Int) :
    (SparsePoly.C m c).eval = (C c : MvPolynomial (Fin m) ℤ) :=
  SparsePoly.eval_C m c

theorem eval_X_bridge (m i : Nat) (hi : i < m) :
    (SparsePoly.X m i hi).eval = (MvPolynomial.X ⟨i, hi⟩ : MvPolynomial (Fin m) ℤ) :=
  SparsePoly.eval_X m i hi

theorem eval_add_bridge {m : Nat} (a b : SparsePoly m) :
    (a.add b).eval = a.eval + b.eval :=
  SparsePoly.eval_add a b

theorem eval_mul_bridge {m : Nat} (a b : SparsePoly m) :
    (a.mul b).eval = a.eval * b.eval :=
  SparsePoly.eval_mul a b

theorem eval_neg_bridge {m : Nat} (a : SparsePoly m) :
    a.neg.eval = -a.eval :=
  SparsePoly.eval_neg a

theorem eval_sub_bridge {m : Nat} (a b : SparsePoly m) :
    (a.sub b).eval = a.eval - b.eval :=
  SparsePoly.eval_sub a b

theorem eval_npow_bridge {m : Nat} (a : SparsePoly m) (n : Nat) :
    (a.npow n).eval = a.eval ^ n :=
  SparsePoly.eval_npow a n

/-- Univariate `X` as sparse IR. -/
def sparseX : SparsePoly 1 := SparsePoly.X 1 0

/-- Multivariate `X₀` / `X₁` over `Fin 2`. -/
def sparseX0 : SparsePoly 2 := SparsePoly.X 2 0
def sparseX1 : SparsePoly 2 := SparsePoly.X 2 1

theorem sparseX_eval :
    sparseX.eval = (MvPolynomial.X (0 : Fin 1) : MvPolynomial (Fin 1) ℤ) :=
  SparsePoly.eval_X 1 0 (by decide)

end MathEvidence.Encoding.Polynomial
