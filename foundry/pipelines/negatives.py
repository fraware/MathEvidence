"""Synthetic negative episodes for tool-selection failure diagnosis."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid5

from foundry.pipelines.common import KNOWN_CAPABILITIES, content_digest

_NS = UUID("6f756e64-7279-4e65-8767-617469766573")  # foundry-negatives


def _neg(
    *,
    slug: str,
    selected: str,
    correct: str,
    rationale: str,
    negative_kind: str,
) -> dict[str, Any]:
    core = {"slug": slug, "selected": selected, "correct": correct}
    return {
        "schemaVersion": "0.1.0",
        "episodeId": str(uuid5(_NS, slug)),
        "kind": "synthetic_negative",
        "capturedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "acceptanceInfluence": False,
        "qualityTier": "Q1_schema_valid",
        "provenance": {
            "sourceKind": "synthetic",
            "sourcePath": f"foundry/pipelines/negatives:{slug}",
            "license": "Apache-2.0",
            "publicationAllowed": True,
            "userConsent": "not_applicable",
            "notes": "Synthetic negative; labeled separately from natural failures.",
        },
        "contamination": {
            "inPublicLibrary": False,
            "publicLibraryRefs": [],
            "trainEvalSeparation": "train",
            "duplicateOf": None,
            "contentDigest": content_digest(core),
            "benchmarkExclusion": True,
            "notes": "Synthetic negatives excluded from eval contamination.",
        },
        "toolUse": {
            "capabilityCandidates": list(KNOWN_CAPABILITIES),
            "selectedCapability": selected,
            "requestedClaim": "soundResult",
            "selectionRationale": rationale,
        },
        "outcome": {
            "resultStatus": "rejected",
            "replayable": False,
            "negative": True,
            "negativeKind": negative_kind,
            "errorCodes": ["tool_selection_error"],
            "humanReviewLabels": ["synthetic", f"correct_capability:{correct}"],
        },
        "payload": {"correctCapability": correct, "slug": slug},
        "notes": "Synthetic tool-selection error for Foundry negative data.",
    }


def synthetic_negatives() -> list[dict[str, Any]]:
    return [
        _neg(
            slug="rational_vs_la",
            selected="algebra.linear_algebra",
            correct="algebra.rational_equality",
            rationale="Wrongly selected matrix inverse for rational equality goal.",
            negative_kind="tool_selection_error",
        ),
        _neg(
            slug="shell_escape",
            selected="system.shell",
            correct="algebra.rational_equality",
            rationale="Attempted arbitrary shell instead of operation-level tool.",
            negative_kind="tool_selection_error",
        ),
        _neg(
            slug="claim_overreach",
            selected="analysis.symbolic_calculus",
            correct="analysis.symbolic_calculus",
            rationale="Requested completeness for a derivative candidate claim.",
            negative_kind="claim_strength_mismatch",
        ),
    ]
