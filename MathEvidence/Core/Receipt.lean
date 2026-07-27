/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.AssuranceMode
import MathEvidence.Core.CapabilityId
import MathEvidence.Core.ClaimClass
import MathEvidence.Core.Digest.Types
import MathEvidence.Core.ResultStatus

/-!
# Checker / certification receipts (v0.3)

Receipts bind candidate bundle, certification record, replay target, theorem,
axiom report, and environment lock digests. Operational `native_checked`
receipts must not claim theorem-level verified statuses.
-/

namespace MathEvidence.Core

/-- Stable checker implementation reference. -/
structure CheckerRef where
  package : String
  module : String
  name : String
  version : String
  soundnessTheorem : Option String := none
  deriving DecidableEq, Repr, Inhabited

/-- Toolchain strings recorded with a checker receipt. -/
structure ReceiptToolchain where
  leanVersion : String
  lakeVersion : String
  mathlibVersion : String := ""
  platform : String := ""
  deriving DecidableEq, Repr, Inhabited

/-- Obligation that remains open after checker replay. -/
structure ReceiptObligation where
  id : String
  description : String
  deriving DecidableEq, Repr, Inhabited

/-- Operational checker evaluation (Wave 0 verify-bundle / native_checked). -/
structure CheckerReceipt where
  schemaVersion : String := "0.3.0"
  receiptDigest : Option ReceiptDigest := none
  requestDigest : RequestDigest
  bundleDigest : BundleDigest
  theoremDigest : Option TheoremDigest := none
  axiomDigests : List ContentDigest := []
  certificateContentDigest : Option ContentDigest := none
  capability : CapabilityRef
  checker : CheckerRef
  claimRequested : ClaimClass
  claimEstablished : Option ClaimClass := none
  unresolvedObligations : List ReceiptObligation := []
  assuranceMode : AssuranceMode
  resultStatus : ResultStatus
  toolchain : ReceiptToolchain
  detail : String := ""
  deriving DecidableEq, Repr

/-- Full certification receipt (v0.3) emitted with a Certification Record. -/
structure CertificationReceipt where
  schemaVersion : String := "0.3.0"
  candidateBundleDigest : BundleDigest
  certificationRecordDigest : BundleDigest
  requestDigest : RequestDigest
  certificateContentDigest : ContentDigest
  replayTargetDigest : ContentDigest
  theoremTypeDigest : TheoremDigest
  proofDeclarationDigest : ContentDigest
  axiomReportDigest : ContentDigest
  environmentLockDigest : ContentDigest
  capability : CapabilityRef
  checker : CheckerRef
  soundnessTheorem : Option String := none
  claimRequested : ClaimClass
  claimEstablished : Option ClaimClass := none
  unresolvedObligations : List ReceiptObligation := []
  assuranceMode : AssuranceMode
  resultStatus : ResultStatus
  toolchain : ReceiptToolchain
  detail : String := ""
  deriving DecidableEq, Repr

private def nonEmpty (s : String) : Bool :=
  !s.isEmpty

def CheckerRef.isStructurallyValid (r : CheckerRef) : Bool :=
  nonEmpty r.package && nonEmpty r.module && nonEmpty r.name && nonEmpty r.version

def ReceiptToolchain.isStructurallyValid (t : ReceiptToolchain) : Bool :=
  nonEmpty t.leanVersion && nonEmpty t.lakeVersion

def ReceiptObligation.isStructurallyValid (o : ReceiptObligation) : Bool :=
  nonEmpty o.id && nonEmpty o.description

private def isVerifiedStatus : ResultStatus → Bool
  | .witnessVerified | .soundnessVerified | .completenessVerified
  | .optimalityVerified | .nativeVerified => true
  | _ => false

/-- Structural validation for operational checker receipts. -/
def CheckerReceipt.isStructurallyValid (r : CheckerReceipt) : Bool :=
  nonEmpty r.schemaVersion &&
    r.checker.isStructurallyValid &&
    r.toolchain.isStructurallyValid &&
    r.unresolvedObligations.all ReceiptObligation.isStructurallyValid &&
    isSha256DigestWire r.requestDigest.value &&
    isSha256DigestWire r.bundleDigest.value &&
    -- native_checked must not report theorem-level verified statuses
    (r.assuranceMode != .nativeChecked || !isVerifiedStatus r.resultStatus) &&
    -- kernel_replay requires theorem digest
    (r.assuranceMode != .kernelReplay ||
      match r.theoremDigest with
      | some t => isSha256DigestWire t.value
      | none => false) &&
    -- verified status requires claimEstablished
    (!isVerifiedStatus r.resultStatus || r.claimEstablished.isSome)

def CheckerReceipt.validate (r : CheckerReceipt) : Except String CheckerReceipt :=
  if r.isStructurallyValid then
    .ok r
  else
    .error "checker receipt failed structural validation"

/-- Schema-coherent validation for certification receipts (v0.3). -/
def CertificationReceipt.isStructurallyValid (r : CertificationReceipt) : Bool :=
  r.schemaVersion == "0.3.0" &&
    r.checker.isStructurallyValid &&
    r.toolchain.isStructurallyValid &&
    r.unresolvedObligations.all ReceiptObligation.isStructurallyValid &&
    isSha256DigestWire r.candidateBundleDigest.value &&
    isSha256DigestWire r.certificationRecordDigest.value &&
    isSha256DigestWire r.requestDigest.value &&
    isSha256DigestWire r.certificateContentDigest.value &&
    isSha256DigestWire r.replayTargetDigest.value &&
    isSha256DigestWire r.theoremTypeDigest.value &&
    isSha256DigestWire r.proofDeclarationDigest.value &&
    isSha256DigestWire r.axiomReportDigest.value &&
    isSha256DigestWire r.environmentLockDigest.value &&
    (r.assuranceMode != .nativeChecked || !isVerifiedStatus r.resultStatus) &&
    (r.assuranceMode != .kernelReplay ||
      (isSha256DigestWire r.theoremTypeDigest.value &&
        isSha256DigestWire r.proofDeclarationDigest.value)) &&
    (!isVerifiedStatus r.resultStatus || r.claimEstablished.isSome) &&
    -- unresolved obligations block verified unless claim class permits (v0: block)
    (r.unresolvedObligations.isEmpty || !isVerifiedStatus r.resultStatus)

def CertificationReceipt.validate (r : CertificationReceipt) :
    Except String CertificationReceipt :=
  if r.isStructurallyValid then
    .ok r
  else
    .error "certification receipt failed structural validation"

end MathEvidence.Core
