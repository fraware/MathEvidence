"""Tests for Product 03/04 orchestration helpers."""

from __future__ import annotations

from adapters.common.canonical import bind_request_digest
from adapters.common.hypothesis_util import find_counterexample, propose_conditions_from_request
from adapters.common.lean_mirrors import check_finite_counterexample, check_linear_algebra
from agent.hypothesis import build_condition_lattice, delete_hypothesis_python
from foundry.capture import capture_episode


def test_propose_conditions_from_div() -> None:
    req = {
        "lhs": {
            "tag": "div",
            "num": {"tag": "int", "value": "1"},
            "den": {"tag": "var", "name": "x"},
        },
        "rhs": {"tag": "int", "value": "0"},
    }
    props = propose_conditions_from_request(req)
    assert props
    assert props[0]["source"] == "backend_proposed"


def test_delete_marks_necessity_open() -> None:
    request = {
        "lhs": {
            "tag": "div",
            "num": {"tag": "int", "value": "1"},
            "den": {"tag": "var", "name": "x"},
        },
        "rhs": {"tag": "int", "value": "1"},
    }
    conditions = [
        {
            "id": "c0",
            "expr": {"tag": "var", "name": "x"},
            "source": "backend_proposed",
            "status": "proposed",
        }
    ]
    out = delete_hypothesis_python(request, conditions, "c0", poly_zero=True)
    assert out["result"] == "not_redundant"
    assert out["necessity"] == "open"
    assert out["authorityStatus"] == "lean_checker_mirror"


def test_lattice_claims_minimal_false() -> None:
    request = {
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
    lattice = build_condition_lattice(artifact_id="t", request=request)
    assert lattice["claimsMinimal"] is False
    assert lattice["authorityStatus"] == "lean_checker_mirror"
    assert lattice["sufficientSets"]


def test_prove_sufficient_lean_authoritative() -> None:
    from agent.hypothesis import (
        SUFFICIENCY_CHECKER_DECL,
        SUFFICIENCY_THEOREM_DECL,
        prove_sufficient_python,
    )

    request = {
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
    conds = propose_conditions_from_request(request)
    out = prove_sufficient_python(
        request,
        conds,
        receipt_ref={"receiptId": "recv-test-1"},
        axiom_report_id="axiom-report-demo",
    )
    assert out["authorityStatus"] == "lean_checker_mirror"
    assert out["outcome"] == "proved"
    assert out["sufficient"] is True
    assert out["evidence"]["theoremDecl"] == SUFFICIENCY_THEOREM_DECL
    assert out["evidence"]["checkerDecl"] == SUFFICIENCY_CHECKER_DECL
    assert out["evidence"]["receiptId"] == "recv-test-1"
    assert out["evidence"]["axiomReportId"] == "axiom-report-demo"


def test_prove_sufficient_refuses_denom_coverage_alone() -> None:
    """Coverage of denoms must not mark sufficiency when poly identity fails."""
    from agent.hypothesis import prove_sufficient_python

    request = {
        "lhs": {
            "tag": "div",
            "num": {"tag": "var", "name": "x"},
            "den": {"tag": "var", "name": "x"},
        },
        "rhs": {"tag": "int", "value": "2"},
    }
    # Correct denom coverage for x/x, but identity x/x = 2 is false.
    conditions = [
        {
            "id": "c0",
            "expr": {"tag": "var", "name": "x"},
            "role": "original_division",
            "source": "backend_proposed",
            "status": "proposed",
        }
    ]
    out = prove_sufficient_python(request, conditions)
    assert out["denominatorsCovered"] is True
    assert out["sufficient"] is False
    assert out["outcome"] == "failed"
    assert out["evidence"]["detail"] == "poly_identity_failed_despite_denom_coverage"
    assert any("denom coverage alone" in n for n in out["notes"])


def test_family_campaign_precision_accounting() -> None:
    from agent.conjecture import run_family_campaign

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
    campaign = run_family_campaign(
        family_id="finite.nat_le_3",
        candidates=[
            {"pred": req["predicate"]["pred"], "request": req},
            {
                "pred": {
                    "tag": "eq",
                    "left": {"tag": "var", "idx": 0},
                    "right": {"tag": "var", "idx": 0},
                },
                "outcome": "formally_proved",
                "theoremRef": "eq_refl_on_nat3",
            },
            {
                "pred": {
                    "tag": "le",
                    "left": {"tag": "var", "idx": 0},
                    "right": {"tag": "var", "idx": 0},
                },
                "outcome": "open",
                "openDetail": "See conjecture-open-problem-nat-le-family.md",
                "searchBound": 4,
            },
        ],
    )
    acc = campaign["precisionAccounting"]
    assert acc["proposed"] == 3
    assert acc["falsified"] == 1
    assert acc["formallyProved"] == 1
    assert acc["openProblems"] == 1


def test_foundry_capture_never_accepts() -> None:
    ep = capture_episode(
        kind="hypothesis_lattice",
        payload={"demo": True},
        episode_dir=__import__("pathlib").Path("foundry/episodes"),
    )
    assert ep["acceptanceInfluence"] is False
    path = __import__("pathlib").Path(ep["_path"])
    assert path.is_file()
    path.unlink()


def test_finite_cex_mirror() -> None:
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
    cert = find_counterexample(req)
    assert cert is not None
    assert check_finite_counterexample(req, cert)


def test_la_inverse_mirror() -> None:
    def rat(n: int, d: int = 1) -> dict:
        return {"tag": "rat", "num": str(n), "den": str(d)}

    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.linear_algebra",
            "capabilityVersion": "0.1.0",
            "operation": "inverse_witness",
            "matrix": {
                "tag": "matrix",
                "rows": 2,
                "cols": 2,
                "entries": [[rat(1, 2), rat(0)], [rat(0), rat(2)]],
            },
            "requestedClaim": "witness",
            "resourcePolicy": {"maxWallTimeMs": 5000, "maxOutputBytes": 65536},
        }
    )
    cert = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.linear_algebra",
        "capabilityVersion": "0.1.0",
        "requestDigest": req["requestDigest"],
        "operation": "inverse_witness",
        "inverse": {
            "tag": "matrix",
            "rows": 2,
            "cols": 2,
            "entries": [[rat(2), rat(0)], [rat(0), rat(1, 2)]],
        },
        "provenance": {"backendId": "test", "adapterVersion": "0.1.0"},
    }
    assert check_linear_algebra(req, cert)


def test_make_condition_node_typed_kinds() -> None:
    from agent.hypothesis import CONDITION_NODE_KINDS, make_condition_node

    node = make_condition_node(
        node_id="c0",
        kind="nonzero_denominator",
        expr={"tag": "var", "name": "x"},
        lean_prop_hint="x ≠ 0",
    )
    assert node["kind"] in CONDITION_NODE_KINDS
    assert node["leanPropHint"] == "x ≠ 0"
    assert node["sufficiencyRequires"] == "lean_proof_and_receipt"
    try:
        make_condition_node(node_id="bad", kind="not_a_kind", expr={})
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
