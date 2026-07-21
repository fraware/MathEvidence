/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.RationalExpr.Eval
import MathEvidence.IR.RationalExpr.Reify
import MathEvidence.IR.RationalExpr.Syntax

/-!
# Encoding — rational expressions

Visible home for the semantic bridge between executable `RationalExpr` IR and
Mathlib `ℚ` evaluation. Checkers and tactics import this module when they need
the interpretation relation, rather than inlining ad-hoc bridges.
-/

namespace MathEvidence.Encoding.Rat

open MathEvidence.IR.RationalExpr

/-- Quotation interpretation: IR expression evaluates to a concrete rational. -/
def Interprets (quoted : Expr) (env : Env ℚ) (value : ℚ) : Prop :=
  eval env quoted = some value

/-- Variable interpretation is the environment lookup. -/
theorem interprets_var (env : Env ℚ) (i : Nat) :
    Interprets (.var i) env (env i) := rfl

/-- Integer literal interpretation. -/
theorem interprets_int (env : Env ℚ) (n : Int) :
    Interprets (.int n) env (↑n) := rfl

/-- Addition preserves interpretation. -/
theorem interprets_add (env : Env ℚ) (a b : Expr) (va vb : ℚ)
    (ha : Interprets a env va) (hb : Interprets b env vb) :
    Interprets (.add a b) env (va + vb) := by
  simp [Interprets, eval] at ha hb ⊢
  simp [ha, hb]

/-- Multiplication preserves interpretation. -/
theorem interprets_mul (env : Env ℚ) (a b : Expr) (va vb : ℚ)
    (ha : Interprets a env va) (hb : Interprets b env vb) :
    Interprets (.mul a b) env (va * vb) := by
  simp [Interprets, eval] at ha hb ⊢
  simp [ha, hb]

/-- Division preserves interpretation under a nonzero denominator value. -/
theorem interprets_div (env : Env ℚ) (n d : Expr) (vn vd : ℚ)
    (hn : Interprets n env vn) (hd : Interprets d env vd) (hvd : vd ≠ 0) :
    Interprets (.div n d) env (vn / vd) := by
  simp [Interprets, eval] at hn hd ⊢
  simp [hn, hd, hvd]

/-- Rejected reifications are not silently accepted. -/
theorem acceptReified_error_ne_ok {r : Reified} {limit : Nat} {err : Reject}
    (h : acceptReified r limit = .error err) :
    ¬ ∃ r', acceptReified r limit = .ok r' := by
  intro ⟨r', hok⟩
  simp [h] at hok

/-- Concrete bridge: `x / 1` interprets as `x` at env mapping 0 ↦ x. -/
theorem interprets_div_by_one (x : ℚ) :
    Interprets (.div (.var 0) (.int 1)) (fun i => if i = 0 then x else 0) (x / 1) := by
  simp [Interprets, eval]

end MathEvidence.Encoding.Rat
