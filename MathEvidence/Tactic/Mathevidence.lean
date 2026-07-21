/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import MathEvidence.Tactic.Discovery
import MathEvidence.Tactic.Replay
import MathEvidence.Tactic.Status

/-!
# `mathevidence` tactic (Project Spec §12.1)

- **Replay:** `mathevidence replay <BundleId>` — committed evidence, no backends.
- **Discovery:** `mathevidence` / `mathevidence discovery` — Meta-reify ℚ equality;
  offline fixture match by default; live adapter spawn when
  `MATHEVIDENCE_DISCOVERY=1`.
- After checker accept, closes under **explicit** nonzero denom hypotheses via
  `field_simp [*] ; ring` (never claims equality at poles).
- Status report always lists claim requested vs established, bundle path, and
  remaining goals.
- Kwargs sugar expands to replay / discovery forms.
-/

namespace MathEvidence.Tactic

open Lean Meta Elab Tactic
open MathEvidence.Core
open MathEvidence.Tactic.Discovery
open MathEvidence.Tactic.Replay

private def bundleIdOfName? : Name → Option BundleId
  | ``BundleId.basicSympy => some .basicSympy
  | ``BundleId.basicMathematica => some .basicMathematica
  | ``BundleId.validIdentity => some .validIdentity
  | ``BundleId.redundantCondition => some .redundantCondition
  | ``BundleId.variablePermutation => some .variablePermutation
  | ``BundleId.largeCoeffs => some .largeCoeffs
  | ``BundleId.falseIdentity => some .falseIdentity
  | ``BundleId.hashMismatch => some .hashMismatch
  | ``BundleId.laInverse2x2 => some .laInverse2x2
  | ``BundleId.laExactSystem => some .laExactSystem
  | ``BundleId.laKernelVector => some .laKernelVector
  | ``BundleId.laDetIdentity => some .laDetIdentity
  | ``BundleId.laSingularInverseRejected => some .laSingularInverseRejected
  | ``BundleId.laHashMismatch => some .laHashMismatch
  | ``BundleId.cexSimpleFalseUniversal => some .cexSimpleFalseUniversal
  | ``BundleId.cexWitnessTypeMismatch => some .cexWitnessTypeMismatch
  | ``BundleId.cexHashMismatch => some .cexHashMismatch
  | ``BundleId.cexOutOfDomainRejected => some .cexOutOfDomainRejected
  | _ => none

private def bundleIdOfShortName? : String → Option BundleId
  | "basicSympy" => some .basicSympy
  | "basicMathematica" => some .basicMathematica
  | "validIdentity" => some .validIdentity
  | "redundantCondition" => some .redundantCondition
  | "variablePermutation" => some .variablePermutation
  | "largeCoeffs" => some .largeCoeffs
  | "falseIdentity" => some .falseIdentity
  | "hashMismatch" => some .hashMismatch
  | "laInverse2x2" => some .laInverse2x2
  | "laExactSystem" => some .laExactSystem
  | "laKernelVector" => some .laKernelVector
  | "laDetIdentity" => some .laDetIdentity
  | "laSingularInverseRejected" => some .laSingularInverseRejected
  | "laHashMismatch" => some .laHashMismatch
  | "cexSimpleFalseUniversal" => some .cexSimpleFalseUniversal
  | "cexWitnessTypeMismatch" => some .cexWitnessTypeMismatch
  | "cexHashMismatch" => some .cexHashMismatch
  | "cexOutOfDomainRejected" => some .cexOutOfDomainRejected
  | _ => none

private def evalBundleIdExpr (e : Expr) : TacticM BundleId := do
  let e ← whnf (← instantiateMVars e)
  let name := e.getAppFn.constName?.getD Name.anonymous
  match bundleIdOfName? name with
  | some id => pure id
  | none => throwError "mathevidence: unknown bundle id {e}"

private def inspectBundle (id : BundleId) : Lean.Elab.Command.CommandElabM Unit := do
  logInfo m!"{(replayStatus id).format}"

private def runReplay (id : BundleId) : TacticM Unit := do
  let report := replayStatus id
  let expectAccept :=
    match id with
    | .falseIdentity | .hashMismatch
    | .laSingularInverseRejected | .laHashMismatch
    | .cexWitnessTypeMismatch | .cexHashMismatch | .cexOutOfDomainRejected => false
    | _ => true
  if expectAccept && report.claimEstablished.isNone then
    throwError "mathevidence replay rejected:\n{report.format}"
  if !expectAccept && report.claimEstablished.isSome then
    throwError "mathevidence replay unexpectedly accepted reject fixture:\n{report.format}"
  logInfo m!"{report.format}"
  match ← tryReplayTheorem id with
  | .closed => pure ()
  | .unsupported report =>
    throwError
      "mathevidence replay: theorem-producing replay is not available for this \
bundle yet. Status-only replay is forbidden and will not close the goal. Use \
`#mathevidence inspect .<bundle>` for a non-closing status report.\n{report.format}"

/-- `mathevidence replay .basicSympy` -/
elab "mathevidence" "replay" id:term : tactic => do
  let e ← elabTerm id (some (mkConst ``BundleId))
  let bid ← evalBundleIdExpr e
  runReplay bid

/-- `#mathevidence inspect .basicSympy` logs replay status and never closes goals. -/
elab "#mathevidence" "inspect" "." id:ident : command => do
  match bundleIdOfShortName? id.getId.getString! with
  | some bid => inspectBundle bid
  | none => throwError "mathevidence inspect: unknown bundle id .{id.getId}"

/-- `#mathevidence inspect basicSympy` logs replay status and never closes goals. -/
elab "#mathevidence" "inspect" id:ident : command => do
  match bundleIdOfShortName? id.getId.getString! with
  | some bid => inspectBundle bid
  | none => throwError "mathevidence inspect: unknown bundle id {id.getId}"

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
