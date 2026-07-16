#!/usr/bin/env python3
"""Metamorphic suite: rename / reassoc / redundant assumptions preserve accept/reject.

TESTING_AND_CI.md §2.2–2.3 companion for rational equality (Python Lean mirror).
"""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.canonical import bind_request_digest  # noqa: E402
from adapters.common.lean_mirrors import check_rational_equality  # noqa: E402
from adapters.common.limits import ResourceLimits, ResourceTracker  # noqa: E402
from adapters.common.rational_ir import (  # noqa: E402
    add_expr,
    div_expr,
    int_expr,
    pow_expr,
    sub_expr,
    var_expr,
)
from adapters.sympy.adapter import compute_rational_equality  # noqa: E402

OUT = ROOT / "benchmarks" / "metamorphic" / "manifest.json"


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


def _reassoc_add(expr: dict[str, Any]) -> dict[str, Any]:
    """(a+b)+c → a+(b+c) when shape matches; else identity."""
    if expr.get("tag") != "add":
        return expr
    left = expr["left"]
    if left.get("tag") != "add":
        return expr
    a, b, c = left["left"], left["right"], expr["right"]
    return add_expr(a, add_expr(b, c))


def _base_true() -> dict[str, Any]:
    lhs = div_expr(
        sub_expr(pow_expr(var_expr("x"), 2), int_expr(1)),
        sub_expr(var_expr("x"), int_expr(1)),
    )
    rhs = add_expr(var_expr("x"), int_expr(1))
    return _request(lhs, rhs, ["x"], assumptions=[])


def _base_false() -> dict[str, Any]:
    lhs = div_expr(
        sub_expr(pow_expr(var_expr("x"), 2), int_expr(1)),
        sub_expr(var_expr("x"), int_expr(1)),
    )
    rhs = add_expr(var_expr("x"), int_expr(2))  # wrong
    return _request(lhs, rhs, ["x"], assumptions=[])


def _request(
    lhs: dict[str, Any],
    rhs: dict[str, Any],
    names: list[str],
    *,
    assumptions: list[dict[str, Any]],
) -> dict[str, Any]:
    req = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "variables": [{"name": n, "type": "Rat"} for n in names],
        "lhs": lhs,
        "rhs": rhs,
        "knownAssumptions": assumptions,
        "requestedClaim": "soundResult",
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
    }
    return bind_request_digest(req)


def _accept(req: dict[str, Any]) -> bool:
    tracker = ResourceTracker(ResourceLimits(max_wall_time_ms=15_000))
    hr = compute_rational_equality(req, tracker)
    return check_rational_equality(req, hr.result["certificate"])


def _run_case(
    case_id: str,
    transform: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    expect_accept: bool,
) -> dict[str, Any]:
    base = _base_true() if expect_accept else _base_false()
    base_ok = _accept(base)
    if base_ok != expect_accept:
        return {
            "id": case_id,
            "status": "fail",
            "reason": f"base outcome {base_ok} != expected {expect_accept}",
        }
    transformed = transform(base)
    # Re-bind digest after structural edits.
    transformed.pop("requestDigest", None)
    transformed = bind_request_digest(transformed)
    got = _accept(transformed)
    ok = got == expect_accept
    return {
        "id": case_id,
        "status": "pass" if ok else "fail",
        "expectAccept": expect_accept,
        "gotAccept": got,
    }


def main() -> int:
    cases: list[dict[str, Any]] = []

    def rename_true(req: dict[str, Any]) -> dict[str, Any]:
        mapping = {"x": "t"}
        return _request(
            _rename_expr(req["lhs"], mapping),
            _rename_expr(req["rhs"], mapping),
            ["t"],
            assumptions=[],
        )

    def rename_false(req: dict[str, Any]) -> dict[str, Any]:
        mapping = {"x": "w"}
        return _request(
            _rename_expr(req["lhs"], mapping),
            _rename_expr(req["rhs"], mapping),
            ["w"],
            assumptions=[],
        )

    def reassoc_true(req: dict[str, Any]) -> dict[str, Any]:
        # Build ((x+1)+0) style RHS then reassociate.
        rhs = add_expr(add_expr(var_expr("x"), int_expr(1)), int_expr(0))
        reassoc = _reassoc_add(rhs)
        return _request(req["lhs"], reassoc, ["x"], assumptions=[])

    def redundant_true(req: dict[str, Any]) -> dict[str, Any]:
        # Redundant nonzero assumption that does not change accept.
        assump = {"kind": "nonzero", "expr": var_expr("x")}
        return _request(req["lhs"], req["rhs"], ["x"], assumptions=[assump])

    for case_id, fn, expect in (
        ("rename_preserves_accept", rename_true, True),
        ("rename_preserves_reject", rename_false, False),
        ("reassoc_preserves_accept", reassoc_true, True),
        ("redundant_assumption_preserves_accept", redundant_true, True),
    ):
        cases.append(_run_case(case_id, fn, expect_accept=expect))

    # Extra: reassoc on a false identity still rejects.
    cases.append(
        _run_case(
            "reassoc_preserves_reject",
            lambda req: _request(
                req["lhs"],
                _reassoc_add(add_expr(add_expr(var_expr("x"), int_expr(2)), int_expr(0))),
                ["x"],
                assumptions=[],
            ),
            expect_accept=False,
        )
    )

    failed = [c for c in cases if c["status"] != "pass"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"version": 1, "cases": cases}, indent=2) + "\n",
        encoding="utf-8",
    )
    if failed:
        print("metamorphic FAIL:", ", ".join(c["id"] for c in failed), file=sys.stderr)
        return 1
    print(f"metamorphic ok ({len(cases)} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
