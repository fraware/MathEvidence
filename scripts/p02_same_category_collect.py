#!/usr/bin/env python3
"""Collect raw Lean observations for the preregistered P02 same-category extension.

This collector reads only the source-only CASE_SPEC file. It does not read the
separately sealed EXPECTED_RESULTS file and performs no classification.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import p02_native_v2_raw as base

SCHEMA_VERSION = "p02_same_category_raw_v1"
EXPECTED_CASE_SCHEMA = "p02_same_category_case_spec_v1"
EXPECTED_PROJECT_SHA = "946d2f7b14840837a5b641150c9df9008c4be9eb"
EXPECTED_TOOLCHAIN = "leanprover/lean4:v4.14.0"
EXPECTED_CLASSIFIER_BLOB_SHA = "75d0599c277806007b1f31db451dbbe1bec3962e"
EXPECTED_N_CASES = 12


def load_spec(path: Path) -> dict[str, Any]:
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec.get("schema_version") != EXPECTED_CASE_SCHEMA:
        raise RuntimeError("unexpected case-spec schema")
    if spec.get("pinned_project_sha") != EXPECTED_PROJECT_SHA:
        raise RuntimeError("case spec pins unexpected project")
    if spec.get("lean_toolchain") != EXPECTED_TOOLCHAIN:
        raise RuntimeError("case spec pins unexpected toolchain")
    if spec.get("classifier_v2_blob_sha") != EXPECTED_CLASSIFIER_BLOB_SHA:
        raise RuntimeError("case spec pins unexpected classifier")
    if spec.get("collection_reads_expectations") is not False:
        raise RuntimeError("case spec does not preserve collection/expectation separation")
    return spec


def flatten_states(spec: dict[str, Any]) -> list[dict[str, Any]]:
    states: list[dict[str, Any]] = []
    pair_ids: set[str] = set()
    for pair in spec.get("pairs") or []:
        pair_id = str(pair["pair_id"])
        if pair_id in pair_ids:
            raise RuntimeError(f"duplicate pair id: {pair_id}")
        pair_ids.add(pair_id)
        rows = pair.get("states") or []
        if {row.get("state") for row in rows} != {"clean", "a", "b", "ab"}:
            raise RuntimeError(f"pair {pair_id} does not contain clean/a/b/ab")
        for row in rows:
            if row.get("pair_id") != pair_id:
                raise RuntimeError(f"pair identity mismatch in {row.get('state_id')}")
            states.append(row)
    if len(states) != EXPECTED_N_CASES:
        raise RuntimeError(f"expected {EXPECTED_N_CASES} states, found {len(states)}")
    ids = [str(row["state_id"]) for row in states]
    if len(set(ids)) != len(ids):
        raise RuntimeError("duplicate state ids")
    return states


def as_case(row: dict[str, Any]) -> base.Case:
    return base.Case(
        case_id=str(row["state_id"]),
        role=f"same_category_{row['pair_id']}_{row['state']}",
        mechanisms=(),
        source=str(row["source"]),
        target_statement=str(row["target_statement"]),
        theorem_name=str(row["theorem_name"]),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-spec", type=Path, required=True)
    parser.add_argument("--pinned-project", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--prereg-commit", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    args = parser.parse_args()

    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"output directory not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    spec_path = args.case_spec.resolve()
    spec = load_spec(spec_path)
    states = flatten_states(spec)
    spec_sha256 = base.sha256_bytes(spec_path.read_bytes())

    project = args.pinned_project.resolve()
    environment = base.environment_snapshot(project)
    base.json_dump(out / "ENVIRONMENT.json", environment)
    errors = base.validate_environment(environment)
    if errors:
        base.json_dump(out / "STATUS.json", {
            "schema_version": SCHEMA_VERSION,
            "status": "BLOCKED_ENVIRONMENT",
            "publication_claim_eligible": False,
            "errors": errors,
        })
        raise RuntimeError("; ".join(errors))

    base.json_dump(out / "CASE_SPEC_USED.json", spec)
    base.json_dump(out / "PAIR_MANIFEST.json", {
        "schema_version": "p02_same_category_pair_manifest_v1",
        "prereg_commit": args.prereg_commit,
        "case_spec_sha256": spec_sha256,
        "pairs": [
            {
                "pair_id": pair["pair_id"],
                "declared_category": pair["category"],
                "state_ids": [row["state_id"] for row in pair["states"]],
            }
            for pair in spec["pairs"]
        ],
    })

    with tempfile.TemporaryDirectory(prefix="p02-same-category-") as tmp:
        scratch = Path(tmp)
        for row in states:
            case = as_case(row)
            observations = base.collect_case(
                case, project=project, scratch=scratch,
                timeout_seconds=args.timeout_seconds,
            )
            base.write_case_bundle(out, case, observations)

    post = base.git_observation(project, "status", "--porcelain")
    status = base.successful_stdout(post)
    if status is None or status:
        raise RuntimeError(f"pinned project changed during run: {status!r}")

    run = {
        "schema_version": SCHEMA_VERSION,
        "status": "RAW_SAME_CATEGORY_EXECUTED_NOT_CLASSIFIED",
        "publication_claim_eligible": False,
        "classification_performed": False,
        "prereg_commit": args.prereg_commit,
        "case_spec_sha256": spec_sha256,
        "expected_results_read_during_collection": False,
        "expected_project_sha": EXPECTED_PROJECT_SHA,
        "expected_toolchain": EXPECTED_TOOLCHAIN,
        "expected_classifier_v2_blob_sha": EXPECTED_CLASSIFIER_BLOB_SHA,
        "n_cases": len(states),
        "n_pairs": len(spec["pairs"]),
        "timeout_seconds": args.timeout_seconds,
        "toolchain_transport": os.environ.get("P02_TOOLCHAIN_TRANSPORT"),
        "toolchain_archive_sha256": os.environ.get("P02_TOOLCHAIN_ARCHIVE_SHA256") or None,
        "harness_branch_sha": os.environ.get("GITHUB_SHA"),
        "non_claims": [
            "This bundle contains raw observations only.",
            "The collector receives the source-only CASE_SPEC and does not receive EXPECTED_RESULTS.",
            "No category or agreement claim is assigned during collection.",
            "The study is a targeted constructed extension and is not a population sample of Lean failures.",
        ],
    }
    base.json_dump(out / "RUN_MANIFEST.json", run)
    files = base.inventory(out)
    integrity = {
        "schema_version": "p02_same_category_raw_integrity_v1",
        "publication_claim_eligible": False,
        "n_files": len(files),
        "files": files,
        "bundle_digest": base.canonical_digest({"files": files}),
    }
    base.json_dump(out / "INTEGRITY_MANIFEST.json", integrity)
    print(json.dumps({"run": run, "integrity": integrity}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
