"""Agent API service handlers — operation-level only."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from adapters.common.bundle import find_role_path, verify_bundle_offline, write_bundle
from adapters.common.errors import AdapterError, stable_error
from adapters.common.limits import ResourceLimits, ResourceTracker
from adapters.common.schema_validate import SchemaStore
from agent.api.bundle_store import BundlePathError, BundleStore, ContentAddressCollision
from agent.api.operations import ALLOWED_BACKENDS, PROTOCOL_VERSION, list_operations
from agent.api.receipt import (
    VERIFIED_STATUSES,
    trusted_status_from_receipt,
    verify_certification_record,
)
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
                out_dir,
                request_digest=manifest["requestDigest"],
                bundle_digest=manifest.get("bundleDigest"),
                kind="candidate",
            )
        except ContentAddressCollision as exc:
            return _agent_result(
                operation_id="compute_evidence",
                result_status="rejected",
                claim_class="candidate",
                error={
                    "code": "content_address_collision",
                    "message": str(exc),
                    "category": "evidence",
                },
                unresolved=[
                    {
                        "id": "content_address_collision",
                        "kind": "schema",
                        "message": str(exc),
                    }
                ],
            )
        except BundlePathError:
            # Keep agent-store write; content-addressed commit is best-effort
            # when digest shape is unexpected.
            pass
        bundle_ref = {
            "bundleId": store_id or out_bundle_id,
            "requestDigest": manifest["requestDigest"],
            "bundleDigest": manifest.get("bundleDigest"),
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
    # Candidate Bundles (v0.3) always report computed — never elevate via receipt.
    artifact_kind = manifest.get("artifactKind", "candidate")
    if (
        artifact_kind == "candidate"
        or (
            manifest.get("bundleVersion") == "0.3.0"
            and "candidateBundleDigest" not in manifest
        )
    ):
        status = "computed"
        trust: dict[str, Any] = {
            "previewAccepted": False,
            "claimEstablished": None,
            "certificationVerified": False,
        }
        trust_notes = [
            "Candidate Bundle opened; status is computed until Certification Record verifies.",
        ]
    else:
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
            "bundleId": body.get("bundleId")
            if isinstance(body.get("bundleId"), str)
            else None,
            "requestDigest": manifest.get("requestDigest"),
            "bundleDigest": manifest.get("bundleDigest"),
            "capability": (manifest.get("capability") or {}).get("id"),
            "capabilityVersion": (manifest.get("capability") or {}).get("version"),
        },
        notes=[
            "Opened committed Candidate Bundle; use open_certification for verified status.",
            "claimEstablished / Certified require a Certification Record from kernel replay.",
            *trust_notes,
        ],
        extra={"manifest": manifest, **trust},
    )


def op_open_certification(body: dict[str, Any]) -> dict[str, Any]:
    """Open and verify a Certification Record (returns verified only on full check)."""
    store = SchemaStore(REPO_ROOT / "agent" / "api" / "schemas")
    try:
        store.validate("open-certification.input.schema.json", body)
    except AdapterError as exc:
        return _agent_result(
            operation_id="open_certification",
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
            "open_certification",
            BundlePathError("public Agent API rejects raw path; use bundleId"),
        )
    cert_id = body.get("bundleId") or body.get("certificationId")
    if not isinstance(cert_id, str) or not cert_id:
        return _agent_result(
            operation_id="open_certification",
            result_status="rejected",
            error={
                "code": "malformed_evidence",
                "message": "certificationId / bundleId required",
                "category": "evidence",
            },
        )
    try:
        path = _bundle_store().path_for_bundle_id(cert_id)
    except BundlePathError as exc:
        return _path_error_result("open_certification", exc)
    try:
        verification = verify_certification_record(path)
    except Exception as exc:  # noqa: BLE001
        return _agent_result(
            operation_id="open_certification",
            result_status="rejected",
            error={
                "code": "malformed_evidence",
                "message": str(exc),
                "category": "evidence",
            },
        )
    status = verification.result_status if verification.verified else "tested"
    if not verification.verified and verification.result_status == "computed":
        status = "computed"
    if not verification.verified and verification.result_status in VERIFIED_STATUSES:
        status = "tested"
    return _agent_result(
        operation_id="open_certification",
        result_status=status if verification.verified else status,
        claim_class="soundResult" if verification.claim_established else "candidate",
        bundle_ref={
            "certificationId": cert_id,
            "candidateBundleDigest": verification.candidate_bundle_digest,
            "certificationRecordDigest": verification.certification_record_digest,
            "requestDigest": verification.request_digest,
        },
        notes=[
            "Certification Record verification complete."
            if verification.verified
            else "Certification Record present but not theorem-verified.",
        ],
        extra={
            "certificationVerified": verification.verified,
            "claimEstablished": verification.claim_established
            if verification.verified
            else None,
            "previewAccepted": verification.preview_accepted,
            "assuranceMode": verification.assurance_mode,
            "theoremTypeDigest": verification.theorem_type_digest,
            "proofDeclarationDigest": verification.proof_declaration_digest,
        },
    )


def op_replay_bundle(body: dict[str, Any]) -> dict[str, Any]:
    return _op_verify_bundle_impl(body, operation_id="replay_bundle")


def op_verify_bundle(body: dict[str, Any]) -> dict[str, Any]:
    """Operational Candidate Bundle verification (Wave 2 / ME-RV-024)."""
    return _op_verify_bundle_impl(body, operation_id="verify_bundle")


def _op_verify_bundle_impl(body: dict[str, Any], *, operation_id: str) -> dict[str, Any]:
    store = SchemaStore(REPO_ROOT / "agent" / "api" / "schemas")
    try:
        store.validate("replay-bundle.input.schema.json", body)
    except AdapterError as exc:
        return _agent_result(
            operation_id=operation_id,
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
            operation_id,
            BundlePathError("public Agent API rejects raw path; use bundleId"),
        )
    try:
        path = _bundle_store().resolve_ref(body)
    except BundlePathError as exc:
        return _path_error_result(operation_id, exc)
    try:
        warnings = verify_bundle_offline(path)
    except Exception as exc:  # noqa: BLE001
        return _agent_result(
            operation_id=operation_id,
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
    # Prefer Lean mathevidence-verify-bundle (operational checkBool only; ME-RV-001).
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
                operation_id=operation_id,
                result_status="rejected",
                error={
                    "code": code,
                    "message": stderr or "mathevidence-verify-bundle failed",
                    "category": "evidence",
                },
                unresolved=[
                    {
                        "id": "lean_verify_failed",
                        "kind": "schema",
                        "message": stderr or "verify-bundle failed",
                    }
                ],
                extra={"leanPackaging": lean_packaging, "warnings": warnings},
            )
    except Exception as exc:  # noqa: BLE001
        lean_packaging = {
            "ok": False,
            "error": str(exc),
            "leanExeMissing": True,
        }

    # Strip path fields from public response (ID-only).
    lean_public = {
        k: v
        for k, v in lean_packaging.items()
        if k not in ("bundlePath", "stdout") and not str(k).lower().endswith("path")
    }
    result_status = "checker_accepted"
    if lean_packaging.get("leanExeMissing"):
        result_status = "tested"
    if isinstance(lean_packaging.get("resultStatus"), str):
        rs = lean_packaging["resultStatus"]
        if rs in VERIFIED_STATUSES:
            result_status = "checker_accepted"
        elif rs in ("checker_accepted", "tested", "computed"):
            result_status = rs

    return _agent_result(
        operation_id=operation_id,
        result_status=result_status,
        claim_class="replay",
        bundle_ref={
            "bundleId": body.get("bundleId")
            if isinstance(body.get("bundleId"), str)
            else None,
        },
        notes=[
            "Operational verify_bundle only (native_checked / checker_accepted at most).",
            "Theorem Certified requires kernel_replay + open_certification.",
            *warnings,
        ],
        extra={
            "certificationVerified": False,
            "claimEstablished": None,
            "assuranceMode": "native_checked",
            "leanPackaging": lean_public,
        },
    )


def op_kernel_replay(body: dict[str, Any]) -> dict[str, Any]:
    """Theorem-producing kernel replay (Wave 2 / ME-RV-022 / ME-RV-024)."""
    store = SchemaStore(REPO_ROOT / "agent" / "api" / "schemas")
    try:
        store.validate("kernel-replay.input.schema.json", body)
    except AdapterError as exc:
        return _agent_result(
            operation_id="kernel_replay",
            result_status="rejected",
            error={"code": exc.code, "message": exc.message, "category": "evidence"},
        )
    if "path" in body:
        return _path_error_result(
            "kernel_replay",
            BundlePathError("public Agent API rejects raw path; use bundleId"),
        )
    try:
        path = _bundle_store().resolve_ref(body)
    except BundlePathError as exc:
        return _path_error_result("kernel_replay", exc)

    from adapters.common.errors import AdapterError as _AE
    from adapters.common.kernel_replay import run_kernel_replay

    require_lean = body.get("requireLean", True)
    if not isinstance(require_lean, bool):
        require_lean = True
    decl = body.get("declarationName")
    if not isinstance(decl, str) or not decl:
        decl = "certified_rational_replay"
    try:
        result = run_kernel_replay(
            bundle_dir=path,
            repo_root=REPO_ROOT,
            declaration_name=decl,
            require_lean=require_lean,
        )
    except _AE as exc:
        return _agent_result(
            operation_id="kernel_replay",
            result_status="rejected",
            error={
                "code": exc.code,
                "message": exc.message,
                "category": exc.category.value,
            },
            unresolved=[
                {
                    "id": (exc.details or {}).get("kernelCode", exc.code)
                    if isinstance(exc.details, dict)
                    else exc.code,
                    "kind": "schema",
                    "message": exc.message,
                }
            ],
        )
    except Exception as exc:  # noqa: BLE001
        return _agent_result(
            operation_id="kernel_replay",
            result_status="rejected",
            error={
                "code": "malformed_evidence",
                "message": str(exc),
                "category": "evidence",
            },
        )

    # Commit certification into content-addressed store when present.
    cert_id = result.get("certificationId")
    record_dir = result.get("recordDir")
    if isinstance(record_dir, str) and Path(record_dir).is_dir():
        try:
            _store_path, opaque = _bundle_store().commit_content_addressed(
                Path(record_dir),
                kind="certification",
                verify=True,
            )
            cert_id = opaque
        except Exception:  # noqa: BLE001
            pass

    return _agent_result(
        operation_id="kernel_replay",
        result_status="computed",
        claim_class="soundResult",
        bundle_ref={
            "bundleId": body.get("bundleId")
            if isinstance(body.get("bundleId"), str)
            else None,
            "certificationId": cert_id,
            "candidateBundleDigest": result.get("candidateBundleDigest"),
            "certificationRecordDigest": result.get("certificationRecordDigest"),
            "requestDigest": None,
        },
        notes=[
            "Kernel replay produced a Certification Record.",
            "Call open_certification with certificationId before Certified labeling.",
        ],
        extra={
            "certificationVerified": False,
            "declarationName": result.get("declarationName"),
            "theoremTypeDigest": result.get("theoremTypeDigest"),
            "leanOk": result.get("leanOk"),
            "axioms": result.get("axioms"),
        },
    )


def op_list_certifications_for_request(body: dict[str, Any]) -> dict[str, Any]:
    store = SchemaStore(REPO_ROOT / "agent" / "api" / "schemas")
    try:
        store.validate("list-certifications.input.schema.json", body)
    except AdapterError as exc:
        return _agent_result(
            operation_id="list_certifications_for_request",
            result_status="rejected",
            error={"code": exc.code, "message": exc.message, "category": "evidence"},
        )
    request_digest = body["requestDigest"]
    ids = _bundle_store().list_certifications_for_request(request_digest)
    return _agent_result(
        operation_id="list_certifications_for_request",
        result_status="computed",
        claim_class="discovery",
        extra={
            "requestDigest": request_digest,
            "certificationIds": ids,
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
    outcome = preview.get("outcome") or (
        "mirror_accepted" if preview.get("mirrorSufficient") or preview.get("sufficient") else "rejected"
    )
    if outcome == "mirror_accepted":
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
            "mirrorSufficient": preview.get("mirrorSufficient"),
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
            "Sufficiency/deletion/CEX status from Python checkBool mirrors only (mirror_accepted).",
            "sufficientSetsCertified requires verified Certification Record.",
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
                "Formal family campaign with refutationRate accounting.",
                "bounded_verified / open are not unbounded theorems.",
                "Mirror acceptance sets refutationPreview only; falsified requires Certification Record.",
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
            "Mirror acceptance sets refutationPreview=mirror_accepted; falsified requires Certification Record.",
            "bounded_verified is not a theorem over the unbounded family.",
            "Training episodes never influence acceptance.",
            "authorityStatus=python_checker_mirror for mirror preview.",
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
