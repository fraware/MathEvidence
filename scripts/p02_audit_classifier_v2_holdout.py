#!/usr/bin/env python3
"""Audit frozen classifier-v2 predictions on the preregistered unseen holdout.

This is a post-classification comparison step. Expected classes come only from
the holdout specification that was frozen before native execution; classifier
outputs come only from the sealed classified bundle. No classifier rule is
changed here and no mismatch is relabeled.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import p02_classify_native_v2_raw as frozen

EXPECTED_SPEC_DIGEST = "sha256:a113c101250c346a89fc8c67b4147a1a6baaaf26df3111fbf05ef0be8f8a5416"
EXPECTED_RAW_BUNDLE_DIGEST = "sha256:4ba819c943fe89e5afef50142c12ef29c5cf9420bf55519406ab8f72878701a3"
EXPECTED_CLASSIFIED_BUNDLE_DIGEST = "sha256:fe5c484cfcdf23a588e53ddc3a225dbdcd67ea02bade9986c4b623903e840178"
EXPECTED_CLASSIFIER_V2_BLOB_SHA = "75d0599c277806007b1f31db451dbbe1bec3962e"
EXPECTED_N = 20


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_bundle(root: Path, expected_digest: str) -> None:
    manifest = load_json(root / "INTEGRITY_MANIFEST.json")
    files = frozen.inventory(root)
    if manifest.get("files") != files:
        raise RuntimeError(f"inventory mismatch: {root}")
    digest = frozen.canonical_digest({"files": files})
    if manifest.get("bundle_digest") != digest:
        raise RuntimeError(f"manifest digest does not reproduce: {root}")
    if digest != expected_digest:
        raise RuntimeError(f"unexpected bundle digest: {root}: {digest}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--classified", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    raw = args.raw.resolve()
    classified = args.classified.resolve()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"output not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    verify_bundle(raw, EXPECTED_RAW_BUNDLE_DIGEST)
    verify_bundle(classified, EXPECTED_CLASSIFIED_BUNDLE_DIGEST)

    spec = load_json(raw / "HOLDOUT_SPEC.json")
    run = load_json(raw / "RUN_MANIFEST.json")
    class_summary = load_json(classified / "CLASSIFICATION_SUMMARY.json")

    if spec.get("spec_digest") != EXPECTED_SPEC_DIGEST:
        raise RuntimeError("holdout spec digest mismatch")
    if spec.get("classifier_v2_blob_sha") != EXPECTED_CLASSIFIER_V2_BLOB_SHA:
        raise RuntimeError("holdout spec classifier identity mismatch")
    if run.get("classification_performed") is not False:
        raise RuntimeError("raw bundle unexpectedly reports classification")
    if run.get("classifier_v2_blob_sha") != EXPECTED_CLASSIFIER_V2_BLOB_SHA:
        raise RuntimeError("raw run classifier identity mismatch")
    if class_summary.get("expectation_metadata_read_during_classification") is not False:
        raise RuntimeError("classified bundle reports expectation access")
    if class_summary.get("classifier_v2_blob_sha") != EXPECTED_CLASSIFIER_V2_BLOB_SHA:
        raise RuntimeError("classified bundle classifier identity mismatch")
    if class_summary.get("raw_bundle_digest") != EXPECTED_RAW_BUNDLE_DIGEST:
        raise RuntimeError("classified bundle raw identity mismatch")
    if class_summary.get("n_cases") != EXPECTED_N or spec.get("n_cases") != EXPECTED_N:
        raise RuntimeError("holdout cardinality mismatch")

    cases = spec.get("cases") or []
    if len(cases) != EXPECTED_N:
        raise RuntimeError("holdout case-list cardinality mismatch")

    rows: list[dict[str, Any]] = []
    confusion: Counter[tuple[str, str]] = Counter()
    by_role: dict[str, Counter[str]] = defaultdict(Counter)
    mismatches: list[dict[str, Any]] = []

    for case in cases:
        cid = case["case_id"]
        pred_path = classified / "cases" / cid / "classification.json"
        if not pred_path.is_file():
            raise RuntimeError(f"missing classification for {cid}")
        pred = load_json(pred_path)
        expected = case["expected_semantic_class"]
        observed = pred["derived_native_class"]
        match = expected == observed
        row = {
            "case_id": cid,
            "role": case["role"],
            "expected_class": expected,
            "observed_class": observed,
            "match": match,
            "rationale": case["rationale"],
            "policy_has_placeholder": pred.get("policy_has_placeholder"),
            "policy_has_custom_axiom": pred.get("policy_has_custom_axiom"),
        }
        rows.append(row)
        confusion[(expected, observed)] += 1
        by_role[case["role"]]["total"] += 1
        by_role[case["role"]]["matches" if match else "mismatches"] += 1
        if not match:
            mismatches.append(row)

    n_matches = sum(1 for r in rows if r["match"])
    n_mismatches = EXPECTED_N - n_matches
    summary = {
        "schema_version": "p02_native_classifier_v2_unseen_holdout_audit_v1",
        "status": "V2_UNSEEN_HOLDOUT_AUDITED",
        "publication_claim_eligible": n_mismatches == 0,
        "evidence_role": "unseen_holdout",
        "comparison_rule": "exact equality between preregistered expected semantic class and frozen-v2 derived class",
        "classifier_version": class_summary.get("classifier_version"),
        "classifier_v2_blob_sha": EXPECTED_CLASSIFIER_V2_BLOB_SHA,
        "holdout_spec_digest": EXPECTED_SPEC_DIGEST,
        "raw_holdout_bundle_digest": EXPECTED_RAW_BUNDLE_DIGEST,
        "classified_holdout_bundle_digest": EXPECTED_CLASSIFIED_BUNDLE_DIGEST,
        "n_cases": EXPECTED_N,
        "n_matches": n_matches,
        "n_mismatches": n_mismatches,
        "exact_match_rate": n_matches / EXPECTED_N,
        "confusion": [
            {"expected_class": e, "observed_class": o, "n": n}
            for (e, o), n in sorted(confusion.items())
        ],
        "by_role": {
            role: {
                "total": counts["total"],
                "matches": counts["matches"],
                "mismatches": counts["mismatches"],
            }
            for role, counts in sorted(by_role.items())
        },
        "mismatches": mismatches,
        "non_claims": [
            "This 20-case holdout is a targeted constructed native suite, not a population sample.",
            "Exact-match performance does not establish proof-generation capability.",
            "The v2 policy scanner remains lexical and is not a complete Lean parser.",
            "No S6 semantic-admissibility claim follows from this audit.",
            "Any future classifier modification would require a new independently frozen holdout."
        ],
    }
    frozen.json_dump(out / "HOLDOUT_AUDIT.json", summary)

    with (out / "HOLDOUT_CASES.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    files = frozen.inventory(out)
    integrity = {
        "schema_version": "p02_native_classifier_v2_unseen_holdout_audit_integrity_v1",
        "n_files": len(files),
        "files": files,
        "bundle_digest": frozen.canonical_digest({"files": files}),
    }
    frozen.json_dump(out / "INTEGRITY_MANIFEST.json", integrity)
    print(json.dumps({"summary": summary, "integrity": integrity}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
