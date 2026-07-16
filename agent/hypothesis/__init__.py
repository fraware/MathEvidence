"""Hypothesis Synthesis orchestration (Product 03) — Agent-side, not TCB."""

from __future__ import annotations

import copy
from typing import Any

from adapters.common.hypothesis_util import propose_conditions_from_request
from adapters.common.rational_ir import collect_division_denominators
from adapters.common.schema_validate import SchemaStore

__all__ = [
    "build_condition_lattice",
    "delete_hypothesis_python",
    "propose_conditions_from_request",
    "prove_sufficient_python",
]


def _cover_ok(lhs: dict[str, Any], rhs: dict[str, Any], factors: list[dict[str, Any]]) -> bool:
    needed = collect_division_denominators(lhs) + collect_division_denominators(rhs)
    have = [f.get("expr") for f in factors]

    def contains(target: dict[str, Any]) -> bool:
        return any(h == target for h in have)

    return all(contains(d) for d in needed)


def prove_sufficient_python(
    request: dict[str, Any], conditions: list[dict[str, Any]], *, poly_zero: bool
) -> dict[str, Any]:
    """Orchestration-only sufficiency preview (Lean owns acceptance)."""
    covered = _cover_ok(request.get("lhs", {}), request.get("rhs", {}), conditions)
    ok = bool(poly_zero) and covered
    return {
        "sufficient": ok,
        "polyZeroHint": poly_zero,
        "denominatorsCovered": covered,
        "notes": [
            "Agent preview only; Lean RationalEquality checker owns acceptance.",
            "Minimality is never asserted here.",
        ],
    }


def delete_hypothesis_python(
    request: dict[str, Any],
    conditions: list[dict[str, Any]],
    target_id: str,
    *,
    poly_zero: bool,
) -> dict[str, Any]:
    remaining = [c for c in conditions if c.get("id") != target_id]
    if len(remaining) == len(conditions):
        return {"result": "missing", "remaining": conditions}
    preview = prove_sufficient_python(request, remaining, poly_zero=poly_zero)
    if preview["sufficient"]:
        return {
            "result": "redundant",
            "remaining": remaining,
            "justification": "sufficiency_preview_holds",
            "notes": [
                "Redundancy preview only; confirm with Lean deleteHypothesis / checkBool."
            ],
        }
    return {
        "result": "not_redundant",
        "remaining": remaining,
        "justification": "sufficiency_preview_failed",
        "necessity": "open",
        "notes": [
            "Absence of a counterexample is not necessity.",
            "Use find_counterexample + verify_counterexample for weaker variants.",
        ],
    }


def build_condition_lattice(
    *,
    artifact_id: str,
    request: dict[str, Any],
    original: list[dict[str, Any]] | None = None,
    proposed: list[dict[str, Any]] | None = None,
    poly_zero: bool = True,
) -> dict[str, Any]:
    original = original or []
    proposed = proposed or propose_conditions_from_request(request)
    all_conds = original + proposed
    preview = prove_sufficient_python(request, all_conds, poly_zero=poly_zero)
    sufficient_sets: list[list[str]] = []
    redundant: list[str] = []
    unresolved: list[str] = []
    working = copy.deepcopy(all_conds)
    if preview["sufficient"]:
        sufficient_sets.append([c["id"] for c in working])
        for cond in list(working):
            deletion = delete_hypothesis_python(
                request, working, cond["id"], poly_zero=poly_zero
            )
            if deletion["result"] == "redundant":
                redundant.append(cond["id"])
                working = deletion["remaining"]
                for c in proposed:
                    if c["id"] == cond["id"]:
                        c["status"] = "redundant"
            elif deletion["result"] == "not_redundant":
                unresolved.append(cond["id"])
                for c in proposed:
                    if c["id"] == cond["id"]:
                        c["status"] = "necessity_open"
        for c in proposed:
            if c["id"] in {w["id"] for w in working} and c["status"] == "proposed":
                c["status"] = "sufficient_member"
    else:
        unresolved = [c["id"] for c in proposed]

    lattice = {
        "schemaVersion": "0.1.0",
        "artifactId": artifact_id,
        "originalAssumptions": original,
        "proposed": proposed,
        "sufficientSets": sufficient_sets,
        "redundant": redundant,
        "weakenedVariants": [],
        "certifiedCounterexamples": [],
        "unresolvedNecessity": unresolved,
        "necessityProofs": [],
        "recommendedInterface": [c["id"] for c in working] if preview["sufficient"] else [],
        "ranking": {
            "criteria": [
                "logical generality",
                "assumption count",
                "library conventions",
                "human readability",
            ],
            "recommendedInterfaceId": "recommended_v0" if preview["sufficient"] else "none",
            "notes": "Minimality is not claimed. Expert review required before upstreaming.",
        },
        "claimsMinimal": False,
    }
    store = SchemaStore()
    store.validate("condition-lattice.schema.json", lattice)
    return lattice
