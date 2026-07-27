/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.AssuranceMode
import MathEvidence.Core.Bundle
import MathEvidence.Core.CapabilityId
import MathEvidence.Core.ClaimClass
import MathEvidence.Core.Digest.Types
import MathEvidence.Core.EnvironmentLock
import MathEvidence.Core.Provenance
import MathEvidence.Core.Receipt
import MathEvidence.Core.ReplayTarget
import MathEvidence.Core.ResultStatus
import MathEvidence.Core.TheoremIdentity

/-!
# Certification Record (Wave 1–2 / ME-RV-012 / ME-RV-020)

A Certification Record references one Candidate Bundle and binds replay target,
checker evaluation, theorem identity, axiom report, and certification receipt.
-/

namespace MathEvidence.Core

/-- Compiled axiom / environment audit report (must not be pending_compiled_audit). -/
structure AxiomReportMeta where
  schemaVersion : String := "0.3.0"
  status : String
  axiomDigests : List ContentDigest := []
  allowedAxioms : List String := []
  deriving DecidableEq, Repr, Inhabited

def AxiomReportMeta.isPlaceholder (r : AxiomReportMeta) : Bool :=
  r.status == "pending_compiled_audit"

/-- Certification Record directory metadata. -/
structure CertificationRecordMetadata where
  schemaVersion : String := "0.3.0"
  artifactKind : BundleKind := .certification
  candidateBundleDigest : BundleDigest
  capability : CapabilityRef
  requestDigest : RequestDigest
  claimClass : ClaimClass
  resultStatus : ResultStatus
  assuranceMode : AssuranceMode
  files : List BundleFileEntry
  certificationDigest : Option BundleDigest := none
  deriving DecidableEq, Repr, Inhabited

/-- Mandatory Certification Record roles. -/
def CertificationRecordMetadata.hasMandatoryRoles (m : CertificationRecordMetadata) : Bool :=
  let roles := m.files.map (·.role)
  roles.contains .replayTarget &&
    roles.contains .checkerEvaluation &&
    roles.contains .theoremIdentity &&
    roles.contains .axiomReport &&
    roles.contains .certificationReceipt

def CertificationRecordMetadata.uniquePaths (m : CertificationRecordMetadata) : Bool :=
  let paths := m.files.map (·.path)
  paths.eraseDups.length == m.files.length

def CertificationRecordMetadata.uniqueRoles (m : CertificationRecordMetadata) : Bool :=
  let roles := m.files.filterMap fun e =>
    match e.role with
    | .other | .readme | .signature => none
    | r => some r
  roles.eraseDups.length == roles.length

/-- Structural well-formedness (no placeholders; roles complete). -/
def CertificationRecordMetadata.wellFormed (m : CertificationRecordMetadata) : Bool :=
  m.schemaVersion == "0.3.0" &&
    m.artifactKind == .certification &&
    !m.files.isEmpty &&
    m.files.all (·.pathOk) &&
    m.uniquePaths &&
    m.uniqueRoles &&
    m.hasMandatoryRoles &&
    isSha256DigestWire m.candidateBundleDigest.value &&
    isSha256DigestWire m.requestDigest.value &&
    m.files.all fun f => isSha256DigestWire f.digest.value

/-- Coherence between assurance mode and result status on a certification receipt. -/
def certificationReceiptCoherent
    (assurance : AssuranceMode) (status : ResultStatus)
    (theoremDigest : Option TheoremDigest)
    (proofDigest : Option ContentDigest) : Bool :=
  match assurance with
  | .nativeChecked =>
    -- native_checked must not report soundness_verified
    status != .soundnessVerified &&
      status != .completenessVerified &&
      status != .optimalityVerified &&
      status != .witnessVerified &&
      status != .nativeVerified
  | .kernelReplay =>
    match theoremDigest, proofDigest with
    | some t, some p =>
      isSha256DigestWire t.value && isSha256DigestWire p.value
    | _, _ => false
  | .verifiedReflection =>
    match theoremDigest with
    | some t => isSha256DigestWire t.value
    | none => false

/-- Full certification coherence with real Wave 2 identity artifacts. -/
def certificationRecordCoherent
    (m : CertificationRecordMetadata)
    (target : ReplayTarget)
    (identity : TheoremIdentity)
    (lock : EnvironmentLock)
    (axioms : AxiomReportMeta) : Bool :=
  m.wellFormed &&
    target.wellFormed &&
    identity.wellFormed &&
    !axioms.isPlaceholder &&
    target.requestDigest == m.requestDigest &&
    identity.environmentLockDigest == target.environmentLockDigest &&
    match lock.digest with
    | .ok d => d == target.environmentLockDigest
    | .error _ => false

end MathEvidence.Core
