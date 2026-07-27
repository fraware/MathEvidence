/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import MathEvidence.Checkers.RationalEquality.Check
import MathEvidence.Checkers.RationalEquality.OfflineFixtures
import MathEvidence.Checkers.RationalEquality.ReplaySound
import MathEvidence.Checkers.RationalEquality.Wire
import MathEvidence.Core.Digest
import MathEvidence.Core.EnvironmentLock
import MathEvidence.Core.EvidenceId
import MathEvidence.Core.ExprSerialize
import MathEvidence.Core.Receipt
import MathEvidence.Core.TheoremIdentity
import MathEvidence.Tactic.Discovery
import MathEvidence.Tactic.RationalClose
import MathEvidence.Tactic.ReifyRational
import MathEvidence.Tactic.Status

/-!
# Theorem-producing replay (Wave 2 / ME-RV-023)

Proof authority is ``replaySound`` / fixture ``sound_*`` via
``eq_of_proposition`` (Bridge). The interactive tactic MUST NOT close the
Mathlib goal with an independent final ``field_simp; ring``. Automation MAY
discharge denominator side conditions and IR-eval transport only.

When the soundness bridge closes the goal, the receipt may report
``soundness_verified`` / ``kernel_replay`` for fixture-backed authority.
Otherwise the path remains operational-only.
-/

namespace MathEvidence.Tactic.Replay

open Lean Meta Elab Tactic
open MathEvidence.Core
open MathEvidence.Tactic
open MathEvidence.Tactic.Discovery
open MathEvidence.Tactic.RationalClose
open MathEvidence.Tactic.ReifyRational
open MathEvidence.Checkers.RationalEquality
open MathEvidence.Checkers.RationalEquality.OfflineFixtures

/-- Result of attempting theorem-producing replay for the current goal. -/
inductive ReplayProofResult where
  | closed
  | unsupported (report : StatusReport)
  deriving Repr

/-- UTF-8 SHA-256 helper for tactic-side binding digests. -/
def sha256Utf8 (s : String) : EvidenceId :=
  sha256Bytes s.toUTF8

/-- Build a receipt after checker accept + soundness-bridge close.

When `viaSoundness` is true, authority is `replaySound` / `checkBool_sound`
applied to the Mathlib goal (ME-RV-023). Otherwise the receipt stays operational.
-/
def makeRationalReplayReceipt
    (id : BundleId)
    (req : Request)
    (bundleDig : BundleDigest)
    (theoremDig : TheoremDigest)
    (envLockDig : ContentDigest)
    (viaSoundness : Bool) : CheckerReceipt :=
  if viaSoundness then
    {
      requestDigest := req.requestDigest
      bundleDigest := bundleDig
      theoremDigest := some theoremDig
      capability := req.capability
      checker := {
        package := "MathEvidence.Checkers.RationalEquality"
        module := "MathEvidence.Checkers.RationalEquality.ReplaySound"
        name := "replaySound"
        version := "0.3.0"
        soundnessTheorem := some "replaySound"
      }
      claimRequested := req.claim.claimClass
      claimEstablished := some .soundResult
      assuranceMode := .kernelReplay
      resultStatus := .soundnessVerified
      toolchain := {
        leanVersion := "leanprover/lean4:v4.14.0"
        lakeVersion := "lake"
        mathlibVersion := "v4.14.0"
      }
      detail :=
        s!"tactic soundness path (eq_of_proposition / replaySound) for bundle {id.toPath}; \
envLock={envLockDig.value}"
    }
  else
    {
      requestDigest := req.requestDigest
      bundleDigest := bundleDig
      theoremDigest := some theoremDig
      capability := req.capability
      checker := {
        package := "MathEvidence.Checkers.RationalEquality"
        module := "MathEvidence.Checkers.RationalEquality.Check"
        name := "checkBool"
        version := "0.3.0"
        soundnessTheorem := some "checkBool_sound"
      }
      claimRequested := req.claim.claimClass
      claimEstablished := none
      assuranceMode := .nativeChecked
      resultStatus := .checkerAccepted
      toolchain := {
        leanVersion := "leanprover/lean4:v4.14.0"
        lakeVersion := "lake"
        mathlibVersion := "v4.14.0"
      }
      detail :=
        s!"tactic operational path (checker accept only; soundness bridge did not close) \
for bundle {id.toPath}; envLock={envLockDig.value}"
    }

/-- Deprecated name retained for call sites. -/
def makeRationalOperationalReceipt
    (id : BundleId)
    (req : Request)
    (bundleDig : BundleDigest)
    (theoremDig : TheoremDigest)
    (envLockDig : ContentDigest) : CheckerReceipt :=
  makeRationalReplayReceipt id req bundleDig theoremDig envLockDig false

/-- Deprecated name retained for call sites. -/
def makeRationalCertificationReceipt
    (id : BundleId)
    (req : Request)
    (bundleDig : BundleDigest)
    (theoremDig : TheoremDigest)
    (envLockDig : ContentDigest) : CheckerReceipt :=
  makeRationalReplayReceipt id req bundleDig theoremDig envLockDig true

/-- Fallback claim-template string when Meta Expr serialization is unavailable.

Live replay uses `ExprSerialize.theoremTypeIdentityOfExpr` (ME-RV-020). -/
def claimTypeCanonical (c : Claim) : String :=
  let binders := String.intercalate " " (c.varNames.map fun n => s!"({n} : Rat)")
  s!"forall {binders}, <lhs> = <rhs>"

/--
Attempt theorem-producing replay for a committed rational-equality bundle.
-/
def tryReplayTheorem (id : BundleId) : TacticM ReplayProofResult := do
  let report := replayStatus id
  if id.operation != .rationalEquality then
    return .unsupported report
  let expectAccept :=
    match id with
    | .falseIdentity | .hashMismatch => false
    | _ => true
  if !expectAccept then
    return .unsupported report
  let bundle := id.replayBundle
  unless checkBool bundle.request bundle.certificate do
    throwError "mathevidence replay: Lean checker rejected committed certificate"
  let expected ←
    match Request.ofClaim bundle.request.claim with
    | .ok r => pure r
    | .error e =>
      throwError s!"mathevidence replay: Request.ofClaim failed: {e}"
  unless bundle.request.requestDigest == expected.requestDigest do
    throwError "mathevidence replay: request digest does not match Lean wire recomputation"
  unless bundle.certificate.requestDigest == expected.requestDigest do
    throwError "mathevidence replay: certificate digest does not match Lean wire recomputation"
  let goal ← getMainGoal
  goal.withContext do
    let tgt ← goal.getType
    match ← reifyEqualityGoal tgt with
    | .error err =>
      throwError "mathevidence replay: reification failed: {Reject.format err}"
    | .ok { claim := c, fvars := fvars } =>
      unless claimsEqual c bundle.request.claim do
        throwError "mathevidence replay: current goal does not match committed claim IR"
      let closed ← tryCloseViaFixtureAuthority id fvars
      unless closed do
        throwError
          "mathevidence replay: checker accepted certificate but soundness bridge \
could not close the equality (add denom ≠ 0 facts; authority is replaySound, not ring)."
      let lock := EnvironmentLock.rationalEqualityDefault
      let envDig ←
        match lock.digest with
        | .ok d => pure d
        | .error e => throwError s!"mathevidence replay: environment lock digest failed: {e}"
      -- ME-RV-020: kernel Expr walk (binders + universes + constants + env lock).
      let typeId ←
        try
          ExprSerialize.theoremTypeIdentityOfExpr tgt envDig
        catch _ =>
          -- Fallback only if Meta walk fails; still refuse empty identity.
          pure {
            elaboratedSerialization :=
              let s := claimTypeCanonical c
              if s.isEmpty then "mathevidence-theorem-identity-fallback" else s
            binders := c.varNames.map fun n =>
              { name := n, kind := .default, typeSerialization := "Rat" }
            constantNames := ["Rat", "Eq"]
            environmentLockDigest := envDig
          }
      let thDig ←
        match typeId.digest with
        | .ok d => pure d
        | .error e => throwError s!"mathevidence replay: theorem type digest failed: {e}"
      let bundleBinding :=
        s!"{envDig.value}|{thDig.value}|{expected.requestDigest.value}|{id.toPath}"
      let bundleEid := sha256Utf8 bundleBinding
      let bundleDig : BundleDigest :=
        match BundleDigest.ofWire? bundleEid.value with
        | some d => d
        | none => ⟨bundleEid.value⟩
      if thDig.value == expected.requestDigest.value then
        throwError
          "mathevidence replay: theorem digest collided with request digest (refusing)"
      if bundleDig.value == expected.requestDigest.value then
        throwError
          "mathevidence replay: bundle digest collided with request digest (refusing)"
      let receipt :=
        makeRationalReplayReceipt id expected bundleDig thDig envDig true
      let established :=
        match receipt.claimEstablished with
        | some cl => cl.toWire
        | none => "none"
      logInfo m!"soundness replay (Wave 2 / ME-RV-023): claimEstablished={established} \
theoremTypeDigest={thDig.value} bundleDigest={bundleDig.value} \
requestDigest={receipt.requestDigest.value} assurance=kernel_replay \
result=soundness_verified envLock={envDig.value} \
authority=eq_of_proposition/replaySound"
      pure .closed

end MathEvidence.Tactic.Replay
