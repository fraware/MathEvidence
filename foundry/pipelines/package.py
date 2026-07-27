"""Release packaging for Foundry corpus slices."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from foundry.pipelines.common import write_json
from foundry.pipelines.quality import tier_composition
from foundry.pipelines.validate import validate_corpus_episode, validate_corpus_release

KNOWN_BIASES = [
    "Corpus mixes evidence/examples, conformance fixtures, and FiniteGraph generated refutations.",
    "Q3/Q4 tiers require human semantic review; unlabeled review_queue packets are not Q3.",
    "Q2_formally_verified requires Certification Record + theorem identity + environment lock (ME-RV-080).",
    "Replayable checker-only episodes are Q1_checker_preview, not Q2.",
    "Synthetic negatives are labeled and excluded from eval contamination.",
    "Splits are source-family based (not random); see splits.json bySourceFamily.",
    "FiniteGraph precision metrics are campaign-local — not field-level performance.",
    "No live frontier formalization sessions are included.",
]


def _resolve_source_commit(explicit: str | None) -> str:
    """Published releases MUST use an immutable Git SHA (never ``workspace``)."""
    if explicit and explicit != "workspace":
        if len(explicit) == 40 and all(c in "0123456789abcdef" for c in explicit):
            return explicit
        raise ValueError(f"invalid sourceCommit {explicit!r}; need 40-char Git SHA")
    import subprocess

    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[2],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        sha = out.strip()
        if len(sha) == 40:
            return sha
    except (OSError, subprocess.CalledProcessError):
        pass
    raise ValueError(
        "sourceCommit: workspace is forbidden; provide an immutable Git SHA "
        "or run from a git checkout (ME-RV-080)"
    )


def package_release(
    episodes: list[dict[str, Any]],
    splits: dict[str, Any],
    *,
    out_dir: Path,
    release_id: str = "foundry-corpus-v0.1",
    version: str = "0.1.0",
    duplicate_count: int = 0,
    source_commit: str | None = None,
) -> dict[str, Any]:
    episodes_dir = out_dir / "episodes"
    if episodes_dir.is_dir():
        for stale in episodes_dir.glob("*.json"):
            stale.unlink()
    episodes_dir.mkdir(parents=True, exist_ok=True)

    rel_paths: list[str] = []
    for ep in episodes:
        validate_corpus_episode(ep)
        fname = f"{ep['episodeId']}.json"
        write_json(episodes_dir / fname, ep)
        rel_paths.append(f"episodes/{fname}")

    in_lib = sum(
        1 for ep in episodes if (ep.get("contamination") or {}).get("inPublicLibrary")
    )
    synth = sum(1 for ep in episodes if ep.get("kind") == "synthetic_negative")

    release = {
        "schemaVersion": "0.1.0",
        "releaseId": release_id,
        "version": version,
        "title": "MathEvidence Foundry certified tool-use corpus (v0.1 scaled)",
        "description": (
            "Public corpus of verification-aware tool-use episodes built from "
            "committed evidence, conformance fixtures, FiniteGraph certified "
            "refutations, and synthetic negatives. Does not influence theorem acceptance."
        ),
        "license": "Apache-2.0",
        "acceptanceInfluence": False,
        "createdAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sourceCommit": _resolve_source_commit(source_commit),
        "tierComposition": tier_composition(episodes),
        "splits": {
            "immutable": True,
            "policy": splits.get("policy") or "source_family",
            "train": list(splits.get("train") or []),
            "eval": list(splits.get("eval") or []),
            "held_out": list(splits.get("held_out") or []),
            "bySourceFamily": dict(splits.get("bySourceFamily") or {}),
        },
        "episodes": rel_paths,
        "benchmarkExclusions": [
            eid
            for eid in (list(splits.get("eval") or []) + list(splits.get("held_out") or []))
        ],
        "datasheet": "DATASHEET.md",
        "knownBiases": list(KNOWN_BIASES),
        "contaminationSummary": {
            "duplicateCount": duplicate_count,
            "inPublicLibraryCount": in_lib,
            "syntheticNegativeCount": synth,
            "notes": (
                "Immutable splits; eval/held_out excluded from train. "
                "Synthetic negatives marked benchmarkExclusion."
            ),
        },
    }
    validate_corpus_release(release)
    write_json(out_dir / "manifest.json", release)
    write_json(out_dir / "splits.json", release["splits"])
    write_json(
        out_dir / "contamination.json",
        {
            "acceptanceInfluence": False,
            "summary": release["contaminationSummary"],
            "benchmarkExclusions": release["benchmarkExclusions"],
            "immutableSplits": True,
        },
    )
    return release
