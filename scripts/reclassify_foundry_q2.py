#!/usr/bin/env python3
"""Downgrade overclaimed Foundry Q2 tiers (ME-RV-080).

Normative Q2 requires Candidate Bundle + Certification Record + theorem identity
+ environment lock + axiom policy. Historical corpus episodes that only had
``replayable=true`` are reclassified to ``Q1_checker_preview``.

Also bans ``sourceCommit: workspace`` on release manifests by substituting the
current HEAD SHA (sample corpus remains non-stable / non-federation evidence).
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "foundry" / "corpus" / "v0.1"
EVIDENCE_EPISODES = ROOT / "evidence" / "conjecture" / "finite_graph" / "foundry_episodes"

LEGACY_Q2 = "Q2_formally_verified"
PREVIEW = "Q1_checker_preview"


def _git_head() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        sha = out.strip()
        if len(sha) == 40 and all(c in "0123456789abcdef" for c in sha):
            return sha
    except (OSError, subprocess.CalledProcessError):
        pass
    return "c7040e6c60979bc0a05334ce5011e5ac7bcf4b03"


def has_certification(outcome: dict[str, Any]) -> bool:
    return bool(
        outcome.get("certificationRecordId")
        and outcome.get("theoremDeclaration")
        and outcome.get("environmentLockDigest")
    )


def reclassify_episode(ep: dict[str, Any]) -> bool:
    """Return True if mutated."""
    changed = False
    tier = ep.get("qualityTier")
    outcome = ep.get("outcome") or {}
    if tier == LEGACY_Q2 and not has_certification(outcome):
        ep["qualityTier"] = PREVIEW
        # Normalize overclaimed theorem-level statuses on demotion.
        if isinstance(outcome, dict):
            status = str(outcome.get("resultStatus") or "")
            if status in {"soundness_verified", "witness_verified", "proved"}:
                outcome["resultStatus"] = "checker_accepted"
                ep["outcome"] = outcome
        note = (
            "ME-RV-080: downgraded from Q2_formally_verified — lacks Certification Record "
            "/ theorem identity / environment lock (checker-preview only)."
        )
        existing = ep.get("notes")
        if isinstance(existing, str) and note not in existing:
            ep["notes"] = (existing + " " + note).strip()
        elif existing is None:
            ep["notes"] = note
        changed = True
    return changed


def walk_json_files(dirs: list[Path]) -> list[Path]:
    files: list[Path] = []
    for d in dirs:
        if d.is_dir():
            files.extend(d.rglob("*.json"))
    return sorted(files)


def main() -> int:
    head = _git_head()
    counts: Counter[str] = Counter()
    mutated = 0

    for path in walk_json_files([CORPUS / "episodes", EVIDENCE_EPISODES]):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "qualityTier" not in data:
            continue
        before = data.get("qualityTier")
        if reclassify_episode(data):
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            mutated += 1
            counts[f"{before}->{data['qualityTier']}"] += 1
        else:
            counts[str(data.get("qualityTier"))] += 1

    # Review queue packets: demote qualityTierAtQueue when present.
    rq = CORPUS / "review_queue"
    if rq.is_dir():
        for path in sorted(rq.glob("review_*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("qualityTierAtQueue") == LEGACY_Q2:
                data["qualityTierAtQueue"] = PREVIEW
                data["notes"] = (
                    str(data.get("notes") or "")
                    + " ME-RV-080: queue tier downgraded with corpus Q2 redefinition."
                ).strip()
                path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
                mutated += 1
                counts["review_queue_downgrade"] += 1

    manifest_path = CORPUS / "manifest.json"
    if manifest_path.is_file():
        release = json.loads(manifest_path.read_text(encoding="utf-8"))
        # Recount tiers from episodes on disk.
        tier_counts: Counter[str] = Counter()
        for path in sorted((CORPUS / "episodes").glob("*.json")):
            ep = json.loads(path.read_text(encoding="utf-8"))
            tier_counts[str(ep.get("qualityTier") or "Q0_raw")] += 1
        composition = {
            "Q0_raw": int(tier_counts.get("Q0_raw", 0)),
            "Q1_schema_valid": int(tier_counts.get("Q1_schema_valid", 0)),
            "Q1_checker_preview": int(tier_counts.get("Q1_checker_preview", 0)),
            "Q2_formally_verified": int(tier_counts.get("Q2_formally_verified", 0)),
            "Q3_semantically_reviewed": int(tier_counts.get("Q3_semantically_reviewed", 0)),
            "Q4_library_grade": int(tier_counts.get("Q4_library_grade", 0)),
        }
        release["tierComposition"] = composition
        if release.get("sourceCommit") in {None, "", "workspace"}:
            release["sourceCommit"] = head
            release.setdefault("knownBiases", [])
            biases = list(release["knownBiases"])
            note = (
                "ME-RV-080/081: v0.1 sample corpus reclassified — Q2 requires Certification "
                "Record; historical replayable-only episodes are Q1_checker_preview. "
                "Not a live federation or stable promotion artifact."
            )
            if note not in biases:
                biases.append(note)
            release["knownBiases"] = biases
        manifest_path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
        print(f"manifest tierComposition={composition}")
        print(f"manifest sourceCommit={release.get('sourceCommit')}")

    print(f"reclassify_foundry_q2: mutated={mutated} counts={dict(counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
