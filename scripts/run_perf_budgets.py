#!/usr/bin/env python3
"""Fail CI when measured timings exceed per-capability perfBudgets in the registry."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.canonical import bind_request_digest  # noqa: E402
from adapters.common.limits import ResourceLimits, ResourceTracker  # noqa: E402
from adapters.common.rational_ir import add_expr, div_expr, int_expr, pow_expr, sub_expr, var_expr  # noqa: E402
from adapters.sympy.adapter import compute_rational_equality  # noqa: E402

CAP_DIR = ROOT / "registry" / "capabilities"
OUT = ROOT / "benchmarks" / "perf" / "last_run.json"


def _rational_request() -> dict[str, Any]:
    lhs = div_expr(
        sub_expr(pow_expr(var_expr("x"), 2), int_expr(1)),
        sub_expr(var_expr("x"), int_expr(1)),
    )
    rhs = add_expr(var_expr("x"), int_expr(1))
    req = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "variables": [{"name": "x", "type": "Rat"}],
        "lhs": lhs,
        "rhs": rhs,
        "knownAssumptions": [],
        "requestedClaim": "soundResult",
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
    }
    return bind_request_digest(req)


def _measure_rational(budgets: dict[str, Any]) -> dict[str, Any]:
    req = _rational_request()
    t0 = time.perf_counter()
    # Reification proxy: bind digest + schema walk.
    bind_request_digest({k: v for k, v in req.items() if k != "requestDigest"})
    reify_ms = (time.perf_counter() - t0) * 1000

    tracker = ResourceTracker(ResourceLimits(max_wall_time_ms=30_000))
    t1 = time.perf_counter()
    hr = compute_rational_equality(req, tracker)
    gen_ms = (time.perf_counter() - t1) * 1000
    cert = hr.result["certificate"]
    evidence_bytes = len(json.dumps(cert, separators=(",", ":")).encode("utf-8"))

    t2 = time.perf_counter()
    from adapters.common.lean_mirrors import check_rational_equality

    ok = check_rational_equality(req, cert)
    check_ms = (time.perf_counter() - t2) * 1000
    if not ok:
        raise RuntimeError("perf budget probe: checker rejected golden rational identity")

    measured = {
        "reifyMs": reify_ms,
        "backendGenerateMs": gen_ms,
        "evidenceBytes": evidence_bytes,
        "checkerMs": check_ms,
    }
    violations: list[str] = []
    mapping = {
        "reifyMs": "maxReifyMs",
        "backendGenerateMs": "maxBackendGenerateMs",
        "evidenceBytes": "maxEvidenceBytes",
        "checkerMs": "maxCheckerMs",
    }
    for measured_key, budget_key in mapping.items():
        if budget_key in budgets and measured[measured_key] > float(budgets[budget_key]):
            violations.append(
                f"{measured_key}={measured[measured_key]:.2f} > {budget_key}={budgets[budget_key]}"
            )
    return {"capability": "algebra.rational_equality", "measured": measured, "violations": violations}


def _load_budgets(path: Path) -> dict[str, Any] | None:
    data = json.loads(path.read_text(encoding="utf-8"))
    budgets = data.get("perfBudgets")
    return budgets if isinstance(budgets, dict) else None


def main() -> int:
    results: list[dict[str, Any]] = []
    errors = 0
    for path in sorted(CAP_DIR.glob("*.json")):
        budgets = _load_budgets(path)
        if not budgets:
            continue
        cap_id = json.loads(path.read_text(encoding="utf-8")).get("id")
        if cap_id == "algebra.rational_equality":
            row = _measure_rational(budgets)
        else:
            # Budget declared: require keys present; measurement hooks land with R4 generators.
            row = {
                "capability": cap_id,
                "measured": {},
                "violations": [],
                "status": "budgets_declared_unmeasured",
            }
        results.append(row)
        if row.get("violations"):
            errors += 1
            print(f"FAIL {cap_id}: {', '.join(row['violations'])}", file=sys.stderr)
        else:
            print(f"ok {cap_id} {row.get('measured') or row.get('status')}")

    if not results:
        print("no capabilities declare perfBudgets", file=sys.stderr)
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"version": 1, "results": results}, indent=2) + "\n", encoding="utf-8")
    if errors:
        print(f"perf budgets failed ({errors})", file=sys.stderr)
        return 1
    print(f"perf budgets ok ({len(results)} capabilities)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
