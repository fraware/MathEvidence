"""Q3 semantic-review queue — review-ready packets without inventing human labels."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from foundry.pipelines.common import DEFAULT_CORPUS_DIR, write_json


REVIEW_STATUSES = (
    "awaiting_human_review",
    "in_review",
    "approved_q3",
    "rejected",
)


def build_review_packet(episode: dict[str, Any]) -> dict[str, Any]:
    """Create a review-ready packet for a Q2 (or Q1) episode awaiting Q3 labels."""
    outcome = episode.get("outcome") or {}
    prov = episode.get("provenance") or {}
    return {
        "schemaVersion": "0.1.0",
        "packetId": f"review:{episode.get('episodeId')}",
        "episodeId": episode.get("episodeId"),
        "status": "awaiting_human_review",
        "createdAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sourceFamily": prov.get("sourceFamily"),
        "qualityTierAtQueue": episode.get("qualityTier"),
        "requestedReview": "semantically_reviewed",
        "humanReviewLabels": list(outcome.get("humanReviewLabels") or []),
        "checklist": [
            "Statement fidelity to the mathematical claim",
            "Witness / certificate interpretation correctness",
            "No overclaim of unbounded theorems from bounded evidence",
            "Contamination / public-library novelty judgment",
        ],
        "artifactRefs": list(episode.get("artifactRefs") or []),
        "notes": (
            "Unlabeled queue item. Do NOT count as Q3 until a human adds "
            "humanReviewLabels including semantically_reviewed."
        ),
        "acceptanceInfluence": False,
    }


def write_review_queue(
    episodes: list[dict[str, Any]],
    *,
    out_dir: Path | None = None,
    target: int = 100,
    require_replayable: bool = True,
) -> dict[str, Any]:
    """Persist ≥target review packets from best Q2 candidates; leave Q3 count at 0."""
    dest = out_dir or (DEFAULT_CORPUS_DIR / "review_queue")
    if dest.is_dir():
        for stale in dest.glob("*.json"):
            if stale.name != "QUEUE.md":
                stale.unlink()
    dest.mkdir(parents=True, exist_ok=True)

    candidates = [
        ep
        for ep in episodes
        if ep.get("qualityTier") == "Q2_formally_verified"
        and (not require_replayable or (ep.get("outcome") or {}).get("replayable"))
        and not (ep.get("outcome") or {}).get("negative")
    ]
    # Prefer diverse source families.
    by_family: dict[str, list[dict[str, Any]]] = {}
    for ep in candidates:
        fam = str((ep.get("provenance") or {}).get("sourceFamily") or "unknown")
        by_family.setdefault(fam, []).append(ep)

    selected: list[dict[str, Any]] = []
    # Round-robin across families for diversity.
    while len(selected) < target and any(by_family.values()):
        progress = False
        for fam in sorted(by_family.keys()):
            bucket = by_family[fam]
            if not bucket:
                continue
            selected.append(bucket.pop(0))
            progress = True
            if len(selected) >= target:
                break
        if not progress:
            break

    packets = [build_review_packet(ep) for ep in selected]
    for pkt in packets:
        write_json(dest / f"{pkt['packetId'].replace(':', '_')}.json", pkt)

    index = {
        "schemaVersion": "0.1.0",
        "queueId": "foundry-q3-review-queue-v0.1",
        "status": "awaiting_human_review",
        "createdAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "packetCount": len(packets),
        "target": target,
        "q3AssignedInCorpus": 0,
        "policy": (
            "Packets are review-ready only. Q3_semantically_reviewed requires "
            "humanReviewLabels; this queue does not invent labels."
        ),
        "packets": [p["packetId"] for p in packets],
        "acceptanceInfluence": False,
    }
    write_json(dest / "index.json", index)
    (dest / "QUEUE.md").write_text(
        "\n".join(
            [
                "# Foundry Q3 semantic review queue",
                "",
                f"Packets: **{len(packets)}** (target {target}).",
                "",
                "Status: `awaiting_human_review`.",
                "",
                "These packets are **not** Q3 corpus episodes. Human reviewers must",
                "add `humanReviewLabels` including `semantically_reviewed` before an",
                "episode may be scored `Q3_semantically_reviewed`.",
                "",
                "Do not invent human confirmations or backdate approvals.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return index
