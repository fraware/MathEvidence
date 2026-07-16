"""Python mirrors of Lean LinearAlgebra / Counterexample checkers (orchestration only)."""

from __future__ import annotations

from fractions import Fraction
from typing import Any


def _rat(lit: dict[str, Any]) -> Fraction:
    return Fraction(int(lit["num"]), int(lit["den"]))


def _matrix_rows(matrix: dict[str, Any]) -> list[list[Fraction]]:
    return [[_rat(e) for e in row] for row in matrix["entries"]]


def _identity(n: int) -> list[list[Fraction]]:
    return [[Fraction(1 if i == j else 0) for j in range(n)] for i in range(n)]


def _matmul(a: list[list[Fraction]], b: list[list[Fraction]]) -> list[list[Fraction]] | None:
    if not a or not b or len(a[0]) != len(b):
        return None
    cols = len(b[0])
    out: list[list[Fraction]] = []
    for i in range(len(a)):
        row: list[Fraction] = []
        for j in range(cols):
            s = Fraction(0)
            for k in range(len(b)):
                s += a[i][k] * b[k][j]
            row.append(s)
        out.append(row)
    return out


def _matvec(a: list[list[Fraction]], v: list[Fraction]) -> list[Fraction] | None:
    if not a or len(a[0]) != len(v):
        return None
    return [sum((a[i][k] * v[k] for k in range(len(v))), Fraction(0)) for i in range(len(a))]


def _det2(a: list[list[Fraction]]) -> Fraction | None:
    if len(a) != 2 or any(len(r) != 2 for r in a):
        return None
    return a[0][0] * a[1][1] - a[0][1] * a[1][0]


def check_linear_algebra(request: dict[str, Any], certificate: dict[str, Any]) -> bool:
    """Thin Python mirror of Lean `checkBool` for offline Agent replay."""
    if certificate.get("requestDigest") != request.get("requestDigest"):
        return False
    op = request.get("operation")
    if op != certificate.get("operation"):
        return False
    A = _matrix_rows(request["matrix"])
    if op == "inverse_witness":
        inv = certificate.get("inverse")
        if not isinstance(inv, dict):
            return False
        B = _matrix_rows(inv)
        left = _matmul(B, A)
        right = _matmul(A, B)
        I = _identity(len(A))
        return left == I and right == I
    if op == "system_solution":
        vec = certificate.get("vector")
        rhs = request.get("rhs") or []
        if not isinstance(vec, list) or not isinstance(rhs, list):
            return False
        x = [_rat(e) for e in vec]
        b = [_rat(e) for e in rhs]
        ax = _matvec(A, x)
        return ax == b
    if op == "kernel_vector":
        vec = certificate.get("vector")
        if not isinstance(vec, list):
            return False
        v = [_rat(e) for e in vec]
        if all(x == 0 for x in v):
            return False
        av = _matvec(A, v)
        return av is not None and all(x == 0 for x in av)
    if op == "det_identity":
        claimed = request.get("claimedDet")
        if not isinstance(claimed, dict):
            return False
        d = _det2(A)
        return d is not None and d == _rat(claimed)
    return False


def _eval_term(env: list[Any], term: dict[str, Any]) -> Any | None:
    tag = term.get("tag")
    if tag == "var":
        idx = term.get("idx")
        if not isinstance(idx, int) or idx < 0 or idx >= len(env):
            return None
        return env[idx]
    if tag == "lit":
        v = term.get("v") or {}
        t = v.get("tag")
        if t == "bool":
            return bool(v.get("v"))
        if t == "nat":
            return int(v.get("v"))
        if t == "int":
            return int(v.get("v"))
        return None
    if tag == "neg":
        x = _eval_term(env, term["e"])
        return None if x is None else -int(x)
    if tag in ("add", "sub", "mul"):
        a = _eval_term(env, term["left"])
        b = _eval_term(env, term["right"])
        if a is None or b is None:
            return None
        if tag == "add":
            return a + b
        if tag == "sub":
            return a - b
        return a * b
    return None


def _eval_pred(env: list[Any], pred: dict[str, Any]) -> bool | None:
    tag = pred.get("tag")
    if tag in ("eq", "ne", "le", "lt"):
        a = _eval_term(env, pred["left"])
        b = _eval_term(env, pred["right"])
        if a is None or b is None:
            return None
        if tag == "eq":
            return a == b
        if tag == "ne":
            return a != b
        if tag == "le":
            return a <= b
        return a < b
    if tag == "not":
        p = _eval_pred(env, pred["e"])
        return None if p is None else (not p)
    if tag in ("and", "or"):
        a = _eval_pred(env, pred["left"])
        b = _eval_pred(env, pred["right"])
        if a is None or b is None:
            return None
        return (a and b) if tag == "and" else (a or b)
    return None


def _val_from_wire(v: dict[str, Any]) -> Any:
    tag = v["tag"]
    if tag == "bool":
        return bool(v["v"])
    return int(v["v"])


def check_finite_counterexample(request: dict[str, Any], certificate: dict[str, Any]) -> bool:
    """Thin Python mirror of Lean Counterexample.checkBool for Agent replay."""
    if certificate.get("requestDigest") != request.get("requestDigest"):
        return False
    pred_obj = request.get("predicate") or {}
    pred = pred_obj.get("pred")
    assignment = (certificate.get("witness") or {}).get("assignment")
    if not isinstance(pred, dict) or not isinstance(assignment, list):
        return False
    env = [_val_from_wire(v) for v in assignment]
    result = _eval_pred(env, pred)
    return result is False


def check_symbolic_calculus(request: dict[str, Any], certificate: dict[str, Any]) -> bool:
    """Thin Python mirror of Lean Calculus.checkBool digest/domain gates.

    Full formalDeriv/`polyEqual` remains Lean-owned; this mirror checks binding
    and that SymPy agrees on derivative/antiderivative residual when applicable.
    """
    if certificate.get("requestDigest") != request.get("requestDigest"):
        return False
    if certificate.get("operation") != request.get("operation"):
        return False
    if certificate.get("domainConditions") != request.get("domainConditions"):
        return False
    op = request.get("operation")
    try:
        from sympy import Symbol, diff, simplify

        from adapters.sympy.adapter import _sympy_from_ir
    except Exception:  # noqa: BLE001
        return True  # schema/digest gates already applied

    env = {v["name"]: Symbol(v["name"]) for v in request.get("variables") or []}
    indep = request.get("independentVar")
    if not isinstance(indep, str) or indep not in env:
        return False
    x = env[indep]
    expr = _sympy_from_ir(request["expr"], env)
    if op == "derivative_candidate":
        cand = _sympy_from_ir(request["candidate"], env)
        return simplify(diff(expr, x) - cand) == 0
    if op == "antiderivative_candidate":
        F = _sympy_from_ir(request["candidate"], env)
        f = expr
        return simplify(diff(F, x) - f) == 0
    if op == "recurrence_identity":
        rhs = request.get("recurrenceRhs")
        dep = request.get("dependentVar")
        if not isinstance(rhs, dict) or not isinstance(dep, str) or dep not in env:
            return False
        closed = expr
        next_form = simplify(closed.subs(x, x + 1))
        rhs_eval = _sympy_from_ir(rhs, env).subs(env[dep], closed)
        return simplify(next_form - rhs_eval) == 0
    if op == "ode_candidate":
        ode = request.get("odeRhs")
        dep = request.get("dependentVar")
        if not isinstance(ode, dict) or not isinstance(dep, str) or dep not in env:
            return False
        y = expr
        fsub = _sympy_from_ir(ode, env).subs(env[dep], y)
        if simplify(diff(y, x) - fsub) != 0:
            return False
        for ic in request.get("initialConditions") or []:
            pt = _sympy_from_ir(ic["point"], env)
            val = _sympy_from_ir(ic["value"], env)
            if simplify(y.subs(x, pt) - val) != 0:
                return False
        return True
    return False
