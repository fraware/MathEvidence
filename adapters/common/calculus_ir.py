"""Symbolic calculus IR helpers (no SymPy imports; adapters own generation)."""

from __future__ import annotations

from typing import Any

from adapters.common.errors import stable_error
from adapters.common.rational_ir import collect_division_denominators, expr_size

Expr = dict[str, Any]

OPS = frozenset(
    {
        "derivative_candidate",
        "antiderivative_candidate",
        "recurrence_identity",
        "ode_candidate",
    }
)


def ensure_sizes(request: dict[str, Any]) -> None:
    for key in ("expr", "candidate", "odeRhs", "recurrenceRhs"):
        node = request.get(key)
        if isinstance(node, dict):
            expr_size(node)
    for cond in request.get("domainConditions") or []:
        expr_size(cond)
    for ic in request.get("initialConditions") or []:
        expr_size(ic["point"])
        expr_size(ic["value"])


def collect_all_dens(request: dict[str, Any]) -> list[Expr]:
    dens: list[Expr] = []
    for key in ("expr", "candidate", "odeRhs", "recurrenceRhs"):
        node = request.get(key)
        if isinstance(node, dict):
            dens.extend(collect_division_denominators(node))
    for cond in request.get("domainConditions") or []:
        dens.extend(collect_division_denominators(cond))
    for ic in request.get("initialConditions") or []:
        dens.extend(collect_division_denominators(ic["point"]))
        dens.extend(collect_division_denominators(ic["value"]))
    out: list[Expr] = []
    seen: set[str] = set()
    for d in dens:
        key = str(d)
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


def validate_operation_fields(request: dict[str, Any]) -> None:
    op = request.get("operation")
    if op not in OPS:
        raise stable_error("backend_unsupported", f"unknown calculus operation {op!r}")
    if op in ("derivative_candidate", "antiderivative_candidate") and "candidate" not in request:
        raise stable_error("malformed_evidence", f"{op} requires candidate")
    if op == "recurrence_identity" and "recurrenceRhs" not in request:
        raise stable_error("malformed_evidence", "recurrence_identity requires recurrenceRhs")
    if op == "ode_candidate" and "odeRhs" not in request:
        raise stable_error("malformed_evidence", "ode_candidate requires odeRhs")
