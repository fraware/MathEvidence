#!/usr/bin/env python3
"""Analyze post-review Lean 4.34.1 transfer against the accepted P02 rule."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import p02_native_v2_raw as base

ACTIVE_PRECEDENCE = (
    "SOURCE_CORRUPTION",
    "INVALID_PROOF",
    "PROHIBITED_PLACEHOLDER",
    "WRONG_TARGET",
)
SIGNATURE = {
    "SOURCE_CORRUPTION": "FRONTEND_REJECT",
    "INVALID_PROOF": "ENVIRONMENT_OR_ELAB_REJECT",
    "PROHIBITED_PLACEHOLDER": "TOOLCHAIN_ACCEPT_POLICY_REJECT",
    "WRONG_TARGET": "TOOLCHAIN_ACCEPT_TARGET_MISMATCH",
}
INERT = "UNKNOWN_TYPE"
CLEAN = "TOOLCHAIN_ACCEPT_TARGET_MATCH"


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def predict(mechanisms: list[str] | tuple[str, ...]) -> str:
    present = set(mechanisms)
    for m in ACTIVE_PRECEDENCE:
        if m in present:
            return SIGNATURE[m]
    return CLEAN


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--states-raw", type=Path, required=True)
    p.add_argument("--states-classified", type=Path, required=True)
    p.add_argument("--repairs-raw", type=Path, required=True)
    p.add_argument("--repairs-classified", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()

    out = a.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"analysis output is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    states: list[dict[str, Any]] = []
    for d in sorted((a.states_raw.resolve() / "cases").iterdir()):
        if not d.is_dir():
            continue
        construction = read(d / "construction.json")
        mechanisms = list(construction["mechanisms"])
        observed = read(
            a.states_classified.resolve() / "cases" / d.name / "classification.json"
        )["derived_native_class"]
        expected = predict(mechanisms)
        states.append(
            {
                "case_id": d.name,
                "mechanisms": mechanisms,
                "predicted_class": expected,
                "observed_class": observed,
                "transferred_model_match": expected == observed,
            }
        )
    if len(states) != 32:
        raise RuntimeError(f"expected 32 states, found {len(states)}")
    state_map = {r["case_id"]: r for r in states}

    edges: list[dict[str, Any]] = []
    for d in sorted((a.repairs_raw.resolve() / "cases").iterdir()):
        if not d.is_dir():
            continue
        meta = read(d / "repair_metadata.json")
        before = state_map[meta["before_state_id"]]
        after_observed = read(
            a.repairs_classified.resolve() / "cases" / d.name / "classification.json"
        )["derived_native_class"]
        before_mechs = list(meta["mechanisms_before"])
        after_mechs = list(meta["mechanisms_after"])
        removed = meta["repair_mechanism"]

        if removed == INERT:
            category = "native_inert"
        else:
            active_before = [m for m in ACTIVE_PRECEDENCE if m in set(before_mechs)]
            if not active_before:
                raise RuntimeError(f"active repair edge lacks active mechanism: {d.name}")
            category = "visible_active" if removed == active_before[0] else "masked_active"

        expected_before = predict(before_mechs)
        expected_after = predict(after_mechs)
        observed_change = before["observed_class"] != after_observed
        expected_change = expected_before != expected_after
        edges.append(
            {
                "edge_id": d.name,
                "repair_mechanism": removed,
                "mechanisms_before": before_mechs,
                "mechanisms_after": after_mechs,
                "category": category,
                "predicted_before_class": expected_before,
                "observed_before_class": before["observed_class"],
                "predicted_after_class": expected_after,
                "observed_after_class": after_observed,
                "expected_transition": "class_change" if expected_change else "class_preserved",
                "observed_transition": "class_change" if observed_change else "class_preserved",
                "transferred_transition_match": expected_change == observed_change,
            }
        )
    if len(edges) != 80:
        raise RuntimeError(f"expected 80 edges, found {len(edges)}")

    categories = Counter(r["category"] for r in edges)
    aggregate = {
        "n_states": 32,
        "state_model_matches": sum(r["transferred_model_match"] for r in states),
        "state_model_mismatches": sum(not r["transferred_model_match"] for r in states),
        "observed_state_class_counts": dict(sorted(Counter(r["observed_class"] for r in states).items())),
        "n_edges": 80,
        "edge_model_matches": sum(r["transferred_transition_match"] for r in edges),
        "edge_model_mismatches": sum(not r["transferred_transition_match"] for r in edges),
        "visible_active_edges": categories["visible_active"],
        "visible_active_class_changes": sum(
            r["category"] == "visible_active" and r["observed_transition"] == "class_change"
            for r in edges
        ),
        "masked_active_edges": categories["masked_active"],
        "masked_active_class_preserved": sum(
            r["category"] == "masked_active" and r["observed_transition"] == "class_preserved"
            for r in edges
        ),
        "native_inert_edges": categories["native_inert"],
        "native_inert_class_preserved": sum(
            r["category"] == "native_inert" and r["observed_transition"] == "class_preserved"
            for r in edges
        ),
    }
    result = {
        "schema_version": "p02_mathai_lean434_version_transfer_analysis_v1",
        "status": "ANALYZED_PENDING_INDEPENDENT_REVIEW",
        "publication_claim_eligible": False,
        "evidence_class": "post_review_version_transfer",
        "transferred_prediction_modified": False,
        "target_toolchain": "leanprover/lean4:v4.34.1",
        "active_precedence": list(ACTIVE_PRECEDENCE),
        "signature_map": SIGNATURE,
        "inert_mechanism": INERT,
        "aggregate": aggregate,
        "states": states,
        "edges": edges,
        "non_claims": [
            "This arm isolates Lean release transport and is not a current-mathlib project replication.",
            "The accepted Lean 4.14.0 denominators remain separate.",
            "A clean transfer would not establish stability across all Lean versions or project configurations.",
            "No autonomous repair agent is evaluated.",
        ],
    }
    base.json_dump(out / "VERSION_TRANSFER_ANALYSIS.json", result)
    files = base.inventory(out)
    integrity = {
        "schema_version": "p02_mathai_lean434_version_transfer_analysis_integrity_v1",
        "publication_claim_eligible": False,
        "n_files": len(files),
        "files": files,
        "bundle_digest": base.canonical_digest({"files": files}),
    }
    base.json_dump(out / "INTEGRITY_MANIFEST.json", integrity)
    print(json.dumps(aggregate, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
