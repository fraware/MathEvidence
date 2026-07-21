"""Studio Certified label requires receipt + proposition (ME-307)."""

from __future__ import annotations

from studio.epistemic_contract import (
    build_certification_surface,
    verify_checker_receipt,
)


def test_verify_checker_receipt_rejects_missing() -> None:
    out = verify_checker_receipt(None)
    assert out["allowCertified"] is False


def test_verify_checker_receipt_requires_claim_established() -> None:
    out = verify_checker_receipt(
        {
            "requestDigest": "sha256:" + ("ab" * 32),
            "resultStatus": "soundness_verified",
            "claimEstablished": None,
        }
    )
    assert out["ok"] is True
    assert out["allowCertified"] is False


def test_verify_checker_receipt_accepts_bound_receipt() -> None:
    dig = "sha256:" + ("ab" * 32)
    out = verify_checker_receipt(
        {
            "requestDigest": dig,
            "resultStatus": "soundness_verified",
            "claimEstablished": "soundResult",
        },
        expected_request_digest=dig,
    )
    assert out["allowCertified"] is True


def test_certification_surface_blocks_certified_without_proposition() -> None:
    surface = build_certification_surface(
        result_status="soundness_verified",
        lean_status="soundness_verified",
        lean_proposition="",
        assumptions=["x ≠ 0"],
    )
    assert surface["epistemic"]["allowCertified"] is False
    assert surface["receiptVerified"] is False


def test_certification_surface_certified_only_with_proposition() -> None:
    surface = build_certification_surface(
        result_status="soundness_verified",
        lean_status="soundness_verified",
        lean_proposition="∀ x : ℚ, x ≠ 0 → (x^2-1)/(x-1) = x+1",
        assumptions=["x ≠ 0"],
    )
    # Surface may allow Certified from lean status + proposition, but Studio
    # still must call verify_checker_receipt before UI Certified.
    assert surface["epistemic"]["allowCertified"] is True
    receipt = verify_checker_receipt(
        {
            "requestDigest": "sha256:" + ("cd" * 32),
            "resultStatus": "soundness_verified",
            "claimEstablished": "soundResult",
        }
    )
    assert receipt["allowCertified"] is True
