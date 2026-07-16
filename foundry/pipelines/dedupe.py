"""Deduplication and content-digest collision handling."""

from __future__ import annotations

from typing import Any


def deduplicate(episodes: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Keep first episode per contentDigest; mark later ones as duplicates."""
    seen: dict[str, str] = {}
    out: list[dict[str, Any]] = []
    dup_count = 0
    for ep in episodes:
        contamination = dict(ep.get("contamination") or {})
        digest = contamination.get("contentDigest")
        if not isinstance(digest, str) or not digest:
            out.append(ep)
            continue
        if digest in seen:
            dup_count += 1
            contamination["duplicateOf"] = seen[digest]
            contamination["benchmarkExclusion"] = True
            contamination["notes"] = (
                (contamination.get("notes") or "")
                + f" Duplicate of {seen[digest]}."
            ).strip()
            # Drop duplicates from primary release list by skipping.
            continue
        seen[digest] = str(ep.get("episodeId"))
        ep = {**ep, "contamination": contamination}
        out.append(ep)
    return out, dup_count
