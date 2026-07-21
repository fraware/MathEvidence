"""Tests for receipt canonicalization, content digest, and optional dev signing."""

from __future__ import annotations

import pytest

from adapters.common.receipt_crypto import (
    attach_receipt_digest,
    ensure_dev_hmac_key,
    receipt_content_digest,
    sign_receipt_hmac,
    verify_receipt_digest,
    verify_receipt_hmac,
    verify_receipt_signature_if_present,
)


def _sample_receipt() -> dict:
    return {
        "schemaVersion": "0.1.0",
        "requestDigest": "sha256:" + "ab" * 32,
        "bundleDigest": "sha256:" + "cd" * 32,
        "theoremDigest": "sha256:" + "ef" * 32,
        "resultStatus": "witness_verified",
        "claimEstablished": "witness",
        "capability": {"id": "algebra.rational_equality", "version": "0.1.0"},
        "checker": {
            "package": "MathEvidence",
            "module": "Checkers.RationalEquality",
            "name": "checkBool",
            "version": "0.1.0",
        },
        "claimRequested": "witness",
        "unresolvedObligations": [],
        "assuranceMode": "kernel_replay",
        "toolchain": {"leanVersion": "4.14.0", "lakeVersion": "5.0.0"},
    }


def test_receipt_digest_is_deterministic() -> None:
    r1 = attach_receipt_digest(_sample_receipt())
    r2 = attach_receipt_digest(_sample_receipt())
    assert r1["receiptDigest"] == r2["receiptDigest"]
    assert r1["contentDigest"] == r1["receiptDigest"]
    assert verify_receipt_digest(r1) == r1["receiptDigest"]


def test_receipt_digest_detects_tamper() -> None:
    r = attach_receipt_digest(_sample_receipt())
    r["detail"] = "tampered"
    with pytest.raises(ValueError, match="mismatch"):
        verify_receipt_digest(r)


def test_hmac_sign_and_verify(tmp_path) -> None:
    key_path = ensure_dev_hmac_key(tmp_path)
    key = key_path.read_bytes()
    signed = sign_receipt_hmac(_sample_receipt(), key=key)
    assert signed["signatureAlg"] == "hmac-sha256"
    assert verify_receipt_hmac(signed, key=key)
    gate = verify_receipt_signature_if_present(signed, key_dir=tmp_path)
    assert gate["ok"] is True
    assert gate["signatureVerified"] is True


def test_unsigned_digest_gate() -> None:
    r = attach_receipt_digest(_sample_receipt())
    gate = verify_receipt_signature_if_present(r)
    assert gate["ok"] is True
    assert gate["digestVerified"] is True
    assert gate["signatureStatus"] == "unsigned"


def test_content_digest_matches_attach() -> None:
    base = _sample_receipt()
    assert receipt_content_digest(base) == attach_receipt_digest(base)["contentDigest"]
