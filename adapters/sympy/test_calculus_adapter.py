"""SymPy symbolic calculus adapter tests (Milestone 5)."""

from __future__ import annotations

from adapters.common.canonical import bind_request_digest
from adapters.common.lean_mirrors import check_symbolic_calculus
from adapters.common.limits import ResourceLimits, ResourceTracker
from adapters.sympy.adapter import compute_symbolic_calculus


def _deriv_req():
    return bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.formal_rational_calculus",
            "capabilityVersion": "0.1.0",
            "operation": "derivative_candidate",
            "variables": [{"name": "x", "type": "Rat"}],
            "independentVar": "x",
            "expr": {"tag": "pow", "base": {"tag": "var", "name": "x"}, "exp": 2},
            "candidate": {
                "tag": "mul",
                "left": {"tag": "int", "value": "2"},
                "right": {"tag": "var", "name": "x"},
            },
            "domainConditions": [],
            "requestedClaim": "candidate",
            "resourcePolicy": {"maxWallTimeMs": 60000, "maxOutputBytes": 1048576},
        }
    )


def test_derivative_candidate_compute() -> None:
    req = _deriv_req()
    result = compute_symbolic_calculus(req, ResourceTracker(ResourceLimits()))
    assert result.result["capability"] == "algebra.formal_rational_calculus"
    cert = result.result["certificate"]
    assert cert["operation"] == "derivative_candidate"
    assert cert["requestDigest"] == req["requestDigest"]
    assert check_symbolic_calculus(req, cert) is True


def test_recurrence_candidate_compute() -> None:
    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.formal_rational_calculus",
            "capabilityVersion": "0.1.0",
            "operation": "recurrence_identity",
            "variables": [
                {"name": "n", "type": "Rat"},
                {"name": "u", "type": "Rat"},
            ],
            "independentVar": "n",
            "dependentVar": "u",
            "expr": {"tag": "var", "name": "n"},
            "candidate": {"tag": "int", "value": "0"},
            "recurrenceRhs": {
                "tag": "add",
                "left": {"tag": "var", "name": "u"},
                "right": {"tag": "int", "value": "1"},
            },
            "domainConditions": [],
            "requestedClaim": "candidate",
            "resourcePolicy": {"maxWallTimeMs": 60000, "maxOutputBytes": 1048576},
        }
    )
    result = compute_symbolic_calculus(req, ResourceTracker(ResourceLimits()))
    cert = result.result["certificate"]
    assert check_symbolic_calculus(req, cert) is True
