"""Mathematica / LeanLink adapter for algebra.rational_equality.

Real Mathematica generation is optional. When Wolfram Language is unavailable,
the adapter runs in **fixture mode**: it serves JSON-RPC and rejects live
`compute` with `backend_unavailable`, while committed evidence under
`evidence/` remains offline-replayable without Mathematica.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from adapters.common.canonical import verify_request_digest
from adapters.common.errors import AdapterError, stable_error
from adapters.common.limits import ResourceTracker
from adapters.common.protocol import CapabilityDescriptor, HandlerResult
from adapters.common.rational_ir import expr_size
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
        "Same evidence contract as SymPy.",
        "Process isolation: fixed executable path; no shell interpolation.",
        "LeanLink integration is scaffolded; see adapters/mathematica/README.md.",
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
        "Fixture/live calculus generation; Lean Calculus checker owns acceptance.",
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
    """Discover Wolfram / LeanLink without shell interpolation."""
    forced = os.environ.get("MATHEVIDENCE_ADAPTER_MODE", "").strip().lower()
    leanlink = os.environ.get("MATHEVIDENCE_LEANLINK")
    if leanlink:
        leanlink = str(Path(leanlink))

    exe = os.environ.get("MATHEVIDENCE_WOLFRAMSCRIPT")
    if exe:
        candidate = Path(exe)
        if not candidate.is_file():
            return MathematicaRuntime(
                False,
                None,
                leanlink,
                "fixture",
                f"MATHEVIDENCE_WOLFRAMSCRIPT not a file: {exe}",
            )
        executable = str(candidate)
    else:
        executable = shutil.which("wolframscript") or shutil.which("math")

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
            "live mode requested but no wolframscript/math found",
        )
    if executable:
        return MathematicaRuntime(
            True, executable, leanlink, "live", "wolfram executable discovered"
        )
    return MathematicaRuntime(
        False,
        None,
        leanlink,
        "fixture",
        "Mathematica/wolframscript not found; fixture mode",
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


def _build_wl_script(request: dict[str, Any]) -> str:
    """Build a self-contained WL script that prints JSON certificate fields."""
    lhs = _wl_encode_expr(request["lhs"])
    rhs = _wl_encode_expr(request["rhs"])
    # Exact arithmetic; Together + Numerator/Denominator; Factor list.
    return f"""
SetOptions[$Output, PageWidth -> Infinity];
lhs = {lhs};
rhs = {rhs};
diff = Together[Cancel[lhs - rhs]];
num = Numerator[diff];
den = Denominator[diff];
fac = If[den === 1, {{}}, FactorList[den]];
ExportString[
  <|
    "differenceNumerator" -> ToString[num, InputForm],
    "denominatorFactors" -> Map[ToString[#, InputForm] &, fac],
    "rawDiff" -> ToString[diff, InputForm]
  |>,
  "JSON"
]
"""


def _run_wolfram(
    executable: str,
    script: str,
    tracker: ResourceTracker,
) -> dict[str, Any]:
    """Run Wolfram with fixed argv (no shell)."""
    tracker.check()
    # -code evaluates the script string; argv is a fixed list.
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
    try:
        return json.loads(out)
    except json.JSONDecodeError as exc:
        raise stable_error(
            "malformed_evidence",
            "wolframscript did not return JSON",
            details={"stdoutPreview": out[:500]},
        ) from exc


def _allowlisted_env() -> dict[str, str]:
    """Minimal environment allow-list for Mathematica subprocess."""
    keep = ("PATH", "SYSTEMROOT", "WINDIR", "HOME", "USERPROFILE", "LANG", "LC_ALL")
    env = {k: v for k, v in os.environ.items() if k in keep}
    # Never forward credentials into evidence generation env unless required.
    for key in ("MATHEVIDENCE_WOLFRAMSCRIPT", "MATHEVIDENCE_LEANLINK"):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


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

    expr_size(request["lhs"])
    expr_size(request["rhs"])
    rt = runtime or discover_runtime()

    if rt.mode != "live" or not rt.available or not rt.executable:
        raise stable_error(
            "backend_unavailable",
            "Mathematica backend unavailable; use committed evidence for offline replay",
            details={
                "mode": rt.mode,
                "detail": rt.detail,
                "leanLink": rt.leanlink_path,
            },
        )

    # LeanLink path is reserved for future native bridge; v0 uses wolframscript.
    _ = rt.leanlink_path
    raw = _run_wolfram(rt.executable, _build_wl_script(request), tracker)

    # Convert WL OutputForm strings into a minimal certificate using SymPy IR
    # round-trip only when live backend returns structured JSON we can map.
    # For live mode scaffolding, require the process to emit IR-compatible JSON
    # via a companion paclet later; for now map numerator "0" specially and
    # otherwise surface backend_unsupported for complex forms.
    numer_s = str(raw.get("differenceNumerator", "")).strip()
    if numer_s in {"0", "0.0"}:
        numer_ir: dict[str, Any] = {"tag": "int", "value": "0"}
    else:
        raise stable_error(
            "backend_unsupported",
            "live Mathematica IR decoder scaffold only accepts zero numerator; "
            "commit evidence offline or extend LeanLink paclet mapping",
            details={"numerator": numer_s[:200]},
        )

    dens_raw = raw.get("denominatorFactors") or []
    factors: list[dict[str, Any]] = []
    # Always include original division denominators from the request IR.
    from adapters.common.rational_ir import collect_division_denominators

    for dens in collect_division_denominators(request["lhs"]) + collect_division_denominators(
        request["rhs"]
    ):
        factors.append({"expr": dens, "role": "original_division", "multiplicity": 1})

    certificate: dict[str, Any] = {
        "schemaVersion": "0.1.0",
        "capability": CAPABILITY_ID,
        "capabilityVersion": CAPABILITY_VERSION,
        "requestDigest": digest,
        "differenceNumerator": numer_ir,
        "denominatorFactors": factors,
        "factorization": {
            "method": "wolfram.Together+FactorList",
            "notes": f"live generation; densRaw={dens_raw!r}"[:500],
        },
        "provenance": {
            "backendId": "mathematica",
            "backendVersion": "wolframscript",
            "adapterVersion": ADAPTER_VERSION,
            "leanLinkVersion": rt.leanlink_path,
            "generatedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "deterministic": True,
        },
    }
    store.validate("rational-equality-certificate.schema.json", certificate)
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
            "leanLinkScaffold": True,
        }
    )


def compute_handler(params: dict[str, Any], tracker: ResourceTracker) -> HandlerResult:
    request = params.get("request")
    if not isinstance(request, dict):
        raise stable_error("malformed_evidence", "compute.params.request must be an object")
    cap = request.get("capability", CAPABILITY_ID)
    if cap == "analysis.symbolic_calculus":
        # Live calculus generation deferred to LeanLink paclet; fixture mode /
        # offline committed evidence is the Milestone 5 path.
        raise stable_error(
            "backend_unavailable",
            "Mathematica calculus live generation unavailable; use committed "
            "evidence/examples/calculus_* for offline replay or SymPy adapter",
            details={"capability": cap, "mode": discover_runtime().mode},
        )
    return compute_rational_equality(request, tracker)
