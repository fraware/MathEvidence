/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import MathEvidence.Tactic.Discovery
import MathEvidence.Tactic.Status

/-!
# `mathevidence` tactic (Project Spec §12.1)

- **Replay:** `mathevidence replay <BundleId>` — committed evidence, no backends.
- **Discovery:** `mathevidence` / `mathevidence discovery` — Meta-reify ℚ equality;
  offline fixture match by default; live adapter spawn when
  `MATHEVIDENCE_DISCOVERY=1`.
- Kwargs sugar expands to replay / discovery forms.
-/

namespace MathEvidence.Tactic

open Lean Meta Elab Tactic
open MathEvidence.Core
open MathEvidence.Tactic.Discovery

private def evalBundleIdExpr (e : Expr) : TacticM BundleId := do
  let e ← whnf (← instantiateMVars e)
  let name := e.getAppFn.constName?.getD Name.anonymous
  match name with
  | ``BundleId.basicSympy => pure .basicSympy
  | ``BundleId.basicMathematica => pure .basicMathematica
  | ``BundleId.validIdentity => pure .validIdentity
  | ``BundleId.redundantCondition => pure .redundantCondition
  | ``BundleId.variablePermutation => pure .variablePermutation
  | ``BundleId.largeCoeffs => pure .largeCoeffs
  | ``BundleId.falseIdentity => pure .falseIdentity
  | ``BundleId.hashMismatch => pure .hashMismatch
  | _ => throwError "mathevidence: unknown bundle id {e}"

private def runReplay (id : BundleId) : TacticM Unit := do
  let report := replayStatus id
  if report.claimEstablished.isNone then
    throwError "mathevidence replay rejected:\n{report.format}"
  let goal ← getMainGoal
  goal.withContext do
    let tgt ← goal.getType
    unless tgt.isConstOf ``True do
      throwError "mathevidence replay expects goal `True` for status-only close; got {tgt}\n{report.format}"
    logInfo m!"{report.format}"
    goal.assign (mkConst ``True.intro)

/-- `mathevidence replay .basicSympy` -/
elab "mathevidence" "replay" id:term : tactic => do
  let e ← elabTerm id (some (mkConst ``BundleId))
  let bid ← evalBundleIdExpr e
  runReplay bid

/-- `mathevidence discovery` — Meta reify + offline/live orchestration. -/
elab "mathevidence" "discovery" : tactic =>
  runDiscoveryOrchestration .none .soundResult

/-- Bare `mathevidence` = discovery orchestration. -/
elab "mathevidence" : tactic =>
  runDiscoveryOrchestration .none .soundResult

/-- Spec §12.1 kwargs sugar → replay. -/
macro "mathevidence" "(" "mode" ":=" ".replay" ")" "(" "bundle" ":=" b:term ")" : tactic =>
  `(tactic| mathevidence replay $b)

/-- Full kwargs sugar including backend/claim/operation → replay. -/
macro "mathevidence"
    "(" "mode" ":=" ".replay" ")"
    "(" "operation" ":=" _op:term ")"
    "(" "backend" ":=" _backend:term ")"
    "(" "claim" ":=" _claim:term ")"
    "(" "bundle" ":=" b:term ")" : tactic =>
  `(tactic| mathevidence replay $b)

/-- Discovery with explicit backend: `mathevidence discovery with .sympy`. -/
elab "mathevidence" "discovery" "with" b:term : tactic => do
  let e ← elabTerm b (some (mkConst ``Backend))
  let e ← whnf (← instantiateMVars e)
  let be ←
    match e.getAppFn.constName?.getD Name.anonymous with
    | ``Backend.sympy => pure Backend.sympy
    | ``Backend.mathematica => pure Backend.mathematica
    | ``Backend.none => pure Backend.none
    | _ => throwError "mathevidence discovery: unknown backend {e}"
  runDiscoveryOrchestration be .soundResult

end MathEvidence.Tactic
