"""Forensic: live Discovery must not overwrite Lean request digest with cert digest.

P0-1 — MathEvidence/Tactic/Discovery.lean must compare cert.requestDigest to a
Lean-derived expected digest and must never construct
`{ Request.ofClaim c with requestDigest := cert.requestDigest }`.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISCOVERY = ROOT / "MathEvidence" / "Tactic" / "Discovery.lean"

FORBIDDEN = "with requestDigest := cert.requestDigest"


def test_discovery_does_not_substitute_cert_request_digest() -> None:
    text = DISCOVERY.read_text(encoding="utf-8")
    assert FORBIDDEN not in text, (
        "P0-1 live request-binding bypass still present: "
        "Discovery.lean overwrites Lean requestDigest with cert.requestDigest. "
        "See docs/security/KNOWN_TRUST_GAPS.md."
    )


def test_discovery_compares_expected_lean_digest() -> None:
    text = DISCOVERY.read_text(encoding="utf-8")
    assert "Request.ofClaim" in text
    # Required shape after PR-Request-Binding: bind expected, then compare.
    assert "expected" in text.lower() or "expectedReq" in text or "expectedRequest" in text, (
        "Discovery.lean must compute an expected Lean request/digest before checkBool"
    )
