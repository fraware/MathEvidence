"""Typed Lean-syntax constructors for exact-replay plugins.

No API accepts raw caller Lean fragments. All identifiers and literals are
escaped or validated before emission.
"""

from __future__ import annotations

import json
import math
import re
from typing import Any

from adapters.common.security_bounds import enforce_integer_digits

_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_INT_RE = re.compile(r"^-?(0|[1-9][0-9]*)$")
_NAT_RE = re.compile(r"^(0|[1-9][0-9]*)$")
_VAR_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_']*$")
_MAX_INTEGER_DIGITS = 4096
_MAX_EXPR_DEPTH = 64
_MAX_EXPR_NODES = 4096


def lean_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def lean_string_list(values: list[str]) -> str:
    return "[" + ", ".join(lean_string(v) for v in values) + "]"


def safe_ident(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"t_{cleaned}"
    return cleaned


def validate_digest(value: Any, *, what: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{what} must be a canonical sha256 digest")
    return value


def validate_semver(value: Any, *, what: str) -> str:
    if not isinstance(value, str) or _SEMVER_RE.fullmatch(value) is None:
        raise ValueError(f"{what} must be a semantic version")
    return value


def validate_schema_version(value: Any, *, expected: str = "0.1.0") -> str:
    if value != expected:
        raise ValueError(f"schemaVersion must be {expected}")
    return expected


def parse_int_string(value: Any, *, what: str) -> int:
    """Parse a decimal integer string; reject floats and malformed forms."""
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError(f"{what}: floats and booleans are rejected in exact mode")
    if isinstance(value, int):
        enforce_integer_digits(str(value), max_digits=_MAX_INTEGER_DIGITS)
        return value
    if not isinstance(value, str) or _INT_RE.fullmatch(value) is None:
        raise ValueError(f"{what} must be a decimal integer string: {value!r}")
    enforce_integer_digits(value, max_digits=_MAX_INTEGER_DIGITS)
    return int(value)


def parse_nat_string(value: Any, *, what: str) -> int:
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError(f"{what}: floats and booleans are rejected in exact mode")
    if isinstance(value, int):
        if value < 0:
            raise ValueError(f"{what} must be nonnegative")
        enforce_integer_digits(str(value), max_digits=_MAX_INTEGER_DIGITS)
        return value
    if not isinstance(value, str) or _NAT_RE.fullmatch(value) is None:
        raise ValueError(f"{what} must be a nonnegative decimal integer string")
    enforce_integer_digits(value, max_digits=_MAX_INTEGER_DIGITS)
    return int(value)


def canonicalize_rat(num: int, den: int) -> tuple[int, int]:
    """Canonical rational: int num, strictly positive den, gcd-normalized, 0 as 0/1."""
    if den == 0:
        raise ValueError("rational denominator must be nonzero")
    if den < 0:
        num, den = -num, -den
    if num == 0:
        return 0, 1
    g = math.gcd(abs(num), den)
    return num // g, den // g


def matching_copy(request: dict[str, Any], certificate: dict[str, Any], field: str) -> None:
    if field in certificate and certificate[field] != request.get(field):
        raise ValueError(f"certificate {field} does not exactly match request {field}")


def reject_float_payload(value: Any, *, path: str = "root") -> None:
    if isinstance(value, float):
        raise ValueError(f"float rejected in exact mode at {path}")
    if isinstance(value, dict):
        for key, child in value.items():
            reject_float_payload(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_float_payload(child, path=f"{path}[{index}]")


def lean_int(n: int) -> str:
    return f"({n} : Int)"


def lean_nat(n: int) -> str:
    if n < 0:
        raise ValueError("Nat literal must be nonnegative")
    return str(n)


def lean_rat_lit(num: int, den: int) -> str:
    cnum, cden = canonicalize_rat(num, den)
    if cden == 1:
        return f"RatLit.ofInt {lean_int(cnum)}"
    return f"⟨{lean_int(cnum)}, {lean_nat(cden)}⟩"


def lean_qq(num: int, den: int) -> str:
    """Render a Mathlib ℚ literal."""
    cnum, cden = canonicalize_rat(num, den)
    if cden == 1:
        return f"({cnum} : ℚ)"
    return f"(({cnum} : ℚ) / ({cden} : ℚ))"


def _count_expr_nodes(expr: dict[str, Any], *, depth: int = 1) -> int:
    if depth > _MAX_EXPR_DEPTH:
        raise ValueError(f"expression nesting exceeds {_MAX_EXPR_DEPTH}")
    if not isinstance(expr, dict):
        raise ValueError("expression node must be an object")
    tag = expr.get("tag")
    if tag in {"add", "sub", "mul"}:
        return (
            1
            + _count_expr_nodes(expr["left"], depth=depth + 1)
            + _count_expr_nodes(expr["right"], depth=depth + 1)
        )
    if tag == "div":
        return (
            1
            + _count_expr_nodes(expr["num"], depth=depth + 1)
            + _count_expr_nodes(expr["den"], depth=depth + 1)
        )
    if tag == "neg":
        return 1 + _count_expr_nodes(expr["arg"], depth=depth + 1)
    if tag == "pow":
        return 1 + _count_expr_nodes(expr["base"], depth=depth + 1)
    if tag in {"var", "int", "rat"}:
        return 1
    raise ValueError(f"unsupported RationalExpr constructor: {tag!r}")


def validate_rational_expr(
    expr: Any,
    *,
    var_names: list[str],
    what: str,
    allow_rat_literal: bool = True,
) -> dict[str, Any]:
    """Validate and return a deep-copied canonical RationalExpr dict."""
    if not isinstance(expr, dict):
        raise ValueError(f"{what} must be an object")
    reject_float_payload(expr, path=what)
    nodes = _count_expr_nodes(expr)
    if nodes > _MAX_EXPR_NODES:
        raise ValueError(f"{what} exceeds {_MAX_EXPR_NODES} nodes")

    def walk(node: dict[str, Any], path: str) -> dict[str, Any]:
        tag = node.get("tag")
        if tag == "var":
            name = node.get("name")
            if not isinstance(name, str) or _VAR_RE.fullmatch(name) is None:
                raise ValueError(f"{path}: invalid variable name")
            if name not in var_names:
                raise ValueError(f"{path}: variable {name!r} not in request variables")
            return {"tag": "var", "name": name}
        if tag == "int":
            value = parse_int_string(node.get("value"), what=f"{path}.value")
            return {"tag": "int", "value": str(value)}
        if tag == "rat":
            if not allow_rat_literal:
                raise ValueError(f"{path}: rat literals unsupported here")
            num = parse_int_string(node.get("num"), what=f"{path}.num")
            den = parse_int_string(node.get("den"), what=f"{path}.den")
            if den == 0:
                raise ValueError(f"{path}: den=0 rejected before Lean")
            cnum, cden = canonicalize_rat(num, den)
            return {"tag": "rat", "num": str(cnum), "den": str(cden)}
        if tag == "neg":
            return {"tag": "neg", "arg": walk(node["arg"], f"{path}.arg")}
        if tag in {"add", "sub", "mul"}:
            return {
                "tag": tag,
                "left": walk(node["left"], f"{path}.left"),
                "right": walk(node["right"], f"{path}.right"),
            }
        if tag == "div":
            return {
                "tag": "div",
                "num": walk(node["num"], f"{path}.num"),
                "den": walk(node["den"], f"{path}.den"),
            }
        if tag == "pow":
            exp = node.get("exp")
            if isinstance(exp, bool) or not isinstance(exp, int) or exp < 0:
                raise ValueError(f"{path}.exp must be a nonnegative int")
            if exp > 1_000_000:
                raise ValueError(f"{path}.exp exceeds maximum")
            return {"tag": "pow", "base": walk(node["base"], f"{path}.base"), "exp": exp}
        raise ValueError(f"{path}: unsupported constructor {tag!r}")

    return walk(expr, what)


def lean_rational_expr(expr: dict[str, Any], var_names: list[str]) -> str:
    """Render a validated RationalExpr as MathEvidence.IR.RationalExpr.Expr."""
    tag = expr["tag"]
    if tag == "var":
        return f"Expr.var {var_names.index(expr['name'])}"
    if tag == "int":
        n = parse_int_string(expr["value"], what="int")
        return f"Expr.int {lean_int(n)}"
    if tag == "rat":
        num = parse_int_string(expr["num"], what="rat.num")
        den = parse_int_string(expr["den"], what="rat.den")
        cnum, cden = canonicalize_rat(num, den)
        return f"Expr.rat {lean_int(cnum)} {lean_nat(cden)}"
    if tag == "neg":
        return f"Expr.neg ({lean_rational_expr(expr['arg'], var_names)})"
    if tag in {"add", "sub", "mul"}:
        left = lean_rational_expr(expr["left"], var_names)
        right = lean_rational_expr(expr["right"], var_names)
        ctor = {"add": "Expr.add", "sub": "Expr.sub", "mul": "Expr.mul"}[tag]
        return f"{ctor} ({left}) ({right})"
    if tag == "div":
        num = lean_rational_expr(expr["num"], var_names)
        den = lean_rational_expr(expr["den"], var_names)
        return f"Expr.div ({num}) ({den})"
    if tag == "pow":
        base = lean_rational_expr(expr["base"], var_names)
        return f"Expr.pow ({base}) {lean_nat(int(expr['exp']))}"
    raise ValueError(f"unsupported tag {tag!r}")


def lean_expr_list(exprs: list[dict[str, Any]], var_names: list[str]) -> str:
    if not exprs:
        return "[]"
    return "[" + ", ".join(lean_rational_expr(e, var_names) for e in exprs) + "]"
