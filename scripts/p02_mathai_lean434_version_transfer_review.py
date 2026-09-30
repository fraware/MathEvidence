#!/usr/bin/env python3
"""Independent recomputation of Lean 4.34.1 version-transfer predictions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ORDER = (
    "SOURCE_CORRUPTION",
    "INVALID_PROOF",
    "PROHIBITED_PLACEHOLDER",
    "WRONG_TARGET",
)
SIG = {
    "SOURCE_CORRUPTION": "FRONTEND_REJECT",
    "INVALID_PROOF": "ENVIRONMENT_OR_ELAB_REJECT",
    "PROHIBITED_PLACEHOLDER": "TOOLCHAIN_ACCEPT_POLICY_REJECT",
    "WRONG_TARGET": "TOOLCHAIN_ACCEPT_TARGET_MISMATCH",
}
INERT = "UNKNOWN_TYPE"
CLEAN = "TOOLCHAIN_ACCEPT_TARGET_MATCH"


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def expected(mechanisms: list[str]) -> str:
    present = set(mechanisms)
    for m in ORDER:
        if m in present:
            return SIG[m]
    return CLEAN


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--states-raw", type=Path, required=True)
    p.add_argument("--states-classified", type=Path, required=True)
    p.add_argument("--repairs-raw", type=Path, required=True)
    p.add_argument("--repairs-classified", type=Path, required=True)
    p.add_argument("--analysis", type=Path, required=True)
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
        mechs = list(construction["mechanisms"])
        obs = read(
            a.states_classified.resolve() / "cases" / d.name / "classification.json"
        )["derived_native_class"]
        exp = expected(mechs)
        states[d.name] = {
            "mechanisms": mechs,
            "observed": obs,
            "expected": exp,
            "match": obs == exp,
        }
    if len(states) != 32:
        raise RuntimeError(f"review expected 32 states, found {len(states)}")

    edges: dict[str, dict[str, Any]] = {}
    for d in sorted((a.repairs_raw.resolve() / "cases").iterdir()):
        if not d.is_dir():
            continue
        meta = read(d / "repair_metadata.json")
        before = states[meta["before_state_id"]]
        after_obs = read(
            a.repairs_classified.resolve() / "cases" / d.name / "classification.json"
        )["derived_native_class"]
        before_mechs = list(meta["mechanisms_before"])
        after_mechs = list(meta["mechanisms_after"])
        removed = meta["repair_mechanism"]

        if removed == INERT:
            category = "native_inert"
        else:
            visible = next(m for m in ORDER if m in set(before_mechs))
            category = "visible_active" if removed == visible else "masked_active"

        exp_before = expected(before_mechs)
        exp_after = expected(after_mechs)
        exp_change = exp_before != exp_after
        obs_change = before["observed"] != after_obs
        edges[d.name] = {
            "category": category,
            "expected_change": exp_change,
            "observed_change": obs_change,
            "match": exp_change == obs_change,
        }
    if len(edges) != 80:
        raise RuntimeError(f"review expected 80 edges, found {len(edges)}")

    aggregate = {
        "n_states": 32,
        "state_matches": sum(v["match"] for v in states.values()),
        "n_edges": 80,
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
        "inert_edges": sum(v["category"] == "native_inert" for v in edges.values()),
        "inert_preserved": sum(
            v["category"] == "native_inert" and not v["observed_change"]
            for v in edges.values()
        ),
    }

    primary = read(a.analysis.resolve() / "VERSION_TRANSFER_ANALYSIS.json")
    ps = {r["case_id"]: r for r in primary["states"]}
    pe = {r["edge_id"]: r for r in primary["edges"]}
    state_disagreements = [
        k for k, v in states.items()
        if k not in ps
        or v["match"] != ps[k]["transferred_model_match"]
        or v["observed"] != ps[k]["observed_class"]
    ]
    edge_disagreements = [
        k for k, v in edges.items()
        if k not in pe
        or v["match"] != pe[k]["transferred_transition_match"]
        or (
            ("class_change" if v["observed_change"] else "class_preserved")
            != pe[k]["observed_transition"]
        )
    ]

    # Publication eligibility here means the computation is independently
    # verified and fully reportable. It does not require a successful transfer.
    eligible = not state_disagreements and not edge_disagreements
    result = {
        "schema_version": "p02_mathai_lean434_version_transfer_review_v1",
        "status": "VERIFIED_BY_INDEPENDENT_RECOMPUTATION" if eligible else "REVIEW_MISMATCH",
        "publication_claim_eligible": eligible,
        "implementation_independent_of_primary_analysis": True,
        "aggregate": aggregate,
        "state_level_disagreements_with_primary_analysis": state_disagreements,
        "edge_level_disagreements_with_primary_analysis": edge_disagreements,
        "transfer_success_is_not_a_review_criterion": True,
        "claim_boundary": [
            "The arm is post-review and tests only Lean 4.34.1 release transport of the accepted source construction.",
            "All transfer failures remain reportable outcomes.",
            "The accepted Lean 4.14.0 denominators remain separate.",
            "This is not a current-mathlib project replication.",
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
