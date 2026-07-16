"""Tests for Trace-to-Plan (Product 05)."""

from __future__ import annotations

import pytest

from agent.trace_to_plan import (
    classify_trace_item,
    hints_never_advance,
    plan_from_traces,
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


def test_reconstructible_advances_only_when_verified() -> None:
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

    verified = plan_from_traces(
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
    vnode = next(n for n in verified["nodes"] if n["id"] == "n_c1")
    assert vnode["advancesProofStatus"] is True
    assert vnode["status"] == "proved"


def test_plan_validates_against_schema() -> None:
    plan = plan_from_traces(
        target_theorem="det A = 1",
        traces=[
            {"id": "t1", "rawKind": "lemma", "content": {"claim": "A invertible"}},
            {"id": "t2", "rawKind": "checker", "content": {"claim": "inverse witness"}},
        ],
        reconstructions={
            "t2": {"method": "LinearAlgebra.checkBool", "resultStatus": "witness_verified"}
        },
    )
    SchemaStore().validate("proof-plan.schema.json", plan)


def test_cycle_rejected() -> None:
    plan = plan_from_traces(target_theorem="goal", traces=[])
    plan["edges"].append({"from": "target", "to": "target", "kind": "depends_on"})
    with pytest.raises(ValueError, match="cycle"):
        validate_plan_invariants(plan)
