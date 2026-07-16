"""Trace-to-Plan engine (Product 05) — Agent-side, not TCB.

Converts untrusted computational traces / hints into a proof-plan DAG.
Only reconstructible step kinds may advance formal proof status.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "ADVANCEABLE_KINDS",
    "STEP_KINDS",
    "classify_trace_item",
    "hints_never_advance",
    "plan_from_traces",
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


def _advances(kind: str, status: str) -> bool:
    """Only reconstructible categories with verified status advance proof status."""
    if kind not in ADVANCEABLE_KINDS:
        return False
    return status in {"proved", "checkable"}


def plan_from_traces(
    *,
    target_theorem: str,
    traces: list[dict[str, Any]],
    reconstructions: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a proof-plan DAG from untrusted traces.

    ``reconstructions`` maps trace ids to optional reconstruction records
    ``{method, resultStatus, bundleRef}``. Hints without reconstruction stay
    ``proposed`` and never set ``advancesProofStatus``.
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
            if str(recon.get("resultStatus", "")).endswith("verified") or recon.get(
                "resultStatus"
            ) in {"proved", "soundness_verified", "witness_verified"}:
                status = "proved"
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
            "advancesProofStatus": _advances(kind, status),
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
            "Only direct_proof_step / reconstructible_computation with proved|checkable status advance.",
        ],
    }
    validate_plan_invariants(plan)
    return plan


def hints_never_advance(plan: dict[str, Any]) -> bool:
    """Invariant: non-advanceable kinds must not set advancesProofStatus."""
    for node in plan.get("nodes", []):
        kind = node.get("stepKind")
        if kind not in ADVANCEABLE_KINDS and node.get("advancesProofStatus"):
            return False
    return True


def validate_plan_invariants(plan: dict[str, Any]) -> None:
    """Raise ValueError if plan violates Product 05 status rules or has cycles."""
    if not hints_never_advance(plan):
        raise ValueError("hints/diagnostics must not advance proof status")

    nodes = {n["id"]: n for n in plan.get("nodes", [])}
    for edge in plan.get("edges", []):
        if edge["from"] not in nodes or edge["to"] not in nodes:
            raise ValueError(f"edge references missing node: {edge}")

    # Cycle detection (Kahn)
    indeg: dict[str, int] = {nid: 0 for nid in nodes}
    adj: dict[str, list[str]] = {nid: [] for nid in nodes}
    for edge in plan.get("edges", []):
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
        if advances and kind not in ADVANCEABLE_KINDS:
            raise ValueError(f"node {node['id']}: non-reconstructible cannot advance")
        if advances and status not in {"proved", "checkable"}:
            raise ValueError(f"node {node['id']}: advances requires proved|checkable")
