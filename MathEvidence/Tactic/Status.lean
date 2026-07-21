/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.Counterexample.Replay
import MathEvidence.Checkers.Counterexample.Tests
import MathEvidence.Checkers.LinearAlgebra.Replay
import MathEvidence.Checkers.LinearAlgebra.Tests
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
  | linearAlgebra
  | finiteCounterexample
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
  | laInverse2x2
  | laExactSystem
  | laKernelVector
  | laDetIdentity
  | laSingularInverseRejected
  | laHashMismatch
  | cexSimpleFalseUniversal
  | cexWitnessTypeMismatch
  | cexHashMismatch
  | cexOutOfDomainRejected
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
  | .laInverse2x2 => "evidence/conformance/linear_algebra/inverse_witness_2x2/bundle"
  | .laExactSystem => "evidence/conformance/linear_algebra/exact_system_solution/bundle"
  | .laKernelVector => "evidence/conformance/linear_algebra/kernel_vector/bundle"
  | .laDetIdentity => "evidence/conformance/linear_algebra/det_identity/bundle"
  | .laSingularInverseRejected =>
      "evidence/conformance/linear_algebra/singular_inverse_rejected/bundle"
  | .laHashMismatch => "evidence/conformance/linear_algebra/hash_mismatch/bundle"
  | .cexSimpleFalseUniversal =>
      "evidence/conformance/finite_counterexample/simple_false_universal/bundle"
  | .cexWitnessTypeMismatch =>
      "evidence/conformance/finite_counterexample/witness_type_mismatch/bundle"
  | .cexHashMismatch => "evidence/conformance/finite_counterexample/hash_mismatch/bundle"
  | .cexOutOfDomainRejected =>
      "evidence/conformance/finite_counterexample/out_of_domain_rejected/bundle"

def BundleId.backend : BundleId → Backend
  | .basicMathematica => .mathematica
  | _ => .sympy

def BundleId.operation : BundleId → Operation
  | .laInverse2x2 | .laExactSystem | .laKernelVector | .laDetIdentity
  | .laSingularInverseRejected | .laHashMismatch => .linearAlgebra
  | .cexSimpleFalseUniversal | .cexWitnessTypeMismatch | .cexHashMismatch
  | .cexOutOfDomainRejected => .finiteCounterexample
  | _ => .rationalEquality

def BundleId.replayBundle : BundleId → ReplayBundle
  | .basicSympy => bundle_basic_sympy
  | .basicMathematica => bundle_basic_mathematica
  | .validIdentity => bundle_valid_identity
  | .redundantCondition => bundle_redundant_condition
  | .variablePermutation => bundle_variable_permutation
  | .largeCoeffs => bundle_large_coeffs
  | .falseIdentity => bundle_false_identity
  | .hashMismatch => bundle_hash_mismatch
  -- Discovery only matches rational BundleIds; LA/CEX use dedicated replayStatus arms.
  | .laInverse2x2 | .laExactSystem | .laKernelVector | .laDetIdentity
  | .laSingularInverseRejected | .laHashMismatch
  | .cexSimpleFalseUniversal | .cexWitnessTypeMismatch | .cexHashMismatch
  | .cexOutOfDomainRejected => bundle_basic_sympy

/-- Replay mode for rational-equality committed bundles. -/
def replayStatusRational (id : BundleId) : StatusReport :=
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

def replayStatusLinearAlgebra (id : BundleId) : StatusReport :=
  let mk (accepted : Bool) (detail : String) (claim : ClaimClass) : StatusReport :=
    { operation := .linearAlgebra
      fragmentSupported := true
      assumptionsExported := []
      conditionsReturned := []
      backend := .sympy
      claimRequested := claim
      claimEstablished := if accepted then some claim else none
      resultStatus := if accepted then .witnessVerified else .rejected
      assuranceMode := .kernelReplay
      evidenceBundle := id.toPath
      remainingGoals := []
      detail := detail }
  match id with
  | .laInverse2x2 =>
      mk (MathEvidence.Checkers.LinearAlgebra.checkBool
            MathEvidence.Checkers.LinearAlgebra.Tests.req_inv
            MathEvidence.Checkers.LinearAlgebra.Tests.cert_inv)
        "linear algebra inverse offline fixture" .witness
  | .laExactSystem =>
      mk (MathEvidence.Checkers.LinearAlgebra.checkBool
            MathEvidence.Checkers.LinearAlgebra.Tests.req_sys
            MathEvidence.Checkers.LinearAlgebra.Tests.cert_sys)
        "linear algebra system offline fixture" .witness
  | .laKernelVector =>
      mk (MathEvidence.Checkers.LinearAlgebra.checkBool
            MathEvidence.Checkers.LinearAlgebra.Tests.req_ker
            MathEvidence.Checkers.LinearAlgebra.Tests.cert_ker)
        "linear algebra kernel offline fixture" .witness
  | .laDetIdentity =>
      mk (MathEvidence.Checkers.LinearAlgebra.checkBool
            MathEvidence.Checkers.LinearAlgebra.Tests.req_det
            MathEvidence.Checkers.LinearAlgebra.Tests.cert_det)
        "linear algebra det offline fixture" .soundResult
  | .laSingularInverseRejected =>
      mk (MathEvidence.Checkers.LinearAlgebra.checkBool
            MathEvidence.Checkers.LinearAlgebra.Tests.req_sing
            MathEvidence.Checkers.LinearAlgebra.Tests.cert_sing_id)
        "singular inverse must be rejected" .witness
  | .laHashMismatch =>
      mk (MathEvidence.Checkers.LinearAlgebra.checkBool
            MathEvidence.Checkers.LinearAlgebra.Tests.req_inv
            MathEvidence.Checkers.LinearAlgebra.Tests.cert_bad_digest)
        "LA hash mismatch must be rejected" .witness
  | _ =>
      { operation := .linearAlgebra
        fragmentSupported := false
        resultStatus := .unsupported
        evidenceBundle := id.toPath
        detail := "unknown linearAlgebra bundle" }

def replayStatusFiniteCounterexample (id : BundleId) : StatusReport :=
  let mk (accepted : Bool) (detail : String) : StatusReport :=
    { operation := .finiteCounterexample
      fragmentSupported := true
      assumptionsExported := []
      conditionsReturned := []
      backend := .sympy
      claimRequested := .refutation
      claimEstablished := if accepted then some .refutation else none
      resultStatus := if accepted then .witnessVerified else .rejected
      assuranceMode := .kernelReplay
      evidenceBundle := id.toPath
      remainingGoals := []
      detail := detail }
  match id with
  | .cexSimpleFalseUniversal =>
      mk (MathEvidence.Checkers.Counterexample.checkBool
            MathEvidence.Checkers.Counterexample.Tests.req_nat_eq0
            MathEvidence.Checkers.Counterexample.Tests.cert_nat_eq0)
        "finite CEX offline fixture"
  | .cexWitnessTypeMismatch =>
      mk (MathEvidence.Checkers.Counterexample.checkBool
            MathEvidence.Checkers.Counterexample.Tests.req_nat_eq0
            MathEvidence.Checkers.Counterexample.Tests.cert_type_mismatch)
        "type mismatch must be rejected"
  | .cexHashMismatch =>
      mk (MathEvidence.Checkers.Counterexample.checkBool
            MathEvidence.Checkers.Counterexample.Tests.req_nat_eq0
            MathEvidence.Checkers.Counterexample.Tests.cert_bad_digest)
        "CEX hash mismatch must be rejected"
  | .cexOutOfDomainRejected =>
      mk (MathEvidence.Checkers.Counterexample.checkBool
            MathEvidence.Checkers.Counterexample.Tests.req_nat_eq0
            MathEvidence.Checkers.Counterexample.Tests.cert_nat_ood)
        "out-of-domain must be rejected"
  | _ =>
      { operation := .finiteCounterexample
        fragmentSupported := false
        resultStatus := .unsupported
        evidenceBundle := id.toPath
        detail := "unknown finiteCounterexample bundle" }

/-- Replay mode: load a committed bundle, run the matching checker, no backends. -/
def replayStatus (id : BundleId) : StatusReport :=
  match id.operation with
  | .linearAlgebra => replayStatusLinearAlgebra id
  | .finiteCounterexample => replayStatusFiniteCounterexample id
  | .rationalEquality => replayStatusRational id

/-- Discovery mode without a live backend: report capability recognition only.

Backends are never started from this path. Callers that need generation must use
an adapter out-of-process and then `replayStatus`. Prefer
`MathEvidence.Tactic.Discovery.runDiscoveryOrchestration` for Meta-reify +
offline fixture match / env-gated live discovery (rational equality).

`ReifierRegistry.liveKinds` lists compile-time live Meta reifiers: rational,
matrix, counterexample, and ideal. Bare `discoveryStatus` remains the rational
unsupported stub; use `mathevidence_linear_algebra` / counterexample / ideal
tactics for those goals, or CLI discover + replay. -/
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
      ["reify Rat equality goal, or provide evidence bundle and switch to replay mode",
       "LA/CEX/ideal: live Meta reifiers — see ReifierRegistry.liveKinds",
       "LA/CEX SymPy generate: mathevidence_cli.py discover --backend sympy"]
    detail :=
      "discovery: rational_equality Meta-reify path recognized; use Discovery \
orchestration (offline fixture match or MATHEVIDENCE_DISCOVERY=1). \
ReifierRegistry marks matrix/counterexample/ideal live via dedicated tactics." }

end MathEvidence.Tactic
