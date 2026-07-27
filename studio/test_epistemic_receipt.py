"""Studio Certified label requires Certification Record gate (ME-RV-024)."""

from __future__ import annotations

from studio.epistemic_contract import (
    build_certification_surface,
    certification_gate,
    verify_checker_receipt,
)


def test_verify_checker_receipt_rejects_missing() -> None:
    out = verify_checker_receipt(None)
    assert out["allowCertified"] is False


def test_verify_checker_receipt_never_certifies_alone() -> None:
    out = verify_checker_receipt(
        {
            "requestDigest": "sha256:" + ("ab" * 32),
            "resultStatus": "soundness_verified",
            "claimEstablished": "soundResult",
        }
    )
    assert out["ok"] is True
    assert out["allowCertified"] is False


def test_certification_gate_requires_full_agent_fields() -> None:
    dig = "sha256:" + ("ab" * 32)
    out = certification_gate(
        certification_verified=True,
        certification_id="cert_sha256_" + ("c" * 64),
        claim_established="soundResult",
        theorem_type_digest=dig,
        result_status="soundness_verified",
    )
    assert out["allowCertified"] is True


def test_certification_surface_blocks_certified_without_proposition() -> None:
    surface = build_certification_surface(
        result_status="soundness_verified",
        lean_status="soundness_verified",
        lean_proposition="",
        assumptions=["x ≠ 0"],
        certification_verified=True,
        certification_id="cert_sha256_" + ("c" * 64),
        claim_established="soundResult",
        theorem_type_digest="sha256:" + ("d" * 64),
    )
    assert surface["epistemic"]["allowCertified"] is False


def test_certification_surface_certified_with_record_and_proposition() -> None:
    surface = build_certification_surface(
        result_status="soundness_verified",
        lean_status="soundness_verified",
        lean_proposition="∀ x : ℚ, x ≠ 0 → (x^2-1)/(x-1) = x+1",
        assumptions=["x ≠ 0"],
        certification_verified=True,
        certification_id="cert_sha256_" + ("c" * 64),
        claim_established="soundResult",
        theorem_type_digest="sha256:" + ("d" * 64),
    )
    assert surface["epistemic"]["allowCertified"] is True
    receipt = verify_checker_receipt(
        {
            "requestDigest": "sha256:" + ("cd" * 32),
            "resultStatus": "soundness_verified",
            "claimEstablished": "soundResult",
        }
    )
    assert receipt["allowCertified"] is False
