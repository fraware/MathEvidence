#!/usr/bin/env python3
"""Compare frozen-v1 P02 adversarial classifications to preregistered expectations.

This is a downstream audit step. Expected classes were frozen in the raw-suite
spec before execution; classifier outputs were generated without reading them.
The comparison uses exact class equality and reports every disagreement.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

import p02_classify_native_v2_raw as frozen

SCHEMA_VERSION = "p02_native_adversarial_comparison_v2"
EXPECTED_RAW_DIGEST = "sha256:a30bd039967f16d65494727ce176fe0d6153ca3b1d4e2d226cbf4df6a669ac10"
EXPECTED_CLASSIFIED_DIGEST = "sha256:3811458ec0aa4a2ae08572ff1ad456d0fbb0a8317f4ec17a4c05a0b466d7bd03"
EXPECTED_SPEC_DIGEST = "sha256:b3db906353bdb5c53a732c2fd3f924ab445b116f58afbdac104c24d5334465c4"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify(root: Path, expected: str, label: str) -> str:
    manifest = read_json(root / "INTEGRITY_MANIFEST.json")
    files = frozen.inventory(root)
    if manifest.get("files") != files:
        raise RuntimeError(f"{label} inventory mismatch")
    digest = frozen.canonical_digest({"files": files})
    if manifest.get("bundle_digest") != digest or digest != expected:
        raise RuntimeError(f"{label} digest mismatch: {digest}")
    return digest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--classified", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw = args.raw.resolve()
    classified = args.classified.resolve()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"comparison output not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    raw_digest = verify(raw, EXPECTED_RAW_DIGEST, "adversarial raw")
    classified_digest = verify(classified, EXPECTED_CLASSIFIED_DIGEST, "adversarial classified")
    spec = read_json(raw / "ADVERSARIAL_SPEC.json")
    if spec.get("spec_digest") != EXPECTED_SPEC_DIGEST or spec.get("n_cases") != 13:
        raise RuntimeError("adversarial spec identity/cardinality mismatch")

    rows: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    by_role: dict[str, Counter[str]] = {}
    confusion: Counter[tuple[str, str]] = Counter()
    for expected in spec["cases"]:
        case_id = str(expected["case_id"])
        observed = read_json(classified / "cases" / case_id / "classification.json")
        observed_class = str(observed["derived_native_class"])
        expected_class = str(expected["expected_semantic_class"])
        match = observed_class == expected_class
        row = {
            "case_id": case_id,
            "role": expected["role"],
            "expected_class": expected_class,
            "observed_class": observed_class,
            "match": match,
            "rationale": expected["rationale"],
            "policy_has_placeholder": observed.get("policy_has_placeholder"),
            "policy_has_custom_axiom": observed.get("policy_has_custom_axiom"),
        }
        rows.append(row)
        confusion[(expected_class, observed_class)] += 1
        role = str(expected["role"])
        if role not in by_role:
            by_role[role] = Counter(total=0, matches=0, mismatches=0)
        by_role[role]["total"] += 1
        by_role[role]["matches" if match else "mismatches"] += 1
        if not match:
            mismatches.append(row)

    n = len(rows)
    n_match = n - len(mismatches)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": "ADVERSARIAL_V1_AUDITED",
        "publication_claim_eligible": False,
        "comparison_rule": "exact equality between preregistered expected semantic class and frozen-v1 derived class",
        "n_cases": n,
        "n_matches": n_match,
        "n_mismatches": len(mismatches),
        "exact_match_rate": n_match / n,
        "mismatches": mismatches,
        "by_role": {role: dict(counts) for role, counts in sorted(by_role.items())},
        "confusion": [
            {"expected_class": e, "observed_class": o, "n": count}
            for (e, o), count in sorted(confusion.items())
        ],
        "raw_adversarial_bundle_digest": raw_digest,
        "classified_adversarial_bundle_digest": classified_digest,
        "spec_digest": EXPECTED_SPEC_DIGEST,
        "classifier_version": "p02_native_observation_classifier_v1",
        "frozen_classifier_blob_sha": "681309212d1b045558277b167a99dc28c45bef71",
        "non_claims": [
            "This adversarial suite is small and targeted; its exact-match rate is not a population estimate.",
            "Failures are retained as classifier falsifications and are not relabeled.",
            "Any v2 hardening motivated by these failures is post-hoc relative to this suite and requires a new holdout validation set.",
            "No proof-generation efficacy or S6 semantic-admissibility claim follows from this audit."
        ],
    }
    frozen.json_dump(out / "ADVERSARIAL_COMPARISON.json", summary)
    with (out / "ADVERSARIAL_CASE_TABLE.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "case_id", "role", "expected_class", "observed_class", "match", "rationale",
            "policy_has_placeholder", "policy_has_custom_axiom",
        ])
        writer.writeheader()
        writer.writerows(rows)

    files = frozen.inventory(out)
    integrity = {
        "schema_version": "p02_native_adversarial_comparison_integrity_v2",
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
