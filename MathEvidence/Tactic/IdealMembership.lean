/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import Mathlib.RingTheory.Ideal.Basic
import Mathlib.RingTheory.Ideal.Span
import Mathlib.RingTheory.MvPolynomial.Basic
import MathEvidence.Checkers.IdealMembership.Check
import MathEvidence.Checkers.IdealMembership.Soundness
import MathEvidence.Checkers.IdealMembership.Search
import MathEvidence.IR.Polynomial.Normalize
import MathEvidence.Tactic.ReifyPolynomial

/-!
# Ideal-membership tactic (ME-RV-034)

`mathevidence_ideal` reifies a Mathlib `Ideal.span` goal, queries a discovery
backend (`lean_reference_search` by default), gates on the trusted checker, and
closes **only** by applying `mem_span_singleton_of_check` /
`mem_span_pair_of_check` / `checkMembership_sound` transported through reifier
equalities. Independent `ring` is not the final theorem authority.
-/

namespace MathEvidence.Tactic.IdealMembership

open Lean Meta Elab Tactic
open MathEvidence.IR.Polynomial
open MathEvidence.Checkers.IdealMembership
open MathEvidence.Checkers.IdealMembership.Search
open MathEvidence.Tactic.ReifyPolynomial

inductive Backend where
  | lean_reference_search
  | sympy
  | sage
  | mathematica
  | replay
  deriving DecidableEq, Repr, Inhabited

def unsupportedMessage : String :=
  "mathevidence_ideal: unsupported goal. Supported: concrete " ++
  "`f ∈ Ideal.span {g₁,…}` over `MvPolynomial (Fin n) ℤ` (1≤n≤4) with a " ++
  "sparse witness accepted by checkMembership; close via checkMembership_sound " ++
  "+ reifier transport. ℚ coefficient rings are rejected."

private def proposeFromBackend {m : Nat}
    (backend : Backend) (f : SparsePoly m) (gens : Array (SparsePoly m)) :
    MetaM (Option (Array (SparsePoly m))) := do
  match backend with
  | .lean_reference_search | .replay =>
    pure (lean_reference_search f gens)
  | .sympy | .sage | .mathematica =>
    logInfo m!"mathevidence_ideal: backend {repr backend} uses lean_reference_search \
      in-process; Agent/adapter discovery + replay is the external path"
    pure (lean_reference_search f gens)

/-- Build `#[e₁, …, eₙ] : Array (SparsePoly m)` as an Expr. -/
private def mkSparsePolyArrayExpr (m : Nat) (es : Array Expr) : MetaM Expr := do
  let ty ← mkAppM ``SparsePoly #[toExpr m]
  let nil ← mkAppOptM ``List.nil #[some ty]
  let list ← es.foldrM
    (fun e acc => mkAppOptM ``List.cons #[some ty, some e, some acc]) nil
  mkAppOptM ``List.toArray #[some ty, some list]

/-- Prove `checkMembership fE gensE multsE = true` via `native_decide` (Expr-level). -/
private def mkCheckMembershipTrue (fE gensE multsE : Expr) : TacticM Expr := do
  let checkE ← mkAppM ``checkMembership #[fE, gensE, multsE]
  let goalType ← mkEq checkE (toExpr true)
  -- Isolate a fresh goal, discharge with native_decide, return its proof.
  let mvar ← mkFreshExprMVar goalType
  let g := mvar.mvarId!
  g.withContext do
    let [] ← Elab.Tactic.run g (evalTactic (← `(tactic| native_decide))) |
      throwError "mathevidence_ideal: native_decide failed on checkMembership"
  instantiateMVars mvar

/-- Close via soundness + reifier transport (ME-RV-033/034).

Uses Expr-level `mkAppM` — never delaborates proof terms (pretty-printer `⋯`
would otherwise destroy reifier equalities on re-elaboration).
-/
private def closeViaSoundness {m : Nat}
    (_f : SparsePoly m) (gens mults : Array (SparsePoly m))
    (fPolyE : Expr) (genPolyEs : Array Expr)
    (eqProofs : Array Expr) : TacticM Unit := do
  logInfo m!"mathevidence_ideal: authority=checkMembership_sound+reifier_transport \
m={m} gens={gens.size} (Candidate/Certification via Agent kernel_replay)"
  unless eqProofs.size == gens.size + 1 do
    throwError "mathevidence_ideal: reifier eqProofs arity mismatch"
  unless genPolyEs.size == gens.size do
    throwError "mathevidence_ideal: generator polyE arity mismatch"
  unless mults.size == gens.size do
    throwError "mathevidence_ideal: multiplier arity mismatch"
  let multPolyEs ← mults.mapM fun p => quoteTypedPoly p
  let goal ← getMainGoal
  match gens.size with
  | 1 =>
    let gensE ← mkSparsePolyArrayExpr m #[genPolyEs[0]!]
    let multsE ← mkSparsePolyArrayExpr m #[multPolyEs[0]!]
    let hCheck ← mkCheckMembershipTrue fPolyE gensE multsE
    -- Infer `m`, `target`, `gMath` from reifier equalities / goal.
    let proof ← mkAppOptM ``mem_span_singleton_of_check #[
      none, some fPolyE, some genPolyEs[0]!, some multPolyEs[0]!,
      none, none, some eqProofs[0]!, some eqProofs[1]!, some hCheck]
    goal.assign proof
    replaceMainGoal []
  | 2 =>
    let gensE ← mkSparsePolyArrayExpr m #[genPolyEs[0]!, genPolyEs[1]!]
    let multsE ← mkSparsePolyArrayExpr m #[multPolyEs[0]!, multPolyEs[1]!]
    let hCheck ← mkCheckMembershipTrue fPolyE gensE multsE
    let proof ← mkAppOptM ``mem_span_pair_of_check #[
      none, some fPolyE, some genPolyEs[0]!, some genPolyEs[1]!,
      some multPolyEs[0]!, some multPolyEs[1]!,
      none, none, none,
      some eqProofs[0]!, some eqProofs[1]!, some eqProofs[2]!, some hCheck]
    goal.assign proof
    replaceMainGoal []
  | 3 =>
    let gensE ← mkSparsePolyArrayExpr m
      #[genPolyEs[0]!, genPolyEs[1]!, genPolyEs[2]!]
    let multsE ← mkSparsePolyArrayExpr m
      #[multPolyEs[0]!, multPolyEs[1]!, multPolyEs[2]!]
    let hCheck ← mkCheckMembershipTrue fPolyE gensE multsE
    let proof ← mkAppOptM ``mem_span_triple_of_check #[
      none, some fPolyE, some genPolyEs[0]!, some genPolyEs[1]!, some genPolyEs[2]!,
      some multPolyEs[0]!, some multPolyEs[1]!, some multPolyEs[2]!,
      none, none, none, none,
      some eqProofs[0]!, some eqProofs[1]!, some eqProofs[2]!, some eqProofs[3]!,
      some hCheck]
    goal.assign proof
    replaceMainGoal []
  | _ =>
    let gensE ← mkSparsePolyArrayExpr m genPolyEs
    let multsE ← mkSparsePolyArrayExpr m multPolyEs
    let hCheck ← mkCheckMembershipTrue fPolyE gensE multsE
    let proof ← mkAppOptM ``checkMembership_sound #[
      none, some fPolyE, some gensE, some multsE, some hCheck]
    -- Only closes Set.range-shaped goals; insert-span for n>2 still unsupported.
    goal.assign proof
    replaceMainGoal []

def runIdeal (backend : Backend) : TacticM Unit := do
  let goal ← getMainGoal
  let goalType ← instantiateMVars (← goal.getType)
  match ← matchMemSpanGenerators goalType with
  | none => throwError "{unsupportedMessage}\nreason: not an Ideal.span membership goal"
  | some (fExpr, genExprs) =>
    match ← reifyLeanPoly fExpr with
    | .error err => throwError "{unsupportedMessage}\nreason: {Reject.format err}"
    | .ok Rf =>
      let some fTyped := SparsePolyᵤ.toSparse? Rf.m Rf.erased |
        throwError "mathevidence_ideal: failed to decode reified target"
      let mut gensTyped : Array (SparsePoly Rf.m) := #[]
      let mut genPolyEs : Array Expr := #[]
      let mut eqProofs : Array Expr := #[Rf.eqProof]
      for gE in genExprs do
        match ← reifyLeanPoly gE with
        | .error err => throwError "{unsupportedMessage}\nreason: {Reject.format err}"
        | .ok Rg =>
          unless Rg.m == Rf.m do
            throwError "mathevidence_ideal: generator arity mismatch"
          let some gT := SparsePolyᵤ.toSparse? Rf.m Rg.erased |
            throwError "mathevidence_ideal: failed to decode generator"
          gensTyped := gensTyped.push gT
          genPolyEs := genPolyEs.push Rg.polyE
          eqProofs := eqProofs.push Rg.eqProof
      for pf in eqProofs do
        let ty ← inferType pf
        unless ty.isAppOf ``Eq do
          throwError "mathevidence_ideal: reifier did not return an equality proof"
      match ← proposeFromBackend backend fTyped gensTyped with
      | none => throwError "mathevidence_ideal: backend proposed no witness"
      | some mults =>
        unless checkMembership fTyped gensTyped mults do
          throwError "mathevidence_ideal: checkMembership rejected proposed multipliers"
        closeViaSoundness fTyped gensTyped mults Rf.polyE genPolyEs eqProofs

syntax "mathevidence_ideal" : tactic
syntax "mathevidence_ideal" "(" &"backend" " := " ident ")" : tactic
syntax "mathevidence_ideal_membership" : tactic

elab_rules : tactic
  | `(tactic| mathevidence_ideal) => runIdeal .lean_reference_search
  | `(tactic| mathevidence_ideal_membership) => runIdeal .lean_reference_search
  | `(tactic| mathevidence_ideal (backend := $b)) => do
    let name := b.getId.toString
    let backend :=
      match name with
      | "sympy" => Backend.sympy
      | "sage" => Backend.sage
      | "mathematica" => Backend.mathematica
      | "replay" => Backend.replay
      | "lean_reference_search" => Backend.lean_reference_search
      | _ => Backend.lean_reference_search
    runIdeal backend

end MathEvidence.Tactic.IdealMembership
