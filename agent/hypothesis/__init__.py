"""Hypothesis Synthesis orchestration (Product 03) — Agent-side, not TCB.

Sufficiency, deletion, and CEX verification return status only from the Python
mirror of Lean ``checkBool`` (``authorityStatus: lean_checker_mirror``). Kernel
replay remains the final authority for theorem acceptance.
"""

from __future__ import annotations

import copy
from typing import Any

from adapters.common.canonical import bind_request_digest
from adapters.common.hypothesis_util import (
    find_counterexample,
    propose_conditions_from_request,
)
from adapters.common.lean_mirrors import check_finite_counterexample, check_rational_equality
from adapters.common.schema_validate import SchemaStore

__all__ = [
    "AUTHORITY_STATUS",
    "build_condition_lattice",
    "delete_hypothesis_python",
    "propose_conditions_from_request",
    "prove_sufficient_python",
    "verify_counterexample_python",
]

# Agent may only assert acceptance via Lean checker mirrors — never heuristics alone.
AUTHORITY_STATUS = "lean_checker_mirror"

_AUTHORITY_NOTES = [
    "Status from Python mirror of Lean RationalEquality/Counterexample.checkBool.",
    "Lean kernel replay remains authoritative for theorem acceptance.",
    "Minimality is never asserted here.",
]


def _condition_exprs(conditions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    factors: list[dict[str, Any]] = []
    for c in conditions:
        expr = c.get("expr")
        if isinstance(expr, dict):
            factors.append(
                {
                    "expr": expr,
                    "role": c.get("role") or "original_division",
                    "multiplicity": int(c.get("multiplicity") or 1),
                }
            )
    return factors


def _ensure_rational_request(request: dict[str, Any]) -> dict[str, Any]:
    """Normalize a rational-equality request for mirror checking."""
    out = dict(request)
    out.setdefault("schemaVersion", "0.1.0")
    out.setdefault("capability", "algebra.rational_equality")
    out.setdefault("capabilityVersion", "0.1.0")
    out.setdefault("requestedClaim", "soundResult")
    out.setdefault(
        "resourcePolicy",
        {"maxWallTimeMs": 30_000, "maxOutputBytes": 1_048_576},
    )
    if "variables" not in out:
        # Minimal variable set from IR names appearing as var tags is optional;
        # mirror only needs lhs/rhs + digest.
        out["variables"] = out.get("variables") or [{"name": "x", "type": "Rat"}]
    return bind_request_digest(out)


def _certificate_for_conditions(
    request: dict[str, Any], conditions: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": request.get("capabilityVersion", "0.1.0"),
        "requestDigest": request["requestDigest"],
        "differenceNumerator": {"tag": "int", "value": "0"},
        "denominatorFactors": _condition_exprs(conditions),
        "factorization": {
            "method": "agent.hypothesis.sufficiency_preview",
            "notes": "Untrusted candidate; Lean checkBool owns acceptance.",
        },
        "provenance": {
            "backendId": "agent.hypothesis",
            "adapterVersion": "0.1.0",
            "deterministic": True,
        },
    }


def prove_sufficient_python(
    request: dict[str, Any],
    conditions: list[dict[str, Any]],
    *,
    poly_zero: bool | None = None,
) -> dict[str, Any]:
    """Sufficiency via Lean RationalEquality.checkBool mirror only.

    ``poly_zero`` is ignored (kept for API compatibility); poly identity is
    decided by the checker mirror, not by an Agent hint.
    """
    del poly_zero  # unused — Lean-authoritative path only
    req = _ensure_rational_request(request)
    cert = _certificate_for_conditions(req, conditions)
    ok = check_rational_equality(req, cert)
    return {
        "sufficient": ok,
        "authorityStatus": AUTHORITY_STATUS,
        "requestDigest": req["requestDigest"],
        "denominatorsCovered": ok,
        "notes": list(_AUTHORITY_NOTES),
    }


def delete_hypothesis_python(
    request: dict[str, Any],
    conditions: list[dict[str, Any]],
    target_id: str,
    *,
    poly_zero: bool | None = None,
) -> dict[str, Any]:
    """Deletion redundancy via Lean sufficiency mirror (checkBool)."""
    del poly_zero
    remaining = [c for c in conditions if c.get("id") != target_id]
    if len(remaining) == len(conditions):
        return {
            "result": "missing",
            "remaining": conditions,
            "authorityStatus": AUTHORITY_STATUS,
            "notes": list(_AUTHORITY_NOTES),
        }
    preview = prove_sufficient_python(request, remaining)
    if preview["sufficient"]:
        return {
            "result": "redundant",
            "remaining": remaining,
            "justification": "lean_checker_mirror_sufficiency",
            "authorityStatus": AUTHORITY_STATUS,
            "notes": list(_AUTHORITY_NOTES)
            + ["Redundancy justified only by checker-mirror sufficiency."],
        }
    return {
        "result": "not_redundant",
        "remaining": remaining,
        "justification": "lean_checker_mirror_sufficiency_failed",
        "necessity": "open",
        "authorityStatus": AUTHORITY_STATUS,
        "notes": list(_AUTHORITY_NOTES)
        + [
            "Absence of a counterexample is not necessity.",
            "Use find_counterexample + verify_counterexample for weaker variants.",
        ],
    }


def verify_counterexample_python(
    request: dict[str, Any], certificate: dict[str, Any]
) -> dict[str, Any]:
    """Verify finite CEX via Lean Counterexample.checkBool mirror."""
    ok = check_finite_counterexample(request, certificate)
    return {
        "verified": ok,
        "authorityStatus": AUTHORITY_STATUS,
        "notes": [
            "Python mirror of Lean Counterexample.checkBool.",
            "Lean kernel replay remains authoritative.",
        ],
    }


def build_condition_lattice(
    *,
    artifact_id: str,
    request: dict[str, Any],
    original: list[dict[str, Any]] | None = None,
    proposed: list[dict[str, Any]] | None = None,
    poly_zero: bool | None = None,
    weaker_variant_request: dict[str, Any] | None = None,
    related_condition_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Propose → sufficiency (checkBool mirror) → deletion → optional certified CEX."""
    del poly_zero
    original = original or []
    proposed = proposed or propose_conditions_from_request(request)
    all_conds = original + proposed
    preview = prove_sufficient_python(request, all_conds)
    sufficient_sets: list[list[str]] = []
    redundant: list[str] = []
    unresolved: list[str] = []
    weakened: list[list[str]] = []
    certified_cex: list[str] = []
    necessity_proofs: list[dict[str, Any]] = []
    working = copy.deepcopy(all_conds)

    if preview["sufficient"]:
        sufficient_sets.append([c["id"] for c in working])
        for cond in list(working):
            deletion = delete_hypothesis_python(request, working, cond["id"])
            if deletion["result"] == "redundant":
                redundant.append(cond["id"])
                working = deletion["remaining"]
                for c in proposed:
                    if c["id"] == cond["id"]:
                        c["status"] = "redundant"
                necessity_proofs.append(
                    {
                        "conditionId": cond["id"],
                        "kind": "redundancy_proof",
                        "detail": "lean_checker_mirror_sufficiency",
                    }
                )
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

    # Certified CEX on a weaker variant (Product 03 deletion → CEX path).
    if weaker_variant_request is not None:
        wreq = bind_request_digest(dict(weaker_variant_request))
        cert = find_counterexample(wreq)
        if cert is not None and check_finite_counterexample(wreq, cert):
            cex_id = "cex_weaker_variant"
            certified_cex.append(cex_id)
            related = related_condition_ids or list(unresolved)
            weakened.append(related)
            for rid in related:
                if rid in unresolved:
                    unresolved = [u for u in unresolved if u != rid]
                for c in proposed:
                    if c["id"] == rid:
                        c["status"] = "weaker_falsified"
                necessity_proofs.append(
                    {
                        "conditionId": rid,
                        "kind": "certified_counterexample",
                        "detail": cex_id,
                    }
                )

    lattice = {
        "schemaVersion": "0.1.0",
        "artifactId": artifact_id,
        "originalAssumptions": original,
        "proposed": proposed,
        "sufficientSets": sufficient_sets,
        "redundant": redundant,
        "weakenedVariants": weakened,
        "certifiedCounterexamples": certified_cex,
        "unresolvedNecessity": unresolved,
        "necessityProofs": necessity_proofs,
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
        "authorityStatus": AUTHORITY_STATUS,
    }
    store = SchemaStore()
    store.validate("condition-lattice.schema.json", lattice)
    return lattice
