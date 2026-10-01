#!/usr/bin/env python3
"""Classify the sealed P02 same-category raw bundle with frozen classifier v2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import p02_classify_native_v2_hardened as v2
import p02_classify_native_v2_raw as v1

EXPECTED_N_CASES = 12
EXPECTED_CLASSIFIER_BLOB_SHA = "75d0599c277806007b1f31db451dbbe1bec3962e"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--prereg-commit", required=True)
    args = parser.parse_args()

    raw = args.raw.resolve()
    integrity = json.loads((raw / "INTEGRITY_MANIFEST.json").read_text(encoding="utf-8"))
    files = v1.inventory(raw)
    raw_digest = v1.canonical_digest({"files": files})
    if integrity.get("files") != files or integrity.get("bundle_digest") != raw_digest:
        raise RuntimeError("raw same-category bundle integrity mismatch")
    run = json.loads((raw / "RUN_MANIFEST.json").read_text(encoding="utf-8"))
    if run.get("classification_performed") is not False or run.get("n_cases") != EXPECTED_N_CASES:
        raise RuntimeError("unexpected raw run manifest")
    if run.get("expected_classifier_v2_blob_sha") != EXPECTED_CLASSIFIER_BLOB_SHA:
        raise RuntimeError("raw run pins unexpected classifier")

    result = v2.classify_bundle(
        raw_root=raw,
        out_root=args.out.resolve(),
        expected_raw_digest=raw_digest,
        expected_n_cases=EXPECTED_N_CASES,
        status="P02_SAME_CATEGORY_V2_CLASSIFIED_UNAUDITED",
        provenance={
            "evidence_role": "preregistered_same_category_extension",
            "prereg_commit": args.prereg_commit,
            "classifier_v2_blob_sha": EXPECTED_CLASSIFIER_BLOB_SHA,
            "expectation_metadata_read_during_classification": False,
        },
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
