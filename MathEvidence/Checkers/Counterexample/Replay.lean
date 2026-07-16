/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.AssuranceMode
import MathEvidence.Core.Bundle
import MathEvidence.Core.ClaimClass
import MathEvidence.Core.Provenance
import MathEvidence.Core.ResultStatus
import MathEvidence.Checkers.Counterexample.Check
import MathEvidence.Checkers.Counterexample.Certificate
import MathEvidence.Checkers.Counterexample.Spec

namespace MathEvidence.Checkers.Counterexample

open MathEvidence.Core

structure ReplayBundle where
  request : Request
  certificate : Certificate
  candidate : Candidate := {}
  deriving Repr

structure ReplayReport where
  accepted : Bool
  resultStatus : ResultStatus
  assuranceMode : AssuranceMode := .kernelReplay
  detail : String := ""
  deriving Repr

def replay (b : ReplayBundle) : ReplayReport :=
  match check b.request b.candidate b.certificate with
  | .accept =>
    { accepted := true
      resultStatus := .witnessVerified
      assuranceMode := .kernelReplay
      detail := "finite counterexample accepted (predicate false at witness)" }
  | .reject code detail =>
    { accepted := false
      resultStatus := .rejected
      assuranceMode := .kernelReplay
      detail := code.toWire ++ (if detail.isEmpty then "" else ": " ++ detail) }

def replayBundleMetadata (b : ReplayBundle) (prov : Provenance) : Option BundleMetadata :=
  let report := replay b
  if !report.accepted then none
  else
    some {
      capability := b.request.capability
      requestDigest := b.request.requestDigest
      claimClass := b.request.claim.claimClass
      resultStatus := report.resultStatus
      assuranceMode := report.assuranceMode
      files := [{
        path := "certificate/finite_counterexample.json"
        digest := b.certificate.requestDigest
        mediaType := "application/json"
      }]
      provenance := prov
    }

end MathEvidence.Checkers.Counterexample
