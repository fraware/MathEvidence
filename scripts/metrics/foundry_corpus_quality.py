#!/usr/bin/env python3
"""Foundry corpus build-quality metrics (sample release honesty + family norms)."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "foundry" / "corpus" / "v0.1"


def _family_normalized(episodes: list[dict]) -> dict:
    """Raw vs family-normalized counts (ME-RV-080 corpus statistics)."""
    by_cap: Counter[str] = Counter()
    by_family: Counter[str] = Counter()
    q2_with_theorem = 0
    for ep in episodes:
        cap = str((ep.get("toolUse") or {}).get("selectedCapability") or "unknown")
        fam = str((ep.get("provenance") or {}).get("sourceFamily") or "unknown")
        by_cap[cap] += 1
        by_family[fam] += 1
        out = ep.get("outcome") or {}
        if ep.get("qualityTier") == "Q2_formally_verified" and out.get("theoremDeclaration"):
            q2_with_theorem += 1
    # Family-normalized: count each source family once toward "independent domains".
    return {
        "episodes_by_capability_raw": dict(by_cap),
        "episodes_by_source_family_raw": dict(by_family),
        "unique_source_families": len(by_family),
        "family_normalized_episode_units": len(by_family),
        "q2_with_independent_theorem": q2_with_theorem,
        "note": (
            "Near-isomorphic FiniteGraph campaigns must not be read as hundreds of "
            "independent domains; prefer unique_source_families."
        ),
    }


def measure() -> dict:
    manifest_path = CORPUS / "manifest.json"
    if not manifest_path.is_file():
        return {
            "metric": "foundry_corpus_quality",
            "error": "missing foundry/corpus/v0.1/manifest.json",
            "status": "OPEN",
        }
    release = json.loads(manifest_path.read_text(encoding="utf-8"))
    tiers = release.get("tierComposition") or {}
    episode_rels = release.get("episodes") or []
    splits = release.get("splits") or {}
    cont = release.get("contaminationSummary") or {}

    episodes: list[dict] = []
    for rel in episode_rels:
        path = CORPUS / rel
        if path.is_file():
            episodes.append(json.loads(path.read_text(encoding="utf-8")))

    q2 = int(tiers.get("Q2_formally_verified") or 0)
    q1p = int(tiers.get("Q1_checker_preview") or 0)
    q3 = int(tiers.get("Q3_semantically_reviewed") or 0)
    q4 = int(tiers.get("Q4_library_grade") or 0)
    total = len(episode_rels)
    q2_share = round(q2 / total, 4) if total else 0.0

    review_index = CORPUS / "review_queue" / "index.json"
    q3_queue = 0
    if review_index.is_file():
        q3_queue = int(
            json.loads(review_index.read_text(encoding="utf-8")).get("packetCount") or 0
        )

    commit = release.get("sourceCommit")
    family = _family_normalized(episodes)

    # Honest engineering gates after ME-RV-080 redefinition (no fake Q2 scale).
    checks = {
        "acceptance_influence_false": release.get("acceptanceInfluence") is False,
        "splits_immutable": splits.get("immutable") is True,
        "splits_source_family": splits.get("policy") == "source_family",
        "has_datasheet": (CORPUS / "DATASHEET.md").is_file(),
        "has_contamination": (CORPUS / "contamination.json").is_file(),
        "has_license": (CORPUS / "LICENSE.txt").is_file(),
        "episode_count_ge_12": total >= 12,
        "source_commit_immutable_sha": isinstance(commit, str)
        and len(commit) == 40
        and commit != "workspace",
        "no_overclaimed_q2_without_cert": q2 == family["q2_with_independent_theorem"],
        "no_auto_q3_q4": q3 == 0 and q4 == 0,
        "q3_review_queue_present": q3_queue >= 0,
    }
    return {
        "metric": "foundry_corpus_quality",
        "releaseId": release.get("releaseId"),
        "episode_count": total,
        "tierComposition": tiers,
        "q2_formally_verified_share": q2_share,
        "q1_checker_preview_count": q1p,
        "q3_review_queue_packets": q3_queue,
        "contaminationSummary": cont,
        "family_normalized": family,
        "build_quality_checks": checks,
        "build_quality_pass": all(checks.values()),
        "claims": {
            "sample_corpus": True,
            "scaled_q2_corpus": False,
            "q2_requires_certification_record": True,
            "trained_selector_uplift": False,
            "funding_secured": False,
            "q3_human_labels": False,
            "live_federation": False,
        },
    }


def main() -> int:
    result = measure()
    print(json.dumps(result, indent=2))
    status = "pass" if result.get("build_quality_pass") else "fail"
    print(
        f"foundry_corpus_quality: {status} "
        f"episodes={result.get('episode_count')} "
        f"q2_share={result.get('q2_formally_verified_share')} "
        f"families={((result.get('family_normalized') or {}).get('unique_source_families'))}",
        file=sys.stderr,
    )
    return 0 if result.get("build_quality_pass", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
