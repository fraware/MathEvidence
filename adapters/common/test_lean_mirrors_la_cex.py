"""Parity tests for Python Lean-mirror checkers (LA / finite CEX)."""

from __future__ import annotations

from adapters.common.canonical import bind_request_digest
from adapters.common.lean_mirrors import check_finite_counterexample, check_linear_algebra


def _rat(n: int, d: int = 1) -> dict:
    return {"tag": "rat", "num": str(n), "den": str(d)}


def test_la_inverse_accepts() -> None:
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
                "entries": [[_rat(1, 2), _rat(0)], [_rat(0), _rat(2)]],
            },
            "requestedClaim": "witness",
            "resourcePolicy": {"maxWallTimeMs": 60000, "maxOutputBytes": 1048576},
        }
    )
    cert = {
        "requestDigest": req["requestDigest"],
        "operation": "inverse_witness",
        "inverse": {
            "tag": "matrix",
            "rows": 2,
            "cols": 2,
            "entries": [[_rat(2), _rat(0)], [_rat(0), _rat(1, 2)]],
        },
    }
    assert check_linear_algebra(req, cert) is True


def test_la_singular_inverse_rejects() -> None:
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
                "entries": [[_rat(1), _rat(2)], [_rat(2), _rat(4)]],
            },
            "requestedClaim": "witness",
            "resourcePolicy": {"maxWallTimeMs": 60000, "maxOutputBytes": 1048576},
        }
    )
    cert = {
        "requestDigest": req["requestDigest"],
        "operation": "inverse_witness",
        "inverse": {
            "tag": "matrix",
            "rows": 2,
            "cols": 2,
            "entries": [[_rat(1), _rat(0)], [_rat(0), _rat(1)]],
        },
    }
    assert check_linear_algebra(req, cert) is False


def test_cex_ood_and_type_mismatch_reject() -> None:
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
            "resourcePolicy": {"maxWallTimeMs": 60000, "maxOutputBytes": 1048576},
        }
    )
    digest = req["requestDigest"]
    good = {
        "requestDigest": digest,
        "witness": {"assignment": [{"tag": "nat", "v": 1}]},
    }
    ood = {
        "requestDigest": digest,
        "witness": {"assignment": [{"tag": "nat", "v": 9}]},
    }
    mismatch = {
        "requestDigest": digest,
        "witness": {"assignment": [{"tag": "bool", "v": False}]},
    }
    assert check_finite_counterexample(req, good) is True
    assert check_finite_counterexample(req, ood) is False
    assert check_finite_counterexample(req, mismatch) is False
