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
# Checker receipts

Typed receipt metadata for replayed checker results. Receipts bind the request,
bundle, theorem proposition, checker/capability contract, unresolved obligations,
and declared toolchain into a structurally validated record.
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

/-- Theorem-level receipt emitted after checker replay. -/
structure CheckerReceipt where
  schemaVersion : String := "0.1.0"
  receiptDigest : Option ReceiptDigest := none
  requestDigest : RequestDigest
  bundleDigest : BundleDigest
  theoremDigest : TheoremDigest
  axiomDigests : List ContentDigest := []
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

private def nonEmpty (s : String) : Bool :=
  !s.isEmpty

def CheckerRef.isStructurallyValid (r : CheckerRef) : Bool :=
  nonEmpty r.package && nonEmpty r.module && nonEmpty r.name && nonEmpty r.version

def ReceiptToolchain.isStructurallyValid (t : ReceiptToolchain) : Bool :=
  nonEmpty t.leanVersion && nonEmpty t.lakeVersion

def ReceiptObligation.isStructurallyValid (o : ReceiptObligation) : Bool :=
  nonEmpty o.id && nonEmpty o.description

/-- Structural validation only: required strings and obligation shape. -/
def CheckerReceipt.isStructurallyValid (r : CheckerReceipt) : Bool :=
  nonEmpty r.schemaVersion &&
    r.checker.isStructurallyValid &&
    r.toolchain.isStructurallyValid &&
    r.unresolvedObligations.all ReceiptObligation.isStructurallyValid

def CheckerReceipt.validate (r : CheckerReceipt) : Except String CheckerReceipt :=
  if r.isStructurallyValid then
    .ok r
  else
    .error "checker receipt failed structural validation"

end MathEvidence.Core
