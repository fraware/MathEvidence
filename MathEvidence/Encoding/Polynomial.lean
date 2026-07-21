/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Algebra.Polynomial.Basic
import Mathlib.Algebra.Polynomial.Eval.Defs
import Mathlib.RingTheory.MvPolynomial.Basic
import MathEvidence.IR.Polynomial.Syntax

/-!
# Encoding — sparse polynomials

Reusable structural quotation lemmas for ideal-membership IR, plus Mathlib
evaluation identity bridges used by Ideal Meta (`Polynomial` / `MvPolynomial`).
-/

namespace MathEvidence.Encoding.Polynomial

open MathEvidence.IR.Polynomial

/-- Quotation is structurally well-formed for the declared variable count. -/
def WellFormedQuote (p : SparsePoly) : Prop :=
  p.wellFormed = true

/-- Point evaluation of a monomial at an integer assignment. -/
def evalMonomial (exps : List Nat) (xs : List Int) : Int :=
  List.zip exps xs |>.foldl (fun acc (e, x) => acc * x ^ e) 1

/-- Point evaluation of a sparse polynomial (structural semantics). -/
def evalSparse (p : SparsePoly) (xs : List Int) : Option Int :=
  if xs.length ≠ p.varCount then none
  else
    some <|
      p.terms.foldl
        (fun acc t => acc + t.coefficient * evalMonomial t.monomial.exponents xs)
        0

/-- Quotation interprets at a point when lengths match. -/
def InterpretsAt (p : SparsePoly) (xs : List Int) (v : Int) : Prop :=
  evalSparse p xs = some v

theorem zero_wellFormed (n : Nat) :
    WellFormedQuote (SparsePoly.zero n) := by
  simp [WellFormedQuote, SparsePoly.zero, SparsePoly.wellFormed]

theorem term_wellFormed_iff (varCount : Nat) (t : Term) :
    Term.wellFormed varCount t = decide (t.monomial.exponents.length = varCount) :=
  rfl

theorem zero_interprets_at (n : Nat) (xs : List Int) (h : xs.length = n) :
    InterpretsAt (SparsePoly.zero n) xs 0 := by
  simp [InterpretsAt, evalSparse, SparsePoly.zero, h]

/-- Constant polynomial `c` in zero variables. -/
def const0 (c : Int) : SparsePoly :=
  { varCount := 0, terms := [{ coefficient := c, monomial := ⟨[]⟩ }] }

theorem const0_wellFormed (c : Int) :
    WellFormedQuote (const0 c) := by
  simp [WellFormedQuote, const0, SparsePoly.wellFormed, Term.wellFormed]

theorem const0_interprets (c : Int) :
    InterpretsAt (const0 c) [] c := by
  simp [InterpretsAt, evalSparse, const0, evalMonomial]

/-- Length mismatch rejects interpretation. -/
theorem interprets_at_length_mismatch (p : SparsePoly) (xs : List Int) (v : Int)
    (h : xs.length ≠ p.varCount) :
    ¬ InterpretsAt p xs v := by
  simp [InterpretsAt, evalSparse, h]

/-- Same-varCount add of well-formed polys stays well-formed (direct unfold). -/
theorem add_zero_right_wellFormed (a : SparsePoly) (ha : WellFormedQuote a) :
    WellFormedQuote (SparsePoly.add a (SparsePoly.zero a.varCount)) := by
  simp [WellFormedQuote, SparsePoly.add, SparsePoly.zero, SparsePoly.wellFormed] at *
  exact ha

/-! ## Mathlib evaluation bridges (Ideal Meta) -/

/-- Univariate constant `C c` as sparse IR (`X⁰`). -/
def sparseC1 (c : Int) : SparsePoly :=
  { varCount := 1, terms := [{ coefficient := c, monomial := ⟨[0]⟩ }] }

/-- Univariate indeterminate `X`. -/
def sparseX : SparsePoly :=
  { varCount := 1, terms := [{ coefficient := 1, monomial := ⟨[1]⟩ }] }

/-- Multivariate `X₀` over `Fin 2`. -/
def sparseX0 : SparsePoly :=
  { varCount := 2, terms := [{ coefficient := 1, monomial := ⟨[1, 0]⟩ }] }

/-- Multivariate `X₁` over `Fin 2`. -/
def sparseX1 : SparsePoly :=
  { varCount := 2, terms := [{ coefficient := 1, monomial := ⟨[0, 1]⟩ }] }

theorem sparseC1_wellFormed (c : Int) :
    WellFormedQuote (sparseC1 c) := by
  simp [WellFormedQuote, sparseC1, SparsePoly.wellFormed, Term.wellFormed]

theorem sparseX_wellFormed :
    WellFormedQuote sparseX := by
  simp [WellFormedQuote, sparseX, SparsePoly.wellFormed, Term.wellFormed]

theorem sparseX0_wellFormed :
    WellFormedQuote sparseX0 := by
  simp [WellFormedQuote, sparseX0, SparsePoly.wellFormed, Term.wellFormed]

theorem sparseX1_wellFormed :
    WellFormedQuote sparseX1 := by
  simp [WellFormedQuote, sparseX1, SparsePoly.wellFormed, Term.wellFormed]

/-- Sparse `C c` evaluates like `Polynomial.eval (Polynomial.C c)`. -/
theorem interprets_sparseC1 (c x : Int) :
    InterpretsAt (sparseC1 c) [x] ((_root_.Polynomial.eval x) (_root_.Polynomial.C c)) := by
  simp [InterpretsAt, evalSparse, sparseC1, evalMonomial, _root_.Polynomial.eval_C]

/-- Sparse `X` evaluates like `Polynomial.eval Polynomial.X`. -/
theorem interprets_sparseX (x : Int) :
    InterpretsAt sparseX [x] ((_root_.Polynomial.eval x) (_root_.Polynomial.X)) := by
  simp [InterpretsAt, evalSparse, sparseX, evalMonomial, _root_.Polynomial.eval_X]

/-- Sparse `C c + X` evaluates like Mathlib `C c + X` (Ideal Meta witness shape). -/
theorem interprets_sparseC1_add_X (c x : Int) :
    InterpretsAt (SparsePoly.add (sparseC1 c) sparseX) [x]
      ((_root_.Polynomial.eval x) ((_root_.Polynomial.C c) + _root_.Polynomial.X)) := by
  simp [InterpretsAt, evalSparse, SparsePoly.add, sparseC1, sparseX, evalMonomial,
    _root_.Polynomial.eval_add, _root_.Polynomial.eval_C, _root_.Polynomial.eval_X]

/-- Sparse `X · X` evaluates like Mathlib `X * X`. -/
theorem interprets_sparseX_mul_X (x : Int) :
    InterpretsAt (SparsePoly.mul sparseX sparseX) [x]
      ((_root_.Polynomial.eval x) ((_root_.Polynomial.X) * _root_.Polynomial.X)) := by
  simp [InterpretsAt, evalSparse, SparsePoly.mul, sparseX, evalMonomial,
    _root_.Polynomial.eval_mul, _root_.Polynomial.eval_X]
  ring

/-- Sparse `X₀` evaluates like `MvPolynomial.X (0 : Fin 2)`. -/
theorem interprets_sparseX0 (a b : Int) :
    InterpretsAt sparseX0 [a, b]
      (MvPolynomial.eval (fun i : Fin 2 => if i = 0 then a else b)
        (MvPolynomial.X (0 : Fin 2) : MvPolynomial (Fin 2) ℤ)) := by
  simp [InterpretsAt, evalSparse, sparseX0, evalMonomial, MvPolynomial.eval_X]

/-- Sparse `X₁` evaluates like `MvPolynomial.X (1 : Fin 2)`. -/
theorem interprets_sparseX1 (a b : Int) :
    InterpretsAt sparseX1 [a, b]
      (MvPolynomial.eval (fun i : Fin 2 => if i = 0 then a else b)
        (MvPolynomial.X (1 : Fin 2) : MvPolynomial (Fin 2) ℤ)) := by
  simp [InterpretsAt, evalSparse, sparseX1, evalMonomial, MvPolynomial.eval_X]

/-- Sparse product `X₀ · X₁` matches Mathlib product evaluation (membership witness). -/
theorem interprets_sparseX0_mul_X1 (a b : Int) :
    InterpretsAt (SparsePoly.mul sparseX0 sparseX1) [a, b]
      (MvPolynomial.eval (fun i : Fin 2 => if i = 0 then a else b)
        ((MvPolynomial.X (0 : Fin 2) : MvPolynomial (Fin 2) ℤ) * MvPolynomial.X (1 : Fin 2))) := by
  simp [InterpretsAt, evalSparse, SparsePoly.mul, sparseX0, sparseX1, evalMonomial,
    MvPolynomial.eval_mul, MvPolynomial.eval_X]

/-- Membership witness identity: `X * C c` sparse eval matches Mathlib. -/
theorem interprets_membership_witness_X_times_C (c x : Int) :
    InterpretsAt (SparsePoly.mul sparseX (sparseC1 c)) [x]
      ((_root_.Polynomial.eval x) ((_root_.Polynomial.X) * _root_.Polynomial.C c)) := by
  simp [InterpretsAt, evalSparse, SparsePoly.mul, sparseX, sparseC1, evalMonomial,
    _root_.Polynomial.eval_mul, _root_.Polynomial.eval_X, _root_.Polynomial.eval_C]
  ring

end MathEvidence.Encoding.Polynomial
