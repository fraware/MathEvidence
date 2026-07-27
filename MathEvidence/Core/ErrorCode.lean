/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
namespace MathEvidence.Core

/-- Stable structured error codes (Project Spec §13).

Free-form exception strings are diagnostic supplements only.
Parity target: `adapters/common/errors.py::STABLE_CODES`. -/
inductive ErrorCode where
  -- Semantic
  | unsupportedExpression
  | unsupportedType
  | ambiguousInterpretation
  | missingAssumption
  | branchConventionRequired
  | partialOperationUnresolved
  | claimStrengthUnavailable
  | goalMismatch
  | sideConditionUnproved
  | encodingVersionUnsupported
  | operationUnsupported
  -- Backend
  | backendUnavailable
  | backendTimeout
  | backendCrash
  | backendUnsupported
  | backendNondeterministicFailure
  -- Evidence
  | malformedEvidence
  | requestDigestMismatch
  | candidateRejected
  | certificateRejected
  | certificateDecodeFailed
  | completenessNotEstablished
  | approximationBoundMissing
  | contentAddressCollision
  | bundleNotFound
  | bundlePathForbidden
  | bundlePathRejected
  | manifestSchemaInvalid
  | contentDigestMismatch
  | capabilityVersionUnsupported
  | checkerReceiptInvalid
  | axiomPolicyViolation
  -- System
  | schemaVersionUnsupported
  | resourceLimitExceeded
  | replayDependencyMissing
  | assuranceModeUnavailable
  | cancelled
  deriving DecidableEq, Repr, Inhabited

/-- Error taxonomy category. -/
inductive ErrorCategory where
  | semantic
  | backend
  | evidence
  | system
  deriving DecidableEq, Repr, Inhabited

def ErrorCode.category : ErrorCode → ErrorCategory
  | .unsupportedExpression | .unsupportedType | .ambiguousInterpretation
  | .missingAssumption | .branchConventionRequired | .partialOperationUnresolved
  | .claimStrengthUnavailable | .goalMismatch | .sideConditionUnproved
  | .encodingVersionUnsupported | .operationUnsupported => .semantic
  | .backendUnavailable | .backendTimeout | .backendCrash | .backendUnsupported
  | .backendNondeterministicFailure => .backend
  | .malformedEvidence | .requestDigestMismatch | .candidateRejected
  | .certificateRejected | .certificateDecodeFailed | .completenessNotEstablished
  | .approximationBoundMissing | .contentAddressCollision | .bundleNotFound
  | .bundlePathForbidden | .bundlePathRejected | .manifestSchemaInvalid
  | .contentDigestMismatch | .capabilityVersionUnsupported | .checkerReceiptInvalid
  | .axiomPolicyViolation => .evidence
  | .schemaVersionUnsupported | .resourceLimitExceeded | .replayDependencyMissing
  | .assuranceModeUnavailable | .cancelled => .system

def ErrorCode.toWire : ErrorCode → String
  | .unsupportedExpression => "unsupported_expression"
  | .unsupportedType => "unsupported_type"
  | .ambiguousInterpretation => "ambiguous_interpretation"
  | .missingAssumption => "missing_assumption"
  | .branchConventionRequired => "branch_convention_required"
  | .partialOperationUnresolved => "partial_operation_unresolved"
  | .claimStrengthUnavailable => "claim_strength_unavailable"
  | .goalMismatch => "goal_mismatch"
  | .sideConditionUnproved => "side_condition_unproved"
  | .encodingVersionUnsupported => "encoding_version_unsupported"
  | .operationUnsupported => "operation_unsupported"
  | .backendUnavailable => "backend_unavailable"
  | .backendTimeout => "backend_timeout"
  | .backendCrash => "backend_crash"
  | .backendUnsupported => "backend_unsupported"
  | .backendNondeterministicFailure => "backend_nondeterministic_failure"
  | .malformedEvidence => "malformed_evidence"
  | .requestDigestMismatch => "request_digest_mismatch"
  | .candidateRejected => "candidate_rejected"
  | .certificateRejected => "certificate_rejected"
  | .certificateDecodeFailed => "certificate_decode_failed"
  | .completenessNotEstablished => "completeness_not_established"
  | .approximationBoundMissing => "approximation_bound_missing"
  | .contentAddressCollision => "content_address_collision"
  | .bundleNotFound => "bundle_not_found"
  | .bundlePathForbidden => "bundle_path_forbidden"
  | .bundlePathRejected => "bundle_path_rejected"
  | .manifestSchemaInvalid => "manifest_schema_invalid"
  | .contentDigestMismatch => "content_digest_mismatch"
  | .capabilityVersionUnsupported => "capability_version_unsupported"
  | .checkerReceiptInvalid => "checker_receipt_invalid"
  | .axiomPolicyViolation => "axiom_policy_violation"
  | .schemaVersionUnsupported => "schema_version_unsupported"
  | .resourceLimitExceeded => "resource_limit_exceeded"
  | .replayDependencyMissing => "replay_dependency_missing"
  | .assuranceModeUnavailable => "assurance_mode_unavailable"
  | .cancelled => "cancelled"

def ErrorCode.ofWire? : String → Option ErrorCode
  | "unsupported_expression" => some .unsupportedExpression
  | "unsupported_type" => some .unsupportedType
  | "ambiguous_interpretation" => some .ambiguousInterpretation
  | "missing_assumption" => some .missingAssumption
  | "branch_convention_required" => some .branchConventionRequired
  | "partial_operation_unresolved" => some .partialOperationUnresolved
  | "claim_strength_unavailable" => some .claimStrengthUnavailable
  | "goal_mismatch" => some .goalMismatch
  | "side_condition_unproved" => some .sideConditionUnproved
  | "encoding_version_unsupported" => some .encodingVersionUnsupported
  | "operation_unsupported" => some .operationUnsupported
  | "backend_unavailable" => some .backendUnavailable
  | "backend_timeout" => some .backendTimeout
  | "backend_crash" => some .backendCrash
  | "backend_unsupported" => some .backendUnsupported
  | "backend_nondeterministic_failure" => some .backendNondeterministicFailure
  | "malformed_evidence" => some .malformedEvidence
  | "request_digest_mismatch" => some .requestDigestMismatch
  | "candidate_rejected" => some .candidateRejected
  | "certificate_rejected" => some .certificateRejected
  | "certificate_decode_failed" => some .certificateDecodeFailed
  | "completeness_not_established" => some .completenessNotEstablished
  | "approximation_bound_missing" => some .approximationBoundMissing
  | "content_address_collision" => some .contentAddressCollision
  | "bundle_not_found" => some .bundleNotFound
  | "bundle_path_forbidden" => some .bundlePathForbidden
  | "bundle_path_rejected" => some .bundlePathRejected
  | "manifest_schema_invalid" => some .manifestSchemaInvalid
  | "content_digest_mismatch" => some .contentDigestMismatch
  | "capability_version_unsupported" => some .capabilityVersionUnsupported
  | "checker_receipt_invalid" => some .checkerReceiptInvalid
  | "axiom_policy_violation" => some .axiomPolicyViolation
  | "schema_version_unsupported" => some .schemaVersionUnsupported
  | "resource_limit_exceeded" => some .resourceLimitExceeded
  | "replay_dependency_missing" => some .replayDependencyMissing
  | "assurance_mode_unavailable" => some .assuranceModeUnavailable
  | "cancelled" => some .cancelled
  | _ => none

/-- Structured error suitable for agents: stable code + optional diagnostic. -/
structure StructuredError where
  code : ErrorCode
  message : String := ""
  deriving DecidableEq, Repr, Inhabited

end MathEvidence.Core
