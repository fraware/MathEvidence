#!/usr/bin/env python3
"""Execute all 96 frozen one-mechanism removals for cross-context replication.

Each successor candidate is executed afresh. Repair metadata is written
separately from raw observations so classification remains blind to the planted
mechanism labels.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import p02_native_v2_raw as frozen
import p02_mathai_cross_context_final_feasibility as design
import p02_mathai_cross_context_full_states as states

SCHEMA_VERSION = "p02_mathai_cross_context_full_repairs_raw_v1"


def subset_rows() -> tuple[tuple[str, ...], ...]:
    return states.all_subsets()


def state_id(ctx: design.Context, mechanisms: tuple[str, ...]) -> str:
    rows = subset_rows()
    i = rows.index(tuple(mechanisms))
    suffix = "CLEAN" if not mechanisms else "+".join(mechanisms)
    return f"{ctx.context_id}-FULL-{i:02d}-{suffix}"


def edge_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ctx in design.CONTEXTS:
        for before in subset_rows():
            if not before:
                continue
            for removed in before:
                after = tuple(m for m in before if m != removed)
                before_id = state_id(ctx, before)
                edge_id = f"{before_id}__FIX__{removed}"
                rows.append(
                    {
                        "edge_id": edge_id,
                        "context_id": ctx.context_id,
                        "before_state_id": before_id,
                        "repair_mechanism": removed,
                        "mechanisms_before": list(before),
                        "mechanisms_after": list(after),
                        "before_source_sha256": frozen.sha256_bytes(
                            design.render_source(ctx, before).encode("utf-8")
                        ),
                        "after_source_sha256": frozen.sha256_bytes(
                            design.render_source(ctx, after).encode("utf-8")
                        ),
                    }
                )
    if len(rows) != 96:
        raise AssertionError(f"expected 96 repair edges, found {len(rows)}")
    if len({r["edge_id"] for r in rows}) != 96:
        raise AssertionError("duplicate repair edge id")
    counts = {ctx.context_id: 0 for ctx in design.CONTEXTS}
    for row in rows:
        counts[row["context_id"]] += 1
    if set(counts.values()) != {32}:
        raise AssertionError(f"unexpected per-context edge counts: {counts}")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pinned-project", type=Path, required=True)
    parser.add_argument("--states-raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    args = parser.parse_args()

    project = args.pinned_project.resolve()
    states_raw = args.states_raw.resolve()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"output directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    states_integrity = json.loads((states_raw / "INTEGRITY_MANIFEST.json").read_text())
    observed_state_files = frozen.inventory(states_raw)
    observed_state_digest = frozen.canonical_digest({"files": observed_state_files})
    if states_integrity.get("bundle_digest") != observed_state_digest:
        raise RuntimeError("state raw bundle integrity mismatch")
    state_run = json.loads((states_raw / "RUN_MANIFEST.json").read_text())
    if state_run.get("n_cases") != 48 or state_run.get("classification_performed") is not False:
        raise RuntimeError("unexpected state-run identity")

    environment = frozen.environment_snapshot(project)
    frozen.json_dump(out / "ENVIRONMENT.json", environment)
    errors = frozen.validate_environment(environment)
    if errors:
        raise RuntimeError("; ".join(errors))

    rows = edge_rows()
    plan = {
        "schema_version": "p02_mathai_cross_context_full_repair_plan_v1",
        "prospective_design_date": "2026-08-27",
        "full_replication_freeze_date": "2026-09-30",
        "state_raw_bundle_digest": observed_state_digest,
        "mechanisms": list(design.MECHANISMS),
        "n_edges": 96,
        "n_edges_per_context": 32,
        "edges": rows,
    }
    plan["plan_digest"] = frozen.canonical_digest(
        {k: v for k, v in plan.items() if k != "plan_digest"}
    )
    frozen.json_dump(out / "REPAIR_PLAN.json", plan)

    contexts = {ctx.context_id: ctx for ctx in design.CONTEXTS}
    with tempfile.TemporaryDirectory(prefix="p02-mathai-xc-full-repairs-") as tmp:
        scratch = Path(tmp)
        for row in rows:
            ctx = contexts[row["context_id"]]
            after = tuple(row["mechanisms_after"])
            case = frozen.Case(
                case_id=row["edge_id"],
                role="cross_context_full_single_repair",
                mechanisms=after,
                source=design.render_source(ctx, after),
                target_statement=ctx.target_statement,
                theorem_name=design.theorem_name(ctx),
            )
            obs = frozen.collect_case(
                case,
                project=project,
                scratch=scratch,
                timeout_seconds=args.timeout_seconds,
            )
            frozen.write_case_bundle(out, case, obs)
            frozen.json_dump(
                out / "cases" / case.case_id / "repair_metadata.json",
                row,
            )

    post = frozen.git_observation(project, "status", "--porcelain")
    post_text = frozen.successful_stdout(post)
    if post_text is None or post_text:
        raise RuntimeError(f"pinned project changed during repair run: {post_text!r}")

    run = {
        "schema_version": SCHEMA_VERSION,
        "status": "FULL_REPAIR_RAW_EXECUTED_NOT_CLASSIFIED",
        "publication_claim_eligible": False,
        "classification_performed": False,
        "n_cases": 96,
        "n_edges": 96,
        "n_contexts": 3,
        "n_edges_per_context": 32,
        "repair_plan_digest": plan["plan_digest"],
        "state_raw_bundle_digest": observed_state_digest,
        "harness_branch_sha": os.environ.get("GITHUB_SHA"),
        "non_claims": [
            "This bundle contains raw successor observations only.",
            "Repair metadata is stored separately from observation records.",
            "No class-change or masking result is assigned before downstream classification and analysis.",
            "Publication promotion requires independent recomputation.",
        ],
    }
    frozen.json_dump(out / "RUN_MANIFEST.json", run)
    files = frozen.inventory(out)
    integrity = {
        "schema_version": "p02_mathai_cross_context_full_repairs_integrity_v1",
        "publication_claim_eligible": False,
        "n_files": len(files),
        "files": files,
        "bundle_digest": frozen.canonical_digest({"files": files}),
    }
    frozen.json_dump(out / "INTEGRITY_MANIFEST.json", integrity)
    print(json.dumps({"run": run, "integrity": integrity}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
