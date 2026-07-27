"""Tests for analytic calculus Python mirror (ME-RV-050..054)."""

from __future__ import annotations

import copy

import pytest

from adapters.common.analytic_calculus import (
    CAPABILITY_ID,
    AnalyticError,
    OFFLINE_FIXTURES,
    check_deriv_python,
    check_ode_python,
    propose_deriv_certificate,
    propose_ode_certificate,
)


def test_capability_id() -> None:
    assert CAPABILITY_ID == "analysis.analytic_calculus"


def test_product_certificate() -> None:
    source = {
        "tag": "mul",
        "lhs": {"tag": "variable", "idx": 0},
        "rhs": {"tag": "variable", "idx": 0},
    }
    cert = propose_deriv_certificate(source)
    assert check_deriv_python(cert)
    assert cert["claimsCompleteness"] is False


def test_completeness_rejected() -> None:
    cert = propose_deriv_certificate({"tag": "variable", "idx": 0})
    bad = copy.deepcopy(cert)
    bad["claimsCompleteness"] = True
    assert check_deriv_python(bad) is False


def test_missing_log_positivity() -> None:
    cert = propose_deriv_certificate({"tag": "log", "arg": {"tag": "variable", "idx": 0}})
    assert check_deriv_python(cert)
    bad = copy.deepcopy(cert)
    bad["obligations"] = []
    assert check_deriv_python(bad) is False


def test_missing_denominator_condition() -> None:
    source = {
        "tag": "div",
        "lhs": {"tag": "variable", "idx": 0},
        "rhs": {"tag": "add", "lhs": {"tag": "variable", "idx": 0}, "rhs": {"tag": "const", "value": "1"}},
    }
    cert = propose_deriv_certificate(source)
    bad = copy.deepcopy(cert)
    bad["obligations"] = []
    assert check_deriv_python(bad) is False


def test_incorrect_derivative_tree() -> None:
    cert = propose_deriv_certificate({"tag": "sin", "arg": {"tag": "variable", "idx": 0}})
    bad = copy.deepcopy(cert)
    bad["proof"] = {"tag": "exp", "p": {"tag": "variable"}}
    assert check_deriv_python(bad) is False


def test_incorrect_claimed_derivative() -> None:
    cert = propose_deriv_certificate({"tag": "sin", "arg": {"tag": "variable", "idx": 0}})
    bad = copy.deepcopy(cert)
    bad["derivative"] = {"tag": "const", "value": "0"}
    assert check_deriv_python(bad) is False


def test_multivariate_rejected() -> None:
    with pytest.raises(AnalyticError):
        propose_deriv_certificate({"tag": "variable", "idx": 1})


def test_nested_sin_exp_log() -> None:
    source = {
        "tag": "sin",
        "arg": {
            "tag": "exp",
            "arg": {"tag": "log", "arg": {"tag": "add", "lhs": {"tag": "variable", "idx": 0}, "rhs": {"tag": "const", "value": "1"}}},
        },
    }
    cert = propose_deriv_certificate(source)
    assert check_deriv_python(cert)
    assert any(o["tag"] == "positive" for o in cert["obligations"])


def test_ode_ic_wrong_still_shape_ok_but_prop_separate() -> None:
    """Checker accepts syntactic IC consts; wrong values are a Prop hypothesis failure."""
    cert = propose_ode_certificate(
        {"tag": "pow", "base": {"tag": "variable", "idx": 0}, "exp": 2},
        initial_conditions=[
            {
                "point": {"tag": "const", "value": "0"},
                "value": {"tag": "const", "value": "1"},  # wrong for y=x^2
            }
        ],
    )
    assert check_ode_python(cert) is True


def test_ode_completeness_rejected() -> None:
    cert = propose_ode_certificate({"tag": "variable", "idx": 0})
    bad = copy.deepcopy(cert)
    bad["claimsCompleteness"] = True
    assert check_ode_python(bad) is False


def test_offline_fixtures() -> None:
    assert len(OFFLINE_FIXTURES) >= 4
    for fx in OFFLINE_FIXTURES:
        if fx.kind == "derivative":
            assert check_deriv_python(fx.certificate)
        else:
            assert check_ode_python(fx.certificate)


def test_pow_and_quotient() -> None:
    pow_cert = propose_deriv_certificate(
        {"tag": "pow", "base": {"tag": "variable", "idx": 0}, "exp": 3}
    )
    assert check_deriv_python(pow_cert)
    quot = propose_deriv_certificate(
        {
            "tag": "div",
            "lhs": {"tag": "const", "value": "1"},
            "rhs": {"tag": "variable", "idx": 0},
        }
    )
    assert check_deriv_python(quot)
    assert any(o["tag"] == "nonzero" for o in quot["obligations"])
