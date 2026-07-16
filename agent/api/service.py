"""Agent API service handlers — operation-level only."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from adapters.common.bundle import verify_bundle_offline, write_bundle
from adapters.common.errors import AdapterError, stable_error
from adapters.common.limits import ResourceLimits, ResourceTracker
from adapters.common.schema_validate import SchemaStore
from agent.api.operations import ALLOWED_BACKENDS, PROTOCOL_VERSION, list_operations
from agent.api.registry_query import (
    REPO_ROOT,
    capability_public_summary,
    find_capability,
    load_backends,
    load_capabilities,
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


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = (REPO_ROOT / path).resolve()
    else:
        path = path.resolve()
    return path


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

    if capability_id not in (
        "algebra.rational_equality",
        "algebra.linear_algebra",
        "logic.finite_counterexample",
        "analysis.symbolic_calculus",
    ):
        return _agent_result(
            operation_id="compute_evidence",
            result_status="unsupported",
            error={
                "code": "backend_unsupported",
                "message": f"compute not implemented for {capability_id} in Agent API",
                "category": "backend",
            },
        )

    if capability_id != "algebra.rational_equality" and backend != "sympy":
        return _agent_result(
            operation_id="compute_evidence",
            result_status="unsupported",
            error={
                "code": "backend_unsupported",
                "message": (
                    f"{capability_id} thin Agent compute currently wired for sympy only"
                ),
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
    write_to = body.get("writeBundleTo")
    if isinstance(write_to, str) and write_to:
        out_dir = _resolve_path(write_to)
        manifest = write_bundle(
            out_dir,
            request=request,
            candidate=result["candidate"],
            certificate=result["certificate"],
            result_status="computed",
            claim_class="candidate",
        )
        bundle_ref = {
            "path": str(out_dir),
            "requestDigest": manifest["requestDigest"],
            "capability": capability_id,
            "capabilityVersion": cap["version"],
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
    store.validate("open-bundle.input.schema.json", body)
    path = _resolve_path(body["path"])
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        return _agent_result(
            operation_id="open_bundle",
            result_status="rejected",
            error={
                "code": "malformed_evidence",
                "message": f"missing manifest.json under {path}",
                "category": "evidence",
            },
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    status = manifest.get("resultStatus", "ambiguous")
    # Map to epistemic UI vocabulary; Agent API never invents Certified.
    if status in ("soundness_verified", "witness_verified", "completeness_verified"):
        # Trust only what the committed manifest claims; Studio must still show Lean replay.
        pass
    return _agent_result(
        operation_id="open_bundle",
        result_status=status if isinstance(status, str) else "ambiguous",
        claim_class=manifest.get("claimClass", "candidate"),
        bundle_ref={
            "path": str(path),
            "requestDigest": manifest.get("requestDigest"),
            "capability": (manifest.get("capability") or {}).get("id"),
            "capabilityVersion": (manifest.get("capability") or {}).get("version"),
        },
        notes=[
            "Opened committed bundle; use replay_bundle for digest verification.",
            "Studio Certified label requires Lean kernel replay, not this summary alone.",
        ],
        extra={"manifest": manifest},
    )


def op_replay_bundle(body: dict[str, Any]) -> dict[str, Any]:
    store = SchemaStore(REPO_ROOT / "agent" / "api" / "schemas")
    store.validate("replay-bundle.input.schema.json", body)
    path = _resolve_path(body["path"])
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
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    notes = ["Python offline schema+digest replay succeeded."]
    notes.extend(warnings)
    notes.append("Lean kernel replay remains a separate step.")
    return _agent_result(
        operation_id="replay_bundle",
        result_status="tested",
        claim_class=manifest.get("claimClass", "candidate"),
        bundle_ref={
            "path": str(path),
            "requestDigest": manifest.get("requestDigest"),
            "capability": (manifest.get("capability") or {}).get("id"),
            "capabilityVersion": (manifest.get("capability") or {}).get("version"),
        },
        notes=notes,
        extra={"warnings": warnings, "replayLink": f"mathevidence://replay?path={path}"},
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
    )
    return _agent_result(
        operation_id="prove_sufficient",
        result_status="computed" if preview["sufficient"] else "rejected",
        claim_class="candidate",
        notes=preview["notes"],
        extra={
            "sufficiency": preview,
            "authorityStatus": preview.get("authorityStatus"),
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
