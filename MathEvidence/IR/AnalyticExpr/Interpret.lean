/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic
import Mathlib.Data.Real.Basic
import MathEvidence.IR.AnalyticExpr.Syntax
import MathEvidence.IR.AnalyticExpr.Domain

/-!
# Analytic interpretation (ME-RV-050)

One-variable semantics: `Expr.interpret : Expr → ℝ → ℝ`.
Variable indices other than `0` interpret as the zero function; the checker
rejects them via `Expr.isUnivariate` before soundness applies.
-/

namespace MathEvidence.IR.AnalyticExpr

open Real

noncomputable section

/-- Interpretation of an analytic expression as a real function of one variable.

Marked `noncomputable` because `ℝ` field operations are not executable. -/
def Expr.interpret : Expr → ℝ → ℝ
  | .variable 0 => fun x => x
  | .variable _ => fun _ => 0
  | .const q => fun _ => (q : ℝ)
  | .add a b => fun x => a.interpret x + b.interpret x
  | .sub a b => fun x => a.interpret x - b.interpret x
  | .mul a b => fun x => a.interpret x * b.interpret x
  | .div n d => fun x => n.interpret x / d.interpret x
  | .inv a => fun x => (a.interpret x)⁻¹
  | .neg a => fun x => -(a.interpret x)
  | .pow a k => fun x => (a.interpret x) ^ k
  | .sin a => fun x => Real.sin (a.interpret x)
  | .cos a => fun x => Real.cos (a.interpret x)
  | .exp a => fun x => Real.exp (a.interpret x)
  | .log a => fun x => Real.log (a.interpret x)

/-- Pointwise satisfaction of a single domain obligation. -/
def DomainObligation.holds : DomainObligation → ℝ → Prop
  | .nonzero e, x => e.interpret x ≠ 0
  | .positive e, x => 0 < e.interpret x
  | .member d e, x => e.interpret x ∈ d

/-- All listed obligations hold at `x`. -/
def SatisfiesObligations (obls : Array DomainObligation) (x : ℝ) : Prop :=
  ∀ i : Fin obls.size, (obls[i]).holds x

/-- Convenience: list form. -/
def SatisfiesObligationsList (obls : List DomainObligation) (x : ℝ) : Prop :=
  ∀ o ∈ obls, o.holds x

theorem SatisfiesObligations_of_list (obls : Array DomainObligation) (x : ℝ)
    (h : SatisfiesObligationsList obls.toList x) :
    SatisfiesObligations obls x := by
  intro i
  exact h (obls[i]) (by simp [Array.getElem_mem_toList])

@[simp] theorem interpret_variable0 : Expr.interpret (.variable 0) = id := rfl

@[simp] theorem interpret_const (q : ℚ) :
    Expr.interpret (.const q) = fun _ => (q : ℝ) := rfl

@[simp] theorem interpret_add (a b : Expr) :
    Expr.interpret (.add a b) = fun x => a.interpret x + b.interpret x := rfl

@[simp] theorem interpret_sub (a b : Expr) :
    Expr.interpret (.sub a b) = fun x => a.interpret x - b.interpret x := rfl

@[simp] theorem interpret_mul (a b : Expr) :
    Expr.interpret (.mul a b) = fun x => a.interpret x * b.interpret x := rfl

@[simp] theorem interpret_div (n d : Expr) :
    Expr.interpret (.div n d) = fun x => n.interpret x / d.interpret x := rfl

@[simp] theorem interpret_inv (a : Expr) :
    Expr.interpret (.inv a) = fun x => (a.interpret x)⁻¹ := rfl

@[simp] theorem interpret_neg (a : Expr) :
    Expr.interpret (.neg a) = fun x => -(a.interpret x) := rfl

@[simp] theorem interpret_pow (a : Expr) (k : Nat) :
    Expr.interpret (.pow a k) = fun x => (a.interpret x) ^ k := rfl

@[simp] theorem interpret_sin (a : Expr) :
    Expr.interpret (.sin a) = fun x => Real.sin (a.interpret x) := rfl

@[simp] theorem interpret_cos (a : Expr) :
    Expr.interpret (.cos a) = fun x => Real.cos (a.interpret x) := rfl

@[simp] theorem interpret_exp (a : Expr) :
    Expr.interpret (.exp a) = fun x => Real.exp (a.interpret x) := rfl

@[simp] theorem interpret_log (a : Expr) :
    Expr.interpret (.log a) = fun x => Real.log (a.interpret x) := rfl

end

end MathEvidence.IR.AnalyticExpr
