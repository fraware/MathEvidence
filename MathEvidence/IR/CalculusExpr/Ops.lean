/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.RationalExpr.Poly
import MathEvidence.IR.RationalExpr.Syntax
import MathEvidence.IR.CalculusExpr.Syntax

namespace MathEvidence.IR.CalculusExpr

open MathEvidence.IR.RationalExpr

/-!
Formal (syntactic) calculus operations over `RationalExpr`.

These are untrusted relative to transcendental analysis; the checker accepts only
when polynomial-numerator identity holds after formal differentiation / substitution.
-/

/-- Formal derivative with respect to variable index `xIdx`. -/
def formalDeriv (xIdx : Nat) : Expr → Expr
  | .var i => if i = xIdx then .int 1 else .int 0
  | .int _ | .rat _ _ => .int 0
  | .neg e => .neg (formalDeriv xIdx e)
  | .add a b => .add (formalDeriv xIdx a) (formalDeriv xIdx b)
  | .sub a b => .sub (formalDeriv xIdx a) (formalDeriv xIdx b)
  | .mul a b =>
    .add (.mul (formalDeriv xIdx a) b) (.mul a (formalDeriv xIdx b))
  | .pow _ 0 => .int 0
  | .pow b (k + 1) =>
    .mul (.mul (.int (Int.ofNat (k + 1))) (.pow b k)) (formalDeriv xIdx b)
  | .div n d =>
    .div
      (.sub (.mul (formalDeriv xIdx n) d) (.mul n (formalDeriv xIdx d)))
      (.pow d 2)

/-- Substitute variable `xIdx` with `replacement` throughout an expression. -/
def formalSubst (xIdx : Nat) (replacement : Expr) : Expr → Expr
  | .var i => if i = xIdx then replacement else .var i
  | .int n => .int n
  | .rat n d => .rat n d
  | .neg e => .neg (formalSubst xIdx replacement e)
  | .add a b => .add (formalSubst xIdx replacement a) (formalSubst xIdx replacement b)
  | .sub a b => .sub (formalSubst xIdx replacement a) (formalSubst xIdx replacement b)
  | .mul a b => .mul (formalSubst xIdx replacement a) (formalSubst xIdx replacement b)
  | .pow b k => .pow (formalSubst xIdx replacement b) k
  | .div n d => .div (formalSubst xIdx replacement n) (formalSubst xIdx replacement d)

/-- Shift independent variable: `e[x ↦ x + 1]`. -/
def formalShift (xIdx : Nat) (e : Expr) : Expr :=
  formalSubst xIdx (.add (.var xIdx) (.int 1)) e

/-- True when two rational expressions are identical as rational functions. -/
def exprEqual (a b : Expr) : Bool :=
  polyEqual a b

/-- True when `e` is identically zero as a rational function. -/
def exprZero (e : Expr) : Bool :=
  polyEqual e (.int 0)

/-- Derivative-candidate obligation: `formalDeriv expr = candidate`. -/
def derivativeOk (xIdx : Nat) (expr candidate : Expr) : Bool :=
  exprEqual (formalDeriv xIdx expr) candidate

/-- Antiderivative-candidate obligation: `formalDeriv F = f` (not completeness). -/
def antiderivativeOk (xIdx : Nat) (f F : Expr) : Bool :=
  exprEqual (formalDeriv xIdx F) f

/-- Recurrence identity: `u(n+1) = rhs[u ↦ u(n)]` for closed form `u`.

`uVarIdx` is the placeholder index for the previous term inside `rhs`. -/
def recurrenceOk (nIdx uVarIdx : Nat) (closedForm rhs : Expr) : Bool :=
  let next := formalShift nIdx closedForm
  let rhsEval := formalSubst uVarIdx closedForm rhs
  exprEqual next rhsEval

/-- First-order ODE candidate: `y' = f(x, y)` after substituting the solution for `y`.

`yVarIdx` is the dependent-variable placeholder inside `odeRhs`. -/
def odeResidualOk (xIdx yVarIdx : Nat) (solution odeRhs : Expr) : Bool :=
  let yp := formalDeriv xIdx solution
  let fSub := formalSubst yVarIdx solution odeRhs
  exprEqual yp fSub

/-- Initial condition: `solution[x ↦ point] = value`. -/
def icOk (xIdx : Nat) (solution : Expr) (ic : InitialCondition) : Bool :=
  exprEqual (formalSubst xIdx ic.point solution) ic.value

def icsOk (xIdx : Nat) (solution : Expr) (ics : List InitialCondition) : Bool :=
  ics.all (icOk xIdx solution)

end MathEvidence.IR.CalculusExpr
