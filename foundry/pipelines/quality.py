"""Quality tier scoring (auditable heuristics; Q3/Q4 require human review)."""

from __future__ import annotations

from typing import Any

TIERS = (
    "Q0_raw",
    "Q1_schema_valid",
    "Q2_formally_verified",
    "Q3_semantically_reviewed",
    "Q4_library_grade",
)


def score_episode(episode: dict[str, Any]) -> dict[str, Any]:
    """Assign or confirm quality tier without claiming Q3/Q4 without labels."""
    ep = dict(episode)
    outcome = ep.get("outcome") or {}
    labels = set(outcome.get("humanReviewLabels") or [])
    tier = ep.get("qualityTier") or "Q0_raw"

    if "library_grade" in labels or "Q4_library_grade" in labels:
        tier = "Q4_library_grade"
    elif "semantically_reviewed" in labels or "Q3_semantically_reviewed" in labels:
        tier = "Q3_semantically_reviewed"
    elif outcome.get("replayable") and not outcome.get("negative"):
        tier = "Q2_formally_verified"
    elif ep.get("schemaVersion") and ep.get("episodeId"):
        # Schema-valid after pipeline validation.
        if tier in {"Q0_raw"}:
            tier = "Q1_schema_valid"

    # Never auto-promote to Q3/Q4.
    reviewed = {
        "library_grade",
        "Q4_library_grade",
        "semantically_reviewed",
        "Q3_semantically_reviewed",
    }
    if tier in {"Q3_semantically_reviewed", "Q4_library_grade"} and not (labels & reviewed):
        tier = "Q2_formally_verified" if outcome.get("replayable") else "Q1_schema_valid"

    ep["qualityTier"] = tier
    return ep


def score_all(episodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [score_episode(ep) for ep in episodes]


def tier_composition(episodes: list[dict[str, Any]]) -> dict[str, int]:
    counts = {t: 0 for t in TIERS}
    for ep in episodes:
        t = ep.get("qualityTier") or "Q0_raw"
        if t not in counts:
            counts[t] = 0
        counts[t] += 1
    return counts
