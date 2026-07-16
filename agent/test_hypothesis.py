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
    lattice = build_condition_lattice(artifact_id="t", request=request, poly_zero=True)
    assert lattice["claimsMinimal"] is False


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
