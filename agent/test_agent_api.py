"""Unit tests for Agent API service (in-process)."""

from __future__ import annotations

from adapters.common.canonical import bind_request_digest
from agent.api import service
from agent.sdk import list_capabilities_local, open_bundle_local, replay_bundle_local


def test_list_capabilities_includes_placeholders() -> None:
    out = list_capabilities_local()
    ids = {c["id"] for c in out["capabilities"]}
    assert "algebra.rational_equality" in ids
    assert "algebra.linear_algebra" in ids
    assert "logic.finite_counterexample" in ids
    assert "analysis.symbolic_calculus" in ids


def test_reject_unknown_capability() -> None:
    out = service.op_check_support({"capability": "nope.missing"})
    assert out["resultStatus"] == "unsupported"


def test_reject_shell_backend() -> None:
    out = service.op_compute_evidence(
        {
            "capability": "algebra.rational_equality",
            "backend": "bash",
            "request": {"schemaVersion": "0.1.0", "capability": "algebra.rational_equality"},
        }
    )
    assert out["resultStatus"] == "unsupported"


def test_open_and_replay_example_bundle() -> None:
    path = "evidence/examples/rational_equality_basic"
    opened = open_bundle_local(path)
    assert opened["bundleRef"]["capability"] == "algebra.rational_equality"
    assert "resultStatus" in opened
    assert isinstance(opened["unresolvedObligations"], list)
    replayed = replay_bundle_local(path)
    assert replayed["resultStatus"] == "tested"


def test_hypothesis_lattice_never_claims_minimal() -> None:
    request = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "lhs": {
            "tag": "div",
            "num": {
                "tag": "sub",
                "left": {"tag": "pow", "base": {"tag": "var", "name": "x"}, "exp": 2},
                "right": {"tag": "int", "value": "1"},
            },
            "den": {
                "tag": "sub",
                "left": {"tag": "var", "name": "x"},
                "right": {"tag": "int", "value": "1"},
            },
        },
        "rhs": {
            "tag": "add",
            "left": {"tag": "var", "name": "x"},
            "right": {"tag": "int", "value": "1"},
        },
    }
    out = service.op_build_condition_lattice(
        {"request": request, "artifactId": "test_lat", "polyZeroHint": True}
    )
    assert out["resultStatus"] == "computed"
    lattice = out["lattice"]
    assert lattice["claimsMinimal"] is False
    assert "c0" in lattice["recommendedInterface"] or lattice["sufficientSets"]


def test_conjecture_campaign_falsifies() -> None:
    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "logic.finite_counterexample",
            "capabilityVersion": "0.1.0",
            "predicate": {
                "varNames": ["x"],
                "domains": [{"ty": "nat", "bound": 3}],
                "pred": {
                    "tag": "eq",
                    "left": {"tag": "var", "idx": 0},
                    "right": {"tag": "lit", "v": {"tag": "nat", "v": 0}},
                },
            },
            "requestedClaim": "refutation",
            "resourcePolicy": {"maxWallTimeMs": 5000, "maxOutputBytes": 65536},
        }
    )
    out = service.op_conjecture_campaign({"request": req, "familyId": "finite.nat_le_3"})
    assert out["resultStatus"] == "computed"
    assert out["episode"]["state"] == "falsified"


def test_list_operations_includes_hypothesis() -> None:
    ops = {o["id"] for o in service.op_list_operations()["operations"]}
    assert "propose_conditions" in ops
    assert "build_condition_lattice" in ops
    assert "conjecture_campaign" in ops
