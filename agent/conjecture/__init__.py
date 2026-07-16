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
    "mark_formally_proved",
    "mark_open_problem",
    "new_episode",
    "precision_accounting",
    "run_family_campaign",
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

AUTHORITY_STATUS = "lean_checker_mirror"


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
        out["authorityStatus"] = AUTHORITY_STATUS
        out["notes"] = "Falsified by certified finite counterexample (Lean checker owns truth)."
    else:
        out["notes"] = "Witness rejected; conjecture state unchanged."
        out["authorityStatus"] = AUTHORITY_STATUS
    return out


def mark_bounded_verified(episode: dict[str, Any], bound: int) -> dict[str, Any]:
    out = dict(episode)
    if out.get("state") in ("falsified", "formally_proved"):
        return out
    out["state"] = "bounded_verified"
    out["searchBound"] = bound
    out["notes"] = "Bounded verification only; not a theorem over the unbounded family."
    return out


def mark_formally_proved(episode: dict[str, Any], theorem_ref: str) -> dict[str, Any]:
    out = dict(episode)
    if out.get("state") == "falsified":
        return out
    out["state"] = "formally_proved"
    out["notes"] = f"Reusable theorem: {theorem_ref}"
    return out


def mark_open_problem(episode: dict[str, Any], detail: str) -> dict[str, Any]:
    out = dict(episode)
    if out.get("state") in ("falsified", "formally_proved"):
        return out
    out["state"] = "open"
    out["notes"] = detail
    return out


def precision_accounting(episodes: list[dict[str, Any]], *, family_id: str) -> dict[str, Any]:
    """Precision accounting for a formal family campaign."""
    counts = {
        "familyId": family_id,
        "proposed": len(episodes),
        "falsified": 0,
        "boundedVerified": 0,
        "formallyProved": 0,
        "openProblems": 0,
    }
    for e in episodes:
        st = e.get("state")
        if st == "falsified":
            counts["falsified"] += 1
        elif st == "bounded_verified":
            counts["boundedVerified"] += 1
        elif st == "formally_proved":
            counts["formallyProved"] += 1
        elif st == "open":
            counts["openProblems"] += 1
    proposed = counts["proposed"]
    counts["precisionRate"] = (
        counts["falsified"] / proposed if proposed else None
    )
    counts["notes"] = [
        "precisionRate = falsified/proposed among campaign candidates.",
        "bounded_verified and open are not unbounded theorems.",
        "formally_proved requires an explicit reusable theorem reference.",
    ]
    return counts


def run_family_campaign(
    *,
    family_id: str,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    """Run one formal family campaign with precision accounting.

    Each candidate is ``{pred, request?, certificate?, outcome?, theoremRef?, openDetail?}``.
    When ``request`` is provided, attempts Lean-mirror certified falsification first.
    """
    episodes: list[dict[str, Any]] = []
    for i, cand in enumerate(candidates):
        pred = cand["pred"]
        ep = to_candidate(new_episode(family_id=family_id, pred=pred))
        req = cand.get("request")
        cert = cand.get("certificate")
        if isinstance(req, dict):
            if cert is None:
                cert = find_counterexample(req)
            if cert is not None:
                ep = certify_refutation(
                    ep,
                    request=req,
                    certificate=cert,
                    refutation_id=cand.get("refutationId") or f"cex_{i}",
                )
        if ep.get("state") != "falsified":
            outcome = cand.get("outcome")
            if outcome == "formally_proved":
                ep = mark_formally_proved(ep, str(cand.get("theoremRef") or "unspecified"))
            elif outcome == "open":
                ep = mark_open_problem(
                    mark_bounded_verified(ep, int(cand.get("searchBound") or 0)),
                    str(cand.get("openDetail") or "Explicit open-problem artifact."),
                )
            elif outcome == "bounded_verified" or (
                isinstance(req, dict) and cert is None
            ):
                ep = mark_bounded_verified(ep, int(cand.get("searchBound") or 0))
        episodes.append(ep)
    accounting = precision_accounting(episodes, family_id=family_id)
    return {
        "familyId": family_id,
        "episodes": episodes,
        "precisionAccounting": accounting,
        "authorityStatus": AUTHORITY_STATUS,
    }
