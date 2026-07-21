"""Agent API service handlers — operation-level only."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from adapters.common.bundle import find_role_path, verify_bundle_offline, write_bundle
from adapters.common.errors import AdapterError, stable_error
from adapters.common.limits import ResourceLimits, ResourceTracker
from adapters.common.schema_validate import SchemaStore
from agent.api.bundle_store import BundlePathError, BundleStore
from agent.api.operations import ALLOWED_BACKENDS, PROTOCOL_VERSION, list_operations
from agent.api.receipt import VERIFIED_STATUSES, trusted_status_from_receipt
from agent.api.registry_query import (
    REPO_ROOT,
    capability_public_summary,
    find_capability,
    load_backends,
    load_capabilities,
    registry_allows_compute,
)


def _agent_result(
    *,
    operation_id: str,
    result_status: str,
    claim_class: str = "discovery",
    unresolved: list[dict[str, Any]] | None = None,
    bundle_ref: dict[str, Any] | None = None,
    requested_claim: str | None = None,
    error: dict[str, Any] | None = None,
    resource_usage: dict[str, Any] | None = None,
    notes: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "operationId": operation_id,
        "protocolVersion": PROTOCOL_VERSION,
        "resultStatus": result_status,
        "claimClass": claim_class,
        "unresolvedObligations": unresolved or [],
        "bundleRef": bundle_ref,
    }
    if requested_claim is not None:
        out["requestedClaim"] = requested_claim
    if error is not None:
        out["error"] = error
    if resource_usage is not None:
        out["resourceUsage"] = resource_usage
    if notes:
        out["notes"] = notes
    if extra:
        out.update(extra)
    return out


def _bundle_store() -> BundleStore:
    return BundleStore.default(REPO_ROOT)


def _path_error_result(operation_id: str, exc: Exception) -> dict[str, Any]:
    return _agent_result(
        operation_id=operation_id,
        result_status="rejected",
        error={
            "code": "bundle_path_forbidden",
            "message": str(exc),
            "category": "evidence",
        },
        unresolved=[
            {
                "id": "bundle_path_forbidden",
                "kind": "schema",
                "message": str(exc),
            }
        ],
    )


def _read_checker_receipt(path: Path) -> dict[str, Any] | None:
    for stem in ("checker-receipt", "receipt"):
        receipt_path = find_role_path(path, stem)
        if receipt_path is not None:
            data = json.loads(receipt_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError(f"{receipt_path.name} must contain a JSON object")
            return data
    return None


def _safe_manifest_status(
    manifest: dict[str, Any],
    receipt_payload: dict[str, Any] | None,
    *,
    bundle_dir: Path | None = None,
) -> tuple[str, dict[str, Any], list[str]]:
    """Return status fields without trusting manifest-only verified claims.

    ``claimEstablished`` and verified ``previewAccepted`` require a receipt whose
    content digests bind to on-disk certificate bytes when ``bundle_dir`` is set.
    """
    manifest_status = manifest.get("resultStatus")
    status = manifest_status if isinstance(manifest_status, str) else "ambiguous"
    trust: dict[str, Any] = {
        "previewAccepted": False,
        "claimEstablished": None,
    }
    notes: list[str] = []
    receipt = trusted_status_from_receipt(
        receipt_payload, manifest, bundle_dir=bundle_dir
    )
    if receipt is not None:
        # Verified statuses are only surfaced when content digests bind.
        if (
            receipt.result_status in VERIFIED_STATUSES
            and not receipt.content_digests_verified
        ):
            notes.append(
                "Checker receipt present but content digests were not verified; "
                "Agent reports tested/computed, not claimEstablished."
            )
            trust["previewAccepted"] = False
            trust["claimEstablished"] = None
            trust["receipt"] = {
                "requestDigest": receipt.request_digest,
                "bundleDigest": receipt.bundle_digest,
                "theoremDigest": receipt.theorem_digest,
                "resultStatus": receipt.result_status,
                "contentDigestsVerified": False,
            }
            return "tested", trust, notes
        trust["previewAccepted"] = receipt.preview_accepted
        trust["claimEstablished"] = (
            receipt.claim_established if receipt.content_digests_verified else None
        )
        trust["receipt"] = {
            "requestDigest": receipt.request_digest,
            "bundleDigest": receipt.bundle_digest,
            "theoremDigest": receipt.theorem_digest,
            "resultStatus": receipt.result_status,
            "contentDigestsVerified": receipt.content_digests_verified,
            "certificateContentDigest": receipt.certificate_content_digest,
        }
        if receipt.content_digests_verified:
            return receipt.result_status, trust, notes
        return "tested", trust, notes
    if status in VERIFIED_STATUSES:
        notes.append(
            "Manifest advertises a verified status, but no checker receipt was present; "
            "Agent API reports computed with claimEstablished=null."
        )
        status = "computed"
    return status, trust, notes


def health() -> dict[str, Any]:
    return {"status": "ok", "protocolVersion": PROTOCOL_VERSION}


def op_list_operations() -> dict[str, Any]:
    return {"protocolVersion": PROTOCOL_VERSION, "operations": list_operations()}


def op_list_capabilities(
    *, status: str | None = None, domain: str | None = None
) -> dict[str, Any]:
    caps = []
    for cap in load_capabilities():
        if status and cap.get("status") != status:
            continue
        if domain and cap.get("domain") != domain:
            continue
        caps.append(capability_public_summary(cap))
    return {
        "operationId": "list_capabilities",
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": caps,
    }


def op_check_support(body: dict[str, Any]) -> dict[str, Any]:
    store = SchemaStore(REPO_ROOT / "agent" / "api" / "schemas")
    store.validate("check-support.input.schema.json", body)

    capability_id = body["capability"]
    cap = find_capability(capability_id)
    if cap is None:
        return _agent_result(
            operation_id="check_support",
            result_status="unsupported",
            error={
                "code": "backend_unsupported",
                "message": f"unknown capability: {capability_id}",
                "category": "backend",
            },
        )

    version = body.get("capabilityVersion")
    if isinstance(version, str) and version != cap["version"]:
        return _agent_result(
            operation_id="check_support",
            result_status="unsupported",
            error={
                "code": "schema_version_unsupported",
                "message": f"capability version {version} != {cap['version']}",
                "category": "semantic",
            },
            extra={"capability": capability_public_summary(cap)},
        )

    requested = body.get("requestedClaim")
    if isinstance(requested, str) and requested not in cap["claimClasses"]:
        return _agent_result(
            operation_id="check_support",
            result_status="unsupported",
            requested_claim=requested,
            error={
                "code": "claim_strength_unavailable",
                "message": f"claim {requested!r} not in {cap['claimClasses']}",
                "category": "semantic",
            },
        )

    backend_id = body.get("backend")
    backends = load_backends()
    if isinstance(backend_id, str):
        if backend_id not in ALLOWED_BACKENDS or backend_id not in backends:
            return _agent_result(
                operation_id="check_support",
                result_status="unsupported",
                error={
                    "code": "backend_unsupported",
                    "message": f"backend not allowed: {backend_id}",
                    "category": "backend",
                },
            )
        be = backends[backend_id]
        supported_ids = {c["id"] for c in be.get("supportedCapabilities", [])}
        if capability_id not in supported_ids:
            return _agent_result(
                operation_id="check_support",
                result_status="unsupported",
                error={
                    "code": "backend_unsupported",
                    "message": f"backend {backend_id} does not declare {capability_id}",
                    "category": "backend",
                },
            )

    notes = []
    if not cap.get("supportClaims", {}).get("conformanceVerified"):
        notes.append("Capability declared but not conformance-verified yet.")

    return _agent_result(
        operation_id="check_support",
        result_status="computed",
        claim_class="discovery",
        requested_claim=requested if isinstance(requested, str) else None,
        notes=notes,
        extra={
            "supported": True,
            "capability": capability_public_summary(cap),
        },
    )


def _invoke_adapter_compute(backend: str, request: dict[str, Any]) -> dict[str, Any]:
    tracker = ResourceTracker(ResourceLimits())
    if backend == "sympy":
        from adapters.sympy.adapter import compute_handler

        return compute_handler({"request": request}, tracker).result
    if backend == "mathematica":
        from adapters.mathematica.adapter import compute_handler

        return compute_handler({"request": request}, tracker).result
    if backend == "sage":
        from adapters.sage.adapter import compute_handler

        return compute_handler({"request": request}, tracker).result
    raise stable_error("backend_unsupported", f"backend not allowed: {backend}")


def op_compute_evidence(body: dict[str, Any]) -> dict[str, Any]:
    store = SchemaStore(REPO_ROOT / "agent" / "api" / "schemas")
    store.validate("compute-evidence.input.schema.json", body)

    capability_id = body["capability"]
    backend = body["backend"]
    request = body["request"]
    write_to = body.get("writeBundleTo")
    bundle_id = body.get("bundleId")
    out_dir: Path | None = None
    out_bundle_id: str | None = None
    if (isinstance(write_to, str) and write_to) or (isinstance(bundle_id, str) and bundle_id):
        try:
            out_dir, out_bundle_id = _bundle_store().resolve_write_target(
                path=write_to if isinstance(write_to, str) and write_to else None,
                bundle_id=bundle_id if isinstance(bundle_id, str) and bundle_id else None,
            )
        except BundlePathError as exc:
            return _path_error_result("compute_evidence", exc)

    if backend not in ALLOWED_BACKENDS:
        return _agent_result(
            operation_id="compute_evidence",
            result_status="unsupported",
            error={
                "code": "backend_unsupported",
                "message": f"backend not allowed: {backend}",
                "category": "backend",
            },
        )

    cap = find_capability(capability_id)
    if cap is None:
        return _agent_result(
            operation_id="compute_evidence",
            result_status="unsupported",
            error={
                "code": "backend_unsupported",
                "message": f"unknown capability: {capability_id}",
                "category": "backend",
            },
        )

    allowed, reason = registry_allows_compute(capability_id, backend)
    if not allowed:
        return _agent_result(
            operation_id="compute_evidence",
            result_status="unsupported",
            error={
                "code": "backend_unsupported",
                "message": reason,
                "category": "backend",
            },
        )

    try:
        result = _invoke_adapter_compute(backend, request)
    except AdapterError as exc:
        status = "unsupported" if "unsupported" in exc.code else "rejected"
        if exc.code == "backend_unavailable":
            status = "rejected"
        return _agent_result(
            operation_id="compute_evidence",
            result_status=status,
            claim_class="candidate",
            requested_claim=request.get("requestedClaim")
            if isinstance(request, dict)
            else None,
            error={
                "code": exc.code,
                "message": exc.message,
                "category": exc.category.value
                if hasattr(exc.category, "value")
                else str(exc.category),
                "details": exc.details,
            },
            unresolved=[
                {
                    "id": exc.code,
                    "kind": "backend_unavailable"
                    if exc.code == "backend_unavailable"
                    else "other",
                    "message": exc.message,
                }
            ],
        )

    bundle_ref = None
    if out_dir is not None:
        bundle_request = result.get("request") if isinstance(result.get("request"), dict) else request
        if isinstance(bundle_request, dict) and "requestDigest" not in bundle_request:
            from adapters.common.canonical import bind_request_digest

            bundle_request = bind_request_digest(bundle_request)
        manifest = write_bundle(
            out_dir,
            request=bundle_request,
            candidate=result["candidate"],
            certificate=result["certificate"],
            result_status="computed",
            claim_class="candidate",
        )
        store = _bundle_store()
        store_path = out_dir
        store_id = out_bundle_id
        try:
            store_path, store_id = store.commit_content_addressed(
                out_dir, request_digest=manifest["requestDigest"]
            )
        except BundlePathError:
            # Keep agent-store write; content-addressed commit is best-effort
            # when digest shape is unexpected.
            pass
        bundle_ref = {
            "path": str(store_path),
            "bundleId": store_id or out_bundle_id,
            "requestDigest": manifest["requestDigest"],
            "capability": capability_id,
            "capabilityVersion": cap["version"],
            "contentAddressed": store_id is not None
            and str(store_id).startswith("sha256_"),
        }

    dens = result.get("certificate", {}).get("denominatorFactors", [])
    unresolved = [
        {
            "id": f"nonzero_{i}",
            "kind": "side_condition",
            "message": "Denominator factor must be proven nonzero in Lean",
            "expr": json.dumps(f.get("expr"), separators=(",", ":")),
        }
        for i, f in enumerate(dens)
        if isinstance(f, dict)
    ]
    for sc in result.get("certificate", {}).get("sideConditions") or []:
        unresolved.append(
            {
                "id": str(sc),
                "kind": "side_condition",
                "message": f"Side condition from adapter: {sc}",
            }
        )
    for i, cond in enumerate(result.get("certificate", {}).get("domainConditions") or []):
        unresolved.append(
            {
                "id": f"domain_{i}",
                "kind": "side_condition",
                "message": "Domain/singularity condition must remain explicit (nonzero)",
                "expr": json.dumps(cond, separators=(",", ":")),
            }
        )

    return _agent_result(
        operation_id="compute_evidence",
        result_status="computed",
        claim_class="candidate",
        requested_claim=request.get("requestedClaim")
        if isinstance(request, dict)
        else None,
        unresolved=unresolved,
        bundle_ref=bundle_ref
        or {
            "requestDigest": result.get("requestDigest"),
            "capability": capability_id,
            "capabilityVersion": cap["version"],
        },
        notes=[
            "Adapter output is untrusted.",
            "Lean checker required before any Certified / soundness_verified label.",
        ],
        extra={
            "candidate": result.get("candidate"),
            "certificate": result.get("certificate"),
            "backend": backend,
        },
    )


def op_open_bundle(body: dict[str, Any]) -> dict[str, Any]:
    store = SchemaStore(REPO_ROOT / "agent" / "api" / "schemas")
    try:
        store.validate("open-bundle.input.schema.json", body)
    except AdapterError as exc:
        return _agent_result(
            operation_id="open_bundle",
            result_status="rejected",
            error={
                "code": "bundle_path_forbidden"
                if "path" in str(body)
                else exc.code,
                "message": exc.message,
                "category": "evidence",
            },
            unresolved=[
                {
                    "id": "bundle_path_forbidden",
                    "kind": "schema",
                    "message": "public Agent API accepts bundleId only; raw path rejected",
                }
            ],
        )
    if "path" in body:
        return _path_error_result(
            "open_bundle",
            BundlePathError("public Agent API rejects raw path; use bundleId"),
        )
    try:
        path = _bundle_store().resolve_ref(body)
    except BundlePathError as exc:
        return _path_error_result("open_bundle", exc)
    manifest_path = find_role_path(path, "manifest")
    if manifest_path is None:
        return _agent_result(
            operation_id="open_bundle",
            result_status="rejected",
            error={
                "code": "malformed_evidence",
                "message": f"missing manifest.cjson/manifest.json under {path}",
                "category": "evidence",
            },
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    try:
        status, trust, trust_notes = _safe_manifest_status(
            manifest, _read_checker_receipt(path), bundle_dir=path
        )
    except Exception as exc:  # noqa: BLE001
        return _agent_result(
            operation_id="open_bundle",
            result_status="rejected",
            error={
                "code": "malformed_evidence",
                "message": str(exc),
                "category": "evidence",
            },
        )
    return _agent_result(
        operation_id="open_bundle",
        result_status=status,
        claim_class=manifest.get("claimClass", "candidate"),
        bundle_ref={
            "path": str(path),
            "bundleId": body.get("bundleId") if isinstance(body.get("bundleId"), str) else None,
            "requestDigest": manifest.get("requestDigest"),
            "capability": (manifest.get("capability") or {}).get("id"),
            "capabilityVersion": (manifest.get("capability") or {}).get("version"),
        },
        notes=[
            "Opened committed bundle; use replay_bundle for full digest verification.",
            "claimEstablished requires a checker receipt with verified content digests.",
            "Studio Certified label requires Lean kernel replay, not this summary alone.",
            *trust_notes,
        ],
        extra={"manifest": manifest, **trust},
    )


def op_replay_bundle(body: dict[str, Any]) -> dict[str, Any]:
    store = SchemaStore(REPO_ROOT / "agent" / "api" / "schemas")
    try:
        store.validate("replay-bundle.input.schema.json", body)
    except AdapterError as exc:
        return _agent_result(
            operation_id="replay_bundle",
            result_status="rejected",
            error={
                "code": "bundle_path_forbidden"
                if "path" in str(body)
                else exc.code,
                "message": exc.message,
                "category": "evidence",
            },
        )
    if "path" in body:
        return _path_error_result(
            "replay_bundle",
            BundlePathError("public Agent API rejects raw path; use bundleId"),
        )
    try:
        path = _bundle_store().resolve_ref(body)
    except BundlePathError as exc:
        return _path_error_result("replay_bundle", exc)
    try:
        warnings = verify_bundle_offline(path)
    except Exception as exc:  # noqa: BLE001
        return _agent_result(
            operation_id="replay_bundle",
            result_status="rejected",
            error={
                "code": "malformed_evidence",
                "message": str(exc),
                "category": "evidence",
            },
            unresolved=[
                {
                    "id": "replay_failed",
                    "kind": "schema",
                    "message": str(exc),
                }
            ],
        )
    # Prefer Lean mathevidence-replay authority (digest + checker + goal match).
    lean_packaging: dict[str, Any] = {}
    try:
        from adapters.common.replay import run_lean_replay

        lean_packaging = run_lean_replay(
            bundle_dir=path,
            repo_root=REPO_ROOT,
            bundle_id=body.get("bundleId")
            if isinstance(body.get("bundleId"), str)
            else None,
        )
        if not lean_packaging.get("ok", False):
            stderr = str(lean_packaging.get("stderr") or "")
            code = "content_digest_mismatch"
            if "goal_mismatch" in stderr:
                code = "goal_mismatch"
            elif "certificate_rejected" in stderr:
                code = "certificate_rejected"
            elif "request_digest_mismatch" in stderr:
                code = "request_digest_mismatch"
            elif "certificate_decode_failed" in stderr:
                code = "certificate_decode_failed"
            return _agent_result(
                operation_id="replay_bundle",
                result_status="rejected",
                error={
                    "code": code,
                    "message": stderr or "mathevidence-replay failed",
                    "category": "evidence",
                },
            )
        warnings = list(warnings) + list(lean_packaging.get("warnings") or [])
    except Exception as exc:  # noqa: BLE001
        return _agent_result(
            operation_id="replay_bundle",
            result_status="rejected",
            error={
                "code": "malformed_evidence",
                "message": str(exc),
                "category": "evidence",
            },
        )
    manifest_path = find_role_path(path, "manifest")
    if manifest_path is None:
        return _agent_result(
            operation_id="replay_bundle",
            result_status="rejected",
            error={
                "code": "malformed_evidence",
                "message": f"missing manifest under {path}",
                "category": "evidence",
            },
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # Lean-written receipt (if any) takes precedence for trust status.
    receipt_payload = _read_checker_receipt(path)
    if receipt_payload is None and isinstance(lean_packaging.get("envelope"), dict):
        env = lean_packaging["envelope"]
        if env.get("claimEstablished") is not None:
            receipt_payload = env
    try:
        status, trust, trust_notes = _safe_manifest_status(
            manifest, receipt_payload, bundle_dir=path
        )
    except Exception as exc:  # noqa: BLE001
        return _agent_result(
            operation_id="replay_bundle",
            result_status="rejected",
            error={
                "code": "malformed_evidence",
                "message": str(exc),
                "category": "evidence",
            },
        )
    notes = ["Python offline schema+digest replay succeeded."]
    notes.extend(warnings)
    notes.extend(trust_notes)
    authority = lean_packaging.get("authority", "python_preview")
    if authority == "lean_exe" and lean_packaging.get("claimEstablished"):
        notes.append(
            "Lean mathevidence-replay established claimEstablished (checker+goal authority)."
        )
        # Prefer Lean-reported verified status when content digests bind.
        lean_status = lean_packaging.get("resultStatus")
        if (
            isinstance(lean_status, str)
            and lean_status in VERIFIED_STATUSES
            and trust.get("claimEstablished") is not None
        ):
            status = lean_status
            trust["claimEstablished"] = lean_packaging.get("claimEstablished")
            trust["previewAccepted"] = True
    else:
        notes.append(
            "Python packaging path is preview/tested only; Lean exe missing or non-verified."
        )
    result_status = status if trust.get("claimEstablished") is not None else "tested"
    if trust.get("claimEstablished") is not None and status in VERIFIED_STATUSES:
        result_status = status
    return _agent_result(
        operation_id="replay_bundle",
        result_status=result_status,
        claim_class=manifest.get("claimClass", "candidate"),
        bundle_ref={
            "path": str(path),
            "bundleId": body.get("bundleId") if isinstance(body.get("bundleId"), str) else None,
            "requestDigest": manifest.get("requestDigest"),
            "capability": (manifest.get("capability") or {}).get("id"),
            "capabilityVersion": (manifest.get("capability") or {}).get("version"),
        },
        notes=notes,
        extra={
            "warnings": warnings,
            "contentDigestsVerified": True,
            "replayAuthority": authority,
            "replayLink": f"mathevidence://replay?bundle={path}",
            **trust,
        },
    )


def _maybe_capture(kind: str, payload: dict[str, Any], body: dict[str, Any]) -> dict[str, Any] | None:
    if not body.get("captureEpisode"):
        return None
    from foundry.capture import capture_episode

    return capture_episode(
        kind=kind,
        payload=payload,
        capability=body.get("request", {}).get("capability")
        if isinstance(body.get("request"), dict)
        else None,
        notes="Captured after orchestration; never influences acceptance.",
    )


def op_propose_conditions(body: dict[str, Any]) -> dict[str, Any]:
    from agent.hypothesis import propose_conditions_from_request

    request = body.get("request")
    if not isinstance(request, dict):
        return _agent_result(
            operation_id="propose_conditions",
            result_status="rejected",
            error={
                "code": "malformed_evidence",
                "message": "request object required",
                "category": "evidence",
            },
        )
    proposed = propose_conditions_from_request(request)
    episode = _maybe_capture("hypothesis_lattice", {"proposed": proposed}, body)
    return _agent_result(
        operation_id="propose_conditions",
        result_status="computed",
        claim_class="candidate",
        notes=[
            "Untrusted proposals; Lean prove_sufficient required.",
            "Minimality never asserted.",
        ],
        extra={"proposedConditions": proposed, "trainingEpisode": episode},
    )


def op_prove_sufficient(body: dict[str, Any]) -> dict[str, Any]:
    from agent.hypothesis import prove_sufficient_python

    request = body.get("request")
    conditions = body.get("conditions") or []
    if not isinstance(request, dict):
        return _agent_result(
            operation_id="prove_sufficient",
            result_status="rejected",
            error={
                "code": "malformed_evidence",
                "message": "request object required",
                "category": "evidence",
            },
        )
    preview = prove_sufficient_python(
        request,
        conditions if isinstance(conditions, list) else [],
        bundle_ref=body.get("bundleRef") if isinstance(body.get("bundleRef"), dict) else None,
        receipt_ref=body.get("receiptRef") if isinstance(body.get("receiptRef"), dict) else None,
        axiom_report_id=body.get("axiomReportId") if isinstance(body.get("axiomReportId"), str) else None,
    )
    outcome = preview.get("outcome") or ("proved" if preview.get("sufficient") else "failed")
    if outcome == "proved":
        status = "computed"
    elif outcome == "unknown":
        status = "ambiguous"
    else:
        status = "rejected"
    return _agent_result(
        operation_id="prove_sufficient",
        result_status=status,
        claim_class="candidate",
        notes=preview["notes"],
        extra={
            "sufficiency": preview,
            "outcome": outcome,
            "authorityStatus": preview.get("authorityStatus"),
            "evidence": preview.get("evidence"),
        },
    )


def op_delete_hypothesis(body: dict[str, Any]) -> dict[str, Any]:
    from agent.hypothesis import delete_hypothesis_python

    request = body.get("request")
    conditions = body.get("conditions") or []
    target = body.get("targetConditionId")
    if not isinstance(request, dict) or not isinstance(target, str):
        return _agent_result(
            operation_id="delete_hypothesis",
            result_status="rejected",
            error={
                "code": "malformed_evidence",
                "message": "request and targetConditionId required",
                "category": "evidence",
            },
        )
    result = delete_hypothesis_python(
        request,
        conditions if isinstance(conditions, list) else [],
        target,
    )
    episode = _maybe_capture("hypothesis_deletion", result, body)
    status = "computed" if result["result"] in ("redundant", "not_redundant") else "rejected"
    return _agent_result(
        operation_id="delete_hypothesis",
        result_status=status,
        claim_class="candidate",
        notes=result.get("notes") or [],
        extra={
            "deletion": result,
            "authorityStatus": result.get("authorityStatus"),
            "trainingEpisode": episode,
        },
    )


def op_find_counterexample(body: dict[str, Any]) -> dict[str, Any]:
    from adapters.common.hypothesis_util import find_counterexample

    request = body.get("request")
    if not isinstance(request, dict):
        return _agent_result(
            operation_id="find_counterexample",
            result_status="rejected",
            error={
                "code": "malformed_evidence",
                "message": "request object required",
                "category": "evidence",
            },
        )
    cert = find_counterexample(request)
    if cert is None:
        return _agent_result(
            operation_id="find_counterexample",
            result_status="rejected",
            notes=["No counterexample within bound; not evidence of truth."],
        )
    return _agent_result(
        operation_id="find_counterexample",
        result_status="computed",
        claim_class="witness",
        notes=["Untrusted witness; call verify_counterexample / Lean checker."],
        extra={"certificate": cert},
    )


def op_verify_counterexample(body: dict[str, Any]) -> dict[str, Any]:
    from agent.hypothesis import verify_counterexample_python

    request = body.get("request")
    certificate = body.get("certificate")
    if not isinstance(request, dict) or not isinstance(certificate, dict):
        return _agent_result(
            operation_id="verify_counterexample",
            result_status="rejected",
            error={
                "code": "malformed_evidence",
                "message": "request and certificate required",
                "category": "evidence",
            },
        )
    verified = verify_counterexample_python(request, certificate)
    ok = bool(verified["verified"])
    episode = _maybe_capture(
        "certified_refutation" if ok else "hypothesis_deletion",
        {"ok": ok, "certificate": certificate},
        body,
    )
    return _agent_result(
        operation_id="verify_counterexample",
        result_status="computed" if ok else "rejected",
        claim_class="refutation" if ok else "candidate",
        notes=verified["notes"],
        extra={
            "verified": ok,
            "authorityStatus": verified.get("authorityStatus"),
            "trainingEpisode": episode,
        },
    )


def op_build_condition_lattice(body: dict[str, Any]) -> dict[str, Any]:
    from agent.hypothesis import build_condition_lattice

    request = body.get("request")
    if not isinstance(request, dict):
        return _agent_result(
            operation_id="build_condition_lattice",
            result_status="rejected",
            error={
                "code": "malformed_evidence",
                "message": "request object required",
                "category": "evidence",
            },
        )
    artifact_id = body.get("artifactId") or "lattice_agent"
    weaker = body.get("weakerVariantRequest")
    related = body.get("relatedConditionIds")
    lattice = build_condition_lattice(
        artifact_id=str(artifact_id),
        request=request,
        original=body.get("original") if isinstance(body.get("original"), list) else None,
        proposed=body.get("conditions") if isinstance(body.get("conditions"), list) else None,
        weaker_variant_request=weaker if isinstance(weaker, dict) else None,
        related_condition_ids=related if isinstance(related, list) else None,
    )
    episode = _maybe_capture("hypothesis_lattice", lattice, body)
    return _agent_result(
        operation_id="build_condition_lattice",
        result_status="computed",
        claim_class="candidate",
        notes=[
            "Condition lattice artifact ready for expert review.",
            "Sufficiency/deletion/CEX status from Lean checkBool mirrors only.",
            "claimsMinimal is false unless necessity proofs cover recommendations.",
        ],
        extra={
            "lattice": lattice,
            "authorityStatus": lattice.get("authorityStatus"),
            "trainingEpisode": episode,
        },
    )


def op_conjecture_campaign(body: dict[str, Any]) -> dict[str, Any]:
    from adapters.common.hypothesis_util import find_counterexample
    from agent.conjecture import (
        certify_refutation,
        mark_bounded_verified,
        new_episode,
        run_family_campaign,
        to_candidate,
    )

    # Multi-candidate formal family campaign with precision accounting.
    if isinstance(body.get("candidates"), list):
        family_id = str(body.get("familyId") or "finite.default")
        campaign = run_family_campaign(
            family_id=family_id, candidates=body["candidates"]
        )
        episode = _maybe_capture("conjecture_campaign", campaign, body)
        return _agent_result(
            operation_id="conjecture_campaign",
            result_status="computed",
            claim_class="candidate",
            notes=[
                "Formal family campaign with precision accounting.",
                "bounded_verified / open are not unbounded theorems.",
                "Falsification status from Lean checkBool mirrors only.",
            ],
            extra={
                "campaign": campaign,
                "precisionAccounting": campaign["precisionAccounting"],
                "authorityStatus": campaign.get("authorityStatus"),
                "trainingEpisode": episode,
            },
        )

    request = body.get("request")
    if not isinstance(request, dict):
        return _agent_result(
            operation_id="conjecture_campaign",
            result_status="rejected",
            error={
                "code": "malformed_evidence",
                "message": "request object or candidates[] required",
                "category": "evidence",
            },
        )
    pred = (request.get("predicate") or {}).get("pred")
    if not isinstance(pred, dict):
        return _agent_result(
            operation_id="conjecture_campaign",
            result_status="rejected",
            error={
                "code": "malformed_evidence",
                "message": "request.predicate.pred required",
                "category": "evidence",
            },
        )
    family_id = body.get("familyId") or "finite.default"
    ep = to_candidate(new_episode(family_id=str(family_id), pred=pred))
    cert = find_counterexample(request)
    if cert is not None:
        ep = certify_refutation(
            ep,
            request=request,
            certificate=cert,
            refutation_id=body.get("refutationId") or "cex_auto",
        )
    else:
        bound = int(body.get("searchBound") or 0)
        ep = mark_bounded_verified(ep, bound)
    episode = _maybe_capture("conjecture_campaign", ep, body)
    return _agent_result(
        operation_id="conjecture_campaign",
        result_status="computed",
        claim_class="refutation" if ep.get("state") == "falsified" else "candidate",
        notes=[
            "Candidates vs certified refutations only.",
            "bounded_verified is not a theorem over the unbounded family.",
            "Training episodes never influence acceptance.",
            "authorityStatus=lean_checker_mirror for falsification.",
        ],
        extra={
            "episode": ep,
            "certificate": cert,
            "authorityStatus": ep.get("authorityStatus"),
            "trainingEpisode": episode,
        },
    )


def op_inspect_bundle(body: dict[str, Any]) -> dict[str, Any]:
    """Spec 15 `inspect_bundle` — same epistemic rules as open_bundle."""
    out = op_open_bundle(body)
    out["operationId"] = "inspect_bundle"
    return out


def op_build_proof_plan(body: dict[str, Any]) -> dict[str, Any]:
    store = SchemaStore(REPO_ROOT / "agent" / "api" / "schemas")
    try:
        store.validate("ttp.input.schema.json", body)
    except AdapterError as exc:
        return _agent_result(
            operation_id="build_proof_plan",
            result_status="rejected",
            error={"code": exc.code, "message": exc.message, "category": "evidence"},
        )
    return _agent_result(
        operation_id="build_proof_plan",
        result_status="unsupported",
        error={
            "code": "operation_unsupported",
            "message": (
                "build_proof_plan requires Lean TraceToPlan; "
                "Python Agent does not fabricate proof plans"
            ),
            "category": "system",
        },
        notes=[
            "Honestly unsupported on Agent without a Lean ProofPlan artifact.",
            "Never upgrades epistemic status.",
        ],
    )


def op_reconstruct_plan(body: dict[str, Any]) -> dict[str, Any]:
    store = SchemaStore(REPO_ROOT / "agent" / "api" / "schemas")
    try:
        store.validate("ttp.input.schema.json", body)
    except AdapterError as exc:
        return _agent_result(
            operation_id="reconstruct_plan",
            result_status="rejected",
            error={"code": exc.code, "message": exc.message, "category": "evidence"},
        )
    return _agent_result(
        operation_id="reconstruct_plan",
        result_status="unsupported",
        error={
            "code": "operation_unsupported",
            "message": (
                "reconstruct_plan requires a content-bound Lean receipt; "
                "hint-only reconstruct is rejected"
            ),
            "category": "system",
        },
        notes=[
            "Honestly unsupported on Agent without a checker receipt.",
            "Hint-only reconstruct must not advance plan state.",
        ],
    )
