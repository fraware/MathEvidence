#!/usr/bin/env python3
"""Classify a sealed MATH-AI cross-context raw bundle with frozen P02 v2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import p02_classify_native_v2_hardened as hardened
import p02_classify_native_v2_raw as v1


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expected-cases", type=int, required=True)
    parser.add_argument("--status", required=True)
    args = parser.parse_args()

    raw = args.raw.resolve()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"classification output is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    raw_integrity = read_json(raw / "INTEGRITY_MANIFEST.json")
    files = v1.inventory(raw)
    if raw_integrity.get("files") != files:
        raise RuntimeError("raw bundle inventory mismatch")
    raw_digest = v1.canonical_digest({"files": files})
    if raw_integrity.get("bundle_digest") != raw_digest:
        raise RuntimeError("raw bundle digest mismatch")

    hardened.self_test_policy_scanner()
    v1.self_test_frozen_rules()

    case_dirs = sorted(path for path in (raw / "cases").iterdir() if path.is_dir())
    if len(case_dirs) != args.expected_cases:
        raise RuntimeError(
            f"expected {args.expected_cases} raw cases, found {len(case_dirs)}"
        )

    results = [hardened.classify_case(case_dir) for case_dir in case_dirs]
    counts = {name: 0 for name in sorted(v1.NATIVE_CLASSES)}
    for row in results:
        counts[row["derived_native_class"]] += 1
        v1.json_dump(out / "cases" / row["case_id"] / "classification.json", row)

    summary = {
        "schema_version": "p02_mathai_cross_context_classification_v1",
        "status": args.status,
        "publication_claim_eligible": False,
        "classifier_version": hardened.CLASSIFIER_VERSION,
        "parent_classifier_version": v1.CLASSIFIER_VERSION,
        "parent_frozen_classifier_blob_sha": v1.FROZEN_CLASSIFIER_BLOB_SHA,
        "policy_scan_version": "lean_lexical_noncode_erasure_v1",
        "n_cases": len(results),
        "derived_class_counts": counts,
        "raw_bundle_digest": raw_digest,
        "construction_metadata_read_during_classification": False,
        "classification_inputs": [
            "candidate.lean",
            "observations.json",
        ],
        "non_claims": [
            "This wrapper reuses the already-frozen v2 classifier rules.",
            "Construction labels are not read during classification.",
            "Classification does not establish cross-context transfer.",
            "Publication promotion remains blocked pending analysis and independent review.",
        ],
    }
    v1.json_dump(out / "CLASSIFICATION_SUMMARY.json", summary)

    output_files = v1.inventory(out)
    integrity = {
        "schema_version": "p02_mathai_cross_context_classification_integrity_v1",
        "publication_claim_eligible": False,
        "n_files": len(output_files),
        "files": output_files,
        "bundle_digest": v1.canonical_digest({"files": output_files}),
    }
    v1.json_dump(out / "INTEGRITY_MANIFEST.json", integrity)
    print(json.dumps({"summary": summary, "integrity": integrity}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
