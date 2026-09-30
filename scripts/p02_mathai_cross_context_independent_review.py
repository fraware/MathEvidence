#!/usr/bin/env python3
"""Independent recomputation for the MATH-AI full cross-context replication.

This reviewer does not import the primary analysis implementation. It reads the
sealed construction metadata, frozen-v2 classifications, and repair metadata
directly, recomputes transferred predictions, and then compares its decisions
with the primary analysis row by row.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

MECHANISMS = (
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
CLEAN = "TOOLCHAIN_ACCEPT_TARGET_MATCH"
CONTEXTS = ("CX1R", "RX2", "RX3")


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def predict(mechanisms: list[str]) -> str:
    selected = set(mechanisms)
    for m in MECHANISMS:
        if m in selected:
            return SIGNATURE[m]
    return CLEAN


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--states-raw", type=Path, required=True)
    p.add_argument("--states-classified", type=Path, required=True)
    p.add_argument("--repairs-raw", type=Path, required=True)
    p.add_argument("--repairs-classified", type=Path, required=True)
    p.add_argument("--primary-analysis", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()

    out = a.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"review output is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    states: dict[str, dict[str, Any]] = {}
    for d in sorted((a.states_raw.resolve() / "cases").iterdir()):
        if not d.is_dir():
            continue
        construction = read(d / "construction.json")
        observed = read(
            a.states_classified.resolve() / "cases" / d.name / "classification.json"
        )["derived_native_class"]
        context = d.name.split("-FULL-", 1)[0]
        mechanisms = list(construction["mechanisms"])
        expected = predict(mechanisms)
        states[d.name] = {
            "context_id": context,
            "mechanisms": mechanisms,
            "expected": expected,
            "observed": observed,
            "match": expected == observed,
        }

    if len(states) != 48:
        raise RuntimeError(f"independent review expected 48 states, found {len(states)}")

    edges: dict[str, dict[str, Any]] = {}
    for d in sorted((a.repairs_raw.resolve() / "cases").iterdir()):
        if not d.is_dir():
            continue
        meta = read(d / "repair_metadata.json")
        before = states[meta["before_state_id"]]
        after_observed = read(
            a.repairs_classified.resolve() / "cases" / d.name / "classification.json"
        )["derived_native_class"]
        before_set = list(meta["mechanisms_before"])
        after_set = list(meta["mechanisms_after"])
        removed = meta["repair_mechanism"]
        exposed = next(m for m in MECHANISMS if m in set(before_set))
        category = "visible_active" if removed == exposed else "masked_active"
        expected_before = predict(before_set)
        expected_after = predict(after_set)
        expected_change = expected_before != expected_after
        observed_change = before["observed"] != after_observed
        edges[d.name] = {
            "context_id": meta["context_id"],
            "category": category,
            "expected_change": expected_change,
            "observed_change": observed_change,
            "match": expected_change == observed_change,
        }

    if len(edges) != 96:
        raise RuntimeError(f"independent review expected 96 edges, found {len(edges)}")

    by_context: list[dict[str, Any]] = []
    for context in CONTEXTS:
        s = [v for v in states.values() if v["context_id"] == context]
        e = [v for v in edges.values() if v["context_id"] == context]
        cats = Counter(v["category"] for v in e)
        row = {
            "context_id": context,
            "n_states": len(s),
            "state_matches": sum(v["match"] for v in s),
            "n_edges": len(e),
            "edge_matches": sum(v["match"] for v in e),
            "visible_edges": cats["visible_active"],
            "visible_changes": sum(
                v["category"] == "visible_active" and v["observed_change"] for v in e
            ),
            "masked_edges": cats["masked_active"],
            "masked_preserved": sum(
                v["category"] == "masked_active" and not v["observed_change"] for v in e
            ),
        }
        by_context.append(row)

    aggregate = {
        "n_states": len(states),
        "state_matches": sum(v["match"] for v in states.values()),
        "n_edges": len(edges),
        "edge_matches": sum(v["match"] for v in edges.values()),
        "visible_edges": sum(v["category"] == "visible_active" for v in edges.values()),
        "visible_changes": sum(
            v["category"] == "visible_active" and v["observed_change"]
            for v in edges.values()
        ),
        "masked_edges": sum(v["category"] == "masked_active" for v in edges.values()),
        "masked_preserved": sum(
            v["category"] == "masked_active" and not v["observed_change"]
            for v in edges.values()
        ),
    }

    expected_context = {
        "n_states": 16,
        "state_matches": 16,
        "n_edges": 32,
        "edge_matches": 32,
        "visible_edges": 15,
        "visible_changes": 15,
        "masked_edges": 17,
        "masked_preserved": 17,
    }
    context_exact = all(
        all(row[k] == v for k, v in expected_context.items())
        for row in by_context
    )
    expected_aggregate = {
        "n_states": 48,
        "state_matches": 48,
        "n_edges": 96,
        "edge_matches": 96,
        "visible_edges": 45,
        "visible_changes": 45,
        "masked_edges": 51,
        "masked_preserved": 51,
    }
    aggregate_exact = aggregate == expected_aggregate

    primary = read(a.primary_analysis.resolve() / "FULL_REPLICATION_ANALYSIS.json")
    primary_states = {r["case_id"]: r for r in primary["states"]}
    primary_edges = {r["edge_id"]: r for r in primary["edges"]}
    state_disagreements = [
        key for key, value in states.items()
        if key not in primary_states
        or value["match"] != primary_states[key]["transferred_model_match"]
        or value["observed"] != primary_states[key]["observed_class"]
    ]
    edge_disagreements = [
        key for key, value in edges.items()
        if key not in primary_edges
        or value["match"] != primary_edges[key]["transferred_transition_match"]
        or (
            ("class_change" if value["observed_change"] else "class_preserved")
            != primary_edges[key]["observed_transition"]
        )
    ]

    eligible = (
        context_exact
        and aggregate_exact
        and not state_disagreements
        and not edge_disagreements
    )

    result = {
        "schema_version": "p02_mathai_cross_context_independent_review_v1",
        "status": "VERIFIED_BY_INDEPENDENT_RECOMPUTATION" if eligible else "REVIEW_MISMATCH",
        "publication_claim_eligible": eligible,
        "implementation_independent_of_primary_analysis": True,
        "transferred_prediction_modified": False,
        "contexts": by_context,
        "aggregate": aggregate,
        "expected_aggregate": expected_aggregate,
        "state_level_disagreements_with_primary_analysis": state_disagreements,
        "edge_level_disagreements_with_primary_analysis": edge_disagreements,
        "claim_boundary": [
            "The result concerns the three frozen contexts in one pinned Lean 4.14.0 project.",
            "The accepted primary denominators remain separate.",
            "The replication does not establish cross-version stability or natural-development prevalence.",
            "No autonomous repair policy is evaluated.",
        ],
    }
    (out / "INDEPENDENT_REVIEW.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if eligible else 1


if __name__ == "__main__":
    raise SystemExit(main())
