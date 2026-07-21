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

# Tiers that may be presented as positive formally-verified corpus examples.
VERIFIED_POSITIVE_TIERS = frozenset(
    {
        "Q2_formally_verified",
        "Q3_semantically_reviewed",
        "Q4_library_grade",
    }
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

    # Q2 requires replayable positive outcome.
    if tier == "Q2_formally_verified" and (
        not outcome.get("replayable") or outcome.get("negative")
    ):
        tier = "Q1_schema_valid"

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


def refuse_q1_as_verified_positive(episode: dict[str, Any]) -> None:
    """Raise if Q1 (or below) is presented as a positive verified example.

    Detects explicit verified-positive claims on schema-only episodes, and
    refuses treating ``resultStatus`` soundness without replay elevation.
    """
    ep = episode
    tier = ep.get("qualityTier") or "Q0_raw"
    outcome = ep.get("outcome") or {}
    claims = ep.get("claims") or []

    verified_claim_kinds = {
        "verified_positive",
        "formally_verified_positive",
        "q2_positive",
        "positive_verified",
    }
    has_verified_claim = any(
        isinstance(c, dict) and str(c.get("kind", "")) in verified_claim_kinds for c in claims
    )

    if tier in {"Q0_raw", "Q1_schema_valid"}:
        if has_verified_claim:
            raise ValueError(
                f"{ep.get('episodeId', '<missing>')}: refuse Q1 as positive verified example "
                f"(tier={tier})"
            )
        # Soundness-looking statuses on non-replayable Q1 must not be treated as verified.
        status = str(outcome.get("resultStatus") or "")
        if (
            status in {"soundness_verified", "witness_verified", "proved"}
            and not outcome.get("replayable")
            and not outcome.get("negative")
        ):
            raise ValueError(
                f"{ep.get('episodeId', '<missing>')}: refuse Q1 soundness status as "
                "positive verified without replayable elevation"
            )


def enforce_tier_claims(episode: dict[str, Any]) -> dict[str, Any]:
    """Reject unsupported uplift claims; never invent Q3/Q4 from tiny selectors."""
    ep = score_episode(episode)
    claims = list(ep.get("claims") or [])
    cleaned: list[Any] = []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        kind = str(claim.get("kind", ""))
        if kind in {"uplift", "q3_auto", "q4_auto"}:
            # Release-blocking if asserted without human labels.
            continue
        cleaned.append(claim)
    ep["claims"] = cleaned
    if ep.get("qualityTier") in {"Q3_semantically_reviewed", "Q4_library_grade"}:
        labels = set((ep.get("outcome") or {}).get("humanReviewLabels") or [])
        reviewed = {
            "library_grade",
            "Q4_library_grade",
            "semantically_reviewed",
            "Q3_semantically_reviewed",
        }
        if not (labels & reviewed):
            ep["qualityTier"] = (
                "Q2_formally_verified"
                if (ep.get("outcome") or {}).get("replayable")
                else "Q1_schema_valid"
            )
            ep.setdefault("notes", [])
            if isinstance(ep["notes"], list):
                ep["notes"].append("Q3/Q4 require humanReviewLabels; auto-uplift stripped.")
            elif isinstance(ep["notes"], str):
                ep["notes"] = ep["notes"] + " Q3/Q4 require humanReviewLabels; auto-uplift stripped."
    return ep
