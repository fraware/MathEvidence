/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
namespace MathEvidence.Core

/-- User-visible establishment status. Distinct from `ClaimClass`.

A result MAY report a weaker status than the requested claim class; it MUST NOT
silently promote. -/
inductive ResultStatus where
  | computed
  | tested
  | witnessVerified
  | soundnessVerified
  | completenessVerified
  | optimalityVerified
  | approximationCertified
  | nativeVerified
  | rejected
  | unsupported
  | ambiguous
  deriving DecidableEq, Repr, Inhabited

def ResultStatus.toWire : ResultStatus → String
  | .computed => "computed"
  | .tested => "tested"
  | .witnessVerified => "witness_verified"
  | .soundnessVerified => "soundness_verified"
  | .completenessVerified => "completeness_verified"
  | .optimalityVerified => "optimality_verified"
  | .approximationCertified => "approximation_certified"
  | .nativeVerified => "native_verified"
  | .rejected => "rejected"
  | .unsupported => "unsupported"
  | .ambiguous => "ambiguous"

def ResultStatus.ofWire? : String → Option ResultStatus
  | "computed" => some .computed
  | "tested" => some .tested
  | "witness_verified" => some .witnessVerified
  | "soundness_verified" => some .soundnessVerified
  | "completeness_verified" => some .completenessVerified
  | "optimality_verified" => some .optimalityVerified
  | "approximation_certified" => some .approximationCertified
  | "native_verified" => some .nativeVerified
  | "rejected" => some .rejected
  | "unsupported" => some .unsupported
  | "ambiguous" => some .ambiguous
  | _ => none

end MathEvidence.Core
