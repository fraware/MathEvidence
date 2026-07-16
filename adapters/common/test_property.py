"""Property-based tests (TESTING_AND_CI.md §2.2).

Covers reify/eval correspondence (IR ↔ SymPy), digest stability, alpha-renaming
invariance, and denominator-factor permutation invariance for rational equality.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from hypothesis import given, settings, strategies as st
from sympy import Symbol, simplify

from adapters.common.canonical import bind_request_digest, canonical_dumps, sha256_digest
from adapters.common.lean_mirrors import check_rational_equality
from adapters.common.limits import ResourceLimits, ResourceTracker
from adapters.common.rational_ir import (
    add_expr,
    div_expr,
    int_expr,
    mul_expr,
    pow_expr,
    sub_expr,
    var_expr,
)
from adapters.sympy.adapter import _ir_from_sympy, _sympy_from_ir, compute_rational_equality


def _var_names(n: int) -> list[str]:
    return [chr(ord("a") + i) for i in range(n)]


@st.composite
def poly_expr_strategy(draw: Any, names: list[str], max_depth: int = 3) -> dict[str, Any]:
    """Polynomial RationalExpr (no division) for stable IR↔SymPy round-trips."""
    if max_depth <= 0 or draw(st.booleans()):
        kind = draw(st.sampled_from(["int", "var"]))
        if kind == "int" or not names:
            return int_expr(draw(st.integers(min_value=-5, max_value=5)))
        return var_expr(draw(st.sampled_from(names)))
    op = draw(st.sampled_from(["add", "sub", "mul", "pow"]))
    left = draw(poly_expr_strategy(names, max_depth - 1))
    if op == "pow":
        return pow_expr(left, draw(st.integers(min_value=0, max_value=3)))
    right = draw(poly_expr_strategy(names, max_depth - 1))
    if op == "add":
        return add_expr(left, right)
    if op == "sub":
        return sub_expr(left, right)
    return mul_expr(left, right)


def _rename_expr(expr: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    tag = expr.get("tag")
    if tag == "var":
        return var_expr(mapping[expr["name"]])
    if tag in {"int", "rat"}:
        return deepcopy(expr)
    if tag == "neg":
        return {"tag": "neg", "arg": _rename_expr(expr["arg"], mapping)}
    if tag == "pow":
        return {"tag": "pow", "base": _rename_expr(expr["base"], mapping), "exp": expr["exp"]}
    if tag in {"add", "sub", "mul"}:
        return {
            "tag": tag,
            "left": _rename_expr(expr["left"], mapping),
            "right": _rename_expr(expr["right"], mapping),
        }
    if tag == "div":
        return {
            "tag": "div",
            "num": _rename_expr(expr["num"], mapping),
            "den": _rename_expr(expr["den"], mapping),
        }
    return deepcopy(expr)


def _make_request(lhs: dict[str, Any], rhs: dict[str, Any], names: list[str]) -> dict[str, Any]:
    req = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "variables": [{"name": n, "type": "Rat"} for n in names],
        "lhs": lhs,
        "rhs": rhs,
        "knownAssumptions": [],
        "requestedClaim": "soundResult",
        "resourcePolicy": {"maxWallTimeMs": 5000, "maxOutputBytes": 1_048_576},
    }
    return bind_request_digest(req)


@given(data=st.data())
@settings(max_examples=40, deadline=None)
def test_reify_eval_roundtrip_polynomial(data: Any) -> None:
    names = _var_names(data.draw(st.integers(min_value=1, max_value=3)))
    expr = data.draw(poly_expr_strategy(names, max_depth=3))
    env = {n: Symbol(n) for n in names}
    sympy_expr = _sympy_from_ir(expr, env)
    back = _ir_from_sympy(sympy_expr)
    again = _sympy_from_ir(back, env)
    assert simplify(sympy_expr - again) == 0


@given(
    payload=st.dictionaries(
        st.text(min_size=1, max_size=4, alphabet="abxy"),
        st.integers(-3, 3),
        max_size=4,
    )
)
@settings(max_examples=50, deadline=None)
def test_digest_stability_under_key_permutation(payload: dict[str, int]) -> None:
    items = list(payload.items())
    a = dict(items)
    b = dict(reversed(items))
    assert canonical_dumps(a) == canonical_dumps(b)
    assert sha256_digest(a) == sha256_digest(b)


@given(data=st.data())
@settings(max_examples=25, deadline=None)
def test_alpha_rename_preserves_checker(data: Any) -> None:
    lhs = div_expr(
        sub_expr(pow_expr(var_expr("x"), 2), int_expr(1)),
        sub_expr(var_expr("x"), int_expr(1)),
    )
    rhs = add_expr(var_expr("x"), int_expr(1))
    new_name = data.draw(st.sampled_from(["u", "v", "t", "z"]))
    mapping = {"x": new_name}
    req = _make_request(_rename_expr(lhs, mapping), _rename_expr(rhs, mapping), [new_name])
    tracker = ResourceTracker(ResourceLimits(max_wall_time_ms=10_000))
    hr = compute_rational_equality(req, tracker)
    cert = hr.result["certificate"]
    assert check_rational_equality(req, cert) is True


@given(data=st.data())
@settings(max_examples=20, deadline=None)
def test_denominator_factor_permutation_preserves_accept(data: Any) -> None:
    req = _make_request(
        div_expr(
            sub_expr(pow_expr(var_expr("x"), 2), int_expr(1)),
            sub_expr(var_expr("x"), int_expr(1)),
        ),
        add_expr(var_expr("x"), int_expr(1)),
        ["x"],
    )
    tracker = ResourceTracker(ResourceLimits(max_wall_time_ms=10_000))
    hr = compute_rational_equality(req, tracker)
    cert = deepcopy(hr.result["certificate"])
    factors = list(cert.get("denominatorFactors") or [])
    if len(factors) >= 2:
        order = data.draw(st.permutations(range(len(factors))))
        cert["denominatorFactors"] = [factors[i] for i in order]
    assert check_rational_equality(req, cert) is True
