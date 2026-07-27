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
import MathEvidence.IR.Polynomial.Normalize
import MathEvidence.IR.Polynomial.Interpret
import MathEvidence.IR.Polynomial.Soundness
import MathEvidence.Encoding.Polynomial

/-!
# Polynomial Meta reification (proof-producing, ME-RV-033)

Lowers concrete Lean polynomial terms into fixed-arity sparse IR and returns a
proof object `h : p.eval = e` (MvPolynomial) or `h : p.evalPoly = e` (ℤ[X]) when
the ambient ring/variable type is supported. Unsupported rings fail.
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

/-- Reification result: erased IR + typed decode key + interpretation equality. -/
structure PolyResult where
  /-- Variable arity. -/
  m : Nat
  /-- Erased sparse IR (well-formed by construction). -/
  erased : SparsePolyᵤ
  /-- Quoted `SparsePoly m` expression (for soundness application). -/
  polyE : Expr
  /-- `true` when ambient ring is `ℚ`; otherwise `ℤ`. -/
  overRat : Bool
  /-- Proof term of `SparsePoly.eval … = original` or `evalPoly … = original`. -/
  eqProof : Expr

/-- Decode reified IR into typed `SparsePoly m`. -/
def PolyResult.toTyped? (r : PolyResult) : Option (SparsePoly r.m) :=
  SparsePolyᵤ.toSparse? r.m r.erased

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
    unless n ≥ 1 && n ≤ 4 do return none
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

/-- Quote a concrete `SparsePoly m` value as an Expr via constructors when possible. -/
def quoteTypedPoly {m : Nat} (p : SparsePoly m) : MetaM Expr := do
  -- Prefer constructor forms when the poly matches C / X / zero.
  if p.terms.isEmpty then
    return ← mkAppM ``SparsePoly.zero #[toExpr m]
  match p.terms with
  | [t] =>
    let exps := t.monomial.exponents.toList
    if exps.all (· = 0) then
      return ← mkAppM ``SparsePoly.C #[toExpr m, toExpr t.coefficient]
    -- Single indeterminate X_i
    let mut idx? : Option Nat := none
    let mut ok := t.coefficient == 1
    let mut j : Nat := 0
    for e in exps do
      if e ≠ 0 then
        if e == 1 && idx?.isNone then idx? := some j
        else ok := false
      j := j + 1
    if ok then
      if let some i := idx? then
        let hi ← mkDecideProof (← mkLt (toExpr i) (toExpr m))
        -- SparsePoly.X (m i : Nat) (hi : i < m); no leading implicit to skip.
        return ← mkAppOptM ``SparsePoly.X #[toExpr m, toExpr i, some hi]
  | _ => pure ()
  -- Fallback: rebuild by summing quoted monomials (closed decide proofs; no metavars).
  let mut acc? : Option Expr := none
  for t in p.terms do
    let xs := t.monomial.exponents.toList
    unless xs.length == m do
      throwError "quoteTypedPoly: exponent arity mismatch"
    let xsE := toExpr xs
    let lenEq ← mkEq (← mkAppM ``List.length #[xsE]) (toExpr m)
    let lenPf ← mkDecideProof lenEq
    let mon ← mkAppM ``Monomial.ofList! #[toExpr m, xsE, lenPf]
    let term ← mkAppM ``MathEvidence.IR.Polynomial.Term.mk #[toExpr t.coefficient, mon]
    let termList ← mkAppM ``List.cons #[term,
      ← mkAppOptM ``List.nil #[some (← mkAppM ``MathEvidence.IR.Polynomial.Term #[toExpr m])]]
    let one ← mkAppM ``SparsePoly.mk #[termList]
    match acc? with
    | none => acc? := some one
    | some acc => acc? := some (← mkAppM ``SparsePoly.add #[acc, one])
  match acc? with
  | some e => return e
  | none => mkAppM ``SparsePoly.zero #[toExpr m]

private structure MvOk where
  poly : SparsePolyᵤ
  polyE : Expr
  eqProof : Expr

/-- Build `eqProof : eval p = e` by composing SparsePoly constructor lemmas. -/
private partial def reifyMv
    (m : Nat) (e : Expr) : MetaM (Except Reject MvOk) := do
  let e ← whnfR e
  let finish (p : SparsePoly m) (polyE : Expr) (proof : Expr) :
      MetaM (Except Reject MvOk) := do
    return .ok { poly := p.toErased, polyE := polyE, eqProof := proof }

  -- X i
  if e.isAppOf ``MvPolynomial.X then
    let args := e.getAppArgs
    let iExpr := args.back!
    let some i := natLitOnly? (← whnfR iExpr) <|> (← do
      if iExpr.isAppOfArity ``OfNat.ofNat 3 then
        pure (natLitOnly? iExpr.appFn!.appArg!)
      else if iExpr.isAppOf ``Fin.mk then
        pure (natLitOnly? (← whnfR iExpr.appFn!.appArg!))
      else pure none)
      | return failExpr "MvPolynomial.X index must be a nat literal"
    if h : i < m then
      let hi ← mkDecideProof (← mkLt (toExpr i) (toExpr m))
      let p : SparsePoly m := SparsePoly.X m i h
      let polyE ← mkAppOptM ``SparsePoly.X #[toExpr m, toExpr i, some hi]
      let eqX ← mkAppOptM ``SparsePoly.eval_X #[toExpr m, toExpr i, some hi]
      let proof ← mkExpectedTypeHint eqX
        (← mkEq (← mkAppM ``SparsePoly.eval #[polyE]) e)
      return ← finish p polyE proof
    else
      return failExpr "MvPolynomial.X index out of range"

  if let some c ← intLit? e then
    let p := SparsePoly.C m c
    let polyE ← mkAppM ``SparsePoly.C #[toExpr m, toExpr c]
    let proof ← mkAppM ``SparsePoly.eval_C #[toExpr m, toExpr c]
    let proof ← mkExpectedTypeHint proof
      (← mkEq (← mkAppM ``SparsePoly.eval #[polyE]) e)
    return ← finish p polyE proof

  if e.isAppOf ``MvPolynomial.C then
    match ← intLit? e.appArg! with
    | some c =>
      let p := SparsePoly.C m c
      let polyE ← mkAppM ``SparsePoly.C #[toExpr m, toExpr c]
      let proof ← mkAppM ``SparsePoly.eval_C #[toExpr m, toExpr c]
      let proof ← mkExpectedTypeHint proof
        (← mkEq (← mkAppM ``SparsePoly.eval #[polyE]) e)
      return ← finish p polyE proof
    | none => return failExpr "MvPolynomial.C expects an integer literal"

  if e.isAppOf ``HAdd.hAdd || e.isAppOf ``Add.add then
    let args := e.getAppArgs
    if args.size ≥ 2 then
      let ea := args[args.size - 2]!
      let eb := args[args.size - 1]!
      match ← reifyMv m ea, ← reifyMv m eb with
      | .ok a, .ok b =>
        let some pa := SparsePolyᵤ.toSparse? m a.poly | return failExpr "add lhs decode"
        let some pb := SparsePolyᵤ.toSparse? m b.poly | return failExpr "add rhs decode"
        let p := pa.add pb
        let polyE ← mkAppM ``SparsePoly.add #[a.polyE, b.polyE]
        let proof ← mkAppM ``reify_add_eq #[a.polyE, b.polyE, ea, eb, a.eqProof, b.eqProof]
        let proof ← mkExpectedTypeHint proof
          (← mkEq (← mkAppM ``SparsePoly.eval #[polyE]) e)
        return ← finish p polyE proof
      | .error err, _ => return .error err
      | _, .error err => return .error err

  if e.isAppOf ``HMul.hMul || e.isAppOf ``Mul.mul then
    let args := e.getAppArgs
    if args.size ≥ 2 then
      let ea := args[args.size - 2]!
      let eb := args[args.size - 1]!
      match ← reifyMv m ea, ← reifyMv m eb with
      | .ok a, .ok b =>
        let some pa := SparsePolyᵤ.toSparse? m a.poly | return failExpr "mul lhs decode"
        let some pb := SparsePolyᵤ.toSparse? m b.poly | return failExpr "mul rhs decode"
        let p := pa.mul pb
        let polyE ← mkAppM ``SparsePoly.mul #[a.polyE, b.polyE]
        let proof ← mkAppM ``reify_mul_eq #[a.polyE, b.polyE, ea, eb, a.eqProof, b.eqProof]
        let proof ← mkExpectedTypeHint proof
          (← mkEq (← mkAppM ``SparsePoly.eval #[polyE]) e)
        return ← finish p polyE proof
      | .error err, _ => return .error err
      | _, .error err => return .error err

  if e.isAppOfArity ``Neg.neg 3 || e.isAppOf ``Neg.neg then
    let ea := e.appArg!
    match ← reifyMv m ea with
    | .error err => return .error err
    | .ok a =>
      let some pa := SparsePolyᵤ.toSparse? m a.poly | return failExpr "neg decode"
      let p := pa.neg
      let polyE ← mkAppM ``SparsePoly.neg #[a.polyE]
      let proof ← mkAppM ``reify_neg_eq #[a.polyE, ea, a.eqProof]
      let proof ← mkExpectedTypeHint proof
        (← mkEq (← mkAppM ``SparsePoly.eval #[polyE]) e)
      return ← finish p polyE proof

  if e.isAppOf ``HSub.hSub || e.isAppOf ``Sub.sub then
    let args := e.getAppArgs
    if args.size ≥ 2 then
      let ea := args[args.size - 2]!
      let eb := args[args.size - 1]!
      match ← reifyMv m ea, ← reifyMv m eb with
      | .ok a, .ok b =>
        let some pa := SparsePolyᵤ.toSparse? m a.poly | return failExpr "sub lhs decode"
        let some pb := SparsePolyᵤ.toSparse? m b.poly | return failExpr "sub rhs decode"
        let p := pa.sub pb
        let polyE ← mkAppM ``SparsePoly.sub #[a.polyE, b.polyE]
        let proof ← mkAppM ``reify_sub_eq #[a.polyE, b.polyE, ea, eb, a.eqProof, b.eqProof]
        let proof ← mkExpectedTypeHint proof
          (← mkEq (← mkAppM ``SparsePoly.eval #[polyE]) e)
        return ← finish p polyE proof
      | .error err, _ => return .error err
      | _, .error err => return .error err

  if e.isAppOf ``HPow.hPow || e.isAppOf ``Pow.pow then
    let args := e.getAppArgs
    if args.size ≥ 2 then
      let ea := args[args.size - 2]!
      match ← reifyMv m ea, ← intLit? args[args.size - 1]! with
      | .ok a, some expNat =>
        if expNat < 0 then return failExpr "negative power"
        let n := expNat.toNat
        let some pa := SparsePolyᵤ.toSparse? m a.poly | return failExpr "pow decode"
        let p := pa.npow n
        let polyE ← mkAppM ``SparsePoly.npow #[a.polyE, toExpr n]
        let proof ← mkAppM ``reify_npow_eq #[a.polyE, toExpr n, ea, a.eqProof]
        let proof ← mkExpectedTypeHint proof
          (← mkEq (← mkAppM ``SparsePoly.eval #[polyE]) e)
        return ← finish p polyE proof
      | .error err, _ => return .error err
      | _, none => return failExpr "power exponent must be nat literal"

  return failExpr s!"unsupported MvPolynomial expression for proof-producing reify"

/-- Meta entry: reify with proof object (ME-RV-033).

Stable fragment: `MvPolynomial (Fin n) Int` for `1 <= n <= 4`.
`Polynomial R` / Rat rings are rejected (use `MvPolynomial (Fin 1) Int`).
-/
def reifyLeanPoly (e : Expr) : MetaM (Except Reject PolyResult) := do
  let ty ← inferType e
  match ← isMvPolyType ty with
  | some (_m, true) =>
    return failType "proof-producing reifier supports Int only (Rat unsupported)"
  | some (m, false) =>
    match ← reifyMv m e with
    | .error err => return .error err
    | .ok r =>
      return .ok {
        m := m
        erased := r.poly
        polyE := r.polyE
        overRat := false
        eqProof := r.eqProof
      }
  | none =>
    match ← isUnivariatePolyType ty with
    | none =>
      return failType s!"expected MvPolynomial (Fin n) Int (got {ty})"
    | some _ =>
      return failType "use MvPolynomial (Fin 1) Int (Polynomial R Meta close deferred)"

/-- Peel wrappers until `Ideal.span` is visible (prefer pre-whnf form). -/
private partial def findIdealSpan (e : Expr) : MetaM (Option Expr) := do
  if e.isAppOf ``Ideal.span then
    return some e
  -- Prefer scanning args before aggressive unfolding.
  for c in e.getAppArgs do
    if c.isAppOf ``Ideal.span then
      return some c
  if e.isAppOf ``SetLike.coe then
    let args := e.getAppArgs
    if args.size ≥ 1 then
      return ← findIdealSpan args.back!
  if e.isAppOf ``Coe.coe || e.isAppOf ``CoeTC.coe || e.isAppOf ``CoeFun.coe then
    let args := e.getAppArgs
    if args.size ≥ 1 then
      return ← findIdealSpan args.back!
  let e' ← whnfR e
  if e'.isAppOf ``Ideal.span then
    return some e'
  if e' != e then
    return ← findIdealSpan e'
  for c in e'.getAppArgs do
    if let some s ← findIdealSpan c then
      return some s
  return none

/-- Collect generators from `{g}` / `{g₁, g₂, …}` / `Insert` chains. -/
private partial def collectSpanGens (e : Expr) (acc : Array Expr) : MetaM (Array Expr) := do
  let e0 := e
  let e ← whnfR e
  if e.isAppOf ``Insert.insert then
    let args := e.getAppArgs
    if args.size ≥ 2 then
      collectSpanGens args.back! (acc.push args[args.size - 2]!)
    else
      pure acc
  else if e.isAppOf ``Singleton.singleton then
    let args := e.getAppArgs
    if args.size ≥ 1 then pure (acc.push args.back!) else pure acc
  else if e.isAppOf ``EmptyCollection.emptyCollection then
    pure acc
  else
    -- Also try the pre-whnf form for notation macros.
    let eTry := if e0 != e then e0 else e
    match eTry.getAppFn.constName? with
    | some n =>
      let s := n.toString
      if (s.endsWith ".insert" || s.endsWith "Insert.insert") && eTry.getAppArgs.size ≥ 2 then
        let args := eTry.getAppArgs
        collectSpanGens args.back! (acc.push args[args.size - 2]!)
      else if (s.endsWith ".singleton" || s.endsWith "Singleton.singleton") &&
          eTry.getAppArgs.size ≥ 1 then
        pure (acc.push eTry.getAppArgs.back!)
      else if e != e0 then
        match e.getAppFn.constName? with
        | some n2 =>
          let s2 := n2.toString
          if s2.endsWith ".insert" && e.getAppArgs.size ≥ 2 then
            let args := e.getAppArgs
            collectSpanGens args.back! (acc.push args[args.size - 2]!)
          else if s2.endsWith ".singleton" && e.getAppArgs.size ≥ 1 then
            pure (acc.push e.getAppArgs.back!)
          else
            pure acc
        | none => pure acc
      else
        pure acc
    | none => pure acc

/-- True when `e` is a membership application (`Membership.mem` / `Set.Mem`). -/
private def isMembershipApp (e : Expr) : Bool :=
  e.isAppOf ``Membership.mem || e.isAppOf ``Set.Mem ||
    (match e.getAppFn.constName? with
     | some n =>
       let s := n.toString
       s.endsWith ".Mem" || s.endsWith ".mem" || s.endsWith "Membership.mem"
     | none => false)

/-- Extract `(element, container)` from a membership application.

Lean 4.14 `Membership.mem : γ → α → Prop` is **container then element**
(`args[n-2] = container`, `args[n-1] = element`). `Set.Mem` uses the same
container-first order. Older code that assumed element-first silently failed
on every live `Ideal.span` goal.
-/
private def membershipEnds (e : Expr) : Option (Expr × Expr) :=
  let args := e.getAppArgs
  if args.size < 2 then none
  else
    -- Try container-first (canonical Lean 4.14), then element-first fallback.
    some (args[args.size - 1]!, args[args.size - 2]!)

/-- Match `f ∈ Ideal.span {g₁, …}` returning `f` and generator exprs.

Handles `Membership.mem`, `Set.Mem`, and `SetLike.coe` wrappers around `Ideal.span`.
-/
partial def matchMemSpanGenerators (goalType : Expr) :
    MetaM (Option (Expr × Array Expr)) := do
  let goal0 ← instantiateMVars goalType
  -- Try both raw and weakly-headed forms: `whnf` may unfold SetLike membership.
  let candidates := #[goal0, ← whnfR goal0, ← whnf goal0]
  for goalType in candidates do
    unless isMembershipApp goalType do
      continue
    let some (fCand, setCand) := membershipEnds goalType | continue
    -- Primary: Lean 4.14 container-first (setCand = container, fCand = element).
    for (f, rawSet) in #[(fCand, setCand), (setCand, fCand)] do
      let some spanExpr ← findIdealSpan rawSet | continue
      let setExpr := spanExpr.appArg!
      let gens ← collectSpanGens setExpr #[]
      if gens.isEmpty then continue
      return some (f, gens)
  return none

end MathEvidence.Tactic.ReifyPolynomial
