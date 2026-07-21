#!/usr/bin/env python3
"""Generate FiniteGraph conjecture artifacts + Foundry-ready replayable episodes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.conjecture.finite_graph import (  # noqa: E402
    ARTIFACT_REL,
    ATLAS_REL,
    GENERATOR_VERSION,
    expand_falsification_variants,
    family_request,
    instance_records,
    load_atlas,
    run_falsification_batch,
    summarize_instances,
    write_campaign_artifacts,
)
from adapters.common.hypothesis_util import find_counterexample  # noqa: E402
from adapters.common.lean_mirrors import check_finite_counterexample  # noqa: E402
from foundry.pipelines.common import content_digest, write_json  # noqa: E402


def _replayable_refutation_episode(
    *,
    candidate_id: str,
    request: dict,
    certificate: dict,
    source_path: str,
) -> dict:
    from datetime import UTC, datetime
    from uuid import UUID, uuid5

    ns = UUID("66696e69-7465-6772-6170-682d71322d76")  # finite-graph-q2-v
    eid = str(uuid5(ns, candidate_id))
    core = {
        "capability": "logic.finite_counterexample",
        "candidateId": candidate_id,
        "requestDigest": request.get("requestDigest"),
        "sourcePath": source_path,
    }
    return {
        "schemaVersion": "0.1.0",
        "episodeId": eid,
        "kind": "certified_refutation",
        "capturedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "acceptanceInfluence": False,
        "qualityTier": "Q2_formally_verified",
        "provenance": {
            "sourceKind": "committed_evidence",
            "sourcePath": source_path,
            "sourceFamily": "finite_graph_conjecture",
            "license": "Apache-2.0",
            "publicationAllowed": True,
            "userConsent": "not_applicable",
            "backendId": "agent.enumerate",
            "adapterVersion": "0.1.0",
            "checkerPackage": "logic.finite_counterexample",
            "notes": f"FiniteGraph calibrated/expanded falsification; {GENERATOR_VERSION}",
        },
        "contamination": {
            "inPublicLibrary": False,
            "publicLibraryRefs": [],
            "trainEvalSeparation": "unassigned",
            "duplicateOf": None,
            "contentDigest": content_digest(core),
            "benchmarkExclusion": False,
            "notes": "Source-family split applied at corpus build.",
        },
        "toolUse": {
            "capabilityCandidates": [
                "logic.finite_counterexample",
                "algebra.rational_equality",
                "algebra.linear_algebra",
            ],
            "selectedCapability": "logic.finite_counterexample",
            "selectedOperation": "refutation",
            "requestedClaim": "refutation",
            "backendId": "agent.enumerate",
            "selectionRationale": f"FiniteGraph candidate {candidate_id}",
        },
        "outcome": {
            "resultStatus": "witness_verified",
            "claimClass": "refutation",
            "assuranceMode": "lean_checker_mirror",
            "requestDigest": request.get("requestDigest"),
            "replayable": True,
            "negative": False,
            "negativeKind": "none",
            "errorCodes": [],
            "humanReviewLabels": [],
        },
        "artifactRefs": [
            source_path,
            str(ARTIFACT_REL / "counterexamples.json").replace("\\", "/"),
        ],
        "payload": {
            "candidateId": candidate_id,
            "generatorVersion": GENERATOR_VERSION,
            "request": request,
            "certificate": certificate,
            "mirrorAccepted": True,
        },
        "notes": "Replayable certified refutation; acceptanceInfluence=false.",
    }


def build_foundry_episode_slice(
    repo_root: Path,
    *,
    campaign_n: int,
    variant_n: int,
    variant_limit: int,
) -> list[dict]:
    """Build ≥variant_limit replayable Q2 episodes from edge-subset falsifications.

    Calibrated Lean-aligned batch uses ``campaign_n`` (default Fin-3).
    Scale variants use ``variant_n`` (Fin-5 has 2^10−1 nonempty edge subsets).
    """
    variants = expand_falsification_variants(variant_n, limit=variant_limit)
    batch = run_falsification_batch(n=campaign_n)
    episodes: list[dict] = []
    source = str(ARTIFACT_REL / "foundry_episodes").replace("\\", "/")
    seen_ids: set[str] = set()

    for cex in batch["counterexamples"]:
        req = cex["request"]
        cert = cex["certificate"]
        if not check_finite_counterexample(req, cert):
            continue
        cid = str(cex["candidateId"])
        seen_ids.add(cid)
        episodes.append(
            _replayable_refutation_episode(
                candidate_id=cid,
                request=req,
                certificate=cert,
                source_path=source,
            )
        )

    for var in variants:
        cid = str(var["id"])
        if cid in seen_ids:
            continue
        req = family_request(variant_n, var["pred"])
        cert = find_counterexample(req)
        if cert is None or not check_finite_counterexample(req, cert):
            continue
        seen_ids.add(cid)
        episodes.append(
            _replayable_refutation_episode(
                candidate_id=cid,
                request=req,
                certificate=cert,
                source_path=source,
            )
        )
    return episodes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=3, help="Fin-n for calibrated Lean-aligned campaign")
    parser.add_argument(
        "--variant-n",
        type=int,
        default=5,
        help="Fin-n for scaled Foundry falsification variants (Fin-5 → up to 1023)",
    )
    parser.add_argument(
        "--foundry-variants",
        type=int,
        default=520,
        help="Target replayable falsification episodes for Foundry Q2 scale",
    )
    parser.add_argument(
        "--skip-foundry-episodes",
        action="store_true",
        help="Only write conjecture artifacts, not Foundry episode JSON files",
    )
    args = parser.parse_args()

    atlas_path = ROOT / ATLAS_REL
    instances = load_atlas(atlas_path)
    records = instance_records(instances)
    summary = summarize_instances(records)
    print(json.dumps({"instances": summary}, indent=2))
    if summary["instanceCount"] < 1000:
        print("FAIL: need ≥1000 nonduplicate instances", file=sys.stderr)
        return 1

    batch = run_falsification_batch(n=args.n)
    # Merge expanded precision sample (Fin-n variant family; not field-level).
    expanded = expand_falsification_variants(args.variant_n, limit=min(64, args.foundry_variants))
    expanded_batch = run_falsification_batch(n=args.variant_n, candidates=expanded)
    paths = write_campaign_artifacts(ROOT, batch=batch, records=records)

    # Also persist expanded precision (not field-level).
    exp_prec = ROOT / ARTIFACT_REL / "precision_expanded_sample.json"
    exp_prec.write_text(
        json.dumps(
            {
                "generatorVersion": GENERATOR_VERSION,
                "note": "Sample expanded falsification precision; not field-level performance.",
                "precisionAccounting": expanded_batch["precisionAccounting"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    paths["precision_expanded_sample"] = exp_prec

    print(
        json.dumps(
            {
                "campaignPrecision": batch["precisionAccounting"],
                "falsifiedInPrimaryBatch": batch["precisionAccounting"]["falsified"],
                "artifactPaths": {k: str(v) for k, v in paths.items()},
            },
            indent=2,
        )
    )

    if not args.skip_foundry_episodes:
        eps = build_foundry_episode_slice(
            ROOT,
            campaign_n=args.n,
            variant_n=args.variant_n,
            variant_limit=args.foundry_variants,
        )
        out_dir = ROOT / ARTIFACT_REL / "foundry_episodes"
        if out_dir.is_dir():
            for stale in out_dir.glob("*.json"):
                stale.unlink()
        out_dir.mkdir(parents=True, exist_ok=True)
        for ep in eps:
            write_json(out_dir / f"{ep['episodeId']}.json", ep)
        index = {
            "generatorVersion": GENERATOR_VERSION,
            "episodeCount": len(eps),
            "qualityTier": "Q2_formally_verified",
            "sourceFamily": "finite_graph_conjecture",
            "note": "Replayable Lean-mirror certified refutations for Foundry ingest.",
        }
        write_json(out_dir / "index.json", index)
        print(json.dumps({"foundryEpisodes": index}, indent=2))
        if len(eps) < 100:
            print(
                f"WARN: only {len(eps)} foundry episodes (expected scale toward 500+ Q2)",
                file=sys.stderr,
            )

    print(f"finite_graph campaign ok → {ROOT / ARTIFACT_REL}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
