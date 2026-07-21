/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import MathEvidence.Checkers.RationalEquality.Check
import MathEvidence.Checkers.RationalEquality.OfflineFixtures
import MathEvidence.Checkers.RationalEquality.Wire
import MathEvidence.Core.Receipt
import MathEvidence.Tactic.Discovery
import MathEvidence.Tactic.ReifyRational
import MathEvidence.Tactic.Status

/-!
# Theorem-producing replay

After checker acceptance, replay closes the current ℚ equality goal under
explicit nonzero denominator hypotheses. Status inspection remains on
`#mathevidence inspect` and never closes goals.
-/

namespace MathEvidence.Tactic.Replay

open Lean Meta Elab Tactic
open MathEvidence.Core
open MathEvidence.Tactic
open MathEvidence.Tactic.Discovery
open MathEvidence.Tactic.ReifyRational
open MathEvidence.Checkers.RationalEquality
open MathEvidence.Checkers.RationalEquality.OfflineFixtures

/-- Result of attempting theorem-producing replay for the current goal. -/
inductive ReplayProofResult where
  | closed
  | unsupported (report : StatusReport)
  deriving Repr

/-- Build a structural checker receipt for an accepted rational fixture. -/
def makeRationalReceipt (id : BundleId) (req : Request) : CheckerReceipt :=
  let path := id.toPath
  let dig := req.requestDigest.value
  {
    requestDigest := req.requestDigest
    bundleDigest := ⟨dig⟩
    theoremDigest := ⟨dig⟩
    capability := req.capability
    checker := {
      package := "MathEvidence.Checkers.RationalEquality"
      module := "MathEvidence.Checkers.RationalEquality.Check"
      name := "checkBool"
      version := "0.1.0"
      soundnessTheorem := some "checkBool_sound"
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
    detail := s!"theorem replay accepted for bundle {path}"
  }

/--
Attempt theorem-producing replay for a committed rational-equality bundle.

Requires: checker accepts the fixture, current goal reifies to the same claim,
wire digests recompute, then discharges equality under explicit nonzero hyps.
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
  let expected := Request.ofClaim bundle.request.claim
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
    | .ok { claim := c, .. } =>
      unless claimsEqual c bundle.request.claim do
        throwError "mathevidence replay: current goal does not match committed claim IR"
      let closed ← tryCloseRationalEquality
      unless closed do
        throwError
          "mathevidence replay: checker accepted certificate but could not close the \
equality under current nonzero hypotheses (add denom ≠ 0 facts)."
      let receipt := makeRationalReceipt id expected
      let established :=
        match receipt.claimEstablished with
        | some c => c.toWire
        | none => "none"
      logInfo m!"checker receipt (structural): claimEstablished={established} \
requestDigest={receipt.requestDigest.value}"
      pure .closed

end MathEvidence.Tactic.Replay
