"""Mathematica adapter for algebra.rational_equality (RFC 0001).

Live generation requires ``MATHEVIDENCE_WOLFRAMSCRIPT`` pointing at ``wolframscript``.
Otherwise the adapter runs in **fixture mode**: JSON-RPC works; live ``compute``
returns ``backend_unavailable``. Committed evidence under ``evidence/`` always
replays offline without Mathematica.

LeanLink remains scaffold-only and outside the theorem TCB
(``docs/architecture/leanlink-adapter-review.md``). The supported live transport
is wolframscript with fixed argv (no shell interpolation).
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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
        "Same evidence contract as SymPy (candidate numerator + denom factors).",
        "Live path: MATHEVIDENCE_WOLFRAMSCRIPT → wolframscript -code (fixed argv).",
        "LeanLink is scaffold-only; not used for theorem acceptance.",
    ],
)

SYMBOLIC_CALCULUS_CAPABILITY = CapabilityDescriptor(
    id="analysis.symbolic_calculus",
    version="0.1.0",
    claim_classes=["candidate", "soundResult", "witness"],
    request_schema="symbolic-calculus-request.schema.json",
    evidence_schema="symbolic-calculus-certificate.schema.json",
    deterministic=True,
    notes=[
        "Live path: wolframscript D/Integrate → RationalExpr ToIR (same fragment as R1a).",
        "Candidate validity ≠ completeness/uniqueness; Lean Calculus checker owns acceptance.",
        "Committed evidence under evidence/examples/calculus_* replays offline.",
    ],
)

MATHEMATICA_CAPABILITIES = [RATIONAL_EQUALITY_CAPABILITY, SYMBOLIC_CALCULUS_CAPABILITY]


@dataclass(frozen=True)
class MathematicaRuntime:
    available: bool
    executable: str | None
    leanlink_path: str | None
    mode: str  # "live" | "fixture"
    detail: str


def discover_runtime() -> MathematicaRuntime:
    """Discover Wolfram live path.

    Live mode is enabled only when ``MATHEVIDENCE_WOLFRAMSCRIPT`` names an
    existing file (unless ``MATHEVIDENCE_ADAPTER_MODE=fixture`` forces fixture).
    Accidental ``wolframscript`` on PATH does not enable live generation — that
    keeps public CI deterministic.
    """
    forced = os.environ.get("MATHEVIDENCE_ADAPTER_MODE", "").strip().lower()
    leanlink = os.environ.get("MATHEVIDENCE_LEANLINK")
    if leanlink:
        leanlink = str(Path(leanlink))

    exe_env = os.environ.get("MATHEVIDENCE_WOLFRAMSCRIPT", "").strip()
    executable: str | None = None
    if exe_env:
        candidate = Path(exe_env)
        if candidate.is_file():
            executable = str(candidate)
        else:
            return MathematicaRuntime(
                False,
                None,
                leanlink,
                "fixture",
                f"MATHEVIDENCE_WOLFRAMSCRIPT not a file: {exe_env}",
            )

    if forced == "fixture":
        return MathematicaRuntime(
            False,
            executable,
            leanlink,
            "fixture",
            "MATHEVIDENCE_ADAPTER_MODE=fixture",
        )
    if forced == "live" and not executable:
        return MathematicaRuntime(
            False,
            None,
            leanlink,
            "fixture",
            "live mode requested but MATHEVIDENCE_WOLFRAMSCRIPT not set to a file",
        )
    if executable:
        return MathematicaRuntime(
            True,
            executable,
            leanlink,
            "live",
            "MATHEVIDENCE_WOLFRAMSCRIPT set; live wolframscript path",
        )
    return MathematicaRuntime(
        False,
        None,
        leanlink,
        "fixture",
        "MATHEVIDENCE_WOLFRAMSCRIPT unset; fixture mode (CI-safe default)",
    )


def _wl_encode_expr(node: dict[str, Any]) -> str:
    """Encode RationalExpr IR as a Wolfram Language InputForm fragment."""
    tag = node.get("tag")
    if tag == "var":
        return str(node["name"])
    if tag == "int":
        return str(int(node["value"]))
    if tag == "rat":
        return f"({int(node['num'])}/{int(node['den'])})"
    if tag == "add":
        return f"({_wl_encode_expr(node['left'])}+{_wl_encode_expr(node['right'])})"
    if tag == "sub":
        return f"({_wl_encode_expr(node['left'])}-{_wl_encode_expr(node['right'])})"
    if tag == "mul":
        return f"({_wl_encode_expr(node['left'])}*{_wl_encode_expr(node['right'])})"
    if tag == "neg":
        return f"(-{_wl_encode_expr(node['arg'])})"
    if tag == "pow":
        return f"({_wl_encode_expr(node['base'])}^{int(node['exp'])})"
    if tag == "div":
        return f"({_wl_encode_expr(node['num'])}/{_wl_encode_expr(node['den'])})"
    raise stable_error("unsupported_expression", f"unsupported tag: {tag!r}")


def _wl_var_list(request: dict[str, Any]) -> str:
    var_names = [str(v["name"]) for v in request["variables"]]
    return "{" + ",".join(f'"{n}"' for n in var_names) + "}"


def _wl_to_ir_preamble(var_list: str) -> str:
    """Shared RationalExpr ToIR helpers (R1a fragment) for rational + calculus."""
    return f"""
SetOptions[$Output, PageWidth -> Infinity];
declared = {var_list};

ClearAll[ToIR, FoldBinary, TimesToIR, PlusToIR, FactorPairs];

FoldBinary[tag_, irList_List] := Module[{{acc}},
  If[Length[irList] === 0, Return[<|"tag" -> "int", "value" -> "1"|>]];
  If[Length[irList] === 1, Return[First[irList]]];
  acc = First[irList];
  Do[acc = <|"tag" -> tag, "left" -> acc, "right" -> irList[[i]]|>, {{i, 2, Length[irList]}}];
  acc
];

ToIR[n_Integer] := <|"tag" -> "int", "value" -> ToString[n]|>;
ToIR[r_Rational] := <|"tag" -> "rat", "num" -> ToString[Numerator[r]], "den" -> ToString[Denominator[r]]|>;
ToIR[s_Symbol] := Module[{{nm = ToString[s]}},
  If[!MemberQ[declared, nm],
    Throw[<|"error" -> "undeclared_symbol", "name" -> nm|>]
  ];
  <|"tag" -> "var", "name" -> nm|>
];
ToIR[Power[b_, e_Integer]] /; e >= 0 := <|"tag" -> "pow", "base" -> ToIR[b], "exp" -> e|>;
ToIR[Power[b_, e_Integer]] /; e < 0 :=
  <|"tag" -> "div", "num" -> ToIR[1], "den" -> ToIR[Power[b, -e]]|>;
ToIR[Times[args__]] := TimesToIR[{{args}}];
ToIR[Plus[args__]] := PlusToIR[{{args}}];
ToIR[expr_] := Throw[<|"error" -> "unsupported_head", "head" -> ToString[Head[expr]], "form" -> ToString[expr, InputForm]|>];

TimesToIR[factors_List] := Module[
  {{numF = {{}}, denF = {{}}, f, b, e, numIR, denIR}},
  Do[
    f = factors[[i]];
    Which[
      MatchQ[f, Power[_, _Integer?(# < 0 &)]],
        b = f[[1]]; e = -f[[2]]; denF = Append[denF, If[e === 1, b, Power[b, e]]],
      Head[f] === Rational && Denominator[f] =!= 1,
        If[Numerator[f] =!= 1, numF = Append[numF, Numerator[f]]];
        denF = Append[denF, Denominator[f]],
      True,
        numF = Append[numF, f]
    ],
    {{i, Length[factors]}}
  ];
  numIR = If[numF === {{}}, ToIR[1], FoldBinary["mul", Map[ToIR, numF]]];
  If[denF === {{}},
    numIR,
    denIR = FoldBinary["mul", Map[ToIR, denF]];
    <|"tag" -> "div", "num" -> numIR, "den" -> denIR|>
  ]
];

PlusToIR[terms_List] := Module[{{acc, t, pos}},
  If[terms === {{}}, Return[ToIR[0]]];
  acc = ToIR[First[terms]];
  Do[
    t = terms[[i]];
    If[MatchQ[t, Times[-1, ___]] || (NumericQ[t] && t < 0),
      pos = -t;
      acc = <|"tag" -> "sub", "left" -> acc, "right" -> ToIR[pos]|>,
      acc = <|"tag" -> "add", "left" -> acc, "right" -> ToIR[t]|>
    ],
    {{i, 2, Length[terms]}}
  ];
  acc
];

FactorPairs[den_] := Module[{{fac, out = {{}}, pair, base, mult}},
  If[den === 1 || den === -1, Return[{{}}]];
  fac = FactorList[den];
  Do[
    pair = fac[[i]];
    base = pair[[1]];
    mult = pair[[2]];
    If[Abs[base] =!= 1,
      out = Append[out, <|"expr" -> ToIR[base], "multiplicity" -> mult|>]
    ],
    {{i, Length[fac]}}
  ];
  out
];
"""


def _build_wl_script(request: dict[str, Any]) -> str:
    """Build a self-contained WL script that prints RationalExpr IR as JSON.

    Covers the full RFC 0001 fragment: vars, int/rat literals, + − * / ^, neg.
    """
    lhs = _wl_encode_expr(request["lhs"])
    rhs = _wl_encode_expr(request["rhs"])
    preamble = _wl_to_ir_preamble(_wl_var_list(request))
    return f"""
{preamble}

result = Catch[
  Module[{{lhs, rhs, diff, num, den, dens}},
    lhs = {lhs};
    rhs = {rhs};
    diff = Together[Cancel[lhs - rhs]];
    num = Expand[Numerator[diff]];
    den = Expand[Denominator[diff]];
    dens = FactorPairs[den];
    <|
      "differenceNumerator" -> ToIR[num],
      "commonDenom" -> If[den === 1 || den === -1, Null, ToIR[den]],
      "denominatorFactors" -> dens,
      "rawDiff" -> ToString[diff, InputForm]
    |>
  ]
];

ExportString[result, "JSON"]
"""


def _build_wl_calculus_script(request: dict[str, Any]) -> str:
    """Build WL script for derivative/antiderivative candidate ToIR (R1a reuse).

    ODE/recurrence ops do not require symbolic solve here — callers echo request
    fields; completeness/uniqueness are never claimed.
    """
    op = request["operation"]
    expr = _wl_encode_expr(request["expr"])
    indep = str(request["independentVar"])
    preamble = _wl_to_ir_preamble(_wl_var_list(request))
    if op == "derivative_candidate":
        body = f"""
result = Catch[
  Module[{{expr, x, cand}},
    expr = {expr};
    x = {indep};
    cand = Together[Simplify[D[expr, x]]];
    <|
      "operation" -> "derivative_candidate",
      "candidate" -> ToIR[cand],
      "rawForm" -> ToString[cand, InputForm]
    |>
  ]
];
"""
    elif op == "antiderivative_candidate":
        body = f"""
result = Catch[
  Module[{{expr, x, cand}},
    expr = {expr};
    x = {indep};
    cand = Together[Simplify[Integrate[expr, x]]];
    <|
      "operation" -> "antiderivative_candidate",
      "candidate" -> ToIR[cand],
      "rawForm" -> ToString[cand, InputForm]
    |>
  ]
];
"""
    else:
        raise stable_error(
            "backend_unsupported",
            f"Mathematica live calculus generate supports derivative/antiderivative only; "
            f"got {op!r} (ode/recurrence use request echo + Lean checker)",
        )
    return f"""
{preamble}
{body}
ExportString[result, "JSON"]
"""


def _validate_ir(node: Any, *, path: str = "expr") -> dict[str, Any]:
    """Validate / normalize a RationalExpr dict from WL JSON."""
    if not isinstance(node, dict):
        raise stable_error(
            "malformed_evidence",
            f"RationalExpr at {path} must be an object",
            details={"got": type(node).__name__},
        )
    tag = node.get("tag")
    if tag == "var":
        name = node.get("name")
        if not isinstance(name, str) or not name:
            raise stable_error("malformed_evidence", f"bad var at {path}")
        return {"tag": "var", "name": name}
    if tag == "int":
        value = node.get("value")
        if value is None:
            raise stable_error("malformed_evidence", f"bad int at {path}")
        return {"tag": "int", "value": str(int(value))}
    if tag == "rat":
        return {
            "tag": "rat",
            "num": str(int(node["num"])),
            "den": str(int(node["den"])),
        }
    if tag in {"add", "sub", "mul"}:
        return {
            "tag": tag,
            "left": _validate_ir(node.get("left"), path=f"{path}.left"),
            "right": _validate_ir(node.get("right"), path=f"{path}.right"),
        }
    if tag == "neg":
        return {"tag": "neg", "arg": _validate_ir(node.get("arg"), path=f"{path}.arg")}
    if tag == "pow":
        exp = node.get("exp")
        if not isinstance(exp, int) or exp < 0:
            raise stable_error("malformed_evidence", f"bad pow exp at {path}")
        return {
            "tag": "pow",
            "base": _validate_ir(node.get("base"), path=f"{path}.base"),
            "exp": exp,
        }
    if tag == "div":
        return {
            "tag": "div",
            "num": _validate_ir(node.get("num"), path=f"{path}.num"),
            "den": _validate_ir(node.get("den"), path=f"{path}.den"),
        }
    raise stable_error(
        "unsupported_expression",
        f"unsupported or missing tag at {path}: {tag!r}",
    )


def _run_wolfram(
    executable: str,
    script: str,
    tracker: ResourceTracker,
) -> dict[str, Any]:
    """Run Wolfram with fixed argv (no shell)."""
    tracker.check()
    cmd = [executable, "-code", script]
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=max(1, tracker.limits.max_wall_time_ms / 1000.0),
            env=_allowlisted_env(),
        )
    except subprocess.TimeoutExpired as exc:
        raise stable_error("backend_timeout", "wolframscript timed out") from exc
    except OSError as exc:
        raise stable_error("backend_unavailable", f"failed to spawn backend: {exc}") from exc

    tracker.check()
    if proc.returncode != 0:
        raise stable_error(
            "backend_crash",
            "wolframscript exited non-zero",
            details={"returncode": proc.returncode, "stderr": proc.stderr[-2000:]},
        )
    out = proc.stdout.strip()
    tracker.ensure_output_size(len(out.encode("utf-8")))
    # wolframscript may print banners; take the last JSON object line.
    payload = _parse_wl_json_stdout(out)
    if isinstance(payload, dict) and payload.get("error"):
        raise stable_error(
            "unsupported_expression",
            f"Wolfram IR encode failed: {payload.get('error')}",
            details=payload,
        )
    if not isinstance(payload, dict):
        raise stable_error(
            "malformed_evidence",
            "wolframscript did not return a JSON object",
            details={"stdoutPreview": out[:500]},
        )
    return payload


def _parse_wl_json_stdout(out: str) -> Any:
    """Parse JSON from wolframscript stdout (tolerate leading noise)."""
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    candidates = list(reversed(lines)) if lines else [out]
    # Also try the full strip once.
    candidates.append(out.strip())
    last_err: Exception | None = None
    for text in candidates:
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            last_err = exc
            # Try to find a JSON object substring.
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError as exc2:
                    last_err = exc2
    raise stable_error(
        "malformed_evidence",
        "wolframscript did not return JSON",
        details={"stdoutPreview": out[:500], "parseError": str(last_err)},
    )


def _allowlisted_env() -> dict[str, str]:
    """Minimal environment allow-list for Mathematica subprocess."""
    keep = ("PATH", "SYSTEMROOT", "WINDIR", "HOME", "USERPROFILE", "LANG", "LC_ALL")
    env = {k: v for k, v in os.environ.items() if k in keep}
    for key in ("MATHEVIDENCE_WOLFRAMSCRIPT", "MATHEVIDENCE_LEANLINK"):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def certificate_from_wl_payload(
    raw: dict[str, Any],
    request: dict[str, Any],
    digest: str,
    *,
    runtime: MathematicaRuntime,
) -> dict[str, Any]:
    """Assemble a schema-valid certificate from WL JSON payload (testable offline)."""
    numer_ir = _validate_ir(raw.get("differenceNumerator"), path="differenceNumerator")
    expr_size(numer_ir)

    factors: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_factor(ir_expr: dict[str, Any], role: str, multiplicity: int = 1) -> None:
        marker = f"{role}:{json.dumps(ir_expr, sort_keys=True)}"
        if marker in seen:
            return
        seen.add(marker)
        factors.append(
            {
                "expr": ir_expr,
                "role": role,
                "multiplicity": max(1, int(multiplicity)),
            }
        )

    for dens in collect_division_denominators(request["lhs"]) + collect_division_denominators(
        request["rhs"]
    ):
        add_factor(dens, "original_division")

    common = raw.get("commonDenom")
    if common is not None and common != "Null":
        add_factor(_validate_ir(common, path="commonDenom"), "common_denominator")

    dens_raw = raw.get("denominatorFactors") or []
    if not isinstance(dens_raw, list):
        raise stable_error("malformed_evidence", "denominatorFactors must be a list")
    for i, item in enumerate(dens_raw):
        if not isinstance(item, dict):
            raise stable_error("malformed_evidence", f"factor[{i}] must be an object")
        expr = _validate_ir(item.get("expr"), path=f"denominatorFactors[{i}].expr")
        mult = item.get("multiplicity", 1)
        add_factor(expr, "factorization", int(mult) if mult is not None else 1)

    return {
        "schemaVersion": "0.1.0",
        "capability": CAPABILITY_ID,
        "capabilityVersion": CAPABILITY_VERSION,
        "requestDigest": digest,
        "differenceNumerator": numer_ir,
        "denominatorFactors": factors,
        "factorization": {
            "method": "wolfram.Together+Cancel+FactorList+ToIR",
            "notes": (
                f"live RationalExpr fragment; rawDiff={raw.get('rawDiff', '')!s}"
            )[:500],
        },
        "provenance": {
            "backendId": "mathematica",
            "backendVersion": "wolframscript",
            "adapterVersion": ADAPTER_VERSION,
            "leanLinkVersion": runtime.leanlink_path,
            "generatedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "deterministic": True,
        },
    }


def compute_rational_equality(
    request: dict[str, Any],
    tracker: ResourceTracker,
    *,
    runtime: MathematicaRuntime | None = None,
    schemas: SchemaStore | None = None,
) -> HandlerResult:
    store = schemas or SchemaStore()
    store.validate("rational-equality-request.schema.json", request)
    try:
        digest = verify_request_digest(request)
    except Exception as exc:  # noqa: BLE001
        raise stable_error("request_digest_mismatch", str(exc)) from exc

    names = [v["name"] for v in request["variables"]]
    if len(names) != len(set(names)):
        raise stable_error("unsupported_expression", "duplicate variable declarations")

    expr_size(request["lhs"])
    expr_size(request["rhs"])
    rt = runtime or discover_runtime()

    if rt.mode != "live" or not rt.available or not rt.executable:
        raise stable_error(
            "backend_unavailable",
            "Mathematica backend unavailable; use committed evidence for offline replay "
            "or set MATHEVIDENCE_WOLFRAMSCRIPT to enable live generation",
            details={
                "mode": rt.mode,
                "detail": rt.detail,
                "leanLink": rt.leanlink_path,
            },
        )

    # LeanLink path is reserved; v0 live transport is wolframscript only.
    _ = rt.leanlink_path
    raw = _run_wolfram(rt.executable, _build_wl_script(request), tracker)
    certificate = certificate_from_wl_payload(raw, request, digest, runtime=rt)
    store.validate("rational-equality-certificate.schema.json", certificate)
    tracker.ensure_output_size(len(str(certificate).encode("utf-8")))

    numer_ir = certificate["differenceNumerator"]
    return HandlerResult(
        {
            "capability": CAPABILITY_ID,
            "capabilityVersion": CAPABILITY_VERSION,
            "requestDigest": digest,
            "candidate": {
                "differenceNumerator": numer_ir,
                "isZeroNumerator": numer_ir == {"tag": "int", "value": "0"},
            },
            "certificate": certificate,
            "resultHint": "candidate",
        },
        resource_usage=tracker.usage(),
    )


def check_support(params: dict[str, Any], tracker: ResourceTracker) -> HandlerResult:
    tracker.check()
    rt = discover_runtime()
    request = params.get("request")
    if isinstance(request, dict):
        cap = request.get("capability", CAPABILITY_ID)
        if cap == "analysis.symbolic_calculus":
            if not rt.available:
                return HandlerResult(
                    {
                        "supported": False,
                        "reasonCode": "backend_unavailable",
                        "message": rt.detail,
                        "mode": rt.mode,
                        "capability": cap,
                    }
                )
            return HandlerResult(
                {
                    "supported": True,
                    "capability": cap,
                    "mode": rt.mode,
                    "transport": "wolframscript",
                    "leanLinkScaffold": True,
                    "notes": "candidate≠completeness; derivative/antiderivative live",
                }
            )
        try:
            expr_size(request.get("lhs", {"tag": "int", "value": "0"}))
            expr_size(request.get("rhs", {"tag": "int", "value": "0"}))
        except AdapterError as exc:
            return HandlerResult(
                {"supported": False, "reasonCode": exc.code, "message": exc.message}
            )
    if not rt.available:
        return HandlerResult(
            {
                "supported": False,
                "reasonCode": "backend_unavailable",
                "message": rt.detail,
                "mode": rt.mode,
            }
        )
    return HandlerResult(
        {
            "supported": True,
            "capability": CAPABILITY_ID,
            "mode": rt.mode,
            "transport": "wolframscript",
            "leanLinkScaffold": True,
        }
    )


def calculus_certificate_from_wl_payload(
    raw: dict[str, Any],
    request: dict[str, Any],
    digest: str,
    *,
    runtime: MathematicaRuntime,
    candidate: dict[str, Any],
    notes: str,
) -> dict[str, Any]:
    """Assemble schema-valid calculus certificate (testable offline from WL JSON)."""
    op = request["operation"]
    domain = list(request.get("domainConditions") or [])
    return {
        "schemaVersion": "0.1.0",
        "capability": "analysis.symbolic_calculus",
        "capabilityVersion": "0.1.0",
        "requestDigest": digest,
        "operation": op,
        "domainConditions": domain,
        "candidateEcho": candidate,
        "notes": notes[:500],
        "provenance": {
            "backendId": "mathematica",
            "backendVersion": "wolframscript",
            "adapterVersion": ADAPTER_VERSION,
            "leanLinkVersion": runtime.leanlink_path,
            "generatedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "deterministic": True,
        },
    }


def compute_symbolic_calculus(
    request: dict[str, Any],
    tracker: ResourceTracker,
    *,
    runtime: MathematicaRuntime | None = None,
    schemas: SchemaStore | None = None,
) -> HandlerResult:
    """Live Mathematica calculus candidates via R1a ToIR patterns.

    Candidate validity never implies completeness or uniqueness.
    """
    from adapters.common.calculus_ir import (
        collect_all_dens,
        ensure_sizes,
        validate_operation_fields,
    )
    from adapters.common.canonical import bind_request_digest

    store = schemas or SchemaStore()
    rt = runtime or discover_runtime()
    if rt.mode != "live" or not rt.available or not rt.executable:
        raise stable_error(
            "backend_unavailable",
            "Mathematica calculus unavailable; use committed "
            "evidence/examples/calculus_* for offline replay, SymPy adapter, "
            "or set MATHEVIDENCE_WOLFRAMSCRIPT for live derivative/antiderivative",
            details={
                "mode": rt.mode,
                "detail": rt.detail,
                "capability": "analysis.symbolic_calculus",
            },
        )

    op = request.get("operation")
    out_req = dict(request)
    notes = ""

    if op in ("derivative_candidate", "antiderivative_candidate"):
        # Live generate ToIR candidate; rebind digest so certificate matches request.
        raw = _run_wolfram(rt.executable, _build_wl_calculus_script(out_req), tracker)
        candidate = _validate_ir(raw.get("candidate"), path="candidate")
        expr_size(candidate)
        out_req["candidate"] = candidate
        if not out_req.get("domainConditions"):
            out_req["domainConditions"] = collect_all_dens(out_req)
        # Drop prior digest before rebind.
        out_req.pop("requestDigest", None)
        out_req = bind_request_digest(out_req)
        store.validate("symbolic-calculus-request.schema.json", out_req)
        validate_operation_fields(out_req)
        ensure_sizes(out_req)
        digest = out_req["requestDigest"]
        notes = (
            f"Live Mathematica {op} via wolframscript ToIR; "
            f"rawForm={raw.get('rawForm', '')!s}; "
            "candidate≠completeness"
        )
    elif op in ("recurrence_identity", "ode_candidate"):
        # Echo path: no symbolic completeness claim; Lean owns acceptance.
        store.validate("symbolic-calculus-request.schema.json", out_req)
        try:
            digest = verify_request_digest(out_req)
        except Exception as exc:  # noqa: BLE001
            raise stable_error("request_digest_mismatch", str(exc)) from exc
        validate_operation_fields(out_req)
        ensure_sizes(out_req)
        out_req.setdefault("candidate", {"tag": "int", "value": "0"})
        if not out_req.get("domainConditions"):
            dens = collect_all_dens(out_req)
            out_req["domainConditions"] = dens
        notes = (
            f"Mathematica live echo for {op}; Lean checks identity only "
            "(no uniqueness/completeness claim)"
        )
        candidate = out_req["candidate"]
    else:
        raise stable_error("backend_unsupported", f"unknown calculus operation {op!r}")

    candidate = out_req["candidate"]
    domain = list(out_req.get("domainConditions") or [])
    certificate = calculus_certificate_from_wl_payload(
        {},
        out_req,
        digest,
        runtime=rt,
        candidate=candidate,
        notes=notes,
    )
    # Keep domainConditions aligned with request after optional dens fill.
    certificate["domainConditions"] = domain
    store.validate("symbolic-calculus-certificate.schema.json", certificate)
    tracker.ensure_output_size(len(str(certificate).encode("utf-8")))

    return HandlerResult(
        {
            "capability": "analysis.symbolic_calculus",
            "capabilityVersion": "0.1.0",
            "requestDigest": digest,
            "candidate": {"reportedOk": True, "expr": candidate},
            "certificate": certificate,
            "resultHint": "candidate",
            "request": out_req,
        },
        resource_usage=tracker.usage(),
    )


def compute_handler(params: dict[str, Any], tracker: ResourceTracker) -> HandlerResult:
    request = params.get("request")
    if not isinstance(request, dict):
        raise stable_error("malformed_evidence", "compute.params.request must be an object")
    cap = request.get("capability", CAPABILITY_ID)
    if cap == "analysis.symbolic_calculus":
        return compute_symbolic_calculus(request, tracker)
    return compute_rational_equality(request, tracker)
