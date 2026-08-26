#!/usr/bin/env python3
"""Classify sealed P02 adversarial raw observations with frozen v1 rules.

This classifier deliberately does not open ADVERSARIAL_SPEC.json or any
expectation.json file. It imports the already-frozen native observation
classifier and assigns classes from candidate source + raw process observations
only. Expectation comparison is a separate downstream step.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import p02_classify_native_v2_raw as frozen

SCHEMA_VERSION = "p02_native_adversarial_classification_v2_from_frozen_v1"
EXPECTED_CASES = 13
EXPECTED_SPEC_DIGEST = "sha256:b3db906353bdb5c53a732c2fd3f924ab445b116f58afbdac104c24d5334465c4"


def verify_raw(root: Path) -> dict[str, Any]:
    integrity = json.loads((root / "INTEGRITY_MANIFEST.json").read_text(encoding="utf-8"))
    files = frozen.inventory(root)
    if integrity.get("files") != files:
        raise RuntimeError("adversarial raw inventory mismatch")
    digest = frozen.canonical_digest({"files": files})
    if integrity.get("bundle_digest") != digest:
        raise RuntimeError("adversarial raw bundle digest mismatch")
    run = json.loads((root / "RUN_MANIFEST.json").read_text(encoding="utf-8"))
    if run.get("status") != "RAW_ADVERSARIAL_OBSERVATIONS_EXECUTED_NOT_CLASSIFIED":
        raise RuntimeError("unexpected adversarial raw status")
    if run.get("classification_performed") is not False:
        raise RuntimeError("adversarial raw reports prior classification")
    if run.get("n_cases") != EXPECTED_CASES:
        raise RuntimeError("adversarial raw case count mismatch")
    if run.get("spec_digest") != EXPECTED_SPEC_DIGEST:
        raise RuntimeError("adversarial spec identity mismatch")
    return {
        "raw_adversarial_bundle_digest": digest,
        "spec_digest": run.get("spec_digest"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw = args.raw.resolve()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"adversarial classification output not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    frozen.self_test_frozen_rules()
    identity = verify_raw(raw)
    case_dirs = sorted(p for p in (raw / "cases").iterdir() if p.is_dir())
    if len(case_dirs) != EXPECTED_CASES:
        raise RuntimeError(f"expected {EXPECTED_CASES} adversarial cases, found {len(case_dirs)}")

    counts = {name: 0 for name in sorted(frozen.NATIVE_CLASSES)}
    for case_dir in case_dirs:
        row = frozen.classify_case(case_dir)
        counts[row["derived_native_class"]] += 1
        frozen.json_dump(out / "cases" / row["case_id"] / "classification.json", row)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": "ADVERSARIAL_CLASSIFIED_NOT_EXPECTATION_ANALYZED",
        "publication_claim_eligible": False,
        "classifier_version": frozen.CLASSIFIER_VERSION,
        "frozen_classifier_blob_sha": frozen.FROZEN_CLASSIFIER_BLOB_SHA,
        "classifier_rules_modified_for_adversarial_suite": False,
        "expectation_metadata_read_during_classification": False,
        "n_cases": len(case_dirs),
        "derived_class_counts": counts,
        **identity,
        "non_claims": [
            "This step applies frozen v1 classification only.",
            "It does not read preregistered expected semantic classes.",
            "No adversarial success rate is assigned until the downstream expectation comparison."
        ],
    }
    frozen.json_dump(out / "CLASSIFICATION_SUMMARY.json", summary)
    files = frozen.inventory(out)
    integrity = {
        "schema_version": "p02_native_adversarial_classification_integrity_v2",
        "publication_claim_eligible": False,
        "n_files": len(files),
        "files": files,
        "bundle_digest": frozen.canonical_digest({"files": files}),
    }
    frozen.json_dump(out / "INTEGRITY_MANIFEST.json", integrity)
    print(json.dumps({"summary": summary, "integrity": integrity}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
