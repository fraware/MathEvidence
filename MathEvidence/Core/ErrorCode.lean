/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
namespace MathEvidence.Core

/-- Stable structured error codes (Project Spec §13).

Free-form exception strings are diagnostic supplements only. -/
inductive ErrorCode where
  -- Semantic
  | unsupportedExpression
  | unsupportedType
  | ambiguousInterpretation
  | missingAssumption
  | branchConventionRequired
  | partialOperationUnresolved
  | claimStrengthUnavailable
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
  | completenessNotEstablished
  | approximationBoundMissing
  -- System
  | schemaVersionUnsupported
  | resourceLimitExceeded
  | replayDependencyMissing
  | assuranceModeUnavailable
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
  | .claimStrengthUnavailable => .semantic
  | .backendUnavailable | .backendTimeout | .backendCrash | .backendUnsupported
  | .backendNondeterministicFailure => .backend
  | .malformedEvidence | .requestDigestMismatch | .candidateRejected
  | .certificateRejected | .completenessNotEstablished | .approximationBoundMissing =>
    .evidence
  | .schemaVersionUnsupported | .resourceLimitExceeded | .replayDependencyMissing
  | .assuranceModeUnavailable => .system

def ErrorCode.toWire : ErrorCode → String
  | .unsupportedExpression => "unsupported_expression"
  | .unsupportedType => "unsupported_type"
  | .ambiguousInterpretation => "ambiguous_interpretation"
  | .missingAssumption => "missing_assumption"
  | .branchConventionRequired => "branch_convention_required"
  | .partialOperationUnresolved => "partial_operation_unresolved"
  | .claimStrengthUnavailable => "claim_strength_unavailable"
  | .backendUnavailable => "backend_unavailable"
  | .backendTimeout => "backend_timeout"
  | .backendCrash => "backend_crash"
  | .backendUnsupported => "backend_unsupported"
  | .backendNondeterministicFailure => "backend_nondeterministic_failure"
  | .malformedEvidence => "malformed_evidence"
  | .requestDigestMismatch => "request_digest_mismatch"
  | .candidateRejected => "candidate_rejected"
  | .certificateRejected => "certificate_rejected"
  | .completenessNotEstablished => "completeness_not_established"
  | .approximationBoundMissing => "approximation_bound_missing"
  | .schemaVersionUnsupported => "schema_version_unsupported"
  | .resourceLimitExceeded => "resource_limit_exceeded"
  | .replayDependencyMissing => "replay_dependency_missing"
  | .assuranceModeUnavailable => "assurance_mode_unavailable"

def ErrorCode.ofWire? : String → Option ErrorCode
  | "unsupported_expression" => some .unsupportedExpression
  | "unsupported_type" => some .unsupportedType
  | "ambiguous_interpretation" => some .ambiguousInterpretation
  | "missing_assumption" => some .missingAssumption
  | "branch_convention_required" => some .branchConventionRequired
  | "partial_operation_unresolved" => some .partialOperationUnresolved
  | "claim_strength_unavailable" => some .claimStrengthUnavailable
  | "backend_unavailable" => some .backendUnavailable
  | "backend_timeout" => some .backendTimeout
  | "backend_crash" => some .backendCrash
  | "backend_unsupported" => some .backendUnsupported
  | "backend_nondeterministic_failure" => some .backendNondeterministicFailure
  | "malformed_evidence" => some .malformedEvidence
  | "request_digest_mismatch" => some .requestDigestMismatch
  | "candidate_rejected" => some .candidateRejected
  | "certificate_rejected" => some .certificateRejected
  | "completeness_not_established" => some .completenessNotEstablished
  | "approximation_bound_missing" => some .approximationBoundMissing
  | "schema_version_unsupported" => some .schemaVersionUnsupported
  | "resource_limit_exceeded" => some .resourceLimitExceeded
  | "replay_dependency_missing" => some .replayDependencyMissing
  | "assurance_mode_unavailable" => some .assuranceModeUnavailable
  | _ => none

/-- Structured error suitable for agents: stable code + optional diagnostic. -/
structure StructuredError where
  code : ErrorCode
  message : String := ""
  deriving DecidableEq, Repr, Inhabited

end MathEvidence.Core
