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
import MathEvidence.Checkers.RationalEquality.Check
import MathEvidence.Checkers.RationalEquality.Certificate
import MathEvidence.Checkers.RationalEquality.Spec

namespace MathEvidence.Checkers.RationalEquality

open MathEvidence.Core

/-- Offline replay input: request + certificate already present (no backend). -/
structure ReplayBundle where
  request : Request
  certificate : Certificate
  candidate : Candidate := {}
  deriving Repr

/-- Replay result. -/
structure ReplayReport where
  accepted : Bool
  resultStatus : ResultStatus
  assuranceMode : AssuranceMode := .kernelReplay
  detail : String := ""
  deriving Repr

/-- Replay mode: validate digests via checker; backends disabled. -/
def replay (b : ReplayBundle) : ReplayReport :=
  match check b.request b.candidate b.certificate with
  | .accept =>
    { accepted := true
      resultStatus := .soundnessVerified
      assuranceMode := .kernelReplay
      detail := "rational equality accepted under explicit denom conditions" }
  | .reject code detail =>
    { accepted := false
      resultStatus := .rejected
      assuranceMode := .kernelReplay
      detail := code.toWire ++ (if detail.isEmpty then "" else ": " ++ detail) }

/-- Build minimal bundle metadata after a successful replay.

Requires an explicit certificate **content** digest — never reuse `requestDigest`
as a file content digest (P0-8). -/
def replayBundleMetadata (b : ReplayBundle) (prov : Provenance)
    (certContent : ContentDigest) : Option BundleMetadata :=
  let report := replay b
  if !report.accepted then none
  else
    some {
      bundleVersion := "0.2.0"
      capability := b.request.capability
      requestDigest := b.request.requestDigest
      claimClass := b.request.claim.claimClass
      resultStatus := report.resultStatus
      assuranceMode := report.assuranceMode
      files := [{
        path := "certificate.json"
        digest := certContent
        mediaType := "application/json"
      }]
      provenance := prov
    }

end MathEvidence.Checkers.RationalEquality
