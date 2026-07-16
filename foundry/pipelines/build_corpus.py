"""Orchestrate Foundry corpus build from evidence + captures + synthetic negatives."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from foundry.pipelines.common import DEFAULT_CORPUS_DIR, REPO_ROOT
from foundry.pipelines.dedupe import deduplicate
from foundry.pipelines.ingest_captures import ingest_capture_dir
from foundry.pipelines.ingest_evidence import ingest_all_evidence_examples
from foundry.pipelines.negatives import synthetic_negatives
from foundry.pipelines.package import package_release
from foundry.pipelines.quality import score_all
from foundry.pipelines.split import assign_splits
from foundry.pipelines.validate import validate_all_episodes


def build_corpus(
    *,
    out_dir: Path | None = None,
    include_captures: bool = True,
    include_synthetic_negatives: bool = True,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Build a public corpus slice without touching theorem acceptance."""
    root = repo_root or REPO_ROOT
    dest = out_dir or DEFAULT_CORPUS_DIR

    episodes: list[dict[str, Any]] = []
    episodes.extend(ingest_all_evidence_examples(repo_root=root))
    if include_captures:
        episodes.extend(ingest_capture_dir())
    if include_synthetic_negatives:
        episodes.extend(synthetic_negatives())

    episodes = score_all(episodes)
    episodes, errors = validate_all_episodes(episodes)
    if errors:
        raise RuntimeError("corpus validation failed:\n" + "\n".join(errors))

    episodes, dup_count = deduplicate(episodes)
    splits = assign_splits(episodes)
    # Re-validate after split mutation.
    episodes, errors = validate_all_episodes(episodes)
    if errors:
        raise RuntimeError("post-split validation failed:\n" + "\n".join(errors))

    release = package_release(
        episodes,
        splits,
        out_dir=dest,
        duplicate_count=dup_count,
    )
    return {
        "outDir": str(dest),
        "episodeCount": len(episodes),
        "duplicateCount": dup_count,
        "splits": splits,
        "tierComposition": release["tierComposition"],
        "acceptanceInfluence": False,
    }


# Re-export for foundry.pipelines.__init__
__all__ = ["build_corpus"]
