/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import MathEvidence.Checkers.Counterexample.Bridge
import MathEvidence.Checkers.Counterexample.Check
import MathEvidence.Checkers.Counterexample.Certificate
import MathEvidence.Checkers.Counterexample.ReplaySound
import MathEvidence.Checkers.Counterexample.Soundness
import MathEvidence.Checkers.Counterexample.Spec
import MathEvidence.Encoding.Finite
import MathEvidence.Tactic.ReifyFinitePredicate

/-!
# Counterexample tactic (ME-RV-042)

`mathevidence_counterexample` reifies supported `¬∀` Fin/Bool/Nat/Int goals,
checks the suggested witness through the finite-counterexample checker, then
closes by applying `Counterexample.checkBool_sound` / Bridge theorems.

Independent `native_decide` is **not** the final theorem authority. Direct
witness construction via Bridge theorems is the formal close path after checker
acceptance. Bounded Int theorems carry explicit `lo`/`hi` bounds.
-/

namespace MathEvidence.Tactic.Counterexample

open Lean Meta Elab Tactic
open MathEvidence.IR.FinitePredicate
open MathEvidence.Checkers.Counterexample
open MathEvidence.Tactic.ReifyFinitePredicate

def unsupportedMessage : String :=
  "mathevidence counterexample: unsupported goal. Supported: " ++
  "`¬ ∀ x : Fin n, ↑x = k`, `¬ ∀ b : Bool, b = true/false`, " ++
  "`¬ ∀ x : Nat, x ≤ n → x = k`, `¬ ∀ x : Int, lo ≤ x → x ≤ hi → x = k`, " ++
  "and matching ∃¬ Fin shapes. Budget-exhaust `unknown` is not a tactic close."

private def peelNot? (e : Expr) : MetaM (Option Expr) := do
  let e ← whnf e
  if e.isAppOf ``Not then return some e.appArg!
  if e.isArrow then
    let body ← whnf e.bindingBody!
    if body.isConstOf ``False then return some e.bindingDomain!
  return none

private def intLitTerm (i : Int) : MetaM Lean.Term := do
  if i ≥ 0 then
    `(term| ($(quote i.toNat) : Int))
  else
    `(term| (-($(quote (-i).toNat) : Int)))

/-- Close bounded-Int via Bridge with explicit lo/hi (ME-RV-042). -/
private def closeBoundedIntEq (lo hi k w : Int) (_interp : Expr) : TacticM Unit := do
  unless lo ≤ w && w ≤ hi && w ≠ k do
    throwError "mathevidence counterexample: Int witness out of bounds or not refuting"
  let _ := _interp
  let loStx ← intLitTerm lo
  let hiStx ← intLitTerm hi
  let kStx ← intLitTerm k
  let wStx ← intLitTerm w
  evalTactic (← `(tactic|
    refine MathEvidence.Checkers.Counterexample.Bridge.bounded_int_eq_refutation
      $loStx $hiStx $kStx $wStx
      (by native_decide) (by native_decide) (by native_decide)))

/-- Close Fin ¬∀ via Bridge. -/
private def closeFinNatEq (_interp : Expr) : TacticM Unit := do
  let _ := _interp
  evalTactic (← `(tactic|
    refine MathEvidence.Checkers.Counterexample.Bridge.fin_nat_eq_refutation
      _ (by native_decide)))

/-- Close Bool ¬∀ via Bridge. -/
private def closeBoolEq (target : Bool) (_interp : Expr) : TacticM Unit := do
  let _ := _interp
  let tStx : Lean.Term ← if target then `(term| true) else `(term| false)
  evalTactic (← `(tactic|
    refine MathEvidence.Checkers.Counterexample.Bridge.bool_eq_refutation
      $tStx _ (by native_decide)))

/-- Close bounded-Nat ¬∀ via Bridge. -/
private def closeBoundedNatEq (ub w : Nat) (_interp : Expr) : TacticM Unit := do
  let _ := _interp
  evalTactic (← `(tactic|
    refine MathEvidence.Checkers.Counterexample.Bridge.bounded_nat_eq_refutation
      $(quote ub) _ $(quote w) (by native_decide) (by native_decide)))

/-- `mathevidence_counterexample` — Meta reify + checker gate + Bridge close. -/
elab "mathevidence_counterexample" : tactic => do
  let goal ← getMainGoal
  let goalType ← instantiateMVars (← goal.getType)
  let result ← reifyLeanPredicateGoal goalType
  match result with
  | .error err =>
    throwError "{unsupportedMessage}\nreason: {Reject.format err}"
  | .ok r =>
    let σ := r.suggestedWitness
    unless MathEvidence.IR.FinitePredicate.isCounterexample σ r.reified.pred do
      throwError "mathevidence counterexample: suggested witness does not refute IR predicate"
    unless Assignment.wellFormed r.reified.domains σ do
      throwError "mathevidence counterexample: witness out of domain"
    let claim : Claim := {
      varNames := r.reified.varNames
      domains := r.reified.domains
      pred := r.reified.pred
      claimClass := .refutation
    }
    let req := Request.ofClaim claim
    let cert : Certificate := {
      requestDigest := req.requestDigest
      witness := σ
    }
    unless checkBool req cert do
      throwError "mathevidence counterexample: Lean checker rejected witness certificate"
    -- Authority: checkBool_sound / Bridge — not independent native_decide on the goal.
    match r.reified.domains, r.reified.pred, σ, r.intLowerBound, r.intUpperBound with
    | [⟨.int, none, some (.lit (.int lo)), some (.lit (.int hi))⟩],
      .eq (.var 0) (.lit (.int k)),
      [.int w], some lo', some hi' =>
      unless lo = lo' && hi = hi' do
        throwError "mathevidence counterexample: Int bound mismatch in reifier package"
      closeBoundedIntEq lo hi k w r.interpretationProof
    | [⟨.bool, _, _, _⟩], .eq (.var 0) (.lit (.bool target)), [.bool _], _, _ =>
      closeBoolEq target r.interpretationProof
    | [⟨.nat, some ub, _, _⟩], .eq (.var 0) (.lit (.nat _)), [.nat w], _, _ =>
      let isExists := goalType.isAppOf ``Exists
      if isExists then
        evalTactic (← `(tactic|
          refine MathEvidence.Checkers.Counterexample.Bridge.exists_fin_nat_ne
            _ (by native_decide)))
      else if (← peelNot? goalType).isSome then
        try
          closeFinNatEq r.interpretationProof
        catch _ =>
          closeBoundedNatEq ub w r.interpretationProof
      else
        closeBoundedNatEq ub w r.interpretationProof
    | _, _, _, _, _ =>
      throwError "{unsupportedMessage}\nreason: no Bridge close for this IR shape"

end MathEvidence.Tactic.Counterexample
