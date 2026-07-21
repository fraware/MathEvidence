/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import Mathlib.Algebra.Polynomial.Basic
import Mathlib.Data.Rat.Defs
import Mathlib.RingTheory.MvPolynomial.Basic
import MathEvidence.IR.Polynomial.Syntax
import MathEvidence.Checkers.IdealMembership.Check

/-!
# Polynomial Meta reification (ideal membership)

Lowers concrete Lean terms into `SparsePoly`:

* univariate `ℤ[X]` / `ℚ[X]` → `varCount = 1`
* multivariate `MvPolynomial (Fin n) ℤ` / `ℚ` (`2 ≤ n ≤ 4`) → `varCount = n`

Symbolic (non-literal) coefficients are rejected. Also matches
`f ∈ Ideal.span {g₁, …}` generator lists for the ideal-membership tactic.
-/

namespace MathEvidence.Tactic.ReifyPolynomial

open Lean Meta
open MathEvidence.IR.Polynomial
open Polynomial
open MvPolynomial

inductive Reject where
  | unsupportedExpression (detail : String)
  | unsupportedType (detail : String)
  deriving Repr, Inhabited

def Reject.format : Reject → String
  | .unsupportedExpression d => s!"unsupportedExpression: {d}"
  | .unsupportedType d => s!"unsupportedType: {d}"

structure PolyResult where
  poly : SparsePoly
  /-- `true` when the ambient ring is `ℚ`; otherwise `ℤ`. -/
  overRat : Bool
  deriving Repr

private def failExpr (d : String) : Except Reject α :=
  .error (.unsupportedExpression d)

private def failType (d : String) : Except Reject α :=
  .error (.unsupportedType d)

private def natLitOnly? (e : Expr) : Option Nat :=
  if let some n := e.rawNatLit? then some n
  else if e.isAppOfArity ``OfNat.ofNat 3 then
    e.appFn!.appArg!.rawNatLit?
  else
    none

private partial def intLit? (e : Expr) : MetaM (Option Int) := do
  let e ← whnfR e
  if let some n := natLitOnly? e then
    return some (Int.ofNat n)
  if e.isAppOf ``Int.ofNat then
    match natLitOnly? (← whnfR e.appArg!) with
    | some n => return some (Int.ofNat n)
    | none => return none
  if e.isAppOf ``Int.negSucc then
    match e.appArg!.rawNatLit? with
    | some n => return some (Int.negOfNat (n + 1))
    | none => return none
  if e.isAppOfArity ``Neg.neg 3 || e.isAppOf ``Neg.neg then
    match ← intLit? e.appArg! with
    | some n => return some (-n)
    | none => return none
  return none

/-- True when `ty` is `Polynomial ℤ` or `Polynomial ℚ`.

In Mathlib 4.14 the elaborated type may carry the `Semiring` instance as an
extra argument (`Polynomial Int Int.instSemiring`). -/
private def isUnivariatePolyType (ty : Expr) : MetaM (Option Bool) := do
  let ty ← whnf ty
  let isPoly :=
    ty.isAppOf ``Polynomial ||
      (match ty.getAppFn.constName? with
       | some n => n.getString! == "Polynomial" || n.toString.endsWith ".Polynomial"
       | none => false)
  unless isPoly && ty.getAppArgs.size ≥ 1 do return none
  let R ← whnf ty.getAppArgs[0]!
  if R.isConstOf ``Int then return some false
  if R.isConstOf ``_root_.Rat then return some true
  match R.getAppFn.constName? with
  | some n =>
    let s := n.getString!
    if s == "Int" then return some false
    if s == "Rat" then return some true
    return none
  | none => return none

/-- Accumulate `coefficient * X ^ exp` into a sparse univariate. -/
private def addTerm (acc : SparsePoly) (c : Int) (exp : Nat) : SparsePoly :=
  if c == 0 then acc
  else
    MathEvidence.Checkers.IdealMembership.normalize {
      varCount := 1
      terms := acc.terms ++ [{ coefficient := c, monomial := ⟨[exp]⟩ }]
    }

private partial def reifyPolyExpr (e : Expr) : MetaM (Except Reject SparsePoly) := do
  let e ← whnfR e
  -- Polynomial.X
  if e.isAppOf ``Polynomial.X || (e.isConst && e.constName!.getString! == "X") then
    return .ok { varCount := 1, terms := [{ coefficient := 1, monomial := ⟨[1]⟩ }] }
  -- Constants via OfNat / C / nat cast
  if let some n ← intLit? e then
    return .ok (addTerm (SparsePoly.zero 1) n 0)
  if e.isAppOf ``Polynomial.C then
    match ← intLit? e.appArg! with
    | some n => return .ok (addTerm (SparsePoly.zero 1) n 0)
    | none => return failExpr "Polynomial.C expects an integer literal"
  if e.isAppOf ``Nat.cast || e.isAppOf ``Int.cast || e.isAppOf ``Rat.cast then
    return ← reifyPolyExpr e.appArg!
  -- Negation
  if e.isAppOfArity ``Neg.neg 3 || e.isAppOf ``Neg.neg then
    match ← reifyPolyExpr e.appArg! with
    | .error err => return .error err
    | .ok p =>
      return .ok {
        varCount := 1
        terms := p.terms.map fun t => { t with coefficient := -t.coefficient }
      }
  -- Binary ops
  if e.isAppOf ``HAdd.hAdd || e.isAppOf ``Add.add then
    let args := e.getAppArgs
    if args.size ≥ 2 then
      match ← reifyPolyExpr args[args.size - 2]!, ← reifyPolyExpr args[args.size - 1]! with
      | .ok a, .ok b =>
        return .ok (MathEvidence.Checkers.IdealMembership.normalize (SparsePoly.add a b))
      | .error err, _ => return .error err
      | _, .error err => return .error err
  if e.isAppOf ``HSub.hSub || e.isAppOf ``Sub.sub then
    let args := e.getAppArgs
    if args.size ≥ 2 then
      match ← reifyPolyExpr args[args.size - 2]!, ← reifyPolyExpr args[args.size - 1]! with
      | .ok a, .ok b =>
        let negB : SparsePoly := {
          varCount := 1
          terms := b.terms.map fun t => { t with coefficient := -t.coefficient }
        }
        return .ok (MathEvidence.Checkers.IdealMembership.normalize (SparsePoly.add a negB))
      | .error err, _ => return .error err
      | _, .error err => return .error err
  if e.isAppOf ``HMul.hMul || e.isAppOf ``Mul.mul then
    let args := e.getAppArgs
    if args.size ≥ 2 then
      match ← reifyPolyExpr args[args.size - 2]!, ← reifyPolyExpr args[args.size - 1]! with
      | .ok a, .ok b =>
        return .ok (MathEvidence.Checkers.IdealMembership.normalize (SparsePoly.mul a b))
      | .error err, _ => return .error err
      | _, .error err => return .error err
  if e.isAppOf ``HPow.hPow || e.isAppOf ``Pow.pow then
    let args := e.getAppArgs
    if args.size ≥ 2 then
      match ← reifyPolyExpr args[args.size - 2]!, ← intLit? args[args.size - 1]! with
      | .ok base, some expNat =>
        if expNat < 0 then return failExpr "negative polynomial power"
        let exp := expNat.toNat
        let mut acc := addTerm (SparsePoly.zero 1) 1 0
        for _ in [:exp] do
          acc := MathEvidence.Checkers.IdealMembership.normalize (SparsePoly.mul acc base)
        return .ok acc
      | .error err, _ => return .error err
      | _, none => return failExpr "polynomial power exponent must be a nat literal"
  -- monomial n c  (optional)
  if e.isAppOf ``Polynomial.monomial then
    let args := e.getAppArgs
    if args.size ≥ 2 then
      match ← intLit? args[args.size - 2]!, ← intLit? args[args.size - 1]! with
      | some exp, some c =>
        if exp < 0 then return failExpr "negative monomial degree"
        return .ok (addTerm (SparsePoly.zero 1) c exp.toNat)
      | _, _ => return failExpr "Polynomial.monomial expects integer literals"
  return failExpr s!"unsupported polynomial expression head {e.getAppFn}"

/-- Meta entry: reify a concrete univariate `ℤ[X]` / `ℚ[X]` term. -/
def reifyLeanUnivariatePoly (e : Expr) : MetaM (Except Reject PolyResult) := do
  let ty ← inferType e
  match ← isUnivariatePolyType ty with
  | none =>
    return failType s!"expected Polynomial Int or Polynomial Rat (got {ty})"
  | some overRat =>
    match ← reifyPolyExpr e with
    | .error err => return .error err
    | .ok p =>
      let p := MathEvidence.Checkers.IdealMembership.normalize p
      if p.varCount != 1 then
        return failExpr "reified polynomial is not univariate"
      return .ok { poly := p, overRat }

/-- `σ` is `Fin n` for a concrete nat literal `n`. -/
private def finArity? (σ : Expr) : MetaM (Option Nat) := do
  let σ ← whnf σ
  if σ.isAppOf ``Fin then
    return natLitOnly? (← whnfR σ.appArg!)
  match σ.getAppFn.constName? with
  | some n =>
    if n.getString! == "Fin" || n.toString.endsWith ".Fin" then
      let args := σ.getAppArgs
      if args.size ≥ 1 then return natLitOnly? (← whnfR args[0]!)
      else return none
    else return none
  | none => return none

/-- True when `ty` is `MvPolynomial (Fin n) ℤ` / `ℚ` (extra instance args allowed).

Uses `whnfR` (not full `whnf`) so `MvPolynomial` is not unfolded to
`AddMonoidAlgebra`.
-/
private def isMvPolyType (ty : Expr) : MetaM (Option (Nat × Bool)) := do
  let ty ← instantiateMVars (← whnfR ty)
  let isMv :=
    ty.isAppOf ``MvPolynomial ||
      (match ty.getAppFn.constName? with
       | some n =>
         n.getString! == "MvPolynomial" || n.toString.endsWith ".MvPolynomial"
       | none => false)
  unless isMv && ty.getAppArgs.size ≥ 2 do return none
  let args := ty.getAppArgs
  match ← finArity? args[0]! with
  | none => return none
  | some n =>
    -- IR supports arbitrary Fin n; Meta close examples currently exercise n∈{2,3}.
    unless n ≥ 2 && n ≤ 4 do return none
    let R ← whnfR args[1]!
    if R.isConstOf ``Int then return some (n, false)
    if R.isConstOf ``_root_.Rat then return some (n, true)
    match R.getAppFn.constName? with
    | some cn =>
      let s := cn.getString!
      if s == "Int" then return some (n, false)
      if s == "Rat" then return some (n, true)
      return none
    | none => return none

/-- Extract a concrete `Fin n` index as `Nat`. -/
private partial def finIndex? (e : Expr) : MetaM (Option Nat) := do
  let e ← whnfR e
  if let some n := natLitOnly? e then return some n
  if e.isAppOfArity ``OfNat.ofNat 3 then
    return natLitOnly? e.appFn!.appArg!
  if e.isAppOf ``Fin.mk then
    let args := e.getAppArgs
    if args.size ≥ 1 then return natLitOnly? (← whnfR args[0]!)
    else return none
  if e.isAppOf ``Fin.ofNat || e.isAppOf ``Fin.ofNat' then
    let args := e.getAppArgs
    if args.size ≥ 1 then return natLitOnly? (← whnfR args.back!)
    else return none
  return none

/-- Zero exponents vector of length `n`. -/
private def zeroExps (n : Nat) : List Nat :=
  List.replicate n 0

/-- Unit vector `e_i` of length `n`. -/
private def unitExps (n i : Nat) : Option (List Nat) :=
  if i ≥ n then none
  else some ((List.range n).map fun j => if j == i then 1 else 0)

/-- Accumulate a sparse multivariate term. -/
private def addMvTerm (n : Nat) (acc : SparsePoly) (c : Int) (exps : List Nat) : SparsePoly :=
  if c == 0 then acc
  else if exps.length != n then acc
  else
    MathEvidence.Checkers.IdealMembership.normalize {
      varCount := n
      terms := acc.terms ++ [{ coefficient := c, monomial := ⟨exps⟩ }]
    }

private partial def reifyMvPolyExpr (n : Nat) (e : Expr) : MetaM (Except Reject SparsePoly) := do
  let e ← whnfR e
  -- MvPolynomial.X i
  let isMvX :=
    e.isAppOf ``MvPolynomial.X ||
      (match e.getAppFn.constName? with
       | some cn =>
         cn.getString! == "X" &&
           (cn.toString.endsWith "MvPolynomial.X" || cn.toString.endsWith ".MvPolynomial.X")
       | none => false)
  if isMvX then
    let args := e.getAppArgs
    if args.size ≥ 1 then
      match ← finIndex? args.back! with
      | none => return failExpr "MvPolynomial.X expects a Fin index literal"
      | some i =>
        match unitExps n i with
        | none => return failExpr s!"MvPolynomial.X index {i} out of range for Fin {n}"
        | some exps =>
          return .ok {
            varCount := n
            terms := [{ coefficient := 1, monomial := ⟨exps⟩ }]
          }
  -- Integer / constant literals
  if let some c ← intLit? e then
    return .ok (addMvTerm n (SparsePoly.zero n) c (zeroExps n))
  if e.isAppOf ``MvPolynomial.C then
    match ← intLit? e.appArg! with
    | some c => return .ok (addMvTerm n (SparsePoly.zero n) c (zeroExps n))
    | none => return failExpr "MvPolynomial.C expects an integer literal"
  if e.isAppOf ``Nat.cast || e.isAppOf ``Int.cast || e.isAppOf ``Rat.cast then
    return ← reifyMvPolyExpr n e.appArg!
  -- Negation
  if e.isAppOfArity ``Neg.neg 3 || e.isAppOf ``Neg.neg then
    match ← reifyMvPolyExpr n e.appArg! with
    | .error err => return .error err
    | .ok p =>
      return .ok {
        varCount := n
        terms := p.terms.map fun t => { t with coefficient := -t.coefficient }
      }
  -- Binary ops
  if e.isAppOf ``HAdd.hAdd || e.isAppOf ``Add.add then
    let args := e.getAppArgs
    if args.size ≥ 2 then
      match ← reifyMvPolyExpr n args[args.size - 2]!, ← reifyMvPolyExpr n args[args.size - 1]! with
      | .ok a, .ok b =>
        return .ok (MathEvidence.Checkers.IdealMembership.normalize (SparsePoly.add a b))
      | .error err, _ => return .error err
      | _, .error err => return .error err
  if e.isAppOf ``HSub.hSub || e.isAppOf ``Sub.sub then
    let args := e.getAppArgs
    if args.size ≥ 2 then
      match ← reifyMvPolyExpr n args[args.size - 2]!, ← reifyMvPolyExpr n args[args.size - 1]! with
      | .ok a, .ok b =>
        let negB : SparsePoly := {
          varCount := n
          terms := b.terms.map fun t => { t with coefficient := -t.coefficient }
        }
        return .ok (MathEvidence.Checkers.IdealMembership.normalize (SparsePoly.add a negB))
      | .error err, _ => return .error err
      | _, .error err => return .error err
  if e.isAppOf ``HMul.hMul || e.isAppOf ``Mul.mul then
    let args := e.getAppArgs
    if args.size ≥ 2 then
      match ← reifyMvPolyExpr n args[args.size - 2]!, ← reifyMvPolyExpr n args[args.size - 1]! with
      | .ok a, .ok b =>
        return .ok (MathEvidence.Checkers.IdealMembership.normalize (SparsePoly.mul a b))
      | .error err, _ => return .error err
      | _, .error err => return .error err
  if e.isAppOf ``HPow.hPow || e.isAppOf ``Pow.pow then
    let args := e.getAppArgs
    if args.size ≥ 2 then
      match ← reifyMvPolyExpr n args[args.size - 2]!, ← intLit? args[args.size - 1]! with
      | .ok base, some expNat =>
        if expNat < 0 then return failExpr "negative polynomial power"
        let exp := expNat.toNat
        let mut acc := addMvTerm n (SparsePoly.zero n) 1 (zeroExps n)
        for _ in [:exp] do
          acc := MathEvidence.Checkers.IdealMembership.normalize (SparsePoly.mul acc base)
        return .ok acc
      | .error err, _ => return .error err
      | _, none => return failExpr "polynomial power exponent must be a nat literal"
  return failExpr s!"unsupported MvPolynomial expression head {e.getAppFn}"

/-- Meta entry: reify concrete `MvPolynomial (Fin n) ℤ` / `ℚ` (n ≤ 4). -/
def reifyLeanMvPoly (e : Expr) : MetaM (Except Reject PolyResult) := do
  let ty ← inferType e
  match ← isMvPolyType ty with
  | none =>
    return failType s!"expected MvPolynomial (Fin n) Int/Rat (got {ty})"
  | some (n, overRat) =>
    match ← reifyMvPolyExpr n e with
    | .error err => return .error err
    | .ok p =>
      let p := MathEvidence.Checkers.IdealMembership.normalize p
      if p.varCount != n then
        return failExpr s!"reified polynomial varCount {p.varCount} ≠ {n}"
      return .ok { poly := p, overRat }

/-- Meta entry: univariate `Polynomial R` or multivariate `MvPolynomial (Fin n) R`. -/
def reifyLeanPoly (e : Expr) : MetaM (Except Reject PolyResult) := do
  let ty ← inferType e
  if (← isUnivariatePolyType ty).isSome then
    reifyLeanUnivariatePoly e
  else if (← isMvPolyType ty).isSome then
    reifyLeanMvPoly e
  else
    return failType s!"expected Polynomial or MvPolynomial (Fin n) over Int/Rat (got {ty})"

/-- Match `f ∈ Ideal.span S` and return generators from a finite set literal.

Supports singleton `{g}` and nested `insert` forms `{g₁, g₂, ...}` (pretty-printed
`Ideal.span {g₁, g₂}`).
-/
def matchMemSpanGenerators (e : Expr) : MetaM (Option (Expr × Array Expr)) := do
  let e0 ← instantiateMVars e
  let candidates := #[e0, ← whnf e0]
  for e in candidates do
    let isMem :=
      e.isAppOf ``Membership.mem ||
        (match e.getAppFn.constName? with
         | some n => n.getString! == "mem" || n.toString.endsWith "Membership.mem"
         | none => false)
    unless isMem do continue
    let args := e.getAppArgs
    if args.size < 2 then continue
    let coll := args[args.size - 2]!
    let f := args[args.size - 1]!
    let s ← whnfR coll
    let spanArgs := s.getAppArgs
    let fnName? := s.getAppFn.constName?
    let isSpan :=
      match fnName? with
      | some n =>
        let str := n.toString
        n.getString! == "span" || str.endsWith ".span" || str.endsWith "Ideal.span"
      | none => false
    unless isSpan && spanArgs.size ≥ 1 do continue
    let setExpr ← whnfR spanArgs.back!
    let mut gens : Array Expr := #[]
    let mut cur ← whnfR setExpr
    let mut guard := 16
    while guard > 0 do
      guard := guard - 1
      if cur.isAppOf ``Singleton.singleton ||
          (match cur.getAppFn.constName? with
           | some n => n.getString! == "singleton" || n.toString.endsWith ".singleton"
           | none => false) then
        let gArgs := cur.getAppArgs
        if gArgs.size ≥ 1 then
          gens := gens.push (← whnfR gArgs.back!)
        break
      if cur.isAppOf ``EmptyCollection.emptyCollection ||
          (match cur.getAppFn.constName? with
           | some n =>
             let s := n.getString!
             s == "emptyCollection" || s == "emptyset" || s == "empty"
           | none => false) then
        break
      if cur.isAppOf ``Insert.insert ||
          (match cur.getAppFn.constName? with
           | some n => n.getString! == "insert" || n.toString.endsWith ".insert"
           | none => false) then
        let gArgs := cur.getAppArgs
        if gArgs.size ≥ 2 then
          gens := gens.push (← whnfR gArgs[gArgs.size - 2]!)
          cur ← whnfR gArgs.back!
          continue
      -- unrecognized set constructor
      gens := #[]
      break
    if gens.size ≥ 1 then
      return some (← whnfR f, gens)
  return none

/-- Match `f ∈ Ideal.span {g}` (singleton generator). -/
def matchMemSpanSingleton (e : Expr) : MetaM (Option (Expr × Expr)) := do
  match ← matchMemSpanGenerators e with
  | some (f, gens) =>
    if gens.size = 1 then return some (f, gens[0]!)
    else return none
  | none => return none

end MathEvidence.Tactic.ReifyPolynomial
