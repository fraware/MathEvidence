"""Tests for Trace-to-Plan (Product 05)."""

from __future__ import annotations

import pytest

from agent.trace_to_plan import (
    classify_trace_item,
    hints_never_advance,
    plan_from_traces,
    reconstruct_from_receipt,
    reconstruction_has_verified_receipt,
    validate_plan_invariants,
)
from adapters.common.schema_validate import SchemaStore


def test_classify_defaults_unknown_to_search_hint() -> None:
    assert classify_trace_item({"id": "a", "rawKind": "mystery", "content": {}}) == "search_hint"


def test_hints_do_not_advance_proof_status() -> None:
    plan = plan_from_traces(
        target_theorem="∀ x, p x",
        traces=[
            {"id": "h1", "rawKind": "smt_hint", "content": {"claim": "try subst"}},
            {"id": "d1", "rawKind": "timing", "content": {"ms": 12}},
        ],
    )
    assert hints_never_advance(plan)
    for node in plan["nodes"]:
        if node["stepKind"] in {"search_hint", "diagnostic_metadata"}:
            assert node["advancesProofStatus"] is False
            assert node["status"] == "proposed"


def test_reconstructible_without_receipt_does_not_advance() -> None:
    bare = plan_from_traces(
        target_theorem="lhs = rhs",
        traces=[
            {
                "id": "c1",
                "rawKind": "certificate",
                "content": {"claim": "poly equal", "capability": "algebra.rational_equality"},
            }
        ],
    )
    node = next(n for n in bare["nodes"] if n["id"] == "n_c1")
    assert node["stepKind"] == "reconstructible_computation"
    assert node["advancesProofStatus"] is False
    assert "c1" in bare["unresolvedNodes"]

    # Method status alone is insufficient — receipt gate required.
    verified_no_receipt = plan_from_traces(
        target_theorem="lhs = rhs",
        traces=[
            {
                "id": "c1",
                "rawKind": "certificate",
                "content": {"claim": "poly equal", "capability": "algebra.rational_equality"},
            }
        ],
        reconstructions={
            "c1": {
                "method": "RationalEquality.checkBool",
                "resultStatus": "soundness_verified",
                "bundleRef": "evidence/examples/...",
            }
        },
    )
    vnode = next(n for n in verified_no_receipt["nodes"] if n["id"] == "n_c1")
    assert vnode["advancesProofStatus"] is False
    assert "c1" in verified_no_receipt["unresolvedNodes"]
    assert not reconstruction_has_verified_receipt(vnode["reconstruction"])


def test_reconstructible_advances_only_with_receipt() -> None:
    good = reconstruct_from_receipt(
        trace_id="c1",
        receipt={
            "requestDigest": "sha256:" + "ab" * 32,
            "resultStatus": "soundness_verified",
            "claimEstablished": "soundResult",
            "bundleDigest": "sha256:" + "cd" * 32,
        },
    )
    assert good is not None
    assert reconstruction_has_verified_receipt(good)

    plan = plan_from_traces(
        target_theorem="lhs = rhs",
        traces=[
            {
                "id": "c1",
                "rawKind": "certificate",
                "content": {
                    "claim": "poly equal",
                    "capability": "algebra.rational_equality",
                },
            }
        ],
        reconstructions={"c1": good},
    )
    vnode = next(n for n in plan["nodes"] if n["id"] == "n_c1")
    assert vnode["advancesProofStatus"] is True
    assert vnode["status"] == "proved"


def test_plan_validates_against_schema() -> None:
    recon = reconstruct_from_receipt(
        trace_id="t2",
        receipt={
            "requestDigest": "sha256:" + "ab" * 32,
            "resultStatus": "soundness_verified",
            "claimEstablished": "soundResult",
            "bundleDigest": "sha256:" + "cd" * 32,
        },
    )
    plan = plan_from_traces(
        target_theorem="det A = 1",
        traces=[
            {"id": "t1", "rawKind": "lemma", "content": {"claim": "A invertible"}},
            {"id": "t2", "rawKind": "checker", "content": {"claim": "inverse witness"}},
        ],
        reconstructions={"t2": recon} if recon else {},
    )
    SchemaStore().validate("proof-plan.schema.json", plan)


def test_cycle_rejected() -> None:
    plan = plan_from_traces(target_theorem="goal", traces=[])
    plan["edges"].append({"from": "target", "to": "target", "kind": "depends_on"})
    with pytest.raises(ValueError, match="cycle"):
        validate_plan_invariants(plan)


def test_reconstruct_from_receipt_advances_only_when_certified() -> None:
    bad = reconstruct_from_receipt(trace_id="c1", receipt={"resultStatus": "ok"})
    assert bad is None

    good = reconstruct_from_receipt(
        trace_id="c1",
        receipt={
            "requestDigest": "sha256:" + "ab" * 32,
            "resultStatus": "soundness_verified",
            "claimEstablished": "soundResult",
            "bundleDigest": "sha256:" + "cd" * 32,
        },
    )
    assert good is not None
    assert good["resultStatus"] == "soundness_verified"

    plan = plan_from_traces(
        target_theorem="lhs = rhs",
        traces=[
            {
                "id": "c1",
                "rawKind": "certificate",
                "content": {
                    "claim": "poly equal",
                    "capability": "algebra.rational_equality",
                },
            }
        ],
        reconstructions={"c1": good},
    )
    vnode = next(n for n in plan["nodes"] if n["id"] == "n_c1")
    assert vnode["advancesProofStatus"] is True


def test_plan_invariants_reject_cycle() -> None:
    with pytest.raises(ValueError, match="cycle"):
        validate_plan_invariants(
            {
                "nodes": [
                    {
                        "id": "a",
                        "stepKind": "direct_proof_step",
                        "status": "proved",
                        "advancesProofStatus": True,
                    },
                    {
                        "id": "b",
                        "stepKind": "direct_proof_step",
                        "status": "proved",
                        "advancesProofStatus": True,
                    },
                ],
                "edges": [{"from": "a", "to": "b"}, {"from": "b", "to": "a"}],
            }
        )


def test_plan_invariants_reject_hint_advancing() -> None:
    with pytest.raises(ValueError, match="non-reconstructible|hints"):
        validate_plan_invariants(
            {
                "nodes": [
                    {
                        "id": "h",
                        "stepKind": "search_hint",
                        "status": "proposed",
                        "advancesProofStatus": True,
                    }
                ],
                "edges": [],
            }
        )


def test_plan_invariants_reject_reconstructible_advance_without_receipt() -> None:
    with pytest.raises(ValueError, match="receiptGate"):
        validate_plan_invariants(
            {
                "nodes": [
                    {
                        "id": "c",
                        "stepKind": "reconstructible_computation",
                        "status": "proved",
                        "advancesProofStatus": True,
                        "reconstruction": {
                            "method": "handwave",
                            "resultStatus": "soundness_verified",
                        },
                    }
                ],
                "edges": [],
            }
        )
