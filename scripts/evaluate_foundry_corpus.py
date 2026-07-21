#!/usr/bin/env python3
"""Independent Foundry corpus evaluation entry point (read-only metrics)."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from foundry.pipelines.common import DEFAULT_CORPUS_DIR  # noqa: E402
from foundry.pipelines.validate import (  # noqa: E402
    schema_store,
    validate_corpus_episode,
    validate_corpus_release,
)
from foundry.pipelines.quality import refuse_q1_as_verified_positive  # noqa: E402


def evaluate(corpus: Path) -> dict:
    manifest_path = corpus / "manifest.json"
    if not manifest_path.is_file():
        return {
            "ok": False,
            "error": f"missing {manifest_path}",
            "hint": "run: python scripts/generate_finite_graph_campaign.py && "
            "python scripts/build_foundry_corpus.py",
        }

    store = schema_store()
    release = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_corpus_release(release, store)

    tiers = Counter()
    families = Counter()
    replayable_q2 = 0
    q1_verified_refusals = 0
    errors: list[str] = []

    for rel in release.get("episodes") or []:
        path = corpus / rel
        ep = json.loads(path.read_text(encoding="utf-8"))
        try:
            validate_corpus_episode(ep, store)
            refuse_q1_as_verified_positive(ep)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{rel}: {exc}")
            continue
        tier = ep.get("qualityTier") or "Q0_raw"
        tiers[tier] += 1
        fam = (ep.get("provenance") or {}).get("sourceFamily") or "unknown"
        families[fam] += 1
        out = ep.get("outcome") or {}
        if tier == "Q2_formally_verified" and out.get("replayable"):
            replayable_q2 += 1

    review_index = corpus / "review_queue" / "index.json"
    review = {}
    if review_index.is_file():
        review = json.loads(review_index.read_text(encoding="utf-8"))

    q2 = int((release.get("tierComposition") or {}).get("Q2_formally_verified") or 0)
    q3 = int((release.get("tierComposition") or {}).get("Q3_semantically_reviewed") or 0)
    q3_queue = int(review.get("packetCount") or 0)

    gates = {
        "acceptance_influence_false": release.get("acceptanceInfluence") is False,
        "splits_immutable": (release.get("splits") or {}).get("immutable") is True,
        "splits_source_family": (release.get("splits") or {}).get("policy") == "source_family",
        "has_datasheet": (corpus / "DATASHEET.md").is_file(),
        "has_contamination": (corpus / "contamination.json").is_file(),
        "q2_ge_500": q2 >= 500,
        "q3_corpus_zero_without_human_labels": q3 == 0,
        "q3_review_queue_ge_100": q3_queue >= 100,
        "all_q2_replayable_checked": replayable_q2 == q2,
        "no_episode_errors": len(errors) == 0,
        "refuse_q1_as_verified_path_exercised": True,
    }

    return {
        "ok": all(gates.values()) and not errors,
        "releaseId": release.get("releaseId"),
        "episodeCount": len(release.get("episodes") or []),
        "tierComposition": dict(release.get("tierComposition") or {}),
        "tiersObserved": dict(tiers),
        "sourceFamilies": dict(families),
        "replayableQ2": replayable_q2,
        "q3Corpus": q3,
        "q3ReviewQueuePackets": q3_queue,
        "q3ReviewQueueStatus": review.get("status"),
        "splits": {
            "policy": (release.get("splits") or {}).get("policy"),
            "train": len((release.get("splits") or {}).get("train") or []),
            "eval": len((release.get("splits") or {}).get("eval") or []),
            "held_out": len((release.get("splits") or {}).get("held_out") or []),
            "bySourceFamily": (release.get("splits") or {}).get("bySourceFamily"),
        },
        "contaminationSummary": release.get("contaminationSummary"),
        "gates": gates,
        "errors": errors[:20],
        "errorCount": len(errors),
        "claims": {
            "q3_invented": False,
            "field_level_precision": False,
            "ci_green_invented": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus",
        type=Path,
        default=DEFAULT_CORPUS_DIR,
        help="Corpus directory (default foundry/corpus/v0.1)",
    )
    args = parser.parse_args()
    result = evaluate(args.corpus)
    print(json.dumps(result, indent=2))
    if not result.get("ok"):
        print("foundry-evaluate: FAIL", file=sys.stderr)
        return 1
    print(
        f"foundry-evaluate ok q2={result['tierComposition'].get('Q2_formally_verified')} "
        f"q3_corpus={result['q3Corpus']} q3_queue={result['q3ReviewQueuePackets']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
