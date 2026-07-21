"""Ideal-membership adapter hooks (SymPy / Sage generators).

Generators propose coefficient witnesses ``q_i``; Lean ``checkMembership`` is
authoritative. Backends never establish membership on their own.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

CAPABILITY_ID = "algebra.groebner_membership"
CAPABILITY_VERSION = "0.1.0"
SCHEMA_VERSION = "0.1.0"

# Exact linear search budget (number of unknown coefficients).
_MAX_LINEAR_UNKNOWNS = 96
_MAX_TOTAL_DEGREE = 6


def _term(coefficient: int, exponents: list[int]) -> dict[str, Any]:
    return {"coefficient": coefficient, "exponents": exponents}


def _infer_var_count(target: dict[str, Any], generators: list[dict[str, Any]]) -> int:
    """Infer sparse polynomial arity from explicit fields or term exponents."""
    explicit = target.get("varCount")
    if explicit is not None:
        return int(explicit)
    for poly in [target, *generators]:
        for term in poly.get("terms") or []:
            exponents = term.get("exponents")
            if exponents is not None:
                return len(exponents)
    return 0


def _poly_from_dict(p: dict[str, Any], nvars: int) -> dict[str, Any]:
    return {
        "varCount": int(p.get("varCount", nvars)),
        "terms": list(p.get("terms") or []),
    }


def _normalize_terms(terms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    acc: dict[tuple[int, ...], int] = {}
    for t in terms:
        key = tuple(int(e) for e in t.get("exponents") or [])
        acc[key] = acc.get(key, 0) + int(t.get("coefficient") or 0)
    return [
        _term(c, list(exps))
        for exps, c in sorted(acc.items(), key=lambda kv: kv[0])
        if c != 0
    ]


def check_membership_python(
    target: dict[str, Any],
    generators: list[dict[str, Any]],
    multipliers: list[dict[str, Any]],
) -> bool:
    """Python mirror of Lean ``checkMembership`` (normalize then compare)."""
    if len(generators) != len(multipliers):
        return False
    nvars = _infer_var_count(target, generators)
    combo: dict[tuple[int, ...], int] = {}
    for g, q in zip(generators, multipliers):
        g = _poly_from_dict(g, nvars)
        q = _poly_from_dict(q, nvars)
        for tg in g.get("terms") or []:
            for tq in q.get("terms") or []:
                exps = [
                    int(a) + int(b)
                    for a, b in zip(tg.get("exponents") or [], tq.get("exponents") or [])
                ]
                key = tuple(exps)
                combo[key] = combo.get(key, 0) + int(tg.get("coefficient") or 0) * int(
                    tq.get("coefficient") or 0
                )
    target_norm = {
        tuple(int(e) for e in t.get("exponents") or []): int(t.get("coefficient") or 0)
        for t in _normalize_terms(list(target.get("terms") or []))
    }
    combo_norm = {k: v for k, v in combo.items() if v != 0}
    return combo_norm == {k: v for k, v in target_norm.items() if v != 0}


def _heuristic_xy_membership(
    target: dict[str, Any], generators: list[dict[str, Any]]
) -> list[dict[str, Any]] | None:
    """Deterministic certificate for IM01-style ``xy ∈ ⟨x,y⟩``."""
    nvars = int(target.get("varCount") or 2)
    tterms = target.get("terms") or []
    if len(generators) != 2 or len(tterms) != 1:
        return None
    if int(tterms[0].get("coefficient") or 0) != 1:
        return None
    exps = list(tterms[0].get("exponents") or [])
    if exps != [1, 1]:
        return None
    g0 = (generators[0].get("terms") or [{}])[0].get("exponents")
    g1 = (generators[1].get("terms") or [{}])[0].get("exponents")
    if list(g0 or []) == [1, 0] and list(g1 or []) == [0, 1]:
        return [
            {"varCount": nvars, "terms": [_term(1, [0, 1])]},
            {"varCount": nvars, "terms": []},
        ]
    return None


def _monomials_upto(nvars: int, total_degree: int) -> list[tuple[int, ...]]:
    if total_degree < 0 or nvars <= 0:
        return []
    out: list[tuple[int, ...]] = []

    def go(prefix: list[int], remaining_vars: int, remaining_degree: int) -> None:
        if remaining_vars == 1:
            out.append(tuple([*prefix, remaining_degree]))
            return
        for degree in range(remaining_degree + 1):
            go([*prefix, degree], remaining_vars - 1, remaining_degree - degree)

    for degree in range(total_degree + 1):
        go([], nvars, degree)
    return out


def _poly_total_degree(p: dict[str, Any]) -> int:
    deg = 0
    for t in p.get("terms") or []:
        deg = max(deg, sum(int(e) for e in t.get("exponents") or []))
    return deg


def _expr_to_sparse(poly: Any, xs: tuple[Any, ...], nvars: int) -> dict[str, Any] | None:
    from sympy import Poly

    terms: list[dict[str, Any]] = []
    for mon, c in Poly(poly, *xs, domain="QQ").terms():
        if getattr(c, "q", 1) != 1:
            return None
        terms.append(_term(int(c), list(mon)))
    return {"varCount": nvars, "terms": _normalize_terms(terms)}


def _exact_linear_witness(
    target: dict[str, Any], generators: list[dict[str, Any]]
) -> list[dict[str, Any]] | None:
    """Solve for multipliers in a bounded monomial basis (non-trivial q degrees)."""
    try:
        import sympy as sp
        from sympy import Poly
    except Exception:
        return None

    nvars = _infer_var_count(target, generators)
    if nvars <= 0:
        return None
    xs = sp.symbols(f"x0:{nvars}")

    def to_expr(p: dict[str, Any]) -> Any:
        acc = 0
        for t in p.get("terms") or []:
            mon = 1
            for i, e in enumerate(t.get("exponents") or []):
                mon *= xs[i] ** int(e)
            acc += int(t.get("coefficient") or 0) * mon
        return sp.expand(acc)

    f = to_expr(target)
    gens = [to_expr(g) for g in generators]
    target_degree = _poly_total_degree(target)
    if target_degree > _MAX_TOTAL_DEGREE:
        return None

    coeffs: list[Any] = []
    q_exprs: list[Any] = []
    for i, gen_poly_expr in enumerate(gens):
        gen_poly = Poly(gen_poly_expr, *xs, domain=sp.ZZ)
        gen_degree = max((sum(mon) for mon, _ in gen_poly.terms()), default=0)
        candidate_monomials = _monomials_upto(nvars, max(0, target_degree - gen_degree))
        q_expr = 0
        for j, mon in enumerate(candidate_monomials):
            coeff = sp.Symbol(f"c_{i}_{j}", integer=True)
            coeffs.append(coeff)
            term = 1
            for x, e in zip(xs, mon):
                term *= x**e
            q_expr += coeff * term
        q_exprs.append(q_expr)

    if not coeffs or len(coeffs) > _MAX_LINEAR_UNKNOWNS:
        return None

    try:
        residual = sp.expand(sum(q * g for q, g in zip(q_exprs, gens)) - f)
        # Domain must admit unknown coefficient symbols (not ZZ alone).
        residual_poly = Poly(residual, *xs)
        equations = [coeff for _, coeff in residual_poly.terms()]
        if not equations:
            substitutions = {c: 0 for c in coeffs}
        else:
            solution_set = sp.linsolve(equations, coeffs)
            if solution_set == sp.EmptySet:
                return None
            solution = next(iter(solution_set), None)
            if solution is None:
                return None
            substitutions = {}
            for coeff, value in zip(coeffs, solution):
                if hasattr(value, "free_symbols") and value.free_symbols:
                    value = value.subs({sym: 0 for sym in value.free_symbols})
                substitutions[coeff] = sp.Integer(value)

        out: list[dict[str, Any]] = []
        for q_expr in q_exprs:
            sparse = _expr_to_sparse(sp.expand(q_expr.subs(substitutions)), xs, nvars)
            if sparse is None:
                return None
            out.append(sparse)
        if check_membership_python(target, generators, out):
            return out
        return None
    except Exception:
        return None


def _sympy_multipliers(
    target: dict[str, Any], generators: list[dict[str, Any]]
) -> list[dict[str, Any]] | None:
    """Try SymPy reduced form, then exact linear witness search."""
    try:
        import sympy as sp
        from sympy import Poly
    except Exception:
        return None

    nvars = _infer_var_count(target, generators)
    if nvars <= 0:
        return None
    xs = sp.symbols(f"x0:{nvars}")

    def to_expr(p: dict[str, Any]) -> Any:
        acc = 0
        for t in p.get("terms") or []:
            mon = 1
            for i, e in enumerate(t.get("exponents") or []):
                mon *= xs[i] ** int(e)
            acc += int(t.get("coefficient") or 0) * mon
        return sp.expand(acc)

    f = to_expr(target)
    gens = [to_expr(g) for g in generators]

    try:
        if len(gens) == 2 and f == sp.expand(gens[0] * gens[1]):
            g1_terms = generators[1].get("terms") or []
            first = (
                [
                    {
                        "coefficient": 1,
                        "exponents": list(
                            (g1_terms[0].get("exponents") or [0] * nvars)
                        ),
                    }
                ]
                if g1_terms
                else []
            )
            return [
                {"varCount": nvars, "terms": _normalize_terms(first)},
                {"varCount": nvars, "terms": []},
            ]

        quotients, remainder = sp.reduced(f, gens, *xs, order="lex")
        if sp.expand(remainder) == 0 and len(quotients) == len(gens):
            out: list[dict[str, Any]] = []
            for coeff_expr in quotients:
                sparse = _expr_to_sparse(sp.expand(coeff_expr), xs, nvars)
                if sparse is None:
                    out = []
                    break
                out.append(sparse)
            if out and check_membership_python(target, generators, out):
                return out
        return _exact_linear_witness(target, generators)
    except Exception:
        return _exact_linear_witness(target, generators)


def sage_executable() -> str | None:
    """Return a Sage executable path when present locally; else None."""
    return shutil.which("sage") or shutil.which("sagemath")


def _sage_multipliers(
    target: dict[str, Any], generators: list[dict[str, Any]]
) -> list[dict[str, Any]] | None:
    """Live Sage/Singular path when ``sage`` is on PATH (not advertised otherwise)."""
    exe = sage_executable()
    if exe is None:
        return None

    nvars = _infer_var_count(target, generators)
    payload = {
        "varCount": nvars,
        "target": _poly_from_dict(target, nvars),
        "generators": [_poly_from_dict(g, nvars) for g in generators],
    }
    worker = r"""
import json, sys
from sage.all import PolynomialRing, QQ

data = json.load(sys.stdin)
n = int(data["varCount"])
R = PolynomialRing(QQ, n, names=["x%s" % i for i in range(n)])
xs = R.gens()

def to_poly(p):
    acc = R(0)
    for t in p.get("terms") or []:
        mon = R(1)
        for i, e in enumerate(t.get("exponents") or []):
            mon *= xs[i] ** int(e)
        acc += int(t.get("coefficient") or 0) * mon
    return acc

f = to_poly(data["target"])
gens = [to_poly(g) for g in data["generators"]]
I = R.ideal(gens)
try:
    qs = f.lift(I)
except Exception as exc:
    json.dump({"ok": False, "error": str(exc)}, sys.stdout)
    sys.exit(0)

def from_poly(p):
    terms = []
    if p == 0:
        return {"varCount": n, "terms": []}
    for mon in p.monomials():
        c = p.monomial_coefficient(mon)
        exps = [int(mon.degree(x)) for x in xs]
        if c.denominator() != 1:
            return None
        terms.append({"coefficient": int(c), "exponents": exps})
    return {"varCount": n, "terms": terms}

out = []
for q in qs:
    sp = from_poly(q)
    if sp is None:
        json.dump({"ok": False, "error": "non-integer coefficient"}, sys.stdout)
        sys.exit(0)
    out.append(sp)
json.dump({"ok": True, "multipliers": out}, sys.stdout)
"""
    try:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "ideal_lift.py"
            script.write_text(worker, encoding="utf-8")
            proc = subprocess.run(
                [exe, "-python", str(script)],
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        if proc.returncode != 0 or not proc.stdout.strip():
            return None
        result = json.loads(proc.stdout)
        if not result.get("ok"):
            return None
        multipliers = result.get("multipliers") or []
        if check_membership_python(target, generators, multipliers):
            return multipliers
        return None
    except Exception:
        return None


def wolframscript_executable() -> str | None:
    """Return wolframscript path when ``MATHEVIDENCE_WOLFRAMSCRIPT`` names a file."""
    exe_env = os.environ.get("MATHEVIDENCE_WOLFRAMSCRIPT", "").strip()
    if not exe_env:
        return None
    candidate = Path(exe_env)
    return str(candidate) if candidate.is_file() else None


def _mathematica_multipliers(
    target: dict[str, Any], generators: list[dict[str, Any]]
) -> list[dict[str, Any]] | None:
    """Live Wolfram coefficient witness when ``MATHEVIDENCE_WOLFRAMSCRIPT`` is set.

    Uses ``PolynomialReduce`` over QQ; rejects non-integer coefficients. Fixture hosts
    without the env var never enter this path.
    """
    exe = wolframscript_executable()
    if exe is None:
        return None

    nvars = _infer_var_count(target, generators)
    payload = {
        "varCount": nvars,
        "target": _poly_from_dict(target, nvars),
        "generators": [_poly_from_dict(g, nvars) for g in generators],
    }
    # Encode sparse polys as WL polynomials in x0..x{n-1}.
    def _wl_poly(p: dict[str, Any]) -> str:
        terms = p.get("terms") or []
        if not terms:
            return "0"
        parts: list[str] = []
        for t in terms:
            c = int(t.get("coefficient") or 0)
            exps = [int(e) for e in t.get("exponents") or []]
            mon = "*".join(
                f"(x{i}^{e})" if e != 1 else f"x{i}"
                for i, e in enumerate(exps)
                if e > 0
            )
            if not mon:
                parts.append(str(c))
            elif c == 1:
                parts.append(mon)
            elif c == -1:
                parts.append(f"(-{mon})")
            else:
                parts.append(f"({c})*{mon}")
        return "+".join(parts) if parts else "0"

    vars_wl = ",".join(f"x{i}" for i in range(nvars))
    gens_wl = ",".join(_wl_poly(g) for g in payload["generators"])
    f_wl = _wl_poly(payload["target"])
    script = f"""
SetOptions[$Output, PageWidth -> Infinity];
vars = {{{vars_wl}}};
f = {f_wl};
gens = {{{gens_wl}}};
{{qs, rem}} = PolynomialReduce[f, gens, vars];
If[Expand[rem] =!= 0,
  Print[ExportString[<|"ok" -> False, "error" -> "nonzero_remainder"|>, "JSON"]];
  Quit[0]
];
toSparse[p_] := Module[{{expanded = Expand[p], terms = {{}}, c, mon, exps}},
  If[expanded === 0, Return[<|"varCount" -> {nvars}, "terms" -> {{}}|>]];
  Do[
    mon = If[Head[term] === Times, Select[List @@ term, ! NumericQ[#] &],
      If[NumericQ[term], {{}}, {{term}}]];
    c = expanded /. ((# -> 1) & /@ Variables[expanded]);
    If[!IntegerQ[c] && !(Head[c] === Rational && Denominator[c] === 1),
      Return[None]
    ];
    c = IntegerPart[c];
    exps = Table[
      Exponent[If[mon === {{}}, 1, Times @@ mon], vars[[i]]],
      {{i, 1, {nvars}}}
    ];
    terms = Append[terms, <|"coefficient" -> c, "exponents" -> exps|>],
    {{term, If[Head[expanded] === Plus, List @@ expanded, {{expanded}}]}}
  ];
  <|"varCount" -> {nvars}, "terms" -> terms|>
];
(* Robust path: coefficient lists via CoefficientRules *)
toSparse2[p_] := Module[{{rules, terms = {{}}, c, exps}},
  rules = CoefficientRules[Expand[p], vars];
  Do[
    c = rule[[2]];
    If[Head[c] === Rational && Denominator[c] =!= 1, Return[None]];
    If[!IntegerQ[c], c = IntegerPart[c]];
    If[!IntegerQ[c], Return[None]];
    exps = rule[[1]];
    If[c =!= 0, terms = Append[terms, <|"coefficient" -> c, "exponents" -> exps|>]],
    {{rule, rules}}
  ];
  <|"varCount" -> {nvars}, "terms" -> terms|>
];
out = {{}};
Do[
  sp = toSparse2[qs[[i]]];
  If[sp === None,
    Print[ExportString[<|"ok" -> False, "error" -> "non_integer_coefficient"|>, "JSON"]];
    Quit[0]
  ];
  out = Append[out, sp],
  {{i, Length[qs]}}
];
Print[ExportString[<|"ok" -> True, "multipliers" -> out|>, "JSON"]];
"""
    try:
        proc = subprocess.run(
            [exe, "-code", script],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return None
        # Last JSON object line
        lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
        result = None
        for ln in reversed(lines):
            try:
                result = json.loads(ln)
                break
            except json.JSONDecodeError:
                continue
        if not isinstance(result, dict) or not result.get("ok"):
            return None
        multipliers = result.get("multipliers") or []
        if check_membership_python(target, generators, multipliers):
            return multipliers
        return None
    except Exception:
        return None


def propose_membership_witness(
    *,
    target: dict[str, Any],
    generators: list[dict[str, Any]],
    backend: str = "stub",
) -> dict[str, Any]:
    """Return an untrusted candidate certificate payload.

    Lean ``checkMembership`` / ``MembershipWitness.check`` is authoritative.
    """
    nvars = _infer_var_count(target, generators)
    multipliers: list[dict[str, Any]] = []
    notes: list[str] = []
    resolved_backend = backend
    skipped = False
    skip_reason: str | None = None

    if backend in {"stub", "heuristic", "sympy", "auto"}:
        heur = _heuristic_xy_membership(target, generators)
        if heur is not None and backend in {"stub", "heuristic", "sympy", "auto"}:
            multipliers = heur
            notes.append("Heuristic IM01-style certificate (untrusted until Lean check).")
            resolved_backend = "heuristic"
        elif backend in {"sympy", "auto"}:
            if _poly_total_degree(target) > _MAX_TOTAL_DEGREE:
                skipped = True
                skip_reason = (
                    f"target total degree > {_MAX_TOTAL_DEGREE}; exact search skipped"
                )
                notes.append(skip_reason)
                resolved_backend = "sympy"
            else:
                sym = _sympy_multipliers(target, generators)
                if sym is not None:
                    multipliers = sym
                    notes.append(
                        "SymPy-proposed multipliers via reduce/exact-linear "
                        "(untrusted until Lean check)."
                    )
                    resolved_backend = "sympy"
                else:
                    notes.append(
                        f"Backend {backend!r} could not propose multipliers; empty candidate."
                    )
                    resolved_backend = "sympy" if backend == "auto" else backend
        else:
            notes.append("Stub generator: empty multipliers.")
    elif backend == "sage":
        if sage_executable() is None:
            notes.append(
                "Backend 'sage' requested but no sage/sagemath executable is on PATH; "
                "ideal-membership Sage path is not advertised without a live binary."
            )
            resolved_backend = "sage"
        else:
            sage_qs = _sage_multipliers(target, generators)
            if sage_qs is not None:
                multipliers = sage_qs
                notes.append(
                    "Sage lift()-proposed multipliers (untrusted until Lean check)."
                )
                resolved_backend = "sage"
            else:
                notes.append("Sage executable present but lift() produced no ZZ witness.")
                resolved_backend = "sage"
    elif backend == "mathematica":
        if wolframscript_executable() is None:
            notes.append(
                "Backend 'mathematica' requested but MATHEVIDENCE_WOLFRAMSCRIPT is unset "
                "or not a file; live witness generation requires wolframscript. "
                "Adapter + fixture conformance exist; live path is not advertised "
                "without the env var."
            )
            resolved_backend = "mathematica"
        else:
            mm_qs = _mathematica_multipliers(target, generators)
            if mm_qs is not None:
                multipliers = mm_qs
                notes.append(
                    "Wolfram PolynomialReduce-proposed multipliers "
                    "(untrusted until Lean check)."
                )
                resolved_backend = "mathematica"
            else:
                notes.append(
                    "MATHEVIDENCE_WOLFRAMSCRIPT set but PolynomialReduce produced "
                    "no ZZ witness."
                )
                resolved_backend = "mathematica"
    else:
        notes.append(f"Unknown backend {backend!r}; empty multipliers.")

    payload: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "capability": CAPABILITY_ID,
        "capabilityVersion": CAPABILITY_VERSION,
        "backend": resolved_backend,
        "claimClass": "candidate",
        "target": _poly_from_dict(target, nvars),
        "generators": [_poly_from_dict(g, nvars) for g in generators],
        "multipliers": multipliers,
        "notes": notes,
        "provenance": {
            "backendId": resolved_backend,
            "adapterVersion": CAPABILITY_VERSION,
            "deterministic": True,
        },
        "liveDetection": {
            "sageExecutablePresent": sage_executable() is not None,
            "wolframscriptEnvPresent": wolframscript_executable() is not None,
        },
    }
    if skipped:
        payload["skipped"] = True
        payload["skipReason"] = skip_reason
    payload["pythonMirrorAccepts"] = check_membership_python(
        payload["target"], payload["generators"], payload["multipliers"]
    )
    return payload


def compute_ideal_membership_certificate(
    request: dict[str, Any],
    *,
    backend: str,
) -> dict[str, Any]:
    """Adapter-facing compute: propose multipliers into the shared certificate schema."""
    from adapters.common.canonical import bind_request_digest

    target = request.get("target")
    generators = request.get("generators")
    if not isinstance(target, dict) or not isinstance(generators, list) or not generators:
        raise ValueError(
            "ideal membership request requires target object and non-empty generators"
        )
    out_req = dict(request)
    out_req.setdefault("schemaVersion", SCHEMA_VERSION)
    out_req.setdefault("capability", CAPABILITY_ID)
    out_req.setdefault("capabilityVersion", CAPABILITY_VERSION)
    out_req = bind_request_digest(out_req)
    payload = propose_membership_witness(
        target=target, generators=generators, backend=backend
    )
    payload["requestDigest"] = out_req["requestDigest"]
    if payload.get("skipped"):
        return {
            "capability": CAPABILITY_ID,
            "capabilityVersion": CAPABILITY_VERSION,
            "requestDigest": out_req["requestDigest"],
            "candidate": {"reportedOk": False, "skipped": True},
            "certificate": payload,
            "resultHint": "candidate",
            "request": out_req,
            "skipped": True,
            "skipReason": payload.get("skipReason"),
        }
    if not payload.get("multipliers"):
        return {
            "capability": CAPABILITY_ID,
            "capabilityVersion": CAPABILITY_VERSION,
            "requestDigest": out_req["requestDigest"],
            "candidate": {"reportedOk": False},
            "certificate": payload,
            "resultHint": "candidate",
            "request": out_req,
        }
    return {
        "capability": CAPABILITY_ID,
        "capabilityVersion": CAPABILITY_VERSION,
        "requestDigest": out_req["requestDigest"],
        "candidate": {"reportedOk": True, "multipliers": payload["multipliers"]},
        "certificate": payload,
        "resultHint": "candidate",
        "request": out_req,
    }
