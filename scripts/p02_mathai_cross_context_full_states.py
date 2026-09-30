#!/usr/bin/env python3
"""Execute the frozen 48-state MATH-AI cross-context replication corpus.

This runner uses exactly the contexts sealed by the successful final
feasibility gate and all 16 subsets of the four transferred active mechanisms.
It records raw native/probe observations only. Classification is downstream.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

import p02_native_v2_raw as frozen
import p02_mathai_cross_context_final_feasibility as design

SCHEMA_VERSION = "p02_mathai_cross_context_full_states_raw_v1"
FEASIBILITY_COMMIT = "d4938cea70fe4713b7da9eef8574447f5bb14901"
EXPECTED_FEASIBILITY_RAW_DIGEST = (
    "sha256:fa89084a1484d3dd2e721041f318757d5cde64b16dc42b25cfc9829a21090b0a"
)


def all_subsets() -> tuple[tuple[str, ...], ...]:
    rows: list[tuple[str, ...]] = []
    for r in range(len(design.MECHANISMS) + 1):
        rows.extend(itertools.combinations(design.MECHANISMS, r))
    if len(rows) != 16:
        raise AssertionError(f"expected 16 subsets, found {len(rows)}")
    return tuple(rows)


def state_case(ctx: design.Context, mask_index: int, mechanisms: tuple[str, ...]) -> frozen.Case:
    suffix = "CLEAN" if not mechanisms else "+".join(mechanisms)
    return frozen.Case(
        case_id=f"{ctx.context_id}-FULL-{mask_index:02d}-{suffix}",
        role=(
            "cross_context_full_clean"
            if not mechanisms
            else "cross_context_full_singleton"
            if len(mechanisms) == 1
            else "cross_context_full_compound"
        ),
        mechanisms=mechanisms,
        source=design.render_source(ctx, mechanisms),
        target_statement=ctx.target_statement,
        theorem_name=design.theorem_name(ctx),
    )


def build_cases() -> tuple[frozen.Case, ...]:
    subsets = all_subsets()
    cases: list[frozen.Case] = []
    for ctx in design.CONTEXTS:
        for i, mechanisms in enumerate(subsets):
            cases.append(state_case(ctx, i, mechanisms))
    if len(cases) != 48:
        raise AssertionError(f"expected 48 state cases, found {len(cases)}")
    if len({c.case_id for c in cases}) != 48:
        raise AssertionError("duplicate state case id")
    return tuple(cases)


def projection(cases: tuple[frozen.Case, ...]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": case.case_id,
            "role": case.role,
            "mechanisms": list(case.mechanisms),
            "source_sha256": frozen.sha256_bytes(case.source.encode("utf-8")),
            "target_sha256": frozen.sha256_bytes(case.target_statement.encode("utf-8")),
            "theorem_name": case.theorem_name,
        }
        for case in cases
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pinned-project", type=Path, required=True)
    parser.add_argument("--feasibility-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    args = parser.parse_args()

    project = args.pinned_project.resolve()
    feasibility = args.feasibility_root.resolve()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"output directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    audit = json.loads((feasibility / "final_feasibility_audit" / "SMOKE_AUDIT.json").read_text())
    if audit.get("all_three_contexts_feasible") is not True:
        raise RuntimeError("full replication blocked: feasibility gate is not true")
    if audit.get("raw_bundle_digest") != EXPECTED_FEASIBILITY_RAW_DIGEST:
        raise RuntimeError("full replication blocked: feasibility raw digest mismatch")
    if audit.get("transferred_prediction_modified") is not False:
        raise RuntimeError("full replication blocked: transferred prediction was modified")
    if any(ctx.get("transferred_singleton_matches") != 4 for ctx in audit.get("contexts", [])):
        raise RuntimeError("full replication blocked: singleton transfer mismatch")

    environment = frozen.environment_snapshot(project)
    frozen.json_dump(out / "ENVIRONMENT.json", environment)
    errors = frozen.validate_environment(environment)
    if errors:
        raise RuntimeError("; ".join(errors))

    cases = build_cases()
    manifest_rows = projection(cases)
    state_spec = {
        "schema_version": "p02_mathai_cross_context_full_states_spec_v1",
        "prospective_design_date": "2026-08-27",
        "full_replication_freeze_date": "2026-09-30",
        "feasibility_evidence_commit": FEASIBILITY_COMMIT,
        "feasibility_raw_bundle_digest": EXPECTED_FEASIBILITY_RAW_DIGEST,
        "pinned_project_sha": frozen.EXPECTED_PROJECT_SHA,
        "pinned_toolchain": frozen.EXPECTED_TOOLCHAIN,
        "contexts": [asdict(ctx) for ctx in design.CONTEXTS],
        "mechanisms": list(design.MECHANISMS),
        "n_states_per_context": 16,
        "n_state_executions": 48,
        "cases": manifest_rows,
        "transferred_precedence": [
            "FRONTEND_REJECT",
            "ENVIRONMENT_OR_ELAB_REJECT",
            "TOOLCHAIN_ACCEPT_POLICY_REJECT",
            "TOOLCHAIN_ACCEPT_TARGET_MISMATCH",
            "TOOLCHAIN_ACCEPT_TARGET_MATCH",
        ],
    }
    state_spec["spec_digest"] = frozen.canonical_digest(
        {k: v for k, v in state_spec.items() if k != "spec_digest"}
    )
    frozen.json_dump(out / "FULL_STATE_SPEC.json", state_spec)

    with tempfile.TemporaryDirectory(prefix="p02-mathai-xc-full-states-") as tmp:
        scratch = Path(tmp)
        for case in cases:
            obs = frozen.collect_case(
                case,
                project=project,
                scratch=scratch,
                timeout_seconds=args.timeout_seconds,
            )
            frozen.write_case_bundle(out, case, obs)

    post = frozen.git_observation(project, "status", "--porcelain")
    post_text = frozen.successful_stdout(post)
    if post_text is None or post_text:
        raise RuntimeError(f"pinned project changed during state run: {post_text!r}")

    run = {
        "schema_version": SCHEMA_VERSION,
        "status": "FULL_STATE_RAW_EXECUTED_NOT_CLASSIFIED",
        "publication_claim_eligible": False,
        "classification_performed": False,
        "n_cases": 48,
        "n_contexts": 3,
        "n_states_per_context": 16,
        "state_spec_digest": state_spec["spec_digest"],
        "harness_branch_sha": os.environ.get("GITHUB_SHA"),
        "non_claims": [
            "This bundle contains raw state observations only.",
            "Construction metadata is stored separately from observations.",
            "No transferred-model match rate is assigned before downstream classification and analysis.",
            "Publication promotion requires complete edge execution and independent review.",
        ],
    }
    frozen.json_dump(out / "RUN_MANIFEST.json", run)

    files = frozen.inventory(out)
    integrity = {
        "schema_version": "p02_mathai_cross_context_full_states_integrity_v1",
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
