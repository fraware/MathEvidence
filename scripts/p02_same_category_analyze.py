#!/usr/bin/env python3
"""Compare classified same-category observations to preregistered expectations."""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import p02_classify_native_v2_raw as common

SCHEMA_VERSION = "p02_same_category_analysis_v1"
EXPECTED_SCHEMA = "p02_same_category_expected_results_v1"


def load_classes(root: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for path in sorted((root / "cases").glob("*/classification.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        case_id = str(row["case_id"])
        if case_id in rows:
            raise RuntimeError(f"duplicate classified case {case_id}")
        rows[case_id] = str(row["derived_native_class"])
    return rows


def error_marker_count(raw_root: Path, case_id: str) -> int:
    obs = json.loads((raw_root / "cases" / case_id / "observations.json").read_text(encoding="utf-8"))
    cand = obs.get("candidate") or {}
    text = (cand.get("stdout") or "") + "\n" + (cand.get("stderr") or "")
    return len(re.findall(r"\berror:\s*", text, flags=re.IGNORECASE))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--classified", type=Path, required=True)
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--prereg-commit", required=True)
    args = parser.parse_args()

    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"analysis output not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    expected = json.loads(args.expected.read_text(encoding="utf-8"))
    if expected.get("schema_version") != EXPECTED_SCHEMA:
        raise RuntimeError("unexpected expectation schema")
    expected_sha256 = common.sha256_bytes(args.expected.read_bytes())
    observed = load_classes(args.classified.resolve())

    state_rows: list[dict[str, Any]] = []
    edge_rows: list[dict[str, Any]] = []
    state_mismatches: list[dict[str, Any]] = []
    edge_mismatches: list[dict[str, Any]] = []
    per_pair: dict[str, dict[str, Any]] = {}

    expected_state_ids: set[str] = set()
    for pair in expected["pairs"]:
        pair_id = str(pair["pair_id"])
        state_expectations = pair["state_expectations"]
        per_pair[pair_id] = {
            "declared_category": pair["category"],
            "state_matches": 0,
            "state_total": len(state_expectations),
            "edge_matches": 0,
            "edge_total": len(pair["edge_expectations"]),
            "category_changes": 0,
            "category_preservations": 0,
        }
        for case_id, exp_class in sorted(state_expectations.items()):
            expected_state_ids.add(case_id)
            obs_class = observed.get(case_id)
            match = obs_class == exp_class
            row = {
                "pair_id": pair_id,
                "case_id": case_id,
                "expected_class": exp_class,
                "observed_class": obs_class,
                "match": match,
                "candidate_error_marker_count": error_marker_count(args.raw.resolve(), case_id),
            }
            state_rows.append(row)
            if match:
                per_pair[pair_id]["state_matches"] += 1
            else:
                state_mismatches.append(row)

        for edge in pair["edge_expectations"]:
            from_id = edge["from"]
            to_id = edge["to"]
            from_class = observed.get(from_id)
            to_class = observed.get(to_id)
            observed_change = from_class != to_class
            expected_change = bool(edge["category_changes"])
            match = observed_change == expected_change
            row = {
                "pair_id": pair_id,
                "from": from_id,
                "to": to_id,
                "removed": edge["removed"],
                "from_class": from_class,
                "to_class": to_class,
                "expected_change": expected_change,
                "observed_change": observed_change,
                "match": match,
            }
            edge_rows.append(row)
            if observed_change:
                per_pair[pair_id]["category_changes"] += 1
            else:
                per_pair[pair_id]["category_preservations"] += 1
            if match:
                per_pair[pair_id]["edge_matches"] += 1
            else:
                edge_mismatches.append(row)

    unexpected_cases = sorted(set(observed) - expected_state_ids)
    missing_cases = sorted(expected_state_ids - set(observed))
    if unexpected_cases or missing_cases:
        state_mismatches.append({"unexpected_cases": unexpected_cases, "missing_cases": missing_cases})

    state_match_count = sum(bool(row.get("match")) for row in state_rows)
    edge_match_count = sum(bool(row.get("match")) for row in edge_rows)
    changes = sum(bool(row["observed_change"]) for row in edge_rows)
    preservations = len(edge_rows) - changes
    all_match = not state_mismatches and not edge_mismatches

    analysis = {
        "schema_version": SCHEMA_VERSION,
        "status": "PREREGISTERED_EXPECTATIONS_MATCH" if all_match else "PREREGISTERED_EXPECTATIONS_MISMATCH",
        "publication_claim_eligible": False,
        "prereg_commit": args.prereg_commit,
        "expected_results_sha256": expected_sha256,
        "n_states": len(state_rows),
        "n_state_matches": state_match_count,
        "n_state_mismatches": len(state_rows) - state_match_count,
        "n_active_edges": len(edge_rows),
        "n_edge_matches": edge_match_count,
        "n_edge_mismatches": len(edge_rows) - edge_match_count,
        "observed_category_changes": changes,
        "observed_category_preservations": preservations,
        "state_mismatches": state_mismatches,
        "edge_mismatches": edge_mismatches,
        "per_pair": per_pair,
        "observed_class_counts": dict(sorted(Counter(observed.values()).items())),
        "candidate_error_marker_counts": {
            row["case_id"]: row["candidate_error_marker_count"] for row in state_rows
        },
        "non_claims": [
            "The three micro-corpora are targeted constructions, not samples from a natural failure population.",
            "Their 12-edge denominator is reported separately from the primary 64 active-edge denominator.",
            "The extension tests shared-category occupancy and does not estimate prevalence in real proof repair.",
            "Error-marker counts describe retained raw candidate output and do not alter classification.",
        ],
    }
    common.json_dump(out / "SAME_CATEGORY_ANALYSIS.json", analysis)
    write_csv(out / "STATE_TABLE.csv", [
        "pair_id", "case_id", "expected_class", "observed_class", "match", "candidate_error_marker_count"
    ], state_rows)
    write_csv(out / "EDGE_TABLE.csv", [
        "pair_id", "from", "to", "removed", "from_class", "to_class", "expected_change", "observed_change", "match"
    ], edge_rows)
    files = common.inventory(out)
    integrity = {
        "schema_version": "p02_same_category_analysis_integrity_v1",
        "publication_claim_eligible": False,
        "n_files": len(files),
        "files": files,
        "bundle_digest": common.canonical_digest({"files": files}),
    }
    common.json_dump(out / "INTEGRITY_MANIFEST.json", integrity)
    print(json.dumps({"analysis": analysis, "integrity": integrity}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
