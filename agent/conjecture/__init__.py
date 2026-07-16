"""Conjecture / falsification orchestration (Product 04) — Agent-side."""

from __future__ import annotations

from typing import Any

from adapters.common.hypothesis_util import find_counterexample
from adapters.common.lean_mirrors import check_finite_counterexample

__all__ = [
    "STATES",
    "certify_refutation",
    "find_counterexample",
    "mark_bounded_verified",
    "new_episode",
    "to_candidate",
]

STATES = (
    "observed_pattern",
    "candidate_statement",
    "falsified",
    "bounded_verified",
    "formally_proved",
    "open",
)


def new_episode(
    *, family_id: str, pred: dict[str, Any], state: str = "observed_pattern"
) -> dict[str, Any]:
    if state not in STATES:
        raise ValueError(f"unknown conjecture state: {state}")
    return {
        "familyId": family_id,
        "candidatePred": pred,
        "state": state,
        "certifiedRefutationId": None,
        "searchBound": 0,
        "notes": "Pattern/candidate only; not a theorem." if state != "formally_proved" else "",
    }


def to_candidate(episode: dict[str, Any]) -> dict[str, Any]:
    out = dict(episode)
    out["state"] = "candidate_statement"
    return out


def certify_refutation(
    episode: dict[str, Any],
    *,
    request: dict[str, Any],
    certificate: dict[str, Any],
    refutation_id: str,
) -> dict[str, Any]:
    out = dict(episode)
    if check_finite_counterexample(request, certificate):
        out["state"] = "falsified"
        out["certifiedRefutationId"] = refutation_id
        out["notes"] = "Falsified by certified finite counterexample (Lean checker owns truth)."
    else:
        out["notes"] = "Witness rejected; conjecture state unchanged."
    return out


def mark_bounded_verified(episode: dict[str, Any], bound: int) -> dict[str, Any]:
    out = dict(episode)
    if out.get("state") in ("falsified", "formally_proved"):
        return out
    out["state"] = "bounded_verified"
    out["searchBound"] = bound
    out["notes"] = "Bounded verification only; not a theorem over the unbounded family."
    return out
