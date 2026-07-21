"""Stable replay / evidence error codes required by closure spec 03."""

from __future__ import annotations

from adapters.common.errors import STABLE_CODES, ErrorCategory


REQUIRED_REPLAY_CODES = {
    "bundle_not_found",
    "bundle_path_forbidden",
    "manifest_schema_invalid",
    "content_digest_mismatch",
    "request_digest_mismatch",
    "capability_version_unsupported",
    "encoding_version_unsupported",
    "goal_mismatch",
    "certificate_decode_failed",
    "certificate_rejected",
    "side_condition_unproved",
    "axiom_policy_violation",
    "checker_receipt_invalid",
    "resource_limit_exceeded",
}


def test_spec03_replay_error_codes_registered() -> None:
    missing = REQUIRED_REPLAY_CODES - set(STABLE_CODES)
    assert not missing, f"missing stable replay codes: {sorted(missing)}"
    assert STABLE_CODES["bundle_not_found"] == ErrorCategory.EVIDENCE
    assert STABLE_CODES["goal_mismatch"] == ErrorCategory.SEMANTIC
    assert STABLE_CODES["resource_limit_exceeded"] == ErrorCategory.SYSTEM


def test_ttp_ops_honestly_unsupported() -> None:
    from agent.api import service

    built = service.op_build_proof_plan({})
    assert built["resultStatus"] == "unsupported"
    recon = service.op_reconstruct_plan({"workspaceId": "w1"})
    assert recon["resultStatus"] == "unsupported"
