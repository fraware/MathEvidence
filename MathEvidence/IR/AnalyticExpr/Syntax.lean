/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Data.Rat.Defs

namespace MathEvidence.IR.AnalyticExpr

/-!
# AnalyticExpr syntax

Executable IR for the analytic-calculus vertical (ME-RV-050). Interpretation
targets Mathlib `HasDerivAt` / `HasDerivWithinAt` on `ℝ → ℝ`.

Public support is the one-variable fragment (`variable 0`). Multivariate
indices are rejected by the checker. `cos` appears so derivative syntax of
`sin` stays inside the IR; `inv` is the explicit reciprocal constructor used
by the inverse derivation rule.
-/

/-- Analytic expression language for the one-variable fragment. -/
inductive Expr where
  | variable (idx : Nat)
  | const (q : ℚ)
  | add (lhs rhs : Expr)
  | sub (lhs rhs : Expr)
  | mul (lhs rhs : Expr)
  | div (num den : Expr)
  | inv (arg : Expr)
  | neg (arg : Expr)
  | pow (base : Expr) (exp : Nat)
  | sin (arg : Expr)
  | cos (arg : Expr)
  | exp (arg : Expr)
  | log (arg : Expr)
  deriving DecidableEq, Repr, Inhabited

/-- Structural size for resource limits. -/
def Expr.size : Expr → Nat
  | .variable _ | .const _ => 1
  | .add lhs rhs | .sub lhs rhs | .mul lhs rhs | .div lhs rhs =>
      1 + lhs.size + rhs.size
  | .inv arg | .neg arg | .sin arg | .cos arg | .exp arg | .log arg =>
      1 + arg.size
  | .pow base _ => 1 + base.size

def defaultSizeLimit : Nat := 10000

def Expr.withinSizeLimit (e : Expr) (limit : Nat := defaultSizeLimit) : Bool :=
  decide (e.size ≤ limit)

/-- True when every variable index is `0` (univariate public fragment). -/
def Expr.isUnivariate : Expr → Bool
  | .variable i => decide (i = 0)
  | .const _ => true
  | .add a b | .sub a b | .mul a b | .div a b => a.isUnivariate && b.isUnivariate
  | .inv a | .neg a | .sin a | .cos a | .exp a | .log a => a.isUnivariate
  | .pow a _ => a.isUnivariate

/-- True when the expression is a rational constant leaf. -/
def Expr.isConst : Expr → Bool
  | .const _ => true
  | _ => false

/-- Extract a rational constant, if any. -/
def Expr.constVal? : Expr → Option ℚ
  | .const q => some q
  | _ => none

end MathEvidence.IR.AnalyticExpr
