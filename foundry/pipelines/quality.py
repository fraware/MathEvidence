"""Quality tier scoring (auditable heuristics; Q3/Q4 require human review).

ME-RV-080 Q2 definition (normative):
  immutable candidate bundle
  + verified certification record
  + exact theorem/refutation identity
  + environment lock
  + passing axiom policy

Replayable checker-only / Python-mirror episodes are at most Q1_checker_preview.
"""

from __future__ import annotations

from typing import Any

TIERS = (
    "Q0_raw",
    "Q1_schema_valid",
    "Q1_checker_preview",
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


def has_certification_record(outcome: dict[str, Any]) -> bool:
    """True when outcome carries Certification Record identity fields."""
    return bool(
        outcome.get("certificationRecordId")
        and outcome.get("theoremDeclaration")
        and outcome.get("environmentLockDigest")
    )


def score_episode(episode: dict[str, Any]) -> dict[str, Any]:
    """Assign or confirm quality tier without claiming Q3/Q4 without labels."""
    ep = dict(episode)
    outcome = dict(ep.get("outcome") or {})
    labels = set(outcome.get("humanReviewLabels") or [])
    tier = ep.get("qualityTier") or "Q0_raw"

    if "library_grade" in labels or "Q4_library_grade" in labels:
        tier = "Q4_library_grade"
    elif "semantically_reviewed" in labels or "Q3_semantically_reviewed" in labels:
        tier = "Q3_semantically_reviewed"
    elif has_certification_record(outcome) and not outcome.get("negative"):
        tier = "Q2_formally_verified"
    elif outcome.get("replayable") and not outcome.get("negative"):
        # Checker / offline replay without Certification Record.
        tier = "Q1_checker_preview"
    elif ep.get("schemaVersion") and ep.get("episodeId"):
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
        if has_certification_record(outcome) and not outcome.get("negative"):
            tier = "Q2_formally_verified"
        elif outcome.get("replayable"):
            tier = "Q1_checker_preview"
        else:
            tier = "Q1_schema_valid"

    # Q2 requires Certification Record fields (not merely replayable).
    if tier == "Q2_formally_verified" and (
        outcome.get("negative") or not has_certification_record(outcome)
    ):
        tier = (
            "Q1_checker_preview"
            if outcome.get("replayable") and not outcome.get("negative")
            else "Q1_schema_valid"
        )

    ep["qualityTier"] = tier
    ep["outcome"] = outcome
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
    refuses treating ``resultStatus`` soundness without certification elevation.
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

    if tier in {"Q0_raw", "Q1_schema_valid", "Q1_checker_preview"}:
        if has_verified_claim:
            raise ValueError(
                f"{ep.get('episodeId', '<missing>')}: refuse Q1 as positive verified example "
                f"(tier={tier})"
            )
        # Schema-only tiers must not carry theorem-level statuses. Preview tier may
        # retain historical resultStatus strings after ME-RV-080 demotion; the tier
        # itself forbids treating them as Q2.
        if tier in {"Q0_raw", "Q1_schema_valid"}:
            status = str(outcome.get("resultStatus") or "")
            if (
                status in {"soundness_verified", "witness_verified", "proved"}
                and not has_certification_record(outcome)
                and not outcome.get("negative")
            ):
                raise ValueError(
                    f"{ep.get('episodeId', '<missing>')}: refuse Q1 soundness status as "
                    "positive verified without Certification Record"
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
            out = ep.get("outcome") or {}
            if has_certification_record(out) and not out.get("negative"):
                ep["qualityTier"] = "Q2_formally_verified"
            elif out.get("replayable"):
                ep["qualityTier"] = "Q1_checker_preview"
            else:
                ep["qualityTier"] = "Q1_schema_valid"
            ep.setdefault("notes", [])
            if isinstance(ep["notes"], list):
                ep["notes"].append("Q3/Q4 require humanReviewLabels; auto-uplift stripped.")
            elif isinstance(ep["notes"], str):
                ep["notes"] = ep["notes"] + " Q3/Q4 require humanReviewLabels; auto-uplift stripped."
    return ep
