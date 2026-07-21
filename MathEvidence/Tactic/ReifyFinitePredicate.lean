/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import MathEvidence.IR.FinitePredicate.Eval
import MathEvidence.IR.FinitePredicate.Reify

/-!
# Finite-predicate Meta reification (ME-103)

Lowers a restricted class of Lean goals into `IR.FinitePredicate`:

* `¬ ∀ x : Fin n, (x : Nat) = k`
* `¬ ∀ b : Bool, b = true` / `b = false`
* `∃ x : Fin n, ¬ ((x : Nat) = k)` (treated as refutation package)
* `¬ ∀ x : Nat, x ≤ n → x = k` (bounded Nat)
* `¬ ∀ x : Int, lo ≤ x → x ≤ hi → x = k` (bounded Int)

Exhaustive absence search is out of scope for the Meta path; the reifier produces
IR for checker/tactic witness closing. Budget-exhaust `unknown` is exercised by
`searchCounterexample` (see Counterexample.Tests).
-/

namespace MathEvidence.Tactic.ReifyFinitePredicate

open Lean Meta
open MathEvidence.IR.FinitePredicate

abbrev Reject := MathEvidence.IR.FinitePredicate.Reject
abbrev Reified := MathEvidence.IR.FinitePredicate.Reified
abbrev Assignment := MathEvidence.IR.FinitePredicate.Assignment

/-- Validate an already-lowered finite predicate package. -/
def validateReified (r : Reified)
    (sizeLimit : Nat := MathEvidence.IR.FinitePredicate.defaultSizeLimit) :
    Except Reject Reified :=
  MathEvidence.IR.FinitePredicate.acceptReified r sizeLimit

/-- Validate that a concrete witness inhabits the declared finite domains. -/
def validateAssignment (domains : List MathEvidence.IR.FinitePredicate.Domain)
    (assignment : Assignment) : Bool :=
  MathEvidence.IR.FinitePredicate.Assignment.wellFormed domains assignment

/-- Evaluate a refutation witness against an already-lowered predicate. -/
def isCounterexample (assignment : Assignment)
    (pred : MathEvidence.IR.FinitePredicate.Pred) : Bool :=
  MathEvidence.IR.FinitePredicate.isCounterexample assignment pred

/-- Suggested witness for a reified package (best-effort, untrusted until checked). -/
structure ReifyGoalResult where
  reified : Reified
  suggestedWitness : Assignment
  deriving Repr

private def failType (d : String) : Except Reject α :=
  .error (.unsupportedType d)

private def failExpr (d : String) : Except Reject α :=
  .error (.unsupportedExpression d)

private def finNat? (e : Expr) : MetaM (Option Nat) := do
  let e ← whnf e
  if e.isAppOfArity ``Fin 1 then
    let nExpr ← whnf e.appArg!
    match nExpr.rawNatLit? with
    | some n => return some n
    | none =>
      if nExpr.isAppOfArity ``OfNat.ofNat 3 then
        return nExpr.appFn!.appArg!.rawNatLit?
      else return none
  else
    return none

private def natLit? (e : Expr) : MetaM (Option Nat) := do
  let e ← whnfR e
  match e.rawNatLit? with
  | some n => return some n
  | none =>
    if e.isAppOfArity ``OfNat.ofNat 3 then
      return e.appFn!.appArg!.rawNatLit?
    else return none

/-- `¬ P` peeling. -/
private def peelNot (e : Expr) : MetaM (Option Expr) := do
  let e ← whnf e
  if e.isAppOf ``Not then
    return some e.appArg!
  -- `Not` may appear as `p → False`
  if e.isArrow then
    let body := e.bindingBody!
    let bodyWhnf ← whnf body
    if bodyWhnf.isConstOf ``False then
      return some e.bindingDomain!
  return none

/-- Match `∀ x : Fin n, ↑x = k` (Nat coercion). -/
private def matchFinNatEq (e : Expr) : MetaM (Option (Nat × Nat)) := do
  forallTelescopeReducing e fun xs body => do
    if xs.size ≠ 1 then return none
    match ← finNat? (← inferType xs[0]!) with
    | none => return none
    | some n =>
      let body ← whnf body
      unless body.isAppOf ``Eq do return none
      let args := body.getAppArgs
      if args.size < 3 then return none
      let rhs ← whnfR args[args.size - 1]!
      match ← natLit? rhs with
      | some k => return some (n, k)
      | none => return none

/-- Match `∀ b : Bool, b = true/false`. -/
private def matchBoolEq (e : Expr) : MetaM (Option Bool) := do
  forallTelescopeReducing e fun xs body => do
    if xs.size ≠ 1 then return none
    let dom ← whnf (← inferType xs[0]!)
    unless dom.isConstOf ``Bool do return none
    let body ← whnf body
    unless body.isAppOf ``Eq do return none
    let args := body.getAppArgs
    if args.size < 3 then return none
    let rhs ← whnfR args[args.size - 1]!
    if rhs.isConstOf ``Bool.true || rhs.isAppOf ``true ||
        (← natLit? rhs) == some 1 then
      -- some elaborations use true as literal
      if rhs.isConstOf ``Bool.false || rhs.isAppOf ``false then return some false
      return some true
    if rhs.isConstOf ``Bool.false || rhs.isAppOf ``false then return some false
    return none

/-- Match `∃ x : Fin n, ¬(↑x = k)`. -/
private def matchExistsFinNatNe (e : Expr) : MetaM (Option (Nat × Nat)) := do
  let e ← whnf e
  if !(e.isAppOf ``Exists || e.isAppOf ``Exists.intro) then
    -- `∃` is `Exists` inductive
    unless e.isAppOf ``Exists do return none
  let args := e.getAppArgs
  if args.size < 2 then return none
  let dom := args[0]!
  let pred := args[1]!
  match ← finNat? dom with
  | none => return none
  | some n =>
    -- pred is `fun x => ¬(↑x = k)`
    let lam ← whnfR pred
    match lam with
    | .lam _ _ b _ =>
      match ← peelNot b with
      | none => return none
      | some eqe =>
        let eqe ← whnf eqe
        unless eqe.isAppOf ``Eq do return none
        let eqArgs := eqe.getAppArgs
        if eqArgs.size < 3 then return none
        match ← natLit? eqArgs[eqArgs.size - 1]! with
        | some k => return some (n, k)
        | none => return none
    | _ => return none

private def intLit? (e : Expr) : MetaM (Option Int) := do
  let e ← whnfR e
  match ← natLit? e with
  | some n => return some (Int.ofNat n)
  | none =>
    if e.isAppOfArity ``Neg.neg 3 || e.isAppOf ``Neg.neg then
      match ← natLit? e.appArg! with
      | some n => return some (Int.negOfNat n)
      | none => return none
    else if e.isAppOf ``Int.ofNat then
      match ← natLit? e.appArg! with
      | some n => return some (Int.ofNat n)
      | none => return none
    else if e.isAppOf ``Int.negSucc then
      match e.appArg!.rawNatLit? with
      | some n => return some (Int.negOfNat (n + 1))
      | none => return none
    else
      return none

/-- Match `∀ x : Nat, x ≤ n → x = k` (Lean may telescope the arrow into a second binder). -/
private def matchBoundedNatEq (e : Expr) : MetaM (Option (Nat × Nat)) := do
  forallTelescopeReducing e fun xs body => do
    let xTy ← inferType xs[0]!
    let hyp? ← do
      if xs.size = 1 then
        let body ← whnf body
        if body.isArrow || body.isForall then
          pure (some (← whnf body.bindingDomain!))
        else
          pure none
      else if xs.size = 2 then
        pure (some (← inferType xs[1]!))
      else
        pure none
    let concl ← do
      if xs.size = 1 then
        let body ← whnf body
        if body.isArrow || body.isForall then
          pure (← whnf body.bindingBody!)
        else
          pure body
      else
        pure (← whnf body)
    let dom ← whnf xTy
    unless dom.isConstOf ``Nat do return none
    let some hyp := hyp? | return none
    let hyp ← whnf hyp
    unless hyp.isAppOf ``LE.le || hyp.isAppOf ``Nat.le do return none
    let hypArgs := hyp.getAppArgs
    if hypArgs.size < 2 then return none
    match ← natLit? hypArgs[hypArgs.size - 1]! with
    | none => return none
    | some n =>
      let concl ← whnf concl
      unless concl.isAppOf ``Eq do return none
      let cargs := concl.getAppArgs
      if cargs.size < 3 then return none
      match ← natLit? cargs[cargs.size - 1]! with
      | some k => return some (n, k)
      | none => return none

private def isIntType (ty : Expr) : MetaM Bool := do
  let ty ← whnf ty
  if ty.isConstOf ``Int then return true
  match ty.getAppFn.constName? with
  | some n => pure (n.getString! == "Int")
  | none => pure false

private def isLeOrGe (e : Expr) : Bool :=
  e.isAppOf ``LE.le || e.isAppOf ``Int.le || e.isAppOf ``GE.ge ||
    e.isAppOf ``LT.lt || e.isAppOf ``Int.lt || e.isAppOf ``GT.gt

/-- From `a ≤ b` / `a ≥ b` involving `x`, recover a lower or upper bound literal. -/
private def boundFromLe (x hyp : Expr) : MetaM (Option (Option Int × Option Int)) := do
  let hyp ← whnfR hyp
  unless isLeOrGe hyp do return none
  let args := hyp.getAppArgs
  if args.size < 2 then return none
  let left := args[args.size - 2]!
  let right := args[args.size - 1]!
  let isGe := hyp.isAppOf ``GE.ge || hyp.isAppOf ``GT.gt
  if (← isDefEq left x) || (left.isFVar && x.isFVar && left.fvarId! == x.fvarId!) then
    -- x ≤ hi  or  x ≥ lo (if isGe)
    match ← intLit? right with
    | some n =>
      if isGe then return some (some n, none) else return some (none, some n)
    | none => return none
  if (← isDefEq right x) || (right.isFVar && x.isFVar && right.fvarId! == x.fvarId!) then
    -- lo ≤ x  or  hi ≥ x (if isGe)
    match ← intLit? left with
    | some n =>
      if isGe then return some (none, some n) else return some (some n, none)
    | none => return none
  return none

/-- Match `∀ x : Int, lo ≤ x → x ≤ hi → x = k` (arrows telescope to extra binders).
Also accepts `lo ≤ x ∧ x ≤ hi → x = k`. -/
private def matchBoundedIntEq (e : Expr) : MetaM (Option (Int × Int × Int)) := do
  forallTelescopeReducing e fun xs body => do
    unless xs.size ≥ 1 do return none
    unless ← isIntType (← inferType xs[0]!) do return none
    let x := xs[0]!
    let mut lo? : Option Int := none
    let mut hi? : Option Int := none
    -- Collect bounds from telescope proof binders.
    for i in [1:xs.size] do
      match ← boundFromLe x (← inferType xs[i]!) with
      | some (l, h) =>
        if let some v := l then lo? := some v
        if let some v := h then hi? := some v
      | none => pure ()
    -- Or from residual arrows / And in the body.
    let mut concl := body
    let mut guard := 8
    while guard > 0 do
      guard := guard - 1
      let c ← whnfR concl
      if c.isArrow || c.isForall then
        match ← boundFromLe x c.bindingDomain! with
        | some (l, h) =>
          if let some v := l then lo? := some v
          if let some v := h then hi? := some v
        | none =>
          -- `lo ≤ x ∧ x ≤ hi`
          let dom ← whnfR c.bindingDomain!
          if dom.isAppOf ``And then
            let dargs := dom.getAppArgs
            if dargs.size ≥ 2 then
              for side in #[dargs[dargs.size - 2]!, dargs[dargs.size - 1]!] do
                match ← boundFromLe x side with
                | some (l, h) =>
                  if let some v := l then lo? := some v
                  if let some v := h then hi? := some v
                | none => pure ()
        concl := c.bindingBody!
      else
        concl := c
        break
    match lo?, hi? with
    | some lo, some hi =>
      let finalConcl ← whnfR concl
      unless finalConcl.isAppOf ``Eq do return none
      let cargs := finalConcl.getAppArgs
      if cargs.size < 3 then return none
      -- Prefer RHS literal; also accept LHS literal with x on RHS.
      let rhs := cargs[cargs.size - 1]!
      let lhs := cargs[cargs.size - 2]!
      if let some k ← intLit? rhs then return some (lo, hi, k)
      if (← isDefEq rhs x) || (rhs.isFVar && x.isFVar && rhs.fvarId! == x.fvarId!) then
        if let some k ← intLit? lhs then return some (lo, hi, k)
      return none
    | _, _ => return none

/-- Meta entry: lower supported ¬∀ / ∃¬ Fin/Bool/Nat/Int goals. -/
def reifyLeanPredicateGoal (e : Expr) : MetaM (Except Reject ReifyGoalResult) := do
  let e ← whnf e
  -- Primary: ¬ ∀ ...
  if let some inner ← peelNot e then
    if let some (n, k) ← matchFinNatEq inner then
      if n = 0 then return failExpr "Fin 0 domain is empty"
      let bound := n - 1
      let r : Reified := {
        varNames := ["x"]
        domains := [{ ty := .nat, bound := some bound }]
        pred := .eq (.var 0) (.lit (.nat k))
      }
      match acceptReified r with
      | .error err => return .error err
      | .ok r =>
        -- Witness: first value ≠ k in range, else 0 if k ≠ 0 else 1 (if bound≥1)
        let w : Nat :=
          if k ≠ 0 then 0
          else if bound ≥ 1 then 1 else 0
        return .ok { reified := r, suggestedWitness := [.nat w] }
    if let some target ← matchBoolEq inner then
      let r : Reified := {
        varNames := ["b"]
        domains := [{ ty := .bool }]
        pred := .eq (.var 0) (.lit (.bool target))
      }
      match acceptReified r with
      | .error err => return .error err
      | .ok r =>
        return .ok {
          reified := r
          suggestedWitness := [.bool (not target)]
        }
    if let some (n, k) ← matchBoundedNatEq inner then
      let r : Reified := {
        varNames := ["x"]
        domains := [{ ty := .nat, bound := some n }]
        pred := .eq (.var 0) (.lit (.nat k))
      }
      match acceptReified r with
      | .error err => return .error err
      | .ok r =>
        let w : Nat := if k ≠ 0 then 0 else if n ≥ 1 then 1 else 0
        return .ok { reified := r, suggestedWitness := [.nat w] }
    if let some (lo, hi, k) ← matchBoundedIntEq inner then
      if hi < lo then return failExpr "empty Int bound interval"
      let r : Reified := {
        varNames := ["x"]
        domains := [{
          ty := .int
          bound := none
          lowerBound := some (.lit (.int lo))
          upperBound := some (.lit (.int hi))
        }]
        pred := .eq (.var 0) (.lit (.int k))
      }
      match acceptReified r with
      | .error err => return .error err
      | .ok r =>
        let w : Int := if k ≠ lo then lo else if hi > lo then lo + 1 else lo
        return .ok { reified := r, suggestedWitness := [.int w] }
    return failType
      "unsupported ¬∀ shape; expected Fin/Bool/bounded-Nat/bounded-Int equality"
  -- Secondary: ∃ x : Fin n, ¬(↑x = k)
  if let some (n, k) ← matchExistsFinNatNe e then
    if n = 0 then return failExpr "Fin 0 domain is empty"
    let bound := n - 1
    let r : Reified := {
      varNames := ["x"]
      domains := [{ ty := .nat, bound := some bound }]
      pred := .eq (.var 0) (.lit (.nat k))
    }
    match acceptReified r with
    | .error err => return .error err
    | .ok r =>
      let w : Nat := if k ≠ 0 then 0 else if bound ≥ 1 then 1 else 0
      return .ok { reified := r, suggestedWitness := [.nat w] }
  return failType
    "finite-predicate Meta reification supports ¬∀ Fin/Bool/Nat/Int and ∃ Fin ¬eq shapes only"

/-- Back-compat: validators-only path returning `Reified` without witness. -/
def reifyLeanPredicateGoalReified (e : Expr) : MetaM (Except Reject Reified) := do
  match ← reifyLeanPredicateGoal e with
  | .ok r => return .ok r.reified
  | .error err => return .error err

def Reject.format : Reject → String
  | .unsupportedExpression d => s!"unsupportedExpression: {d}"
  | .unsupportedType d => s!"unsupportedType: {d}"
  | .illFormed d => s!"illFormed: {d}"
  | .expressionTooLarge sz lim => s!"expressionTooLarge: {sz} > {lim}"
  | .unboundedDomain d => s!"unboundedDomain: {d}"

end MathEvidence.Tactic.ReifyFinitePredicate
