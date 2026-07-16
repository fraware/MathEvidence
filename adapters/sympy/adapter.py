"""SymPy backend for algebra.rational_equality (RFC 0001)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sympy import (
    Add,
    Expr,
    Integer,
    Mul,
    Pow,
    Rational,
    Symbol,
    cancel,
    factor,
    together,
)
from sympy.core.numbers import igcd

from adapters.common.canonical import verify_request_digest
from adapters.common.errors import AdapterError, stable_error
from adapters.common.limits import ResourceTracker
from adapters.common.protocol import CapabilityDescriptor, HandlerResult
from adapters.common.rational_ir import collect_division_denominators, expr_size
from adapters.common.schema_validate import SchemaStore

ADAPTER_VERSION = "0.1.0"
CAPABILITY_ID = "algebra.rational_equality"
CAPABILITY_VERSION = "0.1.0"

RATIONAL_EQUALITY_CAPABILITY = CapabilityDescriptor(
    id=CAPABILITY_ID,
    version=CAPABILITY_VERSION,
    claim_classes=["soundResult", "candidate"],
    request_schema="rational-equality-request.schema.json",
    evidence_schema="rational-equality-certificate.schema.json",
    deterministic=True,
    notes=[
        "Emits candidate numerator + denominator factors; never a trusted Boolean.",
    ],
)

LINEAR_ALGEBRA_CAPABILITY = CapabilityDescriptor(
    id="algebra.linear_algebra",
    version="0.1.0",
    claim_classes=["witness", "candidate"],
    request_schema="linear-algebra-request.schema.json",
    evidence_schema="linear-algebra-certificate.schema.json",
    deterministic=True,
    notes=["Thin SymPy generator; Lean LinearAlgebra checker owns acceptance."],
)

FINITE_COUNTEREXAMPLE_CAPABILITY = CapabilityDescriptor(
    id="logic.finite_counterexample",
    version="0.1.0",
    claim_classes=["witness", "candidate", "refutation"],
    request_schema="finite-counterexample-request.schema.json",
    evidence_schema="finite-counterexample-certificate.schema.json",
    deterministic=True,
    notes=["Bounded search generator; Lean Counterexample checker owns acceptance."],
)

SYMBOLIC_CALCULUS_CAPABILITY = CapabilityDescriptor(
    id="analysis.symbolic_calculus",
    version="0.1.0",
    claim_classes=["candidate", "soundResult", "witness"],
    request_schema="symbolic-calculus-request.schema.json",
    evidence_schema="symbolic-calculus-certificate.schema.json",
    deterministic=True,
    notes=[
        "Generates derivative/antiderivative/ODE/recurrence candidates; Lean Calculus checker owns acceptance.",
        "Never claims completeness; domainConditions must cover singularities.",
    ],
)

SYMPY_CAPABILITIES = [
    RATIONAL_EQUALITY_CAPABILITY,
    LINEAR_ALGEBRA_CAPABILITY,
    FINITE_COUNTEREXAMPLE_CAPABILITY,
    SYMBOLIC_CALCULUS_CAPABILITY,
]


def _sympy_from_ir(node: dict[str, Any], env: dict[str, Symbol]) -> Expr:
    tag = node.get("tag")
    if tag == "var":
        name = node["name"]
        if name not in env:
            raise stable_error(
                "unsupported_expression",
                f"undeclared variable: {name}",
                details={"name": name},
            )
        return env[name]
    if tag == "int":
        return Integer(int(node["value"]))
    if tag == "rat":
        return Rational(int(node["num"]), int(node["den"]))
    if tag == "add":
        return _sympy_from_ir(node["left"], env) + _sympy_from_ir(node["right"], env)
    if tag == "sub":
        return _sympy_from_ir(node["left"], env) - _sympy_from_ir(node["right"], env)
    if tag == "mul":
        return _sympy_from_ir(node["left"], env) * _sympy_from_ir(node["right"], env)
    if tag == "neg":
        return -_sympy_from_ir(node["arg"], env)
    if tag == "pow":
        exp = node["exp"]
        if not isinstance(exp, int) or exp < 0:
            raise stable_error(
                "unsupported_expression",
                "only natural-number powers are supported",
            )
        return _sympy_from_ir(node["base"], env) ** exp
    if tag == "div":
        den = _sympy_from_ir(node["den"], env)
        return _sympy_from_ir(node["num"], env) / den
    raise stable_error("unsupported_expression", f"unsupported tag: {tag!r}")


def _ir_from_sympy(expr: Expr) -> dict[str, Any]:
    """Best-effort conversion of a sympy expression back to RationalExpr IR."""
    expr = expr.expand()
    if expr.is_Integer:
        return {"tag": "int", "value": str(int(expr))}
    if isinstance(expr, Rational) and not expr.is_Integer:
        return {"tag": "rat", "num": str(expr.p), "den": str(expr.q)}
    if expr.is_Symbol:
        return {"tag": "var", "name": str(expr)}
    if isinstance(expr, Pow):
        base, exp = expr.as_base_exp()
        if exp.is_Integer and int(exp) >= 0:
            return {"tag": "pow", "base": _ir_from_sympy(base), "exp": int(exp)}
        raise stable_error(
            "unsupported_expression",
            "cannot encode non-natural power in RationalExpr IR",
        )
    if isinstance(expr, Add):
        args = list(expr.args)
        acc = _ir_from_sympy(args[0])
        for a in args[1:]:
            if a.could_extract_minus_sign():
                acc = {"tag": "sub", "left": acc, "right": _ir_from_sympy(-a)}
            else:
                acc = {"tag": "add", "left": acc, "right": _ir_from_sympy(a)}
        return acc
    if isinstance(expr, Mul):
        # Separate denominator-like Rational factors.
        num_factors: list[Expr] = []
        den_factors: list[Expr] = []
        for a in expr.args:
            if isinstance(a, Rational) and a.q != 1 and a.p == 1:
                den_factors.append(Integer(a.q))
            elif isinstance(a, Rational) and a.q != 1:
                num_factors.append(Integer(a.p))
                den_factors.append(Integer(a.q))
            elif isinstance(a, Pow) and a.exp.is_Integer and int(a.exp) < 0:
                den_factors.append(Pow(a.base, -int(a.exp)))
            else:
                num_factors.append(a)

        def product(fs: list[Expr]) -> dict[str, Any]:
            if not fs:
                return {"tag": "int", "value": "1"}
            acc = _ir_from_sympy(fs[0])
            for f in fs[1:]:
                acc = {"tag": "mul", "left": acc, "right": _ir_from_sympy(f)}
            return acc

        if den_factors:
            return {"tag": "div", "num": product(num_factors), "den": product(den_factors)}
        return product(num_factors)
    # Fallback: try together representation
    t = together(expr)
    num, den = t.as_numer_denom()
    if den != 1:
        return {"tag": "div", "num": _ir_from_sympy(num), "den": _ir_from_sympy(den)}
    raise stable_error(
        "unsupported_expression",
        f"cannot encode sympy expression as RationalExpr: {expr}",
    )


def _factor_list(poly_expr: Expr) -> list[tuple[Expr, int]]:
    """Return irreducible-ish factors over Q with multiplicities."""
    if poly_expr == 0:
        return [(Integer(0), 1)]
    fac = factor(poly_expr)
    factors: list[tuple[Expr, int]] = []
    if isinstance(fac, Mul):
        for a in fac.args:
            if isinstance(a, Pow) and a.exp.is_Integer:
                factors.append((a.base, int(a.exp)))
            else:
                factors.append((a, 1))
    elif isinstance(fac, Pow) and fac.exp.is_Integer:
        factors.append((fac.base, int(fac.exp)))
    else:
        factors.append((fac, 1))
    # Drop ±1 units
    cleaned: list[tuple[Expr, int]] = []
    for base, mult in factors:
        if base in (1, -1):
            continue
        cleaned.append((base, mult))
    return cleaned or [(Integer(1), 1)]


def compute_rational_equality(
    request: dict[str, Any],
    tracker: ResourceTracker,
    *,
    schemas: SchemaStore | None = None,
) -> HandlerResult:
    store = schemas or SchemaStore()
    store.validate("rational-equality-request.schema.json", request)
    try:
        digest = verify_request_digest(request)
    except Exception as exc:  # noqa: BLE001
        raise stable_error(
            "request_digest_mismatch",
            str(exc),
        ) from exc

    tracker.check()
    expr_size(request["lhs"])
    expr_size(request["rhs"])

    variables = request["variables"]
    names = [v["name"] for v in variables]
    if len(names) != len(set(names)):
        raise stable_error("unsupported_expression", "duplicate variable declarations")

    env = {name: Symbol(name) for name in names}
    lhs = _sympy_from_ir(request["lhs"], env)
    rhs = _sympy_from_ir(request["rhs"], env)
    tracker.check()

    diff = together(cancel(lhs - rhs))
    numer, denom = diff.as_numer_denom()
    numer = numer.expand()
    denom = denom.expand()

    # Content cleanup: make numerator content-primitive when possible.
    if numer.is_integer is False and numer.free_symbols:
        try:
            content = Integer(igcd(*[Integer(t.as_coeff_Mul()[0]) for t in Add.make_args(numer)]))
            if content not in (0, 1, -1):
                numer = numer / content
                denom = denom / content
        except Exception:  # noqa: BLE001 — best-effort content extraction
            pass

    original_dens = collect_division_denominators(request["lhs"]) + collect_division_denominators(
        request["rhs"]
    )
    factors: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_factor(ir_expr: dict[str, Any], role: str, multiplicity: int = 1) -> None:
        key = f"{role}:{ir_expr}"
        # Use canonical-ish string of dict for dedupe within process.
        marker = key
        if marker in seen:
            return
        seen.add(marker)
        factors.append(
            {
                "expr": ir_expr,
                "role": role,
                "multiplicity": multiplicity,
            }
        )

    for dens in original_dens:
        add_factor(dens, "original_division")

    if denom != 1:
        for base, mult in _factor_list(denom):
            if base == 0:
                continue
            add_factor(_ir_from_sympy(base), "common_denominator", mult)

    for base, mult in _factor_list(denom if denom != 1 else Integer(1)):
        if base in (0, 1, -1):
            continue
        add_factor(_ir_from_sympy(base), "factorization", mult)

    certificate: dict[str, Any] = {
        "schemaVersion": "0.1.0",
        "capability": CAPABILITY_ID,
        "capabilityVersion": CAPABILITY_VERSION,
        "requestDigest": digest,
        "differenceNumerator": _ir_from_sympy(numer),
        "denominatorFactors": factors,
        "factorization": {
            "method": "sympy.factor+together+cancel",
            "notes": "Untrusted candidate evidence for Lean checker replay.",
        },
        "provenance": {
            "backendId": "sympy",
            "backendVersion": _sympy_version(),
            "adapterVersion": ADAPTER_VERSION,
            "generatedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "deterministic": True,
        },
    }
    store.validate("rational-equality-certificate.schema.json", certificate)
    tracker.ensure_output_size(len(str(certificate).encode("utf-8")))

    candidate = {
        "differenceNumerator": certificate["differenceNumerator"],
        "isZeroNumerator": bool(numer == 0),
    }
    # isZeroNumerator is diagnostic only — not a trusted theorem Boolean.
    return HandlerResult(
        {
            "capability": CAPABILITY_ID,
            "capabilityVersion": CAPABILITY_VERSION,
            "requestDigest": digest,
            "candidate": candidate,
            "certificate": certificate,
            "resultHint": "candidate",  # never soundness_verified from adapter
        },
        resource_usage=tracker.usage(),
    )


def propose_conditions_handler(params: dict[str, Any], tracker: ResourceTracker) -> HandlerResult:
    """JSON-RPC proposeConditions — untrusted side-condition candidates."""
    tracker.check()
    request = params.get("request")
    if not isinstance(request, dict):
        raise stable_error("malformed_evidence", "proposeConditions.params.request required")
    capability = request.get("capability", CAPABILITY_ID)
    if capability != CAPABILITY_ID:
        return HandlerResult(
            {
                "proposedConditions": [],
                "notes": [
                    f"No condition proposal heuristics for {capability} in SymPy adapter v0."
                ],
            }
        )
    from adapters.common.hypothesis_util import propose_conditions_from_request

    proposed = propose_conditions_from_request(request)
    return HandlerResult(
        {
            "capability": CAPABILITY_ID,
            "proposedConditions": proposed,
            "notes": [
                "Untrusted proposals; Lean prove_sufficient / checkBool required.",
                "Minimality is never asserted by this method.",
            ],
        },
        resource_usage=tracker.usage(),
    )


def _rat_lit(n: int, d: int = 1) -> dict[str, Any]:
    return {"tag": "rat", "num": str(n), "den": str(d)}


def _matrix_to_ir(m: Any) -> dict[str, Any]:
    rows, cols = m.rows, m.cols
    entries = []
    for i in range(rows):
        row = []
        for j in range(cols):
            e = m[i, j]
            row.append(_rat_lit(int(e.p), int(e.q)))
        entries.append(row)
    return {"tag": "matrix", "rows": rows, "cols": cols, "entries": entries}


def _matrix_from_ir(node: dict[str, Any]) -> Any:
    from sympy import Matrix, Rational

    entries = []
    for row in node["entries"]:
        entries.append([Rational(int(e["num"]), int(e["den"])) for e in row])
    return Matrix(entries)


def compute_linear_algebra(request: dict[str, Any], tracker: ResourceTracker) -> HandlerResult:
    from datetime import UTC, datetime

    from adapters.common.canonical import verify_request_digest
    from adapters.common.schema_validate import SchemaStore

    store = SchemaStore()
    store.validate("linear-algebra-request.schema.json", request)
    digest = verify_request_digest(request)
    tracker.check()
    A = _matrix_from_ir(request["matrix"])
    op = request["operation"]
    cert: dict[str, Any] = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.linear_algebra",
        "capabilityVersion": "0.1.0",
        "requestDigest": digest,
        "operation": op,
        "provenance": {
            "backendId": "sympy",
            "backendVersion": _sympy_version(),
            "adapterVersion": ADAPTER_VERSION,
            "generatedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "deterministic": True,
        },
    }
    candidate: dict[str, Any] = {"reportedOk": True}
    if op == "inverse_witness":
        if A.det() == 0:
            raise stable_error("certificate_rejected", "matrix is singular")
        cert["inverse"] = _matrix_to_ir(A.inv())
        cert["sideConditions"] = ["matrix_invertible"]
    elif op == "system_solution":
        from sympy import Matrix, Rational

        b = Matrix([Rational(int(e["num"]), int(e["den"])) for e in request.get("rhs", [])])
        sol = A.solve(b)
        cert["vector"] = [_rat_lit(int(e.p), int(e.q)) for e in sol]
    elif op == "kernel_vector":
        null = A.nullspace()
        if not null:
            raise stable_error("certificate_rejected", "trivial kernel")
        v = null[0]
        cert["vector"] = [_rat_lit(int(e.p), int(e.q)) for e in v]
    elif op == "det_identity":
        # Claimed det is on the request; certificate is empty witness.
        pass
    else:
        raise stable_error("backend_unsupported", f"unknown operation {op}")
    store.validate("linear-algebra-certificate.schema.json", cert)
    return HandlerResult(
        {
            "capability": "algebra.linear_algebra",
            "capabilityVersion": "0.1.0",
            "requestDigest": digest,
            "candidate": candidate,
            "certificate": cert,
            "resultHint": "candidate",
        },
        resource_usage=tracker.usage(),
    )


def compute_finite_counterexample(
    request: dict[str, Any], tracker: ResourceTracker
) -> HandlerResult:
    from datetime import UTC, datetime

    from adapters.common.canonical import verify_request_digest
    from adapters.common.hypothesis_util import find_counterexample
    from adapters.common.schema_validate import SchemaStore

    store = SchemaStore()
    store.validate("finite-counterexample-request.schema.json", request)
    digest = verify_request_digest(request)
    tracker.check()
    cert = find_counterexample(request)
    if cert is None:
        raise stable_error(
            "certificate_rejected",
            "no counterexample found within enumeration bound",
        )
    cert["provenance"] = {
        "backendId": "sympy",
        "backendVersion": _sympy_version(),
        "adapterVersion": ADAPTER_VERSION,
        "generatedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "deterministic": True,
    }
    store.validate("finite-counterexample-certificate.schema.json", cert)
    return HandlerResult(
        {
            "capability": "logic.finite_counterexample",
            "capabilityVersion": "0.1.0",
            "requestDigest": digest,
            "candidate": {"reportedFalse": True},
            "certificate": cert,
            "resultHint": "candidate",
        },
        resource_usage=tracker.usage(),
    )


def compute_symbolic_calculus(request: dict[str, Any], tracker: ResourceTracker) -> HandlerResult:
    from datetime import UTC, datetime

    from sympy import Symbol, diff, integrate, simplify

    from adapters.common.calculus_ir import (
        collect_all_dens,
        ensure_sizes,
        validate_operation_fields,
    )
    from adapters.common.canonical import verify_request_digest
    from adapters.common.schema_validate import SchemaStore

    store = SchemaStore()
    store.validate("symbolic-calculus-request.schema.json", request)
    digest = verify_request_digest(request)
    tracker.check()
    validate_operation_fields(request)
    ensure_sizes(request)

    op = request["operation"]
    env = {v["name"]: Symbol(v["name"]) for v in request["variables"]}
    indep = request["independentVar"]
    if indep not in env:
        raise stable_error("unsupported_expression", f"independentVar {indep!r} undeclared")
    x = env[indep]
    expr = _sympy_from_ir(request["expr"], env)

    out_req = dict(request)
    notes = ""
    if op == "derivative_candidate":
        if "candidate" not in out_req:
            out_req["candidate"] = _ir_from_sympy(simplify(diff(expr, x)))
        notes = "SymPy Diff candidate; Lean formalDeriv owns acceptance."
    elif op == "antiderivative_candidate":
        if "candidate" not in out_req:
            out_req["candidate"] = _ir_from_sympy(simplify(integrate(expr, x)))
        notes = "SymPy integrate candidate; Lean checks F'=f only (not completeness)."
    elif op == "recurrence_identity":
        out_req.setdefault("candidate", {"tag": "int", "value": "0"})
        notes = "Recurrence identity: Lean checks u(n+1)=rhs[u↦u(n)]."
    elif op == "ode_candidate":
        out_req.setdefault("candidate", {"tag": "int", "value": "0"})
        notes = "ODE candidate: Lean checks y'=f(x,y) + ICs (not uniqueness)."
    else:
        raise stable_error("backend_unsupported", f"unknown operation {op}")

    if not out_req.get("domainConditions"):
        dens = collect_all_dens(out_req)
        out_req["domainConditions"] = dens

    # Re-bind digest if we filled candidate/domainConditions (caller should send complete request).
    # For generation, recompute digest after fills when requestDigest was placeholder-bound.
    from adapters.common.canonical import bind_request_digest

    # Prefer the verified digest from the original request; domainConditions echo uses request's list.
    domain = list(request.get("domainConditions") or out_req.get("domainConditions") or [])
    candidate = out_req.get("candidate") or {"tag": "int", "value": "0"}

    cert: dict[str, Any] = {
        "schemaVersion": "0.1.0",
        "capability": "analysis.symbolic_calculus",
        "capabilityVersion": "0.1.0",
        "requestDigest": digest,
        "operation": op,
        "domainConditions": domain,
        "candidateEcho": candidate,
        "notes": notes,
        "provenance": {
            "backendId": "sympy",
            "backendVersion": _sympy_version(),
            "adapterVersion": ADAPTER_VERSION,
            "generatedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "deterministic": True,
        },
    }
    store.validate("symbolic-calculus-certificate.schema.json", cert)
    _ = bind_request_digest
    return HandlerResult(
        {
            "capability": "analysis.symbolic_calculus",
            "capabilityVersion": "0.1.0",
            "requestDigest": digest,
            "candidate": {"reportedOk": True, "expr": candidate},
            "certificate": cert,
            "resultHint": "candidate",
        },
        resource_usage=tracker.usage(),
    )


def check_support(params: dict[str, Any], tracker: ResourceTracker) -> HandlerResult:
    tracker.check()
    request = params.get("request")
    if isinstance(request, dict):
        cap = request.get("capability", CAPABILITY_ID)
        if cap == CAPABILITY_ID:
            try:
                expr_size(request.get("lhs", {"tag": "int", "value": "0"}))
                expr_size(request.get("rhs", {"tag": "int", "value": "0"}))
                return HandlerResult({"supported": True, "capability": CAPABILITY_ID})
            except AdapterError as exc:
                return HandlerResult(
                    {
                        "supported": False,
                        "reasonCode": exc.code,
                        "message": exc.message,
                    }
                )
        if cap in (
            "algebra.linear_algebra",
            "logic.finite_counterexample",
            "analysis.symbolic_calculus",
        ):
            return HandlerResult({"supported": True, "capability": cap})
    cap = params.get("capability", CAPABILITY_ID)
    known = {c.id for c in SYMPY_CAPABILITIES}
    if cap not in known:
        return HandlerResult(
            {
                "supported": False,
                "reasonCode": "backend_unsupported",
                "message": f"unsupported capability {cap!r}",
            }
        )
    return HandlerResult({"supported": True, "capability": cap})


def compute_handler(params: dict[str, Any], tracker: ResourceTracker) -> HandlerResult:
    request = params.get("request")
    if not isinstance(request, dict):
        raise stable_error("malformed_evidence", "compute.params.request must be an object")
    cap = request.get("capability", CAPABILITY_ID)
    if cap == "algebra.linear_algebra":
        return compute_linear_algebra(request, tracker)
    if cap == "logic.finite_counterexample":
        return compute_finite_counterexample(request, tracker)
    if cap == "analysis.symbolic_calculus":
        return compute_symbolic_calculus(request, tracker)
    return compute_rational_equality(request, tracker)


def _sympy_version() -> str:
    import sympy

    return str(sympy.__version__)
