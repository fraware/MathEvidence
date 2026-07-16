"""RationalExpr IR helpers shared by adapters (Python side)."""

from __future__ import annotations

from typing import Any

from adapters.common.errors import stable_error
from adapters.common.security_bounds import (
    DEFAULT_MAX_INTEGER_DIGITS,
    enforce_integer_digits,
)

Expr = dict[str, Any]

MAX_NODES = 4096
MAX_AST_DEPTH = 64


def expr_size(
    expr: Any,
    *,
    _count: list[int] | None = None,
    max_nodes: int = MAX_NODES,
    max_depth: int = MAX_AST_DEPTH,
    max_integer_digits: int = DEFAULT_MAX_INTEGER_DIGITS,
) -> int:
    counter = _count if _count is not None else [0]

    def walk(node: Any, depth: int) -> None:
        if depth > max_depth:
            raise stable_error(
                "resource_limit_exceeded",
                f"expression nesting exceeds {max_depth}",
                details={"kind": "nesting_depth", "depth": depth},
            )
        counter[0] += 1
        if counter[0] > max_nodes:
            raise stable_error(
                "resource_limit_exceeded",
                f"expression exceeds {max_nodes} nodes",
                details={"kind": "expr_nodes"},
            )
        if not isinstance(node, dict):
            raise stable_error("unsupported_expression", "expression node must be an object")
        tag = node.get("tag")
        if tag in {"add", "sub", "mul"}:
            walk(node.get("left"), depth + 1)
            walk(node.get("right"), depth + 1)
        elif tag == "neg":
            walk(node.get("arg"), depth + 1)
        elif tag == "pow":
            walk(node.get("base"), depth + 1)
        elif tag == "div":
            walk(node.get("num"), depth + 1)
            walk(node.get("den"), depth + 1)
        elif tag == "var":
            return
        elif tag == "int":
            enforce_integer_digits(str(node.get("value", "")), max_digits=max_integer_digits)
        elif tag == "rat":
            enforce_integer_digits(str(node.get("num", "")), max_digits=max_integer_digits)
            enforce_integer_digits(str(node.get("den", "")), max_digits=max_integer_digits)
        else:
            raise stable_error(
                "unsupported_expression",
                f"unknown or unsupported tag: {tag!r}",
            )

    walk(expr, 1)
    return counter[0]


def collect_division_denominators(expr: Expr) -> list[Expr]:
    found: list[Expr] = []

    def walk(node: Expr) -> None:
        tag = node.get("tag")
        if tag == "div":
            den = node.get("den")
            if isinstance(den, dict):
                found.append(den)
                walk(den)
            num = node.get("num")
            if isinstance(num, dict):
                walk(num)
        elif tag in {"add", "sub", "mul"}:
            left, right = node.get("left"), node.get("right")
            if isinstance(left, dict):
                walk(left)
            if isinstance(right, dict):
                walk(right)
        elif tag == "neg":
            arg = node.get("arg")
            if isinstance(arg, dict):
                walk(arg)
        elif tag == "pow":
            base = node.get("base")
            if isinstance(base, dict):
                walk(base)

    walk(expr)
    return found


def int_expr(value: int) -> Expr:
    return {"tag": "int", "value": str(value)}


def var_expr(name: str) -> Expr:
    return {"tag": "var", "name": name}


def add_expr(left: Expr, right: Expr) -> Expr:
    return {"tag": "add", "left": left, "right": right}


def sub_expr(left: Expr, right: Expr) -> Expr:
    return {"tag": "sub", "left": left, "right": right}


def mul_expr(left: Expr, right: Expr) -> Expr:
    return {"tag": "mul", "left": left, "right": right}


def div_expr(num: Expr, den: Expr) -> Expr:
    return {"tag": "div", "num": num, "den": den}


def pow_expr(base: Expr, exp: int) -> Expr:
    return {"tag": "pow", "base": base, "exp": exp}


def neg_expr(arg: Expr) -> Expr:
    return {"tag": "neg", "arg": arg}
