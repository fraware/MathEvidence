/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import Mathlib.Data.Matrix.Basic
import Mathlib.Data.Rat.Defs
import MathEvidence.IR.MatrixExpr.Ops
import MathEvidence.IR.MatrixExpr.Reify

/-!
# Matrix Meta reification (ME-102)

Lowers concrete Lean terms of type `Matrix (Fin m) (Fin n) ℚ` and
`Fin n → ℚ` into `MatrixExpr.ExactMatrixIR` / `Vector`, reusing
`acceptMatrix` / `acceptVector`. Unsupported symbolic matrices are rejected.
-/

namespace MathEvidence.Tactic.ReifyMatrix

open Lean Meta
open MathEvidence.IR.MatrixExpr

abbrev ExactMatrixIR := MathEvidence.IR.MatrixExpr.ExactMatrixIR
abbrev ExactVectorIR := MathEvidence.IR.MatrixExpr.Vector
abbrev Reject := MathEvidence.IR.MatrixExpr.Reject
abbrev Reified := MathEvidence.IR.MatrixExpr.Reified

/-- Validate an already-lowered exact matrix IR node. -/
def validateExactMatrixIR (A : ExactMatrixIR)
    (sizeLimit : Nat := MathEvidence.IR.MatrixExpr.defaultSizeLimit) :
    Except Reject Reified :=
  MathEvidence.IR.MatrixExpr.acceptMatrix A sizeLimit

/-- Validate an already-lowered exact vector IR node. -/
def validateExactVectorIR (v : ExactVectorIR) (n : Nat) : Except Reject ExactVectorIR :=
  MathEvidence.IR.MatrixExpr.acceptVector v n

/-- Convenience helper retained for fixtures and smoke tests. -/
def reifyIntMatrix (rows : List (List Int)) : Except Reject Reified :=
  MathEvidence.IR.MatrixExpr.reifyIntMatrix rows

/-- Convenience helper retained for fixtures and smoke tests. -/
def reifyIntVector (vals : List Int) : Except Reject ExactVectorIR :=
  MathEvidence.IR.MatrixExpr.reifyIntVector vals

/-- Result of Meta reification: IR plus dimensions. -/
structure MatrixResult where
  reified : Reified
  nrows : Nat
  ncols : Nat
  deriving Repr

structure VectorResult where
  vector : ExactVectorIR
  length : Nat
  deriving Repr

private def failExpr (d : String) : Except Reject α :=
  .error (.unsupportedExpression d)

private def failType (d : String) : Except Reject α :=
  .error (.unsupportedType d)

/-- Extract `n` from `Fin n` (after whnf). -/
private def finNat? (e : Expr) : MetaM (Option Nat) := do
  let e ← whnf e
  if e.isAppOfArity ``Fin 1 then
    let nExpr ← whnf e.appArg!
    match nExpr.rawNatLit? with
    | some n => return some n
    | none =>
      if nExpr.isAppOfArity ``OfNat.ofNat 3 then
        return nExpr.appFn!.appArg!.rawNatLit?
      else
        return none
  else
    return none

/-- True when `ty` is `ℚ` / `Rat`. -/
private def isRatType (ty : Expr) : MetaM Bool := do
  let ty ← whnf ty
  pure (ty.isConstOf ``_root_.Rat)

/-- Parse a concrete rational literal from Lean `Expr`. -/
partial def reifyRatLit (e : Expr) : MetaM (Except Reject RatLit) := do
  let e ← whnf e
  if let some n := e.rawNatLit? then
    return .ok (RatLit.ofInt (Int.ofNat n))
  if e.isAppOfArity ``OfNat.ofNat 3 then
    let nExpr := e.appFn!.appArg!
    if let some n := nExpr.rawNatLit? then
      return .ok (RatLit.ofInt (Int.ofNat n))
    return failExpr "OfNat.ofNat without raw nat literal"
  if e.isAppOf ``Int.ofNat || e.isAppOfArity ``Int.ofNat 1 then
    match ← reifyRatLit e.appArg! with
    | .ok ⟨n, 1⟩ => return .ok ⟨n, 1⟩
    | .ok _ => return failExpr "Int.ofNat expects integer"
    | .error err => return .error err
  if e.isAppOf ``Int.negSucc then
    match e.appArg!.rawNatLit? with
    | some n => return .ok (RatLit.ofInt (Int.negOfNat (n + 1)))
    | none => return failExpr "Int.negSucc without nat"
  -- Reduce `if c then a else b` when `c` is decidable true/false.
  if e.isAppOf ``ite || e.isAppOf ``dite then
    let args := e.getAppArgs
    if args.size ≥ 5 then
      let cond ← whnf args[1]!
      if cond.isAppOf ``True || cond.isConstOf ``True then
        return ← reifyRatLit args[3]!
      if cond.isAppOf ``False || cond.isConstOf ``False then
        return ← reifyRatLit args[4]!
      -- Try decide on Prop
      try
        let d ← mkDecide cond
        let d ← whnf d
        if d.isAppOf ``true || d.isConstOf ``Bool.true then
          return ← reifyRatLit args[3]!
        if d.isAppOf ``false || d.isConstOf ``Bool.false then
          return ← reifyRatLit args[4]!
      catch _ => pure ()
  if e.isAppOfArity ``Neg.neg 3 || e.isAppOf ``Neg.neg then
    match ← reifyRatLit e.appArg! with
    | .ok ⟨num, den⟩ => return .ok ⟨-num, den⟩
    | .error err => return .error err
  if e.isAppOf ``HMul.hMul || e.isAppOf ``Mul.mul then
    let args := e.getAppArgs
    if args.size ≥ 2 then
      match ← reifyRatLit args[args.size - 2]!, ← reifyRatLit args[args.size - 1]! with
      | .ok ⟨n1, d1⟩, .ok ⟨n2, d2⟩ =>
        if d1 = 0 || d2 = 0 then return .error .zeroDenominator
        return .ok ⟨n1 * n2, d1 * d2⟩
      | .error err, _ => return .error err
      | _, .error err => return .error err
  if e.isAppOf ``HAdd.hAdd || e.isAppOf ``Add.add then
    let args := e.getAppArgs
    if args.size ≥ 2 then
      match ← reifyRatLit args[args.size - 2]!, ← reifyRatLit args[args.size - 1]! with
      | .ok ⟨n1, d1⟩, .ok ⟨n2, d2⟩ =>
        if d1 = 0 || d2 = 0 then return .error .zeroDenominator
        -- n1/d1 + n2/d2
        return .ok ⟨n1 * Int.ofNat d2 + n2 * Int.ofNat d1, d1 * d2⟩
      | .error err, _ => return .error err
      | _, .error err => return .error err
  if e.isAppOf ``HDiv.hDiv then
    let args := e.getAppArgs
    if args.size < 2 then return failExpr "HDiv arity"
    match ← reifyRatLit args[args.size - 2]!, ← reifyRatLit args[args.size - 1]! with
    | .ok ⟨n1, d1⟩, .ok ⟨n2, d2⟩ =>
      if d1 = 0 || d2 = 0 || n2 = 0 then return .error .zeroDenominator
      let denNat := d1 * n2.natAbs
      if denNat = 0 then return .error .zeroDenominator
      let num := if n2 < 0 then -(n1 * Int.ofNat d2) else n1 * Int.ofNat d2
      return .ok ⟨num, denNat⟩
    | .error err, _ => return .error err
    | _, .error err => return .error err
  if e.isAppOf ``Rat.mk' then
    let args := e.getAppArgs
    if args.size < 2 then return failExpr "Rat.mk' arity"
    match ← reifyRatLit args[0]!, ← reifyRatLit args[1]! with
    | .ok ⟨n, 1⟩, .ok ⟨d, 1⟩ =>
      if d = 0 then return .error .zeroDenominator
      return .ok ⟨n, d.natAbs⟩
    | .error err, _ => return .error err
    | _, .error err => return .error err
    | _, _ => return failExpr "Rat.mk' expects integer literals"
  if e.isAppOfArity ``_root_.Rat.divInt 2 then
    let args := e.getAppArgs
    match ← reifyRatLit args[0]!, ← reifyRatLit args[1]! with
    | .ok ⟨n, 1⟩, .ok ⟨d, 1⟩ =>
      if d = 0 then return .error .zeroDenominator
      return .ok ⟨n, d.natAbs⟩
    | .error err, _ => return .error err
    | _, .error err => return .error err
    | _, _ => return failExpr "Rat.divInt expects integer literals"
  if let some n := e.getAppFn.constName? then
    if n.getString! == "mk'" || n.getString! == "mkRat" then
      let args := e.getAppArgs
      if args.size ≥ 2 then
        match ← reifyRatLit args[0]!, ← reifyRatLit args[1]! with
        | .ok ⟨num, 1⟩, .ok ⟨den, 1⟩ =>
          if den = 0 then return .error .zeroDenominator
          return .ok ⟨num, den.natAbs⟩
        | .error err, _ => return .error err
        | _, .error err => return .error err
        | _, _ => pure ()
  return failExpr s!"unsupported rational literal head: {e.getAppFn}"

/-- Parse `List ℚ` / nested list literals into IR rows. -/
private partial def reifyRatList (e : Expr) : MetaM (Except Reject (List RatLit)) := do
  let e ← whnfR e
  if e.isAppOf ``List.nil then
    return .ok []
  if e.isAppOfArity ``List.cons 3 || e.isAppOf ``List.cons then
    let args := e.getAppArgs
    let head := args[args.size - 2]!
    let tail := args[args.size - 1]!
    match ← reifyRatLit head, ← reifyRatList tail with
    | .ok x, .ok xs => return .ok (x :: xs)
    | .error err, _ => return .error err
    | _, .error err => return .error err
  return failExpr s!"expected List ℚ literal, got {e.getAppFn}"

private partial def reifyRatListList (e : Expr) : MetaM (Except Reject (List (List RatLit))) := do
  let e ← whnfR e
  if e.isAppOf ``List.nil then
    return .ok []
  if e.isAppOfArity ``List.cons 3 || e.isAppOf ``List.cons then
    let args := e.getAppArgs
    let head := args[args.size - 2]!
    let tail := args[args.size - 1]!
    match ← reifyRatList head, ← reifyRatListList tail with
    | .ok row, .ok rows => return .ok (row :: rows)
    | .error err, _ => return .error err
    | _, .error err => return .error err
  return failExpr s!"expected List (List ℚ) literal, got {e.getAppFn}"

/-- Recognize `Matrix (Fin m) (Fin n) ℚ` and return `(m, n)`.

`Matrix` unfolds to a Pi type under `whnf`, so we accept both the
`Matrix …` application and the unfolded `Fin m → Fin n → ℚ` form. -/
def matrixFinDims? (ty : Expr) : MetaM (Option (Nat × Nat)) := do
  let tyR ← whnfR ty
  if tyR.isAppOf ``_root_.Matrix then
    let args := tyR.getAppArgs
    if args.size ≥ 3 then
      unless ← isRatType args[2]! do return none
      match ← finNat? args[0]!, ← finNat? args[1]! with
      | some m, some n => return some (m, n)
      | _, _ => pure ()
  -- Unfolded: `Fin m → Fin n → ℚ`
  let ty ← whnf ty
  match ty with
  | .forallE _ d1 b1 _ =>
    match ← finNat? d1 with
    | none => return none
    | some m =>
      -- b1 may still contain a binder (non-dependent Matrix).
      match b1 with
      | .forallE _ d2 b2 _ =>
        if b2.hasLooseBVars then return none
        unless ← isRatType b2 do return none
        match ← finNat? d2 with
        | some n => return some (m, n)
        | none => return none
      | _ => return none
  | _ => return none

/-- Recognize `Fin n → ℚ`. -/
def vectorFinDim? (ty : Expr) : MetaM (Option Nat) := do
  let ty ← whnf ty
  match ty with
  | .forallE _ d b _ =>
    unless b.hasLooseBVars do
      unless ← isRatType b do return none
      return ← finNat? d
    return none
  | _ =>
    -- `Fin n → ℚ` may appear as `Arrow`
    if ty.isArrow then
      let d := ty.bindingDomain!
      let b := ty.bindingBody!
      unless ← isRatType b do return none
      return ← finNat? d
    return none

/-- Build IR matrix from nested rational lists. -/
def fromRatLists (rows : List (List RatLit)) : Except Reject Reified :=
  let nrows := rows.length
  let ncols := (rows.headD []).length
  acceptMatrix { nrows := nrows, ncols := ncols, entries := rows }

private def mkFinLit (n i : Nat) : MetaM Expr := do
  let iExpr := mkNatLit i
  let nExpr := mkNatLit n
  let ltType ← mkAppM ``LT.lt #[iExpr, nExpr]
  let lt ← mkDecideProof ltType
  mkAppM ``Fin.mk #[iExpr, lt]

/-- Lower a concrete Mathlib matrix expression into exact IR. -/
partial def reifyLeanMatrixExpr (e : Expr) : MetaM (Except Reject Reified) := do
  let e ← whnfR e
  -- Unfold named definitions (e.g. `A_diag`) so entries reduce to numerals.
  if e.isConst then
    if let some e' ← unfoldDefinition? e then
      return ← reifyLeanMatrixExpr e'
  if let some n := e.getAppFn.constName? then
    let s := n.getString!
    if s == "ofList" || s == "ofLists" then
      let args := e.getAppArgs
      if args.isEmpty then return failExpr "Matrix.ofList without args"
      match ← reifyRatListList args.back! with
      | .ok rows => return fromRatLists rows
      | .error err => return .error err
  let ty ← inferType e
  match ← matrixFinDims? ty with
  | none =>
    return failType
      "expected Matrix (Fin m) (Fin n) Rat (or Matrix.ofList literal)"
  | some (m, n) =>
    if m = 0 || n = 0 then
      return fromRatLists (List.replicate m (List.replicate n (RatLit.ofInt 0)))
    let mut rows : List (List RatLit) := []
    let useOfFn :=
      match e.getAppFn.constName? with
      | some n => n.getString! == "ofFn"
      | none => false
    let f ← do
      if useOfFn then
        pure e.getAppArgs.back!
      else if let some e' ← unfoldDefinition? e then
        pure e'
      else
        pure e
    for i in List.range m do
      let mut row : List RatLit := []
      for j in List.range n do
        let fi ← mkFinLit m i
        let fj ← mkFinLit n j
        let app := if useOfFn then mkAppN f #[fi, fj] else mkAppN f #[fi, fj]
        let cell ← withTransparency .all <| whnf app
        match ← reifyRatLit cell with
        | .ok lit => row := row ++ [lit]
        | .error err => return .error err
      rows := rows ++ [row]
    return fromRatLists rows

/-- Lower a concrete `Fin n → ℚ` vector. -/
def reifyLeanVectorExpr (e : Expr) : MetaM (Except Reject VectorResult) := do
  let e ← whnfR e
  let ty ← inferType e
  match ← vectorFinDim? ty with
  | none => return failType "expected Fin n → Rat"
  | some n =>
    let mut vals : List RatLit := []
    for i in List.range n do
      let fi ← mkFinLit n i
      let cell ← whnfR (mkApp e fi)
      match ← reifyRatLit cell with
      | .ok lit => vals := vals ++ [lit]
      | .error err => return .error err
    match acceptVector vals n with
    | .ok v => return .ok { vector := v, length := n }
    | .error err => return .error err

/-- Reify matrix type alone into a zero matrix of matching shape (shape probe). -/
def reifyMatrixType (ty : Expr) : MetaM (Except Reject (Nat × Nat)) := do
  match ← matrixFinDims? ty with
  | some dims => return .ok dims
  | none => return failType "expected Matrix (Fin m) (Fin n) Rat"

def Reject.format : Reject → String
  | .unsupportedExpression d => s!"unsupportedExpression: {d}"
  | .unsupportedType d => s!"unsupportedType: {d}"
  | .illFormed d => s!"illFormed: {d}"
  | .expressionTooLarge sz lim => s!"expressionTooLarge: {sz} > {lim}"
  | .zeroDenominator => "zeroDenominator"

end MathEvidence.Tactic.ReifyMatrix
