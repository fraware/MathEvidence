#!/usr/bin/env python3
"""Collect raw Lean observations for the preregistered P02 v2 repair plan.

This script performs the 80 frozen one-mechanism counterfactual repairs and one
five-step cumulative trajectory. It assigns no native classes. Repair metadata
is stored separately from observation records so later classification can use
only source + raw process observations under the already-frozen decision rules.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import p02_native_v2_raw as base

SCHEMA_VERSION = "p02_native_repair_raw_v2"
PLAN_VERSION = "p02_native_repair_plan_v2"
EXPECTED_BASELINE_BUNDLE_DIGEST = (
    "sha256:482f21fe8bafd4e3784e7c3a7e0a5dc103820c087691fc0e66e5ff3dd61a63ea"
)
EXPECTED_PLAN_DIGEST = (
    "sha256:0b610ed6bd984acf6403046e5adf56ed5f8ae0d9a6fbce4178c6a8ede4e20565"
)
CUMULATIVE_REPAIR_ORDER: tuple[str, ...] = (
    "SOURCE_CORRUPTION",
    "UNKNOWN_TYPE",
    "INVALID_PROOF",
    "PROHIBITED_PLACEHOLDER",
    "WRONG_TARGET",
)

_HELPER = "theorem p02Placeholder : True := by\n  sorry\n\n"
_CORRUPT_DECL_RE = re.compile(
    r"^theorem p02Native \(n : ([A-Za-z0-9_'.]+) : (.+) := by$",
    re.MULTILINE,
)


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def repair_source(source: str, mechanism: str) -> str:
    if mechanism not in base.FAULT_MECHANISMS:
        raise ValueError(f"unknown repair mechanism: {mechanism}")
    if mechanism == "SOURCE_CORRUPTION":
        matches = list(_CORRUPT_DECL_RE.finditer(source))
        if len(matches) != 1:
            raise ValueError(
                f"expected exactly one source-corruption site, found {len(matches)}"
            )
        match = matches[0]
        replacement = (
            f"theorem {base.THEOREM_NAME} (n : {match.group(1)}) : "
            f"{match.group(2)} := by"
        )
        return source[: match.start()] + replacement + source[match.end() :]
    if mechanism == "UNKNOWN_TYPE":
        if source.count("P02MissingType") != 1:
            raise ValueError("expected exactly one P02MissingType repair site")
        return source.replace("P02MissingType", "Nat", 1)
    if mechanism == "PROHIBITED_PLACEHOLDER":
        if not source.startswith(_HELPER) or source.count(_HELPER) != 1:
            raise ValueError("expected exactly one prohibited-placeholder helper")
        return source[len(_HELPER) :]
    if mechanism == "INVALID_PROOF":
        if source.count("  exact n\n") != 1:
            raise ValueError("expected exactly one invalid-proof repair site")
        return source.replace("  exact n\n", "  rfl\n", 1)
    if mechanism == "WRONG_TARGET":
        token = ": 0 = 0 := by"
        if source.count(token) != 1:
            raise ValueError("expected exactly one wrong-target repair site")
        return source.replace(token, ": n = n := by", 1)
    raise AssertionError(mechanism)


def build_repair_plan() -> dict[str, Any]:
    edges: list[dict[str, Any]] = []
    for case in base.build_corpus()[:32]:
        if not case.mechanisms:
            continue
        for mechanism in case.mechanisms:
            remaining = tuple(m for m in case.mechanisms if m != mechanism)
            after = repair_source(case.source, mechanism)
            expected = base.render_case_source(remaining)
            if after != expected:
                raise AssertionError(
                    f"non-local repair {case.case_id} / {mechanism}"
                )
            edges.append(
                {
                    "edge_id": f"{case.case_id}__FIX__{mechanism}",
                    "case_id": case.case_id,
                    "repair_mechanism": mechanism,
                    "mechanisms_before": list(case.mechanisms),
                    "mechanisms_after": list(remaining),
                    "before_source_sha256": sha256_text(case.source),
                    "after_source_sha256": sha256_text(after),
                }
            )
    if len(edges) != 80:
        raise AssertionError(f"repair edge cardinality mismatch: {len(edges)}")
    payload = {
        "plan_version": PLAN_VERSION,
        "corpus_version": "p02_native_corpus_v2",
        "corpus_digest": base.EXPECTED_CORPUS_DIGEST,
        "n_edges": len(edges),
        "cumulative_repair_order": list(CUMULATIVE_REPAIR_ORDER),
        "edges": edges,
    }
    payload["plan_digest"] = base.canonical_digest(payload)
    if payload["plan_digest"] != EXPECTED_PLAN_DIGEST:
        raise RuntimeError(
            f"repair plan digest mismatch: {payload['plan_digest']} != {EXPECTED_PLAN_DIGEST}"
        )
    return payload


def assert_pairwise_commutativity() -> None:
    for case in base.build_corpus()[:32]:
        mechs = case.mechanisms
        for i, left in enumerate(mechs):
            for right in mechs[i + 1 :]:
                left_right = repair_source(repair_source(case.source, left), right)
                right_left = repair_source(repair_source(case.source, right), left)
                if left_right != right_left:
                    raise AssertionError(
                        f"non-commuting repairs {case.case_id}: {left}, {right}"
                    )


def verify_baseline(raw_root: Path) -> dict[str, Any]:
    manifest = json.loads(
        (raw_root / "INTEGRITY_MANIFEST.json").read_text(encoding="utf-8")
    )
    observed_files = base.inventory(raw_root)
    if manifest.get("files") != observed_files:
        raise RuntimeError("baseline raw inventory mismatch")
    observed_digest = base.canonical_digest({"files": observed_files})
    if observed_digest != EXPECTED_BASELINE_BUNDLE_DIGEST:
        raise RuntimeError(
            f"baseline raw bundle mismatch: {observed_digest} != {EXPECTED_BASELINE_BUNDLE_DIGEST}"
        )
    corpus = json.loads(
        (raw_root / "CORPUS_MANIFEST.json").read_text(encoding="utf-8")
    )
    if corpus.get("observed_corpus_digest") != base.EXPECTED_CORPUS_DIGEST:
        raise RuntimeError("baseline corpus digest mismatch")
    return {
        "baseline_bundle_digest": observed_digest,
        "baseline_corpus_digest": corpus.get("observed_corpus_digest"),
    }


def write_repair_case(
    out_root: Path,
    case_id: str,
    source: str,
    target: str,
    repair_meta: dict[str, Any],
    observations: dict[str, base.Observation | None],
) -> None:
    case_dir = out_root / "cases" / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "candidate.lean").write_text(source, encoding="utf-8")
    (case_dir / "target.txt").write_text(target + "\n", encoding="utf-8")
    base.json_dump(case_dir / "repair_meta.json", repair_meta)
    observation_json: dict[str, Any] = {
        "case_id": case_id,
        "source_empty": not source.strip(),
    }
    for key, obs in observations.items():
        observation_json[key] = None if obs is None else {
            "command": list(obs.command),
            "returncode": obs.returncode,
            "stdout": obs.stdout,
            "stderr": obs.stderr,
            "elapsed_seconds": obs.elapsed_seconds,
            "timed_out": obs.timed_out,
            "spawn_error": obs.spawn_error,
        }
        if obs is not None:
            (case_dir / f"{key}.stdout.txt").write_text(obs.stdout, encoding="utf-8")
            (case_dir / f"{key}.stderr.txt").write_text(obs.stderr, encoding="utf-8")
    base.json_dump(case_dir / "observations.json", observation_json)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--pinned-project", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    args = parser.parse_args()

    baseline = args.baseline.resolve()
    project = args.pinned_project.resolve()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"repair output directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    baseline_identity = verify_baseline(baseline)
    plan = build_repair_plan()
    assert_pairwise_commutativity()
    environment = base.environment_snapshot(project)
    env_errors = base.validate_environment(environment)
    base.json_dump(out / "ENVIRONMENT.json", environment)
    if env_errors:
        raise RuntimeError("repair environment invalid: " + "; ".join(env_errors))
    base.json_dump(out / "REPAIR_PLAN.json", plan)

    case_by_id = {case.case_id: case for case in base.build_corpus()[:32]}
    n_written = 0
    for edge in plan["edges"]:
        case = case_by_id[edge["case_id"]]
        baseline_source_path = baseline / "cases" / case.case_id / "candidate.lean"
        before_source = baseline_source_path.read_text(encoding="utf-8")
        if before_source != case.source:
            raise RuntimeError(f"retained baseline source drift: {case.case_id}")
        after_source = repair_source(before_source, edge["repair_mechanism"])
        remaining = tuple(edge["mechanisms_after"])
        if after_source != base.render_case_source(remaining):
            raise RuntimeError(f"repair-source drift: {edge['edge_id']}")
        repaired = base.Case(
            case_id=edge["edge_id"],
            role="counterfactual_repair",
            mechanisms=remaining,
            source=after_source,
            target_statement=case.target_statement,
            theorem_name=case.theorem_name,
        )
        import tempfile
        with tempfile.TemporaryDirectory(prefix="p02-repair-edge-") as tmp:
            observations = base.collect_case(
                repaired,
                project=project,
                scratch=Path(tmp),
                timeout_seconds=args.timeout_seconds,
            )
        write_repair_case(
            out,
            edge["edge_id"],
            after_source,
            case.target_statement,
            {
                **edge,
                "role": "counterfactual_repair",
                "baseline_case_id": case.case_id,
            },
            observations,
        )
        n_written += 1

    full = next(
        case
        for case in base.build_corpus()[:32]
        if set(case.mechanisms) == set(base.FAULT_MECHANISMS)
    )
    current_source = (baseline / "cases" / full.case_id / "candidate.lean").read_text(
        encoding="utf-8"
    )
    if current_source != full.source:
        raise RuntimeError("full-fault retained baseline source drift")
    remaining = list(full.mechanisms)
    for step, mechanism in enumerate(CUMULATIVE_REPAIR_ORDER, start=1):
        before_source = current_source
        current_source = repair_source(current_source, mechanism)
        remaining.remove(mechanism)
        expected = base.render_case_source(tuple(remaining))
        if current_source != expected:
            raise RuntimeError(f"cumulative source drift after {mechanism}")
        cumulative_id = f"ND2-CUMULATIVE-{step}-{mechanism}"
        repaired = base.Case(
            case_id=cumulative_id,
            role="cumulative_repair",
            mechanisms=tuple(remaining),
            source=current_source,
            target_statement=full.target_statement,
            theorem_name=full.theorem_name,
        )
        import tempfile
        with tempfile.TemporaryDirectory(prefix="p02-repair-cumulative-") as tmp:
            observations = base.collect_case(
                repaired,
                project=project,
                scratch=Path(tmp),
                timeout_seconds=args.timeout_seconds,
            )
        write_repair_case(
            out,
            cumulative_id,
            current_source,
            full.target_statement,
            {
                "role": "cumulative_repair",
                "step": step,
                "repair_mechanism": mechanism,
                "mechanisms_after": list(remaining),
                "baseline_case_id": full.case_id,
                "before_source_sha256": sha256_text(before_source),
                "after_source_sha256": sha256_text(current_source),
            },
            observations,
        )
        n_written += 1

    if n_written != 85:
        raise AssertionError(f"expected 85 repair observations, wrote {n_written}")
    post_status = base.git_observation(project, "status", "--porcelain")
    post_status_text = base.successful_stdout(post_status)
    if post_status_text is None or post_status_text:
        raise RuntimeError(f"pinned project changed during repair run: {post_status_text!r}")

    run_manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "RAW_REPAIR_OBSERVATIONS_EXECUTED_NOT_CLASSIFIED",
        "publication_claim_eligible": False,
        "plan_digest": EXPECTED_PLAN_DIGEST,
        "n_counterfactual_edges": 80,
        "n_cumulative_steps": 5,
        "n_observation_cases": n_written,
        "cumulative_repair_order": list(CUMULATIVE_REPAIR_ORDER),
        "classification_performed": False,
        "toolchain_transport": os.environ.get("P02_TOOLCHAIN_TRANSPORT", "elan_release_host"),
        "toolchain_archive_sha256": os.environ.get("P02_TOOLCHAIN_ARCHIVE_SHA256"),
        "toolchain_expected_identity": "Lean 4.14.0 commit 410fab728470",
        **baseline_identity,
        "non_claims": [
            "This bundle contains raw repair/recheck observations only.",
            "Repair metadata is stored separately from observation records.",
            "No native-class transition, masking rate, or repair success claim is assigned here.",
            "The UNKNOWN_TYPE mechanism remains in the preregistered plan even if baseline evidence shows it is native-inert.",
            "Toolchain transport metadata records how the exact Lean 4.14.0 binary was obtained; it does not alter the frozen repair plan."
        ],
    }
    base.json_dump(out / "RUN_MANIFEST.json", run_manifest)
    files = base.inventory(out)
    integrity = {
        "schema_version": "p02_native_repair_raw_integrity_v2",
        "publication_claim_eligible": False,
        "n_files": len(files),
        "files": files,
        "bundle_digest": base.canonical_digest({"files": files}),
    }
    base.json_dump(out / "INTEGRITY_MANIFEST.json", integrity)
    print(json.dumps({"run": run_manifest, "integrity": integrity}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
