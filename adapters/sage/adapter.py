"""SageMath open backend adapter for algebra.rational_equality.

Same evidence contract as SymPy. When Sage is not installed, the adapter runs in
**fixture mode**: JSON-RPC is available; live `compute` returns
`backend_unavailable`. Committed evidence under `evidence/` remains
offline-replayable without Sage.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
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
        "Same evidence contract as SymPy.",
        "Optional third open backend; fixture mode when Sage is unavailable.",
    ],
)

_SAGE_WORKER = r'''
import json
import sys

from sage.all import QQ, SR, factor  # type: ignore


def from_ir(node, env):
    tag = node["tag"]
    if tag == "var":
        return env[node["name"]]
    if tag == "int":
        return QQ(int(node["value"]))
    if tag == "rat":
        return QQ(int(node["num"])) / QQ(int(node["den"]))
    if tag == "add":
        return from_ir(node["left"], env) + from_ir(node["right"], env)
    if tag == "sub":
        return from_ir(node["left"], env) - from_ir(node["right"], env)
    if tag == "mul":
        return from_ir(node["left"], env) * from_ir(node["right"], env)
    if tag == "neg":
        return -from_ir(node["arg"], env)
    if tag == "pow":
        return from_ir(node["base"], env) ** int(node["exp"])
    if tag == "div":
        return from_ir(node["num"], env) / from_ir(node["den"], env)
    raise ValueError(f"unsupported tag: {tag!r}")


def to_ir(expr):
    expr = SR(expr).expand()
    if expr.is_integer():
        return {"tag": "int", "value": str(int(expr))}
    if expr in env_symbols_rev:
        return {"tag": "var", "name": env_symbols_rev[expr]}
    # Best-effort integer zero check for identity path
    try:
        if expr == 0:
            return {"tag": "int", "value": "0"}
    except Exception:
        pass
    raise ValueError(f"cannot encode sage expression: {expr}")


req = json.load(sys.stdin)
names = [v["name"] for v in req["variables"]]
env = {n: SR.var(n) for n in names}
env_symbols_rev = {v: k for k, v in env.items()}
lhs = from_ir(req["lhs"], env)
rhs = from_ir(req["rhs"], env)
diff = (lhs - rhs).simplify_full()
numer = SR(diff).numerator()
denom = SR(diff).denominator()
numer_ir = {"tag": "int", "value": "0"} if numer == 0 else to_ir(numer)
factors = []
if denom != 1 and denom != 0:
    try:
        for base, mult in list(factor(denom)):
            factors.append({"base": str(base), "multiplicity": int(mult)})
    except Exception:
        factors.append({"base": str(denom), "multiplicity": 1})
try:
    import sage.version as _sv
    sage_ver = str(getattr(_sv, "version", "unknown"))
except Exception:
    sage_ver = "unknown"
json.dump(
    {
        "differenceNumerator": numer_ir,
        "isZeroNumerator": bool(numer == 0),
        "denominatorFactorHints": factors,
        "sageVersion": sage_ver,
    },
    sys.stdout,
)
'''


@dataclass(frozen=True)
class SageRuntime:
    available: bool
    executable: str | None
    mode: str  # "live" | "fixture"
    detail: str


def discover_runtime() -> SageRuntime:
    forced = os.environ.get("MATHEVIDENCE_ADAPTER_MODE", "").strip().lower()
    # Also honor sage-specific override.
    sage_forced = os.environ.get("MATHEVIDENCE_SAGE_MODE", "").strip().lower()
    mode_force = sage_forced or forced

    exe = os.environ.get("MATHEVIDENCE_SAGE")
    if exe:
        candidate = Path(exe)
        if not candidate.is_file() and shutil.which(exe) is None:
            return SageRuntime(
                False,
                None,
                "fixture",
                f"MATHEVIDENCE_SAGE not found: {exe}",
            )
        executable = str(candidate) if candidate.is_file() else str(shutil.which(exe))
    else:
        executable = shutil.which("sage") or shutil.which("sagemath")

    if mode_force == "fixture":
        return SageRuntime(
            False,
            executable,
            "fixture",
            "MATHEVIDENCE_*_MODE=fixture",
        )
    if mode_force == "live" and not executable:
        return SageRuntime(
            False,
            None,
            "fixture",
            "live mode requested but sage executable not found",
        )
    if executable:
        return SageRuntime(True, executable, "live", "sage executable discovered")
    return SageRuntime(
        False,
        None,
        "fixture",
        "SageMath not found; fixture mode (JSON-RPC up, compute unavailable)",
    )


def _allowlisted_env() -> dict[str, str]:
    keep = ("PATH", "SYSTEMROOT", "WINDIR", "HOME", "USERPROFILE", "LANG", "LC_ALL")
    env = {k: v for k, v in os.environ.items() if k in keep}
    if "MATHEVIDENCE_SAGE" in os.environ:
        env["MATHEVIDENCE_SAGE"] = os.environ["MATHEVIDENCE_SAGE"]
    return env


def _run_sage(
    executable: str,
    request: dict[str, Any],
    tracker: ResourceTracker,
) -> dict[str, Any]:
    """Run Sage with fixed argv (no shell interpolation)."""
    tracker.check()
    with tempfile.TemporaryDirectory(prefix="mathevidence-sage-") as tmp:
        worker = Path(tmp) / "worker.py"
        worker.write_text(_SAGE_WORKER, encoding="utf-8")
        # Prefer `sage -python` when available; fall back to `sage -c` is avoided
        # because it encourages shell-like string assembly.
        cmd = [executable, "-python", str(worker)]
        try:
            proc = subprocess.run(
                cmd,
                input=json.dumps(request),
                check=False,
                capture_output=True,
                text=True,
                timeout=max(1, tracker.limits.max_wall_time_ms / 1000.0),
                env=_allowlisted_env(),
            )
        except subprocess.TimeoutExpired as exc:
            raise stable_error("backend_timeout", "sage timed out") from exc
        except OSError as exc:
            raise stable_error(
                "backend_unavailable", f"failed to spawn sage: {exc}"
            ) from exc

    tracker.check()
    if proc.returncode != 0:
        raise stable_error(
            "backend_crash",
            "sage exited non-zero",
            details={"returncode": proc.returncode, "stderr": (proc.stderr or "")[-2000:]},
        )
    out = (proc.stdout or "").strip()
    tracker.ensure_output_size(len(out.encode("utf-8")))
    try:
        return json.loads(out)
    except json.JSONDecodeError as exc:
        raise stable_error(
            "malformed_evidence",
            "sage did not return JSON",
            details={"stdoutPreview": out[:500]},
        ) from exc


def compute_rational_equality(
    request: dict[str, Any],
    tracker: ResourceTracker,
    *,
    runtime: SageRuntime | None = None,
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
            "SageMath backend unavailable; use committed evidence for offline replay",
            details={"mode": rt.mode, "detail": rt.detail},
        )

    raw = _run_sage(rt.executable, request, tracker)
    numer_ir = raw.get("differenceNumerator")
    if not isinstance(numer_ir, dict):
        raise stable_error("malformed_evidence", "sage worker missing differenceNumerator")

    factors: list[dict[str, Any]] = []
    for dens in collect_division_denominators(request["lhs"]) + collect_division_denominators(
        request["rhs"]
    ):
        factors.append({"expr": dens, "role": "original_division", "multiplicity": 1})

    for hint in raw.get("denominatorFactorHints") or []:
        if not isinstance(hint, dict):
            continue
        # Live path may only prove zero-numerator identities in the scaffold worker;
        # non-IR factors are recorded as notes via factorization, not as trusted IR.
        _ = hint

    certificate: dict[str, Any] = {
        "schemaVersion": "0.1.0",
        "capability": CAPABILITY_ID,
        "capabilityVersion": CAPABILITY_VERSION,
        "requestDigest": digest,
        "differenceNumerator": numer_ir,
        "denominatorFactors": factors,
        "factorization": {
            "method": "sage.simplify_full+factor",
            "notes": "Untrusted candidate evidence for Lean checker replay.",
        },
        "provenance": {
            "backendId": "sage",
            "backendVersion": str(raw.get("sageVersion", "unknown")),
            "adapterVersion": ADAPTER_VERSION,
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
                "isZeroNumerator": bool(raw.get("isZeroNumerator")),
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
        {"supported": True, "capability": CAPABILITY_ID, "mode": rt.mode}
    )


def compute_handler(params: dict[str, Any], tracker: ResourceTracker) -> HandlerResult:
    request = params.get("request")
    if not isinstance(request, dict):
        raise stable_error("malformed_evidence", "compute.params.request must be an object")
    return compute_rational_equality(request, tracker)
