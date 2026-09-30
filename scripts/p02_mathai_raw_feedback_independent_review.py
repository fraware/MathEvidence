#!/usr/bin/env python3
"""Independent review of the post-review MATH-AI richer-feedback audit.

This implementation is intentionally separate from
p02_mathai_raw_feedback_aliasing_audit.py. It recursively removes only
run-specific JSON keys, normalizes generated temporary Lean paths, and compares
the resulting raw observation records directly. It then cross-checks the
previous audit artifact.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

TMP_RE = re.compile(r"/tmp/[^\s:'\"\n]+\.lean")
DROP_KEYS = frozenset({"case_id", "command", "elapsed_seconds"})


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: canonicalize(val)
            for key, val in sorted(value.items())
            if key not in DROP_KEYS
        }
    if isinstance(value, list):
        return [canonicalize(x) for x in value]
    if isinstance(value, str):
        return TMP_RE.sub("<CANDIDATE>.lean", value)
    return value


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--prior-audit", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    root = args.root.resolve()
    transition = root / "evidence/p02_native_v2/transition_analysis_first_full/REPAIR_EDGE_TABLE.csv"
    baseline = root / "evidence/p02_native_v2/raw_first_full/cases"
    repaired = root / "evidence/p02_native_v2/repair_raw_first_full/cases"

    with transition.open("r", encoding="utf-8", newline="") as fh:
        edges = [
            row for row in csv.DictReader(fh)
            if row["category"] == "masked_later_repair"
        ]
    if len(edges) != 34:
        raise RuntimeError(f"expected 34 masked edges, found {len(edges)}")

    rows = []
    mech = Counter()
    before_class = Counter()
    for edge in edges:
        b = canonicalize(load_json(baseline / edge["baseline_case_id"] / "observations.json"))
        a = canonicalize(load_json(repaired / edge["edge_id"] / "observations.json"))
        same = b == a
        rows.append({
            "edge_id": edge["edge_id"],
            "repair_mechanism": edge["repair_mechanism"],
            "before_class": edge["before_class"],
            "identical": same,
        })
        mech[(edge["repair_mechanism"], "identical" if same else "different")] += 1
        before_class[(edge["before_class"], "identical" if same else "different")] += 1

    identical = sum(r["identical"] for r in rows)
    different = len(rows) - identical

    prior = load_json(args.prior_audit)
    pm = prior["masked_active_edges"]
    if (identical, different) != (
        pm["normalized_feedback_identical"],
        pm["normalized_feedback_different"],
    ):
        raise RuntimeError("independent aggregate disagrees with prior audit")

    prior_rows = {
        row["edge_id"]: bool(row["normalized_feedback_identical"])
        for row in prior["rows"]
    }
    disagreements = [
        row for row in rows
        if prior_rows.get(row["edge_id"]) is not row["identical"]
    ]
    if disagreements:
        raise RuntimeError(f"edge-level disagreement with prior audit: {disagreements}")

    expected_mech = {
        ("INVALID_PROOF", "identical"): 8,
        ("INVALID_PROOF", "different"): 0,
        ("PROHIBITED_PLACEHOLDER", "identical"): 0,
        ("PROHIBITED_PLACEHOLDER", "different"): 12,
        ("WRONG_TARGET", "identical"): 8,
        ("WRONG_TARGET", "different"): 6,
    }
    for key, expected in expected_mech.items():
        if mech[key] != expected:
            raise RuntimeError(f"mechanism count {key}: {mech[key]} != {expected}")

    summary = {
        "schema_version": "p02_mathai_raw_feedback_independent_review_v1",
        "status": "VERIFIED_BY_INDEPENDENT_RECOMPUTATION",
        "publication_claim_eligible": True,
        "review_method": {
            "implementation_independent_of_primary_audit": True,
            "dropped_json_keys": sorted(DROP_KEYS),
            "path_normalization": "generated /tmp/.../*.lean -> <CANDIDATE>.lean",
            "comparison": "recursive equality of all remaining raw observation JSON",
        },
        "n_masked_active_edges": len(rows),
        "identical": identical,
        "different": different,
        "edge_level_disagreements_with_primary_audit": 0,
        "by_mechanism": {
            mechanism: {
                "identical": mech[(mechanism, "identical")],
                "different": mech[(mechanism, "different")],
            }
            for mechanism in ("INVALID_PROOF", "PROHIBITED_PLACEHOLDER", "WRONG_TARGET")
        },
        "by_before_class": {
            cls: {
                "identical": before_class[(cls, "identical")],
                "different": before_class[(cls, "different")],
            }
            for cls in sorted({row["before_class"] for row in rows})
        },
        "claim_boundary": [
            "The reviewed result concerns the stored native/probe observation payload after explicit run-metadata normalization.",
            "It does not establish equality of Lean internal state.",
            "It was designed after reviewer feedback and remains post-review descriptive evidence.",
            "It does not estimate natural-development or autonomous-agent prevalence.",
        ],
    }

    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "INDEPENDENT_REVIEW.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
