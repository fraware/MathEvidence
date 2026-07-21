/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Data.Rat.Defs

namespace MathEvidence.IR.AnalyticExpr

/-!
# AnalyticExpr syntax

Executable IR for the analytic-calculus vertical. Interpretation targets Mathlib
`HasDerivAt` / `HasDerivWithinAt`. Division and log carry explicit domain
conditions (nonzero / positivity) at the Encoding/checker boundary.
-/

/-- Analytic expression language for the v0.1 fragment. -/
inductive Expr where
  | variable (idx : Nat)
  | const (q : ℚ)
  | add (lhs rhs : Expr)
  | sub (lhs rhs : Expr)
  | mul (lhs rhs : Expr)
  | div (num den : Expr)
  | neg (arg : Expr)
  | pow (base : Expr) (exp : Nat)
  | sin (arg : Expr)
  | exp (arg : Expr)
  | log (arg : Expr)
  deriving DecidableEq, Repr, Inhabited

/-- Structural size for resource limits. -/
def Expr.size : Expr → Nat
  | .variable _ | .const _ => 1
  | .add lhs rhs | .sub lhs rhs | .mul lhs rhs | .div lhs rhs =>
      1 + lhs.size + rhs.size
  | .neg arg | .sin arg | .exp arg | .log arg => 1 + arg.size
  | .pow base _ => 1 + base.size

def defaultSizeLimit : Nat := 10000

def Expr.withinSizeLimit (e : Expr) (limit : Nat := defaultSizeLimit) : Bool :=
  decide (e.size ≤ limit)

end MathEvidence.IR.AnalyticExpr
