"""Discovery orchestration: spawn adapter → compute → write bundle → verify.

CI-safe default: callers should leave ``MATHEVIDENCE_DISCOVERY`` unset and use
committed evidence / offline replay. This module is the live path used by
``scripts/mathevidence_cli.py discover`` and the Lean tactic when discovery is
explicitly enabled.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adapters.common.bundle import verify_bundle_offline, write_bundle
from adapters.common.canonical import bind_request_digest, verify_request_digest
from adapters.common.errors import AdapterError, stable_error
from adapters.common.limits import ResourceLimits
from adapters.common.rpc_client import RpcClient, default_adapter_argv
from adapters.common.schema_validate import SchemaStore

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class DiscoveryResult:
    backend: str
    request: dict[str, Any]
    candidate: dict[str, Any]
    certificate: dict[str, Any]
    bundle_dir: Path | None
    via_rpc: bool
    warnings: list[str]


def discovery_env_enabled() -> bool:
    v = os.environ.get("MATHEVIDENCE_DISCOVERY", "").strip().lower()
    return v in {"1", "true", "live", "on"}


def _direct_compute(backend: str, request: dict[str, Any]) -> dict[str, Any]:
    """In-process compute (SymPy always; others respect fixture/live gates)."""
    from adapters.common.limits import ResourceTracker
    from adapters.common.schema_validate import SchemaStore as SS

    schemas = SS()
    tracker = ResourceTracker(ResourceLimits.from_policy(request.get("resourcePolicy")))
    if backend == "sympy":
        from adapters.sympy.adapter import compute_rational_equality

        return compute_rational_equality(request, tracker, schemas=schemas).result
    if backend == "mathematica":
        from adapters.mathematica.adapter import compute_rational_equality

        return compute_rational_equality(request, tracker, schemas=schemas).result
    if backend == "sage":
        from adapters.sage.adapter import compute_rational_equality

        return compute_rational_equality(request, tracker, schemas=schemas).result
    raise stable_error("backend_unsupported", f"unknown backend: {backend}")


def _rpc_compute(backend: str, request: dict[str, Any]) -> dict[str, Any]:
    argv = default_adapter_argv(backend, root=ROOT)
    env = os.environ.copy()
    # Discovery spawn must not inherit an accidental live Mathematica/Sage unless
    # the operator already set adapter mode; CI sets fixture explicitly.
    if "MATHEVIDENCE_ADAPTER_MODE" not in env and backend != "sympy":
        env["MATHEVIDENCE_ADAPTER_MODE"] = "fixture"
    limits = ResourceLimits.from_policy(request.get("resourcePolicy"))
    with RpcClient.spawn(argv, cwd=ROOT, env=env, limits=limits) as client:
        client.request("initialize", {"client": "mathevidence.discovery", "version": "0.1.0"})
        support = client.request(
            "checkSupport",
            {"request": request},
        )
        if isinstance(support, dict) and support.get("supported") is False:
            raise stable_error(
                "unsupported_expression",
                support.get("reason", "adapter rejected support"),
                details=support,
            )
        result = client.request("compute", {"request": request})
        if not isinstance(result, dict):
            raise stable_error("malformed_evidence", "compute result must be an object")
        return result


def discover_rational_equality(
    request: dict[str, Any],
    *,
    backend: str = "sympy",
    bundle_dir: Path | None = None,
    use_rpc: bool | None = None,
    schemas: SchemaStore | None = None,
) -> DiscoveryResult:
    """Run discovery for ``algebra.rational_equality``.

    ``use_rpc`` defaults to True when ``MATHEVIDENCE_DISCOVERY_RPC=1``, else
    in-process compute (still CI-safe for SymPy).
    """
    if "requestDigest" not in request or not request.get("requestDigest"):
        request = bind_request_digest(request)
    else:
        verify_request_digest(request)

    if use_rpc is None:
        use_rpc = os.environ.get("MATHEVIDENCE_DISCOVERY_RPC", "").strip().lower() in {
            "1",
            "true",
            "on",
        }

    warnings: list[str] = []
    if use_rpc:
        try:
            out = _rpc_compute(backend, request)
            via_rpc = True
        except AdapterError as exc:
            warnings.append(f"RPC path failed ({exc}); falling back to in-process")
            out = _direct_compute(backend, request)
            via_rpc = False
    else:
        out = _direct_compute(backend, request)
        via_rpc = False

    candidate = out.get("candidate") or {}
    certificate = out.get("certificate") or {}
    if not certificate:
        raise stable_error("malformed_evidence", "compute returned no certificate")

    written: Path | None = None
    if bundle_dir is not None:
        store = schemas or SchemaStore()
        write_bundle(
            Path(bundle_dir),
            request=request,
            candidate=candidate,
            certificate=certificate,
            result_status=out.get("resultStatus", "computed"),
            claim_class=out.get("claimClass", "candidate"),
            schemas=store,
        )
        written = Path(bundle_dir)
        warnings.extend(verify_bundle_offline(written, schemas=store))

    return DiscoveryResult(
        backend=backend,
        request=request,
        candidate=candidate,
        certificate=certificate,
        bundle_dir=written,
        via_rpc=via_rpc,
        warnings=warnings,
    )
