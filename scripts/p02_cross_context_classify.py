#!/usr/bin/env python3
"""Classify preregistered cross-context raw evidence with the frozen hardened mapper."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import p02_classify_native_v2_hardened as v2
import p02_classify_native_v2_raw as v1
CLASSIFIER="75d0599c277806007b1f31db451dbbe1bec3962e"

def main()->int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--raw",type=Path,required=True); p.add_argument("--out",type=Path,required=True); p.add_argument("--prereg-commit",required=True); a=p.parse_args()
    raw=a.raw.resolve(); integ=json.loads((raw/"INTEGRITY_MANIFEST.json").read_text(encoding="utf-8")); files=v1.inventory(raw); digest=v1.canonical_digest({"files":files})
    if integ.get("files")!=files or integ.get("bundle_digest")!=digest: raise RuntimeError("raw integrity mismatch")
    run=json.loads((raw/"RUN_MANIFEST.json").read_text(encoding="utf-8"))
    if run.get("classification_performed") is not False or run.get("n_cases")!=144 or run.get("expected_classifier_v2_blob_sha")!=CLASSIFIER: raise RuntimeError("raw manifest mismatch")
    result=v2.classify_bundle(raw_root=raw,out_root=a.out.resolve(),expected_raw_digest=digest,expected_n_cases=144,status="P02_CROSS_CONTEXT_V2_CLASSIFIED_UNAUDITED",provenance={"evidence_role":"preregistered_cross_context_replication","prereg_commit":a.prereg_commit,"classifier_v2_blob_sha":CLASSIFIER,"expectation_metadata_read_during_classification":False})
    print(json.dumps(result,indent=2,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
