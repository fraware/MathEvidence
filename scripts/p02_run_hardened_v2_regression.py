#!/usr/bin/env python3
"""Run P02 classifier-v2 development/regression checks on already sealed raw data.

This is not holdout validation. It applies post-hoc v2 to (a) the original
34-case native bundle, (b) the 85-case repair bundle, and (c) the 13-case
adversarial development bundle. It then checks class-level non-regression on
(a)/(b) against frozen v1 and reports development-suite agreement separately.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import p02_classify_native_v2_hardened as v2
import p02_classify_native_v2_raw as v1

BASE_RAW = "sha256:482f21fe8bafd4e3784e7c3a7e0a5dc103820c087691fc0e66e5ff3dd61a63ea"
REPAIR_RAW = "sha256:40b4c6a1397edb126774cf38ff06cbc54c73b216e9dbe4ef9c8a81d3e2fe4857"
ADV_RAW = "sha256:a30bd039967f16d65494727ce176fe0d6153ca3b1d4e2d226cbf4df6a669ac10"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compare_classes(old_root: Path, new_root: Path) -> list[dict[str, str]]:
    diffs: list[dict[str, str]] = []
    old_dirs = sorted(p for p in (old_root / "cases").iterdir() if p.is_dir())
    new_ids = {p.name for p in (new_root / "cases").iterdir() if p.is_dir()}
    if {p.name for p in old_dirs} != new_ids:
        raise RuntimeError("old/new case-id sets differ")
    for case_dir in old_dirs:
        case_id = case_dir.name
        old = read_json(case_dir / "classification.json")["derived_native_class"]
        new = read_json(new_root / "cases" / case_id / "classification.json")["derived_native_class"]
        if old != new:
            diffs.append({"case_id": case_id, "v1_class": old, "v2_class": new})
    return diffs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-raw", type=Path, required=True)
    parser.add_argument("--baseline-v1", type=Path, required=True)
    parser.add_argument("--repair-raw", type=Path, required=True)
    parser.add_argument("--repair-v1", type=Path, required=True)
    parser.add_argument("--adv-raw", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.out_root.resolve()
    root.mkdir(parents=True, exist_ok=True)

    baseline_v2 = root / "baseline_classified_v2"
    repair_v2 = root / "repair_classified_v2"
    adv_v2 = root / "adversarial_development_classified_v2"
    for path in (baseline_v2, repair_v2, adv_v2):
        if path.exists() and any(path.iterdir()):
            raise RuntimeError(f"output already populated: {path}")

    base_result = v2.classify_bundle(
        raw_root=args.baseline_raw.resolve(), out_root=baseline_v2,
        expected_raw_digest=BASE_RAW, expected_n_cases=34,
        status="V2_BASELINE_RECLASSIFIED_DEVELOPMENT_REGRESSION",
        provenance={"evidence_role": "development_regression"},
    )
    repair_result = v2.classify_bundle(
        raw_root=args.repair_raw.resolve(), out_root=repair_v2,
        expected_raw_digest=REPAIR_RAW, expected_n_cases=85,
        status="V2_REPAIR_RECLASSIFIED_DEVELOPMENT_REGRESSION",
        provenance={"evidence_role": "development_regression"},
    )
    adv_result = v2.classify_bundle(
        raw_root=args.adv_raw.resolve(), out_root=adv_v2,
        expected_raw_digest=ADV_RAW, expected_n_cases=13,
        status="V2_ADVERSARIAL_DEVELOPMENT_RECLASSIFIED",
        provenance={"evidence_role": "development_set_not_holdout"},
    )

    baseline_diffs = compare_classes(args.baseline_v1.resolve(), baseline_v2)
    repair_diffs = compare_classes(args.repair_v1.resolve(), repair_v2)

    spec = read_json(args.adv_raw.resolve() / "ADVERSARIAL_SPEC.json")
    adv_rows: list[dict[str, Any]] = []
    for expected in spec["cases"]:
        case_id = expected["case_id"]
        observed = read_json(adv_v2 / "cases" / case_id / "classification.json")["derived_native_class"]
        adv_rows.append({
            "case_id": case_id,
            "expected_class": expected["expected_semantic_class"],
            "observed_class": observed,
            "match": observed == expected["expected_semantic_class"],
        })
    adv_mismatches = [row for row in adv_rows if not row["match"]]

    summary = {
        "schema_version": "p02_native_classifier_v2_development_regression_v1",
        "status": "V2_DEVELOPMENT_REGRESSION_COMPLETE_NOT_HOLDOUT_VALIDATED",
        "publication_claim_eligible": False,
        "classifier_version": v2.CLASSIFIER_VERSION,
        "posthoc_relative_to_development_suite": True,
        "baseline": {
            "n_cases": 34,
            "v1_v2_class_differences": baseline_diffs,
            "n_class_differences": len(baseline_diffs),
            "v2_bundle_digest": base_result["integrity"]["bundle_digest"],
        },
        "repair": {
            "n_cases": 85,
            "v1_v2_class_differences": repair_diffs,
            "n_class_differences": len(repair_diffs),
            "v2_bundle_digest": repair_result["integrity"]["bundle_digest"],
        },
        "development_adversarial": {
            "n_cases": 13,
            "n_matches": len(adv_rows) - len(adv_mismatches),
            "n_mismatches": len(adv_mismatches),
            "exact_match_rate": (len(adv_rows) - len(adv_mismatches)) / len(adv_rows),
            "mismatches": adv_mismatches,
            "v2_bundle_digest": adv_result["integrity"]["bundle_digest"],
        },
        "non_claims": [
            "The 13-case adversarial result is a development-set check because it motivated v2.",
            "Zero regression on existing constructed bundles would not establish external validity.",
            "A separately frozen holdout suite is required before v2 robustness is used in publication claims."
        ],
    }
    v1.json_dump(root / "V2_DEVELOPMENT_REGRESSION.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
