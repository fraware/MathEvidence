"""Stable structured errors (Project Spec §13)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ErrorCategory(str, Enum):
    SEMANTIC = "semantic"
    BACKEND = "backend"
    EVIDENCE = "evidence"
    SYSTEM = "system"


# JSON-RPC application error codes (outside reserved -32768..-32000 conflicts).
RPC_APPLICATION_ERROR = -32000

STABLE_CODES: dict[str, ErrorCategory] = {
    # Semantic
    "unsupported_expression": ErrorCategory.SEMANTIC,
    "unsupported_type": ErrorCategory.SEMANTIC,
    "ambiguous_interpretation": ErrorCategory.SEMANTIC,
    "missing_assumption": ErrorCategory.SEMANTIC,
    "branch_convention_required": ErrorCategory.SEMANTIC,
    "partial_operation_unresolved": ErrorCategory.SEMANTIC,
    "claim_strength_unavailable": ErrorCategory.SEMANTIC,
    # Backend
    "backend_unavailable": ErrorCategory.BACKEND,
    "backend_timeout": ErrorCategory.BACKEND,
    "backend_crash": ErrorCategory.BACKEND,
    "backend_unsupported": ErrorCategory.BACKEND,
    "backend_nondeterministic_failure": ErrorCategory.BACKEND,
    # Evidence
    "malformed_evidence": ErrorCategory.EVIDENCE,
    "request_digest_mismatch": ErrorCategory.EVIDENCE,
    "candidate_rejected": ErrorCategory.EVIDENCE,
    "certificate_rejected": ErrorCategory.EVIDENCE,
    "completeness_not_established": ErrorCategory.EVIDENCE,
    "approximation_bound_missing": ErrorCategory.EVIDENCE,
    # System
    "schema_version_unsupported": ErrorCategory.SYSTEM,
    "resource_limit_exceeded": ErrorCategory.SYSTEM,
    "replay_dependency_missing": ErrorCategory.SYSTEM,
    "assurance_mode_unavailable": ErrorCategory.SYSTEM,
    "cancelled": ErrorCategory.SYSTEM,
}


@dataclass
class AdapterError(Exception):
    code: str
    message: str
    details: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.code not in STABLE_CODES:
            raise ValueError(f"unknown stable error code: {self.code}")
        super().__init__(self.message)

    @property
    def category(self) -> ErrorCategory:
        return STABLE_CODES[self.code]

    def to_rpc_error(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "errorCode": self.code,
            "category": self.category.value,
        }
        if self.details:
            data["details"] = self.details
        return {
            "code": RPC_APPLICATION_ERROR,
            "message": self.message,
            "data": data,
        }


def stable_error(
    code: str,
    message: str,
    *,
    details: dict[str, Any] | None = None,
) -> AdapterError:
    return AdapterError(code=code, message=message, details=details)
