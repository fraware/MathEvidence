"""Wave 2 digest vectors for theorem identity / replay target / env lock."""

from __future__ import annotations

from pathlib import Path

from adapters.common.theorem_identity import (
    THEOREM_IDENTITY_SERIALIZER_VERSION,
    environment_lock_digest,
    replay_target_digest,
    theorem_type_digest,
)
from adapters.common.theorem_identity_vectors import DIGEST_VECTORS, published_digests

ROOT = Path(__file__).resolve().parents[2]


def test_serializer_version_pinned() -> None:
    assert THEOREM_IDENTITY_SERIALIZER_VERSION == "mathevidence-theorem-identity-0.4"


def test_published_vectors_stable() -> None:
    digests = published_digests()
    assert "env_lock_rational_default" in digests
    assert "theorem_type_add0" in digests
    assert "replay_target_add0" in digests
    # Digests must be wire-shaped.
    for d in digests.values():
        assert d.startswith("sha256:")
        assert len(d) == 71


def test_vector_recompute_matches_published() -> None:
    for vector in DIGEST_VECTORS:
        kind = vector["kind"]
        payload = vector["payload"]
        expected = vector["digest"]
        if kind == "environment_lock":
            assert environment_lock_digest(payload) == expected
        elif kind == "theorem_type":
            assert theorem_type_digest(payload) == expected
        elif kind == "replay_target":
            assert replay_target_digest(payload) == expected
        elif kind == "theorem_identity":
            # Identity role digest is the theorem type digest for this vector.
            assert theorem_type_digest(
                {
                    "schemaVersion": payload["schemaVersion"],
                    "serializerVersion": payload["serializerVersion"],
                    "elaboratedSerialization": payload["elaboratedSerialization"],
                    "universeParams": payload.get("universeParams") or [],
                    "binders": payload.get("binders") or [],
                    "constantNames": payload.get("constantNames") or [],
                    "environmentLockDigest": payload["environmentLockDigest"],
                }
            ) == expected


def test_pretty_print_alone_insufficient() -> None:
    """Changing only pretty text without binders/env must change digest."""
    base = next(v for v in DIGEST_VECTORS if v["id"] == "theorem_type_add0")
    payload = dict(base["payload"])
    payload["elaboratedSerialization"] = "x + 0 = x  -- pretty only"
    assert theorem_type_digest(payload) != base["digest"]


def test_serializer_version_required_in_binding() -> None:
    """Serializer version participates in the digest (schema bump discipline)."""
    base = next(v for v in DIGEST_VECTORS if v["id"] == "theorem_type_add0")
    payload = dict(base["payload"])
    payload["serializerVersion"] = "mathevidence-theorem-identity-0.2"
    assert theorem_type_digest(payload) != base["digest"]
    payload["serializerVersion"] = THEOREM_IDENTITY_SERIALIZER_VERSION
    assert theorem_type_digest(payload) == base["digest"]


def test_binders_and_universe_params_participate() -> None:
    """Stronger structural binding: binders + universeParams change the digest."""
    base = next(v for v in DIGEST_VECTORS if v["id"] == "theorem_type_add0")
    payload = dict(base["payload"])
    payload["binders"] = [
        {
            "name": "y",
            "kind": "implicit",
            "typeSerialization": "Nat",
        }
    ]
    assert theorem_type_digest(payload) != base["digest"]
    payload = dict(base["payload"])
    payload["universeParams"] = ["u"]
    assert theorem_type_digest(payload) != base["digest"]
    payload = dict(base["payload"])
    payload["constantNames"] = ["Rat", "Eq", "HAdd"]
    assert theorem_type_digest(payload) != base["digest"]


def test_environment_lock_digest_required() -> None:
    """Environment lock is part of theorem-type identity binding."""
    base = next(v for v in DIGEST_VECTORS if v["id"] == "theorem_type_add0")
    payload = dict(base["payload"])
    payload["environmentLockDigest"] = "sha256:" + ("11" * 32)
    assert theorem_type_digest(payload) != base["digest"]


def test_lean_expr_serialize_is_kernel_walk() -> None:
    """ME-RV-020: Lean Meta uses Expr structure walk, not ppExpr, for digests."""
    expr_ser = (ROOT / "MathEvidence" / "Core" / "ExprSerialize.lean").read_text(
        encoding="utf-8"
    )
    assert "partial def serializeExpr" in expr_ser
    assert "partial def serializeLevel" in expr_ser
    assert "theoremTypeIdentityOfExpr" in expr_ser
    # Doc may mention ppExpr as the non-authority; the def must not call it.
    assert "toString <$> ppExpr" not in expr_ser
    assert "← ppExpr" not in expr_ser
    replay = (ROOT / "MathEvidence" / "Tactic" / "Replay.lean").read_text(
        encoding="utf-8"
    )
    assert "ExprSerialize.theoremTypeIdentityOfExpr" in replay
    assert "ppExpr tgt" not in replay
    tests = (ROOT / "MathEvidence" / "Core" / "ExprSerializeTests.lean").read_text(
        encoding="utf-8"
    )
    assert "#test_theorem_identity_expr" in tests


def test_proof_term_serialize_not_expr_hash() -> None:
    """ME-RV-020: proof-term digests use serializeExpr; never Lean Expr.hash."""
    expr_ser = (ROOT / "MathEvidence" / "Core" / "ExprSerialize.lean").read_text(
        encoding="utf-8"
    )
    assert "def proofTermSerializationOfConst?" in expr_ser
    assert "def proofTermDigestOfConst?" in expr_ser
    assert "serializeExpr v" in expr_ser
    # Must not call Lean's unstable Expr.hash for identity digests.
    assert "← Expr.hash" not in expr_ser
    assert "Expr.hash v" not in expr_ser
    assert "hash v" not in expr_ser
    tests = (ROOT / "MathEvidence" / "Core" / "ExprSerializeTests.lean").read_text(
        encoding="utf-8"
    )
    assert "proofTermSerializationOfConst?" in tests
    assert "proofTermDigestOfConst?" in tests
