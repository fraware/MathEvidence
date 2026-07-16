"""Shared untrusted condition / counterexample helpers (adapter-safe)."""

from __future__ import annotations

from itertools import product
from typing import Any

from adapters.common.lean_mirrors import check_finite_counterexample
from adapters.common.rational_ir import collect_division_denominators


def propose_conditions_from_request(request: dict[str, Any]) -> list[dict[str, Any]]:
    dens = collect_division_denominators(request.get("lhs", {})) + collect_division_denominators(
        request.get("rhs", {})
    )
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i, expr in enumerate(dens):
        key = str(expr)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "id": f"c{i}",
                "expr": expr,
                "source": "backend_proposed",
                "status": "proposed",
                "notes": "Denominator factor from IR; sufficiency requires Lean checker.",
            }
        )
    return out


def enumerate_domain(domain: dict[str, Any]) -> list[dict[str, Any]]:
    ty = domain["ty"]
    if ty == "bool":
        return [{"tag": "bool", "v": False}, {"tag": "bool", "v": True}]
    bound = domain.get("bound")
    if bound is None:
        return []
    b = int(bound)
    if ty == "nat":
        return [{"tag": "nat", "v": i} for i in range(b + 1)]
    if ty == "int":
        return [{"tag": "int", "v": i} for i in range(-b, b + 1)]
    return []


def find_counterexample(
    request: dict[str, Any], *, max_assignments: int = 4096
) -> dict[str, Any] | None:
    pred_obj = request["predicate"]
    domains = pred_obj["domains"]
    pools = [enumerate_domain(d) for d in domains]
    if any(not p for p in pools):
        return None
    count = 0
    for combo in product(*pools):
        count += 1
        if count > max_assignments:
            break
        cert = {
            "schemaVersion": "0.1.0",
            "capability": "logic.finite_counterexample",
            "capabilityVersion": "0.1.0",
            "requestDigest": request["requestDigest"],
            "witness": {"assignment": list(combo)},
            "provenance": {
                "backendId": "agent.enumerate",
                "adapterVersion": "0.1.0",
                "deterministic": True,
            },
        }
        if check_finite_counterexample(request, cert):
            return cert
    return None
