/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import MathEvidence.Checkers.Counterexample.Check
import MathEvidence.Checkers.Counterexample.Certificate
import MathEvidence.Checkers.Counterexample.Soundness
import MathEvidence.Checkers.Counterexample.Spec
import MathEvidence.Encoding.Finite
import MathEvidence.Tactic.ReifyFinitePredicate

/-!
# Counterexample tactic (ME-103)

`mathevidence_counterexample` reifies supported `¬∀` Fin/Bool/Nat/Int goals, checks the
suggested witness through the finite-counterexample checker contract, then
closes by `native_decide` (finite domains) or an explicit Int witness close
(bounded Int is not `native_decide`-friendly as an unbounded `∀`).
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

private def intLitTerm (i : Int) : MetaM Lean.Term := do
  if i ≥ 0 then
    `(term| ($(quote i.toNat) : Int))
  else
    `(term| (-($(quote (-i).toNat) : Int)))

/-- Close `¬ ∀ x : Int, lo ≤ x → x ≤ hi → x = k` with an explicit refuting witness. -/
private def closeBoundedIntEq (lo hi k w : Int) : TacticM Unit := do
  unless lo ≤ w && w ≤ hi && w ≠ k do
    throwError "mathevidence counterexample: Int witness out of bounds or not refuting"
  let wStx ← intLitTerm w
  let kStx ← intLitTerm k
  -- Goal is `¬ ∀ ...`. Introduce the forall, apply at `w`, contradict `w = k`.
  evalTactic (← `(tactic|
    refine fun h =>
      (by native_decide : ¬($wStx = $kStx))
        (h $wStx (by native_decide) (by native_decide))))

/-- `mathevidence_counterexample` — Meta reify + checker gate + close. -/
elab "mathevidence_counterexample" : tactic => do
  let goal ← getMainGoal
  let goalType ← instantiateMVars (← goal.getType)
  let result ← reifyLeanPredicateGoal goalType
  match result with
  | .error err =>
    throwError "{unsupportedMessage}\nreason: {Reject.format err}"
  | .ok { reified := r, suggestedWitness := σ } =>
    unless MathEvidence.IR.FinitePredicate.isCounterexample σ r.pred do
      throwError "mathevidence counterexample: suggested witness does not refute IR predicate"
    unless Assignment.wellFormed r.domains σ do
      throwError "mathevidence counterexample: witness out of domain"
    let claim : Claim := {
      varNames := r.varNames
      domains := r.domains
      pred := r.pred
      claimClass := .refutation
    }
    let req := Request.ofClaim claim
    let cert : Certificate := {
      requestDigest := req.requestDigest
      witness := σ
    }
    unless checkBool req cert do
      throwError "mathevidence counterexample: Lean checker rejected witness certificate"
    -- Bounded Int: close with explicit witness (∀ over Int is not native_decide).
    match r.domains, r.pred, σ with
    | [⟨.int, none, some (.lit (.int lo)), some (.lit (.int hi))⟩],
      .eq (.var 0) (.lit (.int k)),
      [.int w] =>
      closeBoundedIntEq lo hi k w
    | _, _, _ =>
      evalTactic (← `(tactic| native_decide))

end MathEvidence.Tactic.Counterexample
