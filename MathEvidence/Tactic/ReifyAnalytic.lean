/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import Mathlib.Data.Rat.Defs
import Mathlib.Data.Real.Basic
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic
import MathEvidence.IR.AnalyticExpr.Syntax
import MathEvidence.IR.AnalyticExpr.Interpret

/-!
# Restricted AnalyticExpr Meta reifier (ME-RV-054)

Supports the one-variable public fragment:

* polynomial / rational expressions over a single `ℝ` free variable;
* `Real.sin`, `Real.exp`, `Real.log` (domain obligations are *not* invented here —
  callers must attach them to certificates);
* explicit nonzero assumptions are recorded only as structural obligations on
  the resulting IR, never as trusted Booleans.

Multivariate expressions are rejected.
-/

namespace MathEvidence.Tactic.ReifyAnalytic

open Lean Meta
open MathEvidence.IR.AnalyticExpr

inductive Reject where
  | unsupportedExpression (detail : String)
  | unsupportedType (detail : String)
  | multivariate (detail : String)
  deriving Repr, Inhabited

def Reject.format : Reject → String
  | .unsupportedExpression d => s!"unsupportedExpression: {d}"
  | .unsupportedType d => s!"unsupportedType: {d}"
  | .multivariate d => s!"multivariate: {d}"

/-- Reification result: IR expression + free variable (must be unique ℝ). -/
structure Result where
  expr : Expr
  fvar : Lean.Expr
  deriving Repr

private def failExpr (d : String) : Except Reject α :=
  .error (.unsupportedExpression d)

private def failType (d : String) : Except Reject α :=
  .error (.unsupportedType d)

private def failMulti (d : String) : Except Reject α :=
  .error (.multivariate d)

private def isRealType (ty : Lean.Expr) : MetaM Bool := do
  let ty ← whnf ty
  pure (ty.isConstOf ``Real || ty.isConstOf ``_root_.Real)

private def natLitOnly? (e : Lean.Expr) : Option Nat :=
  if let some n := e.rawNatLit? then some n
  else if e.isAppOfArity ``OfNat.ofNat 3 then
    e.appFn!.appArg!.rawNatLit?
  else
    none

private partial def ratLit? (e : Lean.Expr) : MetaM (Option ℚ) := do
  let e ← whnfR e
  if let some n := natLitOnly? e then
    return some (n : ℚ)
  if e.isAppOfArity ``Neg.neg 3 || e.isAppOf ``Neg.neg then
    match ← ratLit? e.appArg! with
    | some q => return some (-q)
    | none => return none
  if e.isAppOfArity ``OfNat.ofNat 3 then
    match natLitOnly? e with
    | some n => return some (n : ℚ)
    | none => return none
  return none

/-- Collect free variables of type `ℝ`. -/
private def collectRealFVars (e : Lean.Expr) : MetaM (Array Lean.Expr) := do
  let fvarSet := (Lean.collectFVars {} e).fvarSet
  let mut out : Array Lean.Expr := #[]
  for decl in (← getLCtx) do
    if decl.isImplementationDetail then continue
    if fvarSet.contains decl.fvarId then
      if ← isRealType decl.type then
        out := out.push decl.toExpr
  pure out

private partial def reifyWithFVar (x : Lean.Expr) (e : Lean.Expr) :
    MetaM (Except Reject Expr) := do
  let e ← whnfR e
  if e == x then
    return .ok (.variable 0)
  if e.isFVar then
    return failMulti s!"additional real fvar {e}"
  if let some q ← ratLit? e then
    return .ok (.const q)
  if e.isAppOfArity ``Neg.neg 3 || e.isAppOf ``Neg.neg then
    match ← reifyWithFVar x e.appArg! with
    | .ok a => return .ok (.neg a)
    | .error err => return .error err
  if e.isAppOfArity ``HAdd.hAdd 6 || e.isAppOf ``HAdd.hAdd then
    let args := e.getAppArgs
    if args.size < 2 then return failExpr "HAdd arity"
    match ← reifyWithFVar x args[args.size - 2]!, ← reifyWithFVar x args.back! with
    | .ok a, .ok b => return .ok (.add a b)
    | .error err, _ => return .error err
    | _, .error err => return .error err
  if e.isAppOfArity ``HSub.hSub 6 || e.isAppOf ``HSub.hSub then
    let args := e.getAppArgs
    if args.size < 2 then return failExpr "HSub arity"
    match ← reifyWithFVar x args[args.size - 2]!, ← reifyWithFVar x args.back! with
    | .ok a, .ok b => return .ok (.sub a b)
    | .error err, _ => return .error err
    | _, .error err => return .error err
  if e.isAppOfArity ``HMul.hMul 6 || e.isAppOf ``HMul.hMul then
    let args := e.getAppArgs
    if args.size < 2 then return failExpr "HMul arity"
    match ← reifyWithFVar x args[args.size - 2]!, ← reifyWithFVar x args.back! with
    | .ok a, .ok b => return .ok (.mul a b)
    | .error err, _ => return .error err
    | _, .error err => return .error err
  if e.isAppOfArity ``HDiv.hDiv 6 || e.isAppOf ``HDiv.hDiv then
    let args := e.getAppArgs
    if args.size < 2 then return failExpr "HDiv arity"
    match ← reifyWithFVar x args[args.size - 2]!, ← reifyWithFVar x args.back! with
    | .ok a, .ok b => return .ok (.div a b)
    | .error err, _ => return .error err
    | _, .error err => return .error err
  if e.isAppOfArity ``Inv.inv 3 || e.isAppOf ``Inv.inv then
    match ← reifyWithFVar x e.appArg! with
    | .ok a => return .ok (.inv a)
    | .error err => return .error err
  if e.isAppOfArity ``HPow.hPow 6 || e.isAppOf ``HPow.hPow then
    let args := e.getAppArgs
    if args.size < 2 then return failExpr "HPow arity"
    match ← reifyWithFVar x args[args.size - 2]!, natLitOnly? args.back! with
    | .ok a, some k => return .ok (.pow a k)
    | .error err, _ => return .error err
    | _, none => return failExpr "HPow exponent not a nat literal"
  if e.isAppOf ``Real.sin then
    match ← reifyWithFVar x e.appArg! with
    | .ok a => return .ok (.sin a)
    | .error err => return .error err
  if e.isAppOf ``Real.cos then
    match ← reifyWithFVar x e.appArg! with
    | .ok a => return .ok (.cos a)
    | .error err => return .error err
  if e.isAppOf ``Real.exp then
    match ← reifyWithFVar x e.appArg! with
    | .ok a => return .ok (.exp a)
    | .error err => return .error err
  if e.isAppOf ``Real.log then
    match ← reifyWithFVar x e.appArg! with
    | .ok a => return .ok (.log a)
    | .error err => return .error err
  return failExpr s!"unsupported analytic construct: {e}"

/-- Reify a `ℝ`-valued expression in a single free variable. -/
def reify (e : Lean.Expr) : MetaM (Except Reject Result) := do
  let ty ← InferType.inferType e
  unless ← isRealType ty do
    return failType s!"expected Real, got {ty}"
  let fvars ← collectRealFVars e
  match fvars.size with
  | 0 =>
    -- constant expression: invent no variable; use a dummy is disallowed —
    -- constants are allowed with a fresh placeholder only when caller binds one.
    -- Here we reject empty environment to keep univariate interpret aligned.
    match ← reifyWithFVar (Lean.mkConst ``True) e with
    | .ok _ => return failExpr "constant reification requires an explicit ℝ binder"
    | .error err =>
      -- try pure constant path
      match ← ratLit? e with
      | some q =>
          -- Represent constants without a free variable by refusing multivariate
          -- and returning a synthetic error directing callers to bind `x`.
          return failExpr s!"constant {q} has no free variable; bind an ℝ variable"
      | none => return .error err
  | 1 =>
    let x := fvars[0]!
    match ← reifyWithFVar x e with
    | .ok ir =>
      if ir.isUnivariate then
        return .ok { expr := ir, fvar := x }
      else
        return failMulti "reified expression is not univariate"
    | .error err => return .error err
  | _ =>
    return failMulti s!"expected one ℝ free variable, found {fvars.size}"

end MathEvidence.Tactic.ReifyAnalytic
