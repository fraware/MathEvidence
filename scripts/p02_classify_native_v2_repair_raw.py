#!/usr/bin/env python3
"""Classify P02 v2 repair raw observations with the pre-run frozen v1 rules.

This classifier is committed before the repair campaign executes. It imports
the already-frozen baseline classification rules, verifies the repair bundle's
own integrity and preregistered plan digest, and deliberately does not read
repair_meta.json during class assignment.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import p02_classify_native_v2_raw as frozen

SCHEMA_VERSION = "p02_native_repair_classification_v2_from_frozen_v1"
EXPECTED_PLAN_DIGEST = (
    "sha256:0b610ed6bd984acf6403046e5adf56ed5f8ae0d9a6fbce4178c6a8ede4e20565"
)
EXPECTED_BASELINE_BUNDLE_DIGEST = (
    "sha256:482f21fe8bafd4e3784e7c3a7e0a5dc103820c087691fc0e66e5ff3dd61a63ea"
)


def verify_raw_repair_bundle(raw_root: Path) -> dict[str, Any]:
    integrity_path = raw_root / "INTEGRITY_MANIFEST.json"
    if not integrity_path.is_file():
        raise RuntimeError("missing repair raw integrity manifest")
    manifest = json.loads(integrity_path.read_text(encoding="utf-8"))
    observed_files = frozen.inventory(raw_root)
    if manifest.get("files") != observed_files:
        raise RuntimeError("repair raw file inventory mismatch")
    observed_digest = frozen.canonical_digest({"files": observed_files})
    if manifest.get("bundle_digest") != observed_digest:
        raise RuntimeError("repair raw bundle digest does not reproduce")
    run = json.loads((raw_root / "RUN_MANIFEST.json").read_text(encoding="utf-8"))
    if run.get("status") != "RAW_REPAIR_OBSERVATIONS_EXECUTED_NOT_CLASSIFIED":
        raise RuntimeError("unexpected repair raw status")
    if run.get("classification_performed") is not False:
        raise RuntimeError("repair raw bundle reports prior classification")
    if run.get("plan_digest") != EXPECTED_PLAN_DIGEST:
        raise RuntimeError("repair plan digest mismatch")
    if run.get("baseline_bundle_digest") != EXPECTED_BASELINE_BUNDLE_DIGEST:
        raise RuntimeError("repair run baseline identity mismatch")
    if run.get("n_counterfactual_edges") != 80 or run.get("n_cumulative_steps") != 5:
        raise RuntimeError("repair run cardinality mismatch")
    if run.get("n_observation_cases") != 85:
        raise RuntimeError("repair observation case count mismatch")
    return {
        "raw_repair_bundle_digest": observed_digest,
        "plan_digest": run.get("plan_digest"),
        "baseline_bundle_digest": run.get("baseline_bundle_digest"),
    }


def classify_case(case_dir: Path) -> dict[str, Any]:
    # Same oracle boundary as baseline classification: source + observations only.
    source = (case_dir / "candidate.lean").read_text(encoding="utf-8")
    raw = json.loads((case_dir / "observations.json").read_text(encoding="utf-8"))
    source_empty = not source.strip()
    if bool(raw.get("source_empty")) != source_empty:
        raise RuntimeError(f"source_empty mismatch for {case_dir.name}")
    candidate = frozen.observation_from_json(raw.get("candidate"))
    if candidate is None:
        raise RuntimeError(f"missing candidate observation for {case_dir.name}")
    observations = frozen.NativeObservations(
        source_empty=source_empty,
        candidate=candidate,
        declaration_probe=frozen.observation_from_json(raw.get("declaration_probe")),
        target_probe=frozen.observation_from_json(raw.get("target_probe")),
        policy_has_placeholder=bool(frozen._PLACEHOLDER_RE.search(source)),
        policy_has_custom_axiom=bool(frozen._AXIOM_RE.search(source)),
    )
    derived = frozen.derive_native_class(observations)
    if derived not in frozen.NATIVE_CLASSES:
        raise AssertionError(f"invalid native class {derived}")
    return {
        "case_id": raw.get("case_id") or case_dir.name,
        "derived_native_class": derived,
        "classifier_version": frozen.CLASSIFIER_VERSION,
        "frozen_classifier_blob_sha": frozen.FROZEN_CLASSIFIER_BLOB_SHA,
        "policy_admissible": observations.policy_admissible,
        "policy_has_placeholder": observations.policy_has_placeholder,
        "policy_has_custom_axiom": observations.policy_has_custom_axiom,
        "source_sha256": frozen.sha256_bytes(source.encode("utf-8")),
        "observations_sha256": frozen.sha256_bytes((case_dir / "observations.json").read_bytes()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw_root = args.raw.resolve()
    out_root = args.out.resolve()
    if out_root.exists() and any(out_root.iterdir()):
        raise RuntimeError(f"repair classification output not empty: {out_root}")
    out_root.mkdir(parents=True, exist_ok=True)

    frozen.self_test_frozen_rules()
    raw_identity = verify_raw_repair_bundle(raw_root)
    case_dirs = sorted(p for p in (raw_root / "cases").iterdir() if p.is_dir())
    if len(case_dirs) != 85:
        raise RuntimeError(f"expected 85 repair case directories, found {len(case_dirs)}")

    results = [classify_case(case_dir) for case_dir in case_dirs]
    counts = {name: 0 for name in sorted(frozen.NATIVE_CLASSES)}
    for row in results:
        counts[row["derived_native_class"]] += 1
        frozen.json_dump(
            out_root / "cases" / row["case_id"] / "classification.json", row
        )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": "REPAIR_CLASSIFIED_NOT_TRANSITION_ANALYZED",
        "publication_claim_eligible": False,
        "classifier_version": frozen.CLASSIFIER_VERSION,
        "frozen_classifier_blob_sha": frozen.FROZEN_CLASSIFIER_BLOB_SHA,
        "classifier_rules_modified_after_repair_run": False,
        "repair_metadata_read_during_classification": False,
        "n_cases": len(results),
        "derived_class_counts": counts,
        **raw_identity,
        "non_claims": [
            "This step classifies repair observations but does not inspect repair metadata.",
            "No masking, repair-success, or transition-rate claim is made here.",
            "UNKNOWN remains unchanged under the frozen classifier.",
            "Transition analysis is a separate post-classification step."
        ],
    }
    frozen.json_dump(out_root / "CLASSIFICATION_SUMMARY.json", summary)
    files = frozen.inventory(out_root)
    integrity = {
        "schema_version": "p02_native_repair_classification_integrity_v2",
        "publication_claim_eligible": False,
        "n_files": len(files),
        "files": files,
        "bundle_digest": frozen.canonical_digest({"files": files}),
    }
    frozen.json_dump(out_root / "INTEGRITY_MANIFEST.json", integrity)
    print(json.dumps({"summary": summary, "integrity": integrity}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
