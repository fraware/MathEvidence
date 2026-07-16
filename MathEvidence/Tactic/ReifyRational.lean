/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import Mathlib.Data.Rat.Defs
import MathEvidence.Checkers.RationalEquality.Spec
import MathEvidence.IR.RationalExpr.Reify
import MathEvidence.IR.RationalExpr.Syntax

/-!
# Meta-level reification of ℚ expressions

Walks Lean `Expr` trees into `IR.RationalExpr.Expr`, reusing `acceptReified`.
Unsupported constructs (transcendentals, conditionals, approx numerals, …) are
rejected with structured `Reject` values — never silently totalized.
-/

namespace MathEvidence.Tactic.ReifyRational

open Lean Meta
open MathEvidence.Checkers.RationalEquality

abbrev RExpr := MathEvidence.IR.RationalExpr.Expr
abbrev Reject := MathEvidence.IR.RationalExpr.Reject

/-- Meta reification result: IR claim plus ordered free variables (ℚ). -/
structure Result where
  claim : Claim
  fvars : Array Expr
  deriving Repr

private def isRatType (ty : Expr) : MetaM Bool := do
  let ty ← whnf ty
  pure (ty.isConstOf ``_root_.Rat)

private def fvarName (e : Expr) : MetaM String := do
  let .fvar id := e | throwError "expected fvar"
  let decl ← id.getDecl
  pure decl.userName.toString

/-- Collect free variables of type `ℚ` in deterministic local-context order. -/
private def collectRatFVars (e : Expr) : MetaM (Array Expr) := do
  let fvarSet := (Lean.collectFVars {} e).fvarSet
  let mut out : Array Expr := #[]
  for decl in (← getLCtx) do
    if decl.isImplementationDetail then continue
    if fvarSet.contains decl.fvarId then
      if ← isRatType decl.type then
        out := out.push decl.toExpr
  pure out

private partial def reifyWithNames (names : List String) (fvars : Array Expr)
    (e : Expr) : MetaM (Except Reject RExpr) := do
  -- Prefer reducible-only reduction so `HAdd`/`HMul`/`HDiv` remain visible.
  let e ← whnfR e
  let fail (d : String) : Except Reject RExpr :=
    .error (.unsupportedExpression d)
  if e.isFVar then
    match fvars.findIdx? (· == e) with
    | some i => return .ok (.var i)
    | none => return fail s!"fvar not in collected Rat environment: {e}"
  if let some n := e.rawNatLit? then
    return .ok (.int (Int.ofNat n))
  if e.isAppOfArity ``OfNat.ofNat 3 then
    let nExpr := e.appFn!.appArg!
    if let some n := nExpr.rawNatLit? then
      return .ok (.int (Int.ofNat n))
    return fail "OfNat.ofNat without raw nat literal"
  if e.isAppOfArity ``Neg.neg 3 || e.isAppOf ``Neg.neg then
    let args := e.getAppArgs
    if args.size < 1 then return fail "Neg without argument"
    match ← reifyWithNames names fvars args.back! with
    | .ok a => return .ok (.neg a)
    | .error err => return .error err
  -- Unfolded Rat field operations (after deeper reduction).
  if e.isAppOfArity' (Name.mkStr2 "Rat" "neg") 1 then
    match ← reifyWithNames names fvars e.appArg! with
    | .ok a => return .ok (.neg a)
    | .error err => return .error err
  if e.isAppOf ``HPow.hPow then
    let args := e.getAppArgs
    if args.size < 2 then return fail "HPow without arguments"
    let base := args[args.size - 2]!
    let exp := args[args.size - 1]!
    let exp ← whnfR exp
    let k? : Option Nat :=
      match exp.rawNatLit? with
      | some k => some k
      | none =>
        if exp.isAppOfArity ``OfNat.ofNat 3 then
          exp.appFn!.appArg!.rawNatLit?
        else
          none
    match k? with
    | none => return fail "exponent must be a Nat literal"
    | some k =>
      match ← reifyWithNames names fvars base with
      | .ok b => return .ok (.pow b k)
      | .error err => return .error err
  -- `npow` / `Rat.pow` style (`a ^ n` with Nat exponent).
  if e.isAppOfArity' (Name.mkStr2 "Rat" "pow") 2 || e.isAppOfArity ``Pow.pow 4 then
    let args := e.getAppArgs
    let base := args[0]!
    let exp ← whnfR args.back!
    let k? : Option Nat :=
      match exp.rawNatLit? with
      | some k => some k
      | none =>
        if exp.isAppOfArity ``OfNat.ofNat 3 then
          exp.appFn!.appArg!.rawNatLit?
        else
          none
    match k? with
    | none => return fail "Rat.pow exponent must be a Nat literal"
    | some k =>
      match ← reifyWithNames names fvars base with
      | .ok b => return .ok (.pow b k)
      | .error err => return .error err
  let bin6 (name : Name) (ctor : RExpr → RExpr → RExpr) :
      MetaM (Option (Except Reject RExpr)) := do
    if e.isAppOf name then
      let args := e.getAppArgs
      if args.size < 2 then return none
      let a := args[args.size - 2]!
      let b := args[args.size - 1]!
      match ← reifyWithNames names fvars a with
      | .error err => return some (.error err)
      | .ok left =>
        match ← reifyWithNames names fvars b with
        | .error err => return some (.error err)
        | .ok right => return some (.ok (ctor left right))
    else
      return none
  let bin2 (op : String) (ctor : RExpr → RExpr → RExpr) :
      MetaM (Option (Except Reject RExpr)) := do
    if e.isAppOfArity' (Name.mkStr2 "Rat" op) 2 then
      let a := e.appFn!.appArg!
      let b := e.appArg!
      match ← reifyWithNames names fvars a with
      | .error err => return some (.error err)
      | .ok left =>
        match ← reifyWithNames names fvars b with
        | .error err => return some (.error err)
        | .ok right => return some (.ok (ctor left right))
    else
      return none
  if let some r ← bin6 ``HAdd.hAdd .add then return r
  if let some r ← bin6 ``HSub.hSub .sub then return r
  if let some r ← bin6 ``HMul.hMul .mul then return r
  if let some r ← bin6 ``HDiv.hDiv .div then return r
  if let some r ← bin2 "add" .add then return r
  if let some r ← bin2 "sub" .sub then return r
  if let some r ← bin2 "mul" .mul then return r
  if let some r ← bin2 "div" .div then return r
  if e.isAppOfArity ``Int.cast 2 || e.isAppOfArity ``Nat.cast 2 then
    return ← reifyWithNames names fvars e.appArg!
  if e.isAppOf ``Int.cast || e.isAppOf ``Nat.cast then
    let args := e.getAppArgs
    if args.size ≥ 1 then
      return ← reifyWithNames names fvars args.back!
  if e.isAppOfArity' (Name.mkStr2 "Rat" "ofInt") 1 then
    return ← reifyWithNames names fvars e.appArg!
  if e.isAppOfArity' (Name.mkStr2 "Rat" "divInt") 2 then
    match ← reifyWithNames names fvars e.appFn!.appArg! with
    | .error err => return .error err
    | .ok num =>
      match ← reifyWithNames names fvars e.appArg! with
      | .error err => return .error err
      | .ok den => return .ok (.div num den)
  -- Last resort: unfold further once and retry field ops only.
  let e2 ← whnf e
  unless e2 == e do
    return ← reifyWithNames names fvars e2
  let fn := e.getAppFn
  if let some n := fn.constName? then
    let s := n.toString
    if s.endsWith "sin" || s.endsWith "cos" || s.endsWith "exp" || s.endsWith "log" then
      return fail "transcendental function rejected"
  if fn.isConstOf ``ite || fn.isConstOf ``dite then
    return fail "conditional rejected"
  if e.isAppOf ``Float.ofNat || e.isConstOf ``Float then
    return fail "approximate numeral / Float rejected"
  return fail s!"unsupported expression head: {e.getAppFn}"

/-- Reify a single ℚ term into IR (variable environment from free vars). -/
def reifyTerm (e : Expr) : MetaM (Except Reject Result) := do
  let fvars ← collectRatFVars e
  let names ← fvars.mapM fvarName
  let nameList := names.toList
  match ← reifyWithNames nameList fvars e with
  | .error err => return .error err
  | .ok expr =>
    match MathEvidence.IR.RationalExpr.acceptReified ⟨nameList, expr⟩ with
    | .error err => return .error err
    | .ok r =>
      return .ok {
        claim := {
          varNames := r.varNames
          lhs := r.expr
          rhs := .int 0
        }
        fvars := fvars
      }

/-- Reify a goal of the form `lhs = rhs` at type `ℚ`. -/
def reifyEqualityGoal (goalType : Expr) : MetaM (Except Reject Result) := do
  let goalType ← whnf goalType
  let some (_, lhs, rhs) := goalType.eq? |
    return .error (.unsupportedType "goal is not an equality")
  let ty ← inferType lhs
  unless ← isRatType ty do
    return .error (.unsupportedType "equality is not over Rat")
  let fvarsL ← collectRatFVars lhs
  let fvarsR ← collectRatFVars rhs
  let mut seen : Array Expr := #[]
  for v in fvarsL do
    unless seen.any (· == v) do
      seen := seen.push v
  for v in fvarsR do
    unless seen.any (· == v) do
      seen := seen.push v
  let names ← seen.mapM fvarName
  let nameList := names.toList
  match ← reifyWithNames nameList seen lhs with
  | .error err => return .error err
  | .ok l =>
    match ← reifyWithNames nameList seen rhs with
    | .error err => return .error err
    | .ok r =>
      match MathEvidence.IR.RationalExpr.acceptReified ⟨nameList, .sub l r⟩ with
      | .error err => return .error err
      | .ok _ =>
        return .ok {
          claim := {
            varNames := nameList
            lhs := l
            rhs := r
          }
          fvars := seen
        }

/-- True when two claims are structurally identical (fixture matching). -/
def claimsEqual (a b : Claim) : Bool :=
  a.varNames == b.varNames && a.lhs == b.lhs && a.rhs == b.rhs

def Reject.format : Reject → String
  | .unsupportedExpression d => s!"unsupportedExpression: {d}"
  | .unsupportedType d => s!"unsupportedType: {d}"
  | .unknownConstant d => s!"unknownConstant: {d}"
  | .expressionTooLarge sz lim => s!"expressionTooLarge: {sz} > {lim}"
  | .noncanonicalBinder d => s!"noncanonicalBinder: {d}"
  | .illFormed d => s!"illFormed: {d}"

end MathEvidence.Tactic.ReifyRational
