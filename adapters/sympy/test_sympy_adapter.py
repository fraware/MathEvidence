"""SymPy rational-equality adapter tests."""

from __future__ import annotations

from adapters.common.canonical import bind_request_digest
from adapters.common.errors import AdapterError
from adapters.common.limits import ResourceLimits, ResourceTracker
from adapters.common.rational_ir import add_expr, div_expr, int_expr, pow_expr, sub_expr, var_expr
from adapters.sympy.adapter import compute_rational_equality


def _req(lhs, rhs, variables):
    return bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.rational_equality",
            "capabilityVersion": "0.1.0",
            "variables": [{"name": n, "type": "Rat"} for n in variables],
            "lhs": lhs,
            "rhs": rhs,
            "knownAssumptions": [],
            "requestedClaim": "soundResult",
            "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
        }
    )


def test_valid_identity_zero_numerator() -> None:
    x = var_expr("x")
    lhs = div_expr(sub_expr(pow_expr(x, 2), int_expr(1)), sub_expr(x, int_expr(1)))
    rhs = add_expr(x, int_expr(1))
    result = compute_rational_equality(_req(lhs, rhs, ["x"]), ResourceTracker(ResourceLimits()))
    assert result.result["candidate"]["isZeroNumerator"] is True
    roles = {f["role"] for f in result.result["certificate"]["denominatorFactors"]}
    assert "original_division" in roles


def test_false_identity_nonzero_numerator() -> None:
    x = var_expr("x")
    result = compute_rational_equality(
        _req(div_expr(x, x), int_expr(2), ["x"]), ResourceTracker(ResourceLimits())
    )
    assert result.result["candidate"]["isZeroNumerator"] is False


def test_undeclared_variable_rejected() -> None:
    try:
        compute_rational_equality(
            _req(var_expr("y"), int_expr(0), ["x"]), ResourceTracker(ResourceLimits())
        )
        raise AssertionError("expected AdapterError")
    except AdapterError as exc:
        assert exc.code == "unsupported_expression"
