#!/usr/bin/env python3
"""Analyze transferred-model state and intervention results for MATH-AI replication.

Construction labels are joined only after state and successor observations have
been independently classified with the frozen v2 classifier.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import p02_native_v2_raw as frozen
import p02_mathai_cross_context_final_feasibility as design

SCHEMA_VERSION = "p02_mathai_cross_context_full_analysis_v1"

SIGNATURE = {
    "SOURCE_CORRUPTION": "FRONTEND_REJECT",
    "INVALID_PROOF": "ENVIRONMENT_OR_ELAB_REJECT",
    "PROHIBITED_PLACEHOLDER": "TOOLCHAIN_ACCEPT_POLICY_REJECT",
    "WRONG_TARGET": "TOOLCHAIN_ACCEPT_TARGET_MISMATCH",
}
PRECEDENCE = tuple(design.MECHANISMS)
CLEAN_CLASS = "TOOLCHAIN_ACCEPT_TARGET_MATCH"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def expected_class(mechanisms: list[str] | tuple[str, ...]) -> str:
    present = set(mechanisms)
    for mechanism in PRECEDENCE:
        if mechanism in present:
            return SIGNATURE[mechanism]
    return CLEAN_CLASS


def state_rows(raw_root: Path, classified_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_dir in sorted((raw_root / "cases").iterdir()):
        if not case_dir.is_dir():
            continue
        construction = load_json(case_dir / "construction.json")
        classification = load_json(
            classified_root / "cases" / case_dir.name / "classification.json"
        )
        mechanisms = list(construction["mechanisms"])
        observed = classification["derived_native_class"]
        predicted = expected_class(mechanisms)
        context_id = case_dir.name.split("-FULL-", 1)[0]
        rows.append(
            {
                "case_id": case_dir.name,
                "context_id": context_id,
                "mechanisms": mechanisms,
                "predicted_class": predicted,
                "observed_class": observed,
                "transferred_model_match": observed == predicted,
            }
        )
    if len(rows) != 48:
        raise RuntimeError(f"expected 48 state rows, found {len(rows)}")
    return rows


def edge_rows(
    states: list[dict[str, Any]],
    repair_raw: Path,
    repair_classified: Path,
) -> list[dict[str, Any]]:
    state_by_id = {row["case_id"]: row for row in states}
    rows: list[dict[str, Any]] = []
    for case_dir in sorted((repair_raw / "cases").iterdir()):
        if not case_dir.is_dir():
            continue
        meta = load_json(case_dir / "repair_metadata.json")
        after_cls = load_json(
            repair_classified / "cases" / case_dir.name / "classification.json"
        )["derived_native_class"]
        before = state_by_id[meta["before_state_id"]]
        before_mechanisms = list(meta["mechanisms_before"])
        after_mechanisms = list(meta["mechanisms_after"])
        removed = meta["repair_mechanism"]

        first_present = next(m for m in PRECEDENCE if m in set(before_mechanisms))
        category = "visible_active" if removed == first_present else "masked_active"
        predicted_before = expected_class(before_mechanisms)
        predicted_after = expected_class(after_mechanisms)
        expected_transition = (
            "class_change" if predicted_before != predicted_after else "class_preserved"
        )
        observed_transition = (
            "class_change" if before["observed_class"] != after_cls else "class_preserved"
        )
        rows.append(
            {
                "edge_id": case_dir.name,
                "context_id": meta["context_id"],
                "before_state_id": meta["before_state_id"],
                "repair_mechanism": removed,
                "mechanisms_before": before_mechanisms,
                "mechanisms_after": after_mechanisms,
                "category": category,
                "predicted_before_class": predicted_before,
                "observed_before_class": before["observed_class"],
                "predicted_after_class": predicted_after,
                "observed_after_class": after_cls,
                "expected_transition": expected_transition,
                "observed_transition": observed_transition,
                "transferred_transition_match": observed_transition == expected_transition,
            }
        )
    if len(rows) != 96:
        raise RuntimeError(f"expected 96 edge rows, found {len(rows)}")
    return rows


def summarize_context(context_id: str, states: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    s = [r for r in states if r["context_id"] == context_id]
    e = [r for r in edges if r["context_id"] == context_id]
    categories = Counter(r["category"] for r in e)
    transitions = Counter((r["category"], r["observed_transition"]) for r in e)
    return {
        "context_id": context_id,
        "n_states": len(s),
        "state_model_matches": sum(r["transferred_model_match"] for r in s),
        "state_model_mismatches": sum(not r["transferred_model_match"] for r in s),
        "n_edges": len(e),
        "edge_model_matches": sum(r["transferred_transition_match"] for r in e),
        "edge_model_mismatches": sum(not r["transferred_transition_match"] for r in e),
        "visible_active_edges": categories["visible_active"],
        "visible_active_class_changes": transitions[("visible_active", "class_change")],
        "visible_active_class_preserved": transitions[("visible_active", "class_preserved")],
        "masked_active_edges": categories["masked_active"],
        "masked_active_class_changes": transitions[("masked_active", "class_change")],
        "masked_active_class_preserved": transitions[("masked_active", "class_preserved")],
        "observed_state_class_counts": dict(sorted(Counter(r["observed_class"] for r in s).items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--states-raw", type=Path, required=True)
    parser.add_argument("--states-classified", type=Path, required=True)
    parser.add_argument("--repairs-raw", type=Path, required=True)
    parser.add_argument("--repairs-classified", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"output directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    states = state_rows(args.states_raw.resolve(), args.states_classified.resolve())
    edges = edge_rows(states, args.repairs_raw.resolve(), args.repairs_classified.resolve())

    context_ids = [ctx.context_id for ctx in design.CONTEXTS]
    summaries = [summarize_context(cid, states, edges) for cid in context_ids]

    aggregate = {
        "n_contexts": 3,
        "n_states": 48,
        "state_model_matches": sum(r["transferred_model_match"] for r in states),
        "state_model_mismatches": sum(not r["transferred_model_match"] for r in states),
        "n_edges": 96,
        "edge_model_matches": sum(r["transferred_transition_match"] for r in edges),
        "edge_model_mismatches": sum(not r["transferred_transition_match"] for r in edges),
        "visible_active_edges": sum(r["category"] == "visible_active" for r in edges),
        "visible_active_class_changes": sum(
            r["category"] == "visible_active" and r["observed_transition"] == "class_change"
            for r in edges
        ),
        "masked_active_edges": sum(r["category"] == "masked_active" for r in edges),
        "masked_active_class_preserved": sum(
            r["category"] == "masked_active" and r["observed_transition"] == "class_preserved"
            for r in edges
        ),
    }

    result = {
        "schema_version": SCHEMA_VERSION,
        "status": "ANALYZED_PENDING_INDEPENDENT_REVIEW",
        "publication_claim_eligible": False,
        "transferred_prediction_modified": False,
        "signature_map": SIGNATURE,
        "precedence": list(PRECEDENCE),
        "clean_class": CLEAN_CLASS,
        "contexts": summaries,
        "aggregate": aggregate,
        "states": states,
        "edges": edges,
        "non_claims": [
            "The accepted 32-state/80-edge primary denominators are not pooled into this extension.",
            "This extension remains one pinned Lean 4.14.0 project and does not establish cross-version stability.",
            "State and edge matches do not establish prevalence in natural Lean developments.",
            "No autonomous repair agent is evaluated.",
            "Publication promotion remains blocked pending independent recomputation.",
        ],
    }
    frozen.json_dump(out / "FULL_REPLICATION_ANALYSIS.json", result)

    files = frozen.inventory(out)
    integrity = {
        "schema_version": "p02_mathai_cross_context_full_analysis_integrity_v1",
        "publication_claim_eligible": False,
        "n_files": len(files),
        "files": files,
        "bundle_digest": frozen.canonical_digest({"files": files}),
    }
    frozen.json_dump(out / "INTEGRITY_MANIFEST.json", integrity)
    print(json.dumps({"aggregate": aggregate, "contexts": summaries}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
