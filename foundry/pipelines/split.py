"""Immutable train / eval / held_out split assignment."""

from __future__ import annotations

from typing import Any

from foundry.pipelines.common import SPLIT_EVAL_SUFFIXES, SPLIT_HELD_OUT_SUFFIXES


def _assign_split(episode: dict[str, Any]) -> str:
    contamination = episode.get("contamination") or {}
    existing = contamination.get("trainEvalSeparation")
    if existing in {"train", "eval", "held_out"} and episode.get("kind") == "synthetic_negative":
        return existing

    source = (episode.get("provenance") or {}).get("sourcePath") or ""
    for suffix in SPLIT_HELD_OUT_SUFFIXES:
        if suffix in source:
            return "held_out"
    for suffix in SPLIT_EVAL_SUFFIXES:
        if suffix in source:
            return "eval"
    return "train"


def assign_splits(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Mutate episodes with split labels; return immutable split lists."""
    train: list[str] = []
    eval_ids: list[str] = []
    held_out: list[str] = []

    updated: list[dict[str, Any]] = []
    for ep in episodes:
        split = _assign_split(ep)
        contamination = dict(ep.get("contamination") or {})
        contamination["trainEvalSeparation"] = split
        # Held-out and eval episodes are excluded from training releases' train set.
        if split in {"eval", "held_out"}:
            contamination["benchmarkExclusion"] = True
        eid = str(ep["episodeId"])
        if split == "train":
            train.append(eid)
        elif split == "eval":
            eval_ids.append(eid)
        else:
            held_out.append(eid)
        updated.append({**ep, "contamination": contamination})

    # Replace caller list in-place semantics via return.
    episodes.clear()
    episodes.extend(updated)

    return {
        "immutable": True,
        "train": train,
        "eval": eval_ids,
        "held_out": held_out,
    }
