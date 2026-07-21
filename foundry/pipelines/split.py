"""Immutable train / eval / held_out split assignment by source family."""

from __future__ import annotations

from typing import Any


# Source-family → split. Not random. Families listed here are pinned; unknown
# families default to train unless path suffixes match legacy held_out/eval cues.
FAMILY_SPLITS: dict[str, str] = {
    # Eval families
    "conformance_linear_algebra": "eval",
    "conformance_calculus": "eval",
    # Held-out families
    "conformance_finite_cex": "held_out",
    "synthetic_negative": "held_out",
    # Train (explicit)
    "evidence_examples": "train",
    "finite_graph_conjecture": "train",
    "conformance_rational": "train",
    "conformance_ideal": "train",
    "conformance_other": "train",
}

# Legacy path-suffix pins (kept for committed evidence/examples continuity).
SPLIT_HELD_OUT_SUFFIXES = (
    "finite_counterexample_nat_eq0",
    "calculus_ode_y_eq_x",
)
SPLIT_EVAL_SUFFIXES = (
    "linear_algebra_inverse_2x2",
    "calculus_antiderivative_x2",
)


def infer_source_family(episode: dict[str, Any]) -> str:
    prov = episode.get("provenance") or {}
    explicit = prov.get("sourceFamily")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    if episode.get("kind") == "synthetic_negative":
        return "synthetic_negative"
    source = str(prov.get("sourcePath") or "")
    if "conjecture/finite_graph" in source or "finite_graph" in source:
        return "finite_graph_conjecture"
    if "evidence/conformance" in source or "/conformance/" in source:
        cap = str((episode.get("toolUse") or {}).get("selectedCapability") or "")
        return {
            "algebra.rational_equality": "conformance_rational",
            "algebra.linear_algebra": "conformance_linear_algebra",
            "logic.finite_counterexample": "conformance_finite_cex",
            "algebra.formal_rational_calculus": "conformance_calculus",
            "algebra.groebner_membership": "conformance_ideal",
        }.get(cap, "conformance_other")
    if "evidence/examples" in source:
        return "evidence_examples"
    return "evidence_examples"


def _assign_split(episode: dict[str, Any]) -> str:
    contamination = episode.get("contamination") or {}
    existing = contamination.get("trainEvalSeparation")
    if existing in {"train", "eval", "held_out"} and episode.get("kind") == "synthetic_negative":
        return existing

    family = infer_source_family(episode)
    if family in FAMILY_SPLITS:
        return FAMILY_SPLITS[family]

    source = (episode.get("provenance") or {}).get("sourcePath") or ""
    for suffix in SPLIT_HELD_OUT_SUFFIXES:
        if suffix in source:
            return "held_out"
    for suffix in SPLIT_EVAL_SUFFIXES:
        if suffix in source:
            return "eval"
    return "train"


def assign_splits(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Mutate episodes with split labels; return immutable split lists + family map."""
    train: list[str] = []
    eval_ids: list[str] = []
    held_out: list[str] = []
    by_family: dict[str, dict[str, int]] = {}

    updated: list[dict[str, Any]] = []
    for ep in episodes:
        family = infer_source_family(ep)
        split = _assign_split(ep)
        prov = dict(ep.get("provenance") or {})
        prov["sourceFamily"] = family
        contamination = dict(ep.get("contamination") or {})
        contamination["trainEvalSeparation"] = split
        if split in {"eval", "held_out"}:
            contamination["benchmarkExclusion"] = True
        eid = str(ep["episodeId"])
        if split == "train":
            train.append(eid)
        elif split == "eval":
            eval_ids.append(eid)
        else:
            held_out.append(eid)
        fam_counts = by_family.setdefault(family, {"train": 0, "eval": 0, "held_out": 0})
        fam_counts[split] = fam_counts.get(split, 0) + 1
        updated.append({**ep, "provenance": prov, "contamination": contamination})

    episodes.clear()
    episodes.extend(updated)

    return {
        "immutable": True,
        "policy": "source_family",
        "train": train,
        "eval": eval_ids,
        "held_out": held_out,
        "bySourceFamily": by_family,
    }
