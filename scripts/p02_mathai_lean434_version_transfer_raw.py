#!/usr/bin/env python3
"""Collect post-review Lean 4.34.1 version-transfer observations.

The exact accepted P02 source generator is reused. This script records raw
observations for all 32 lattice states and all 80 one-mechanism removals under
Lean 4.34.1. It performs no operational classification or transfer analysis.
"""
from __future__ import annotations

import argparse
import json
import re
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

import p02_native_v2_raw as base

TOOLCHAIN = "leanprover/lean4:v4.34.1"
EXPECTED_VERSION = "4.34.1"
EXPECTED_COMMIT_PREFIX = "5045d0056413"
SCHEMA = "p02_mathai_lean434_version_transfer_raw_v1"


def run_lean(source: str, *, scratch: Path, stem: str, timeout: float) -> base.Observation:
    path = scratch / f"{stem}.lean"
    path.write_text(source, encoding="utf-8")
    return base.run_process(
        ("elan", "run", TOOLCHAIN, "lean", str(path.resolve())),
        cwd=scratch,
        timeout_seconds=timeout,
    )


def collect(case: base.Case, *, scratch: Path, timeout: float) -> dict[str, base.Observation | None]:
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", case.case_id)
    candidate = run_lean(case.source, scratch=scratch, stem=f"{stem}-candidate", timeout=timeout)
    declaration = None
    target = None
    if candidate.returncode == 0 and not candidate.timed_out and candidate.spawn_error is None:
        declaration = run_lean(
            case.source + f"\n#check {case.theorem_name}\n",
            scratch=scratch,
            stem=f"{stem}-declaration",
            timeout=timeout,
        )
        if declaration.returncode == 0 and not declaration.timed_out and declaration.spawn_error is None:
            target = run_lean(
                case.source + f"\nexample : {case.target_statement} := {case.theorem_name}\n",
                scratch=scratch,
                stem=f"{stem}-target",
                timeout=timeout,
            )
    return {"candidate": candidate, "declaration_probe": declaration, "target_probe": target}


def verify_frozen_generator() -> tuple[base.Case, ...]:
    full = base.build_corpus()
    digest = base.canonical_digest({"cases": base.corpus_projection(full)})
    if digest != base.EXPECTED_CORPUS_DIGEST:
        raise RuntimeError(f"accepted corpus generator digest mismatch: {digest}")
    lattice = full[:32]
    if len(lattice) != 32:
        raise AssertionError("expected first 32 cases to be the complete lattice")
    return tuple(lattice)


def environment_snapshot() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="p02-v434-env-") as tmp:
        obs = base.run_process(
            ("elan", "run", TOOLCHAIN, "lean", "--version"),
            cwd=Path(tmp),
            timeout_seconds=60.0,
        )
    text = (obs.stdout + "\n" + obs.stderr).strip()
    match = base.LEAN_VERSION_RE.search(text)
    version = match.group(1) if match else None
    ok = (
        obs.returncode == 0
        and not obs.timed_out
        and obs.spawn_error is None
        and version == EXPECTED_VERSION
        and EXPECTED_COMMIT_PREFIX in text
    )
    return {
        "toolchain": TOOLCHAIN,
        "expected_version": EXPECTED_VERSION,
        "expected_commit_prefix": EXPECTED_COMMIT_PREFIX,
        "observed_version": version,
        "lean_version_observation": asdict(obs),
        "identity_ok": ok,
    }


def repair_rows(lattice: tuple[base.Case, ...]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for before in lattice:
        for removed in before.mechanisms:
            after = tuple(m for m in before.mechanisms if m != removed)
            rows.append(
                {
                    "edge_id": f"V434-{before.case_id}__FIX__{removed}",
                    "before_state_id": before.case_id,
                    "repair_mechanism": removed,
                    "mechanisms_before": list(before.mechanisms),
                    "mechanisms_after": list(after),
                    "before_source_sha256": base.sha256_bytes(before.source.encode("utf-8")),
                    "after_source_sha256": base.sha256_bytes(base.render_case_source(after).encode("utf-8")),
                }
            )
    if len(rows) != 80:
        raise AssertionError(f"expected 80 repair rows, found {len(rows)}")
    return rows


def seal_bundle(root: Path, *, schema: str, run: dict[str, Any]) -> dict[str, Any]:
    base.json_dump(root / "RUN_MANIFEST.json", run)
    files = base.inventory(root)
    integrity = {
        "schema_version": schema,
        "publication_claim_eligible": False,
        "n_files": len(files),
        "files": files,
        "bundle_digest": base.canonical_digest({"files": files}),
    }
    base.json_dump(root / "INTEGRITY_MANIFEST.json", integrity)
    return integrity


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--timeout-seconds", type=float, default=30.0)
    a = p.parse_args()

    root = a.out.resolve()
    if root.exists() and any(root.iterdir()):
        raise RuntimeError(f"output root is not empty: {root}")
    root.mkdir(parents=True, exist_ok=True)
    states_root = root / "states_raw"
    repairs_root = root / "repairs_raw"
    states_root.mkdir()
    repairs_root.mkdir()

    env = environment_snapshot()
    base.json_dump(root / "ENVIRONMENT.json", env)
    if not env["identity_ok"]:
        raise RuntimeError(f"Lean 4.34.1 identity check failed: {env}")

    lattice = verify_frozen_generator()
    state_spec = {
        "schema_version": "p02_mathai_lean434_state_spec_v1",
        "evidence_class": "post_review_version_transfer",
        "toolchain": TOOLCHAIN,
        "original_corpus_digest": base.EXPECTED_CORPUS_DIGEST,
        "n_states": 32,
        "cases": base.corpus_projection(lattice),
    }
    state_spec["spec_digest"] = base.canonical_digest(
        {k: v for k, v in state_spec.items() if k != "spec_digest"}
    )
    base.json_dump(states_root / "STATE_SPEC.json", state_spec)

    with tempfile.TemporaryDirectory(prefix="p02-v434-states-") as tmp:
        scratch = Path(tmp)
        for case in lattice:
            obs = collect(case, scratch=scratch, timeout=a.timeout_seconds)
            base.write_case_bundle(states_root, case, obs)

    state_run = {
        "schema_version": SCHEMA,
        "status": "LEAN434_STATE_RAW_EXECUTED_NOT_CLASSIFIED",
        "publication_claim_eligible": False,
        "classification_performed": False,
        "n_cases": 32,
        "toolchain": TOOLCHAIN,
        "state_spec_digest": state_spec["spec_digest"],
        "non_claims": [
            "This is a post-review version-transfer arm.",
            "No state-transfer result is assigned before frozen-v2 classification.",
            "The accepted Lean 4.14.0 denominator remains separate.",
        ],
    }
    state_integrity = seal_bundle(
        states_root,
        schema="p02_mathai_lean434_states_integrity_v1",
        run=state_run,
    )

    edges = repair_rows(lattice)
    plan = {
        "schema_version": "p02_mathai_lean434_repair_plan_v1",
        "n_edges": 80,
        "state_raw_bundle_digest": state_integrity["bundle_digest"],
        "edges": edges,
    }
    plan["plan_digest"] = base.canonical_digest(
        {k: v for k, v in plan.items() if k != "plan_digest"}
    )
    base.json_dump(repairs_root / "REPAIR_PLAN.json", plan)

    by_id = {case.case_id: case for case in lattice}
    with tempfile.TemporaryDirectory(prefix="p02-v434-repairs-") as tmp:
        scratch = Path(tmp)
        for row in edges:
            before = by_id[row["before_state_id"]]
            after = tuple(row["mechanisms_after"])
            case = base.Case(
                case_id=row["edge_id"],
                role="lean434_single_repair",
                mechanisms=after,
                source=base.render_case_source(after),
                target_statement=before.target_statement,
                theorem_name=before.theorem_name,
            )
            obs = collect(case, scratch=scratch, timeout=a.timeout_seconds)
            base.write_case_bundle(repairs_root, case, obs)
            base.json_dump(repairs_root / "cases" / case.case_id / "repair_metadata.json", row)

    repair_run = {
        "schema_version": SCHEMA,
        "status": "LEAN434_REPAIR_RAW_EXECUTED_NOT_CLASSIFIED",
        "publication_claim_eligible": False,
        "classification_performed": False,
        "n_cases": 80,
        "n_edges": 80,
        "toolchain": TOOLCHAIN,
        "repair_plan_digest": plan["plan_digest"],
        "non_claims": [
            "This is a post-review version-transfer arm.",
            "No edge-transfer result is assigned before frozen-v2 classification.",
            "The accepted Lean 4.14.0 denominator remains separate.",
        ],
    }
    repair_integrity = seal_bundle(
        repairs_root,
        schema="p02_mathai_lean434_repairs_integrity_v1",
        run=repair_run,
    )

    root_manifest = {
        "schema_version": SCHEMA,
        "status": "RAW_VERSION_TRANSFER_EXECUTED_NOT_CLASSIFIED",
        "publication_claim_eligible": False,
        "toolchain": TOOLCHAIN,
        "states_raw_bundle_digest": state_integrity["bundle_digest"],
        "repairs_raw_bundle_digest": repair_integrity["bundle_digest"],
        "n_state_executions": 32,
        "n_edge_executions": 80,
    }
    base.json_dump(root / "ROOT_MANIFEST.json", root_manifest)
    print(json.dumps(root_manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
