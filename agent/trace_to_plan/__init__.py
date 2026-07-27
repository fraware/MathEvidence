"""Trace-to-Plan engine (Product 05) — Agent-side, not TCB.

Converts untrusted computational traces / hints into a proof-plan DAG.
Only reconstructible step kinds may advance formal proof status.
``reconstructible_computation`` advances only when reconstruction carries a
verified Certification Record gate (see ``reconstruct_from_receipt``).
``direct_proof_step`` advances only with theorem digest / env / axiom evidence.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agent.epistemic_states import PRODUCT_STATES

__all__ = [
    "ADVANCEABLE_KINDS",
    "STEP_KINDS",
    "check_plan_soundness",
    "classify_trace_item",
    "direct_proof_evidence_ok",
    "hints_never_advance",
    "plan_from_traces",
    "reconstruct_from_receipt",
    "reconstruction_has_verified_receipt",
    "validate_plan_invariants",
]

STEP_KINDS = (
    "direct_proof_step",
    "reconstructible_computation",
    "lemma_candidate",
    "search_hint",
    "diagnostic_metadata",
)

ADVANCEABLE_KINDS = frozenset({"direct_proof_step", "reconstructible_computation"})

# Plan-local statuses plus shared product states.
PLAN_STATUSES = frozenset(
    {
        *PRODUCT_STATES,
        "checkable",
        "blocked",
        # Legacy alias retained in schema for transitional fixtures.
        "proved",
    }
)

_RAW_KIND_MAP: dict[str, str] = {
    "proof_step": "direct_proof_step",
    "direct": "direct_proof_step",
    "kernel": "direct_proof_step",
    "reconstructible": "reconstructible_computation",
    "checker": "reconstructible_computation",
    "computation": "reconstructible_computation",
    "certificate": "reconstructible_computation",
    "lemma": "lemma_candidate",
    "goal": "lemma_candidate",
    "subgoal": "lemma_candidate",
    "hint": "search_hint",
    "strategy": "search_hint",
    "ordering": "search_hint",
    "substitution": "search_hint",
    "smt_hint": "search_hint",
    "timing": "diagnostic_metadata",
    "perf": "diagnostic_metadata",
    "diagnostic": "diagnostic_metadata",
    "backend_internal": "diagnostic_metadata",
}


def classify_trace_item(item: dict[str, Any]) -> str:
    """Classify an untrusted trace item into the Product 05 taxonomy."""
    if item.get("classifiedAs") in STEP_KINDS:
        return str(item["classifiedAs"])
    raw = str(item.get("rawKind", "")).lower().replace("-", "_").replace(" ", "_")
    for key, kind in _RAW_KIND_MAP.items():
        if key in raw:
            return kind
    return "search_hint"


def reconstruction_has_verified_receipt(recon: dict[str, Any] | None) -> bool:
    """True when reconstruction was gated by a verified Certification Record."""
    if not isinstance(recon, dict):
        return False
    gate = recon.get("certificationGate") or recon.get("receiptGate")
    if not isinstance(gate, dict):
        return False
    if not gate.get("ok"):
        return False
    # Studio structural allowCertified is never sufficient (ME-RV-024/062).
    return bool(
        gate.get("certificationVerified")
        or gate.get("verified")
        or gate.get("authoritative")
    )


def direct_proof_evidence_ok(recon: dict[str, Any] | None) -> bool:
    """``direct_proof_step`` may advance only with theorem/env/axiom evidence."""
    if not isinstance(recon, dict):
        return False
    th_decl = recon.get("theoremDeclaration")
    th_digest = recon.get("theoremTypeDigest")
    env = recon.get("environmentLockDigest")
    if not isinstance(th_decl, str) or not th_decl.strip():
        return False
    if not isinstance(th_digest, str) or not th_digest.startswith("sha256:"):
        return False
    if not isinstance(env, str) or not env.startswith("sha256:"):
        return False
    axiom = recon.get("axiomReport") or recon.get("axiomReportDigest")
    provenance = recon.get("proofProvenance") or recon.get("importedProofProvenance")
    if axiom:
        return True
    if isinstance(provenance, dict) and provenance.get("validated") is True:
        return True
    if isinstance(provenance, str) and provenance.strip():
        return True
    return False


def _verified_status(recon: dict[str, Any]) -> bool:
    if reconstruction_has_verified_receipt(recon):
        return True
    return str(recon.get("resultStatus", "")) in {
        "kernel_certified",
        "soundness_verified",
        "witness_verified",
    }


def _advances(kind: str, status: str, *, recon: dict[str, Any] | None = None) -> bool:
    """Only reconstructible categories with verified evidence advance proof status."""
    if kind not in ADVANCEABLE_KINDS:
        return False
    if status not in {"kernel_certified", "proved", "checkable"}:
        return False
    if kind == "reconstructible_computation":
        return reconstruction_has_verified_receipt(recon)
    if kind == "direct_proof_step":
        return direct_proof_evidence_ok(recon)
    return False


def plan_from_traces(
    *,
    target_theorem: str,
    traces: list[dict[str, Any]],
    reconstructions: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a proof-plan DAG from untrusted traces.

    ``reconstructions`` maps trace ids to optional reconstruction records.
    Hints without reconstruction stay ``proposed`` and never set
    ``advancesProofStatus``. Reconstructible nodes advance only when a
    Certification Record gate is verified. Direct steps need theorem digest
    evidence.
    """
    reconstructions = reconstructions or {}
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    classified_traces: list[dict[str, Any]] = []
    unresolved: list[str] = []

    target_id = "target"
    nodes.append(
        {
            "id": target_id,
            "claim": target_theorem,
            "stepKind": "lemma_candidate",
            "status": "proposed",
            "advancesProofStatus": False,
            "suggestedCapability": None,
            "suggestedTactic": None,
            "sourceTraceIds": [],
            "confidence": 1.0,
            "reconstruction": None,
        }
    )

    prev_id: str | None = None
    for raw in traces:
        tid = str(raw.get("id") or f"trace_{len(classified_traces)}")
        kind = classify_trace_item(raw)
        classified = dict(raw)
        classified["id"] = tid
        classified["classifiedAs"] = kind
        classified_traces.append(classified)

        recon = reconstructions.get(tid)
        if kind in ADVANCEABLE_KINDS and recon is not None:
            status = "checkable"
            if kind == "reconstructible_computation":
                if reconstruction_has_verified_receipt(recon):
                    status = "kernel_certified"
                else:
                    unresolved.append(tid)
            elif kind == "direct_proof_step":
                if direct_proof_evidence_ok(recon):
                    status = "kernel_certified"
                else:
                    unresolved.append(tid)
            elif _verified_status(recon):
                # Non-authoritative verified strings stay checkable only.
                status = "checkable"
                unresolved.append(tid)
        elif kind in ADVANCEABLE_KINDS:
            status = "proposed"
            unresolved.append(tid)
        elif kind == "lemma_candidate":
            status = "proposed"
            unresolved.append(tid)
        else:
            status = "proposed"

        node_id = f"n_{tid}"
        conf = raw.get("confidence")
        confidence = float(conf) if isinstance(conf, (int, float)) else 0.5
        suggested_cap = None
        content = raw.get("content") if isinstance(raw.get("content"), dict) else {}
        if isinstance(content.get("capability"), str):
            suggested_cap = content["capability"]
        elif kind == "reconstructible_computation":
            suggested_cap = "algebra.rational_equality"

        node = {
            "id": node_id,
            "claim": str(content.get("claim") or content.get("goal") or tid),
            "stepKind": kind,
            "status": status,
            "advancesProofStatus": _advances(kind, status, recon=recon),
            "suggestedCapability": suggested_cap,
            "suggestedTactic": content.get("tactic") if isinstance(content, dict) else None,
            "sourceTraceIds": [tid],
            "confidence": confidence,
            "reconstruction": recon,
        }
        nodes.append(node)
        edges.append({"from": node_id, "to": target_id, "kind": "depends_on"})
        if prev_id is not None:
            edges.append({"from": prev_id, "to": node_id, "kind": "suggests"})
        prev_id = node_id

    plan = {
        "schemaVersion": "0.1.0",
        "targetTheorem": target_theorem,
        "nodes": nodes,
        "edges": edges,
        "sourceTraces": classified_traces,
        "unresolvedNodes": unresolved,
        "notes": [
            "Traces are untrusted until reconstructed.",
            "search_hint and diagnostic_metadata never advance proof status.",
            "Only direct_proof_step with theorem/env/axiom evidence, or "
            "reconstructible_computation with a verified Certification Record, "
            "may advance proof status.",
        ],
    }
    validate_plan_invariants(plan)
    check_plan_soundness(plan)
    return plan


def reconstruct_from_receipt(
    *,
    trace_id: str,
    certification_record_dir: Path | str | None = None,
    candidate_dir: Path | str | None = None,
    receipt: dict[str, Any] | None = None,
    method: str = "verify_certification_record",
) -> dict[str, Any] | None:
    """Build a typed reconstruction from an authoritative Certification Record.

    Studio's structural receipt checker cannot authorize proof advancement
    (ME-RV-062). A bare ``receipt`` dict is diagnostic only and returns None
    for advancement purposes. Pass ``certification_record_dir`` to invoke
    ``verify_certification_record``.
    """
    del receipt  # Structural receipts never authorize advancement.
    if certification_record_dir is None:
        return None

    from agent.api.receipt import verify_certification_record

    record_path = Path(certification_record_dir)
    cand_path = Path(candidate_dir) if candidate_dir is not None else None
    try:
        verification = verify_certification_record(record_path, candidate_dir=cand_path)
    except Exception:  # noqa: BLE001 — incomplete records never authorize
        return None
    if not verification.verified:
        return None

    gate = {
        "ok": True,
        "certificationVerified": True,
        "verified": True,
        "authoritative": True,
        "allowCertified": True,
        "detail": "verified Certification Record",
        "certificationRecordDigest": verification.certification_record_digest,
        "assuranceMode": verification.assurance_mode,
        "resultStatus": verification.result_status,
    }
    return {
        "method": method,
        "resultStatus": "kernel_certified",
        "bundleRef": verification.candidate_bundle_digest,
        "requestDigest": verification.request_digest,
        "traceId": trace_id,
        "theoremTypeDigest": verification.theorem_type_digest,
        "proofDeclarationDigest": verification.proof_declaration_digest,
        "environmentLockDigest": verification.environment_lock_digest,
        "axiomReportDigest": verification.axiom_report_digest,
        "certificationGate": gate,
        "receiptGate": gate,
    }


def hints_never_advance(plan: dict[str, Any]) -> bool:
    """Invariant: non-advanceable kinds must not set advancesProofStatus."""
    for node in plan.get("nodes", []):
        kind = node.get("stepKind")
        if kind not in ADVANCEABLE_KINDS and node.get("advancesProofStatus"):
            return False
    return True


def check_plan_soundness(plan: dict[str, Any]) -> None:
    """Final plan soundness check (ME-RV-062 DAG semantics)."""
    nodes = {n["id"]: n for n in plan.get("nodes", [])}
    depends: dict[str, list[str]] = {nid: [] for nid in nodes}
    for edge in plan.get("edges", []):
        kind = edge.get("kind") or "depends_on"
        # Suggestion edges never imply proof dependency.
        if kind == "suggests":
            continue
        if kind in ("depends_on", "reconstructs"):
            depends[edge["to"]].append(edge["from"])

    for node in nodes.values():
        status = node.get("status")
        advances = bool(node.get("advancesProofStatus"))
        if status in {"kernel_certified", "proved"} or advances:
            kind = node.get("stepKind")
            recon = node.get("reconstruction")
            if kind == "reconstructible_computation":
                if not reconstruction_has_verified_receipt(recon):
                    raise ValueError(
                        f"node {node['id']}: proved reconstructible lacks "
                        "verified Certification Record evidence"
                    )
            elif kind == "direct_proof_step":
                if not direct_proof_evidence_ok(recon):
                    raise ValueError(
                        f"node {node['id']}: direct_proof_step lacks theorem "
                        "digest/env/axiom evidence"
                    )
            elif kind == "lemma_candidate" and node["id"] == "target":
                # Target proved only when all required incoming deps are proved
                # and a reconstruction theorem exists.
                incoming = depends.get(node["id"], [])
                required = [
                    nodes[src]
                    for src in incoming
                    if nodes[src].get("advancesProofStatus")
                    or nodes[src].get("stepKind") in ADVANCEABLE_KINDS
                ]
                if status in {"kernel_certified", "proved"}:
                    if not required:
                        raise ValueError(
                            "target proved without proved incoming dependencies"
                        )
                    for dep in required:
                        if dep.get("status") not in {"kernel_certified", "proved"}:
                            raise ValueError(
                                f"target depends on unproved node {dep['id']}"
                            )
                    if not any(
                        reconstruction_has_verified_receipt(d.get("reconstruction"))
                        or direct_proof_evidence_ok(d.get("reconstruction"))
                        for d in required
                    ):
                        raise ValueError(
                            "target proved without reconstruction theorem evidence"
                        )


def validate_plan_invariants(plan: dict[str, Any]) -> None:
    """Raise ValueError if plan violates Product 05 status rules or has cycles."""
    if not hints_never_advance(plan):
        raise ValueError("hints/diagnostics must not advance proof status")

    nodes = {n["id"]: n for n in plan.get("nodes", [])}
    for edge in plan.get("edges", []):
        if edge["from"] not in nodes or edge["to"] not in nodes:
            raise ValueError(f"edge references missing node: {edge}")

    # Cycle detection (Kahn) over depends_on / reconstructs only.
    indeg: dict[str, int] = {nid: 0 for nid in nodes}
    adj: dict[str, list[str]] = {nid: [] for nid in nodes}
    for edge in plan.get("edges", []):
        if edge.get("kind") == "suggests":
            continue
        adj[edge["from"]].append(edge["to"])
        indeg[edge["to"]] += 1
    queue = [nid for nid, d in indeg.items() if d == 0]
    seen = 0
    while queue:
        cur = queue.pop()
        seen += 1
        for nxt in adj[cur]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                queue.append(nxt)
    if seen != len(nodes):
        raise ValueError("proof-plan DAG contains a cycle")

    for node in nodes.values():
        kind = node["stepKind"]
        advances = bool(node.get("advancesProofStatus"))
        status = node.get("status")
        if status not in PLAN_STATUSES:
            raise ValueError(f"node {node['id']}: unsupported status {status!r}")
        if advances and kind not in ADVANCEABLE_KINDS:
            raise ValueError(f"node {node['id']}: non-reconstructible cannot advance")
        if advances and status not in {"kernel_certified", "proved", "checkable"}:
            raise ValueError(
                f"node {node['id']}: advances requires kernel_certified|proved|checkable"
            )
        if advances and kind == "reconstructible_computation":
            if not reconstruction_has_verified_receipt(node.get("reconstruction")):
                raise ValueError(
                    f"node {node['id']}: reconstructible_computation advances only with "
                    "verified Certification Record gate"
                )
        if advances and kind == "direct_proof_step":
            if not direct_proof_evidence_ok(node.get("reconstruction")):
                raise ValueError(
                    f"node {node['id']}: direct_proof_step advances only with "
                    "theorem digest/env/axiom evidence"
                )

