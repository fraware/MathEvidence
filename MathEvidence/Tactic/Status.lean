/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.RationalEquality.Check
import MathEvidence.Checkers.RationalEquality.OfflineFixtures
import MathEvidence.Checkers.RationalEquality.Replay
import MathEvidence.Core.AssuranceMode
import MathEvidence.Core.ClaimClass
import MathEvidence.Core.ResultStatus

namespace MathEvidence.Tactic

open MathEvidence.Core
open MathEvidence.Checkers.RationalEquality
open MathEvidence.Checkers.RationalEquality.OfflineFixtures

/-! ## Spec §12.1 status report -/

inductive Operation where
  | rationalEquality
  deriving DecidableEq, Repr, Inhabited

inductive Backend where
  | sympy
  | mathematica
  | none
  deriving DecidableEq, Repr, Inhabited

inductive TacticMode where
  | discovery
  | replay
  deriving DecidableEq, Repr, Inhabited

structure StatusReport where
  operation : Operation := .rationalEquality
  fragmentSupported : Bool := true
  assumptionsExported : List String := []
  conditionsReturned : List String := []
  backend : Backend := .none
  claimRequested : ClaimClass := .soundResult
  claimEstablished : Option ClaimClass := none
  resultStatus : ResultStatus := .unsupported
  assuranceMode : AssuranceMode := .kernelReplay
  evidenceBundle : String := ""
  remainingGoals : List String := []
  detail : String := ""
  deriving Repr

def StatusReport.format (r : StatusReport) : String :=
  Id.run do
    let mut lines : List String := []
    lines := lines ++ [s!"operation: {repr r.operation}"]
    lines := lines ++ [s!"fragmentSupported: {r.fragmentSupported}"]
    lines := lines ++ [s!"assumptionsExported: {r.assumptionsExported}"]
    lines := lines ++ [s!"conditionsReturned: {r.conditionsReturned}"]
    lines := lines ++ [s!"backend: {repr r.backend}"]
    lines := lines ++ [s!"claimRequested: {r.claimRequested.toWire}"]
    let established :=
      match r.claimEstablished with
      | some c => c.toWire
      | none => "none"
    lines := lines ++ [s!"claimEstablished: {established}"]
    lines := lines ++ [s!"resultStatus: {r.resultStatus.toWire}"]
    lines := lines ++ [s!"assuranceMode: {r.assuranceMode.toWire}"]
    lines := lines ++ [s!"evidenceBundle: {r.evidenceBundle}"]
    lines := lines ++ [s!"remainingGoals: {r.remainingGoals}"]
    if !r.detail.isEmpty then
      lines := lines ++ [s!"detail: {r.detail}"]
    pure (String.intercalate "\n" lines)

/-- Named committed bundles available for Lean-side offline replay (no backends). -/
inductive BundleId where
  | basicSympy
  | basicMathematica
  | validIdentity
  | redundantCondition
  | variablePermutation
  | largeCoeffs
  | falseIdentity
  | hashMismatch
  deriving DecidableEq, Repr, Inhabited

def BundleId.toPath : BundleId → String
  | .basicSympy => "evidence/examples/rational_equality_basic"
  | .basicMathematica => "evidence/examples/rational_equality_mathematica_offline"
  | .validIdentity => "evidence/conformance/rfc0001/valid_identity/bundle"
  | .redundantCondition => "evidence/conformance/rfc0001/redundant_condition/bundle"
  | .variablePermutation => "evidence/conformance/rfc0001/variable_permutation/bundle"
  | .largeCoeffs => "evidence/conformance/rfc0001/large_coeffs/bundle"
  | .falseIdentity => "evidence/conformance/rfc0001/false_identity/bundle"
  | .hashMismatch => "evidence/conformance/rfc0001/hash_mismatch/bundle"

def BundleId.backend : BundleId → Backend
  | .basicMathematica => .mathematica
  | _ => .sympy

def BundleId.replayBundle : BundleId → ReplayBundle
  | .basicSympy => bundle_basic_sympy
  | .basicMathematica => bundle_basic_mathematica
  | .validIdentity => bundle_valid_identity
  | .redundantCondition => bundle_redundant_condition
  | .variablePermutation => bundle_variable_permutation
  | .largeCoeffs => bundle_large_coeffs
  | .falseIdentity => bundle_false_identity
  | .hashMismatch => bundle_hash_mismatch

/-- Replay mode: load a committed bundle, run the RationalEquality checker, no backends. -/
def replayStatus (id : BundleId) : StatusReport :=
  let b := id.replayBundle
  let report := replay b
  let conds := b.certificate.denomFactors.map fun e => reprStr e
  if report.accepted then
    { operation := .rationalEquality
      fragmentSupported := true
      assumptionsExported := []
      conditionsReturned := conds
      backend := id.backend
      claimRequested := b.request.claim.claimClass
      claimEstablished := some .soundResult
      resultStatus := report.resultStatus
      assuranceMode := report.assuranceMode
      evidenceBundle := id.toPath
      remainingGoals := conds.map fun c => s!"nonzero: {c}"
      detail := report.detail }
  else
    { operation := .rationalEquality
      fragmentSupported := true
      assumptionsExported := []
      conditionsReturned := conds
      backend := id.backend
      claimRequested := b.request.claim.claimClass
      claimEstablished := none
      resultStatus := report.resultStatus
      assuranceMode := .kernelReplay
      evidenceBundle := id.toPath
      remainingGoals := []
      detail := report.detail }

/-- Discovery mode without a live backend: report capability recognition only.

Backends are never started from this path. Callers that need generation must use
an adapter out-of-process and then `replayStatus`. Prefer
`MathEvidence.Tactic.Discovery.runDiscoveryOrchestration` for Meta-reify +
offline fixture match / env-gated live discovery. -/
def discoveryStatus (backend : Backend := .none) (claim : ClaimClass := .soundResult) :
    StatusReport :=
  { operation := .rationalEquality
    fragmentSupported := true
    assumptionsExported := []
    conditionsReturned := []
    backend := backend
    claimRequested := claim
    claimEstablished := none
    resultStatus := .unsupported
    assuranceMode := .kernelReplay
    evidenceBundle := ""
    remainingGoals :=
      ["reify Rat equality goal, or provide evidence bundle and switch to replay mode"]
    detail :=
      "discovery: rational_equality fragment recognized; use Discovery orchestration \
(offline fixture match or MATHEVIDENCE_DISCOVERY=1)" }

end MathEvidence.Tactic
