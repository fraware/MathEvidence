#!/usr/bin/env python3
"""Foundry corpus build-quality metrics (sample release honesty)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "foundry" / "corpus" / "v0.1"


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
    episodes = release.get("episodes") or []
    splits = release.get("splits") or {}
    cont = release.get("contaminationSummary") or {}

    q2 = int(tiers.get("Q2_formally_verified") or 0)
    q3 = int(tiers.get("Q3_semantically_reviewed") or 0)
    q4 = int(tiers.get("Q4_library_grade") or 0)
    total = len(episodes)
    q2_share = round(q2 / total, 4) if total else 0.0

    # Build quality gates (engineering)
    checks = {
        "acceptance_influence_false": release.get("acceptanceInfluence") is False,
        "splits_immutable": splits.get("immutable") is True,
        "has_datasheet": (CORPUS / "DATASHEET.md").is_file(),
        "has_contamination": (CORPUS / "contamination.json").is_file(),
        "has_license": (CORPUS / "LICENSE.txt").is_file(),
        "episode_count_ge_12": total >= 12,
        "no_auto_q3_q4": q3 == 0 and q4 == 0,
    }
    return {
        "metric": "foundry_corpus_quality",
        "releaseId": release.get("releaseId"),
        "episode_count": total,
        "tierComposition": tiers,
        "q2_formally_verified_share": q2_share,
        "contaminationSummary": cont,
        "build_quality_checks": checks,
        "build_quality_pass": all(checks.values()),
        "claims": {
            "sample_corpus": True,
            "trained_selector_uplift": False,
            "funding_secured": False,
        },
    }


def main() -> int:
    result = measure()
    print(json.dumps(result, indent=2))
    status = "pass" if result.get("build_quality_pass") else "fail"
    print(
        f"foundry_corpus_quality: {status} "
        f"episodes={result.get('episode_count')} "
        f"q2_share={result.get('q2_formally_verified_share')}",
        file=sys.stderr,
    )
    return 0 if result.get("build_quality_pass", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
