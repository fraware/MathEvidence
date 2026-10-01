#!/usr/bin/env python3
"""Collect raw Lean observations for the preregistered P02 cross-context replication.

The collector reads only CASE_SPEC. It performs no classification and does not
read EXPECTED_RESULTS.
"""
from __future__ import annotations
import argparse, json, os, tempfile
from pathlib import Path
from typing import Any
import p02_native_v2_raw as base

SCHEMA="p02_cross_context_v2_raw_v1"
CASE_SCHEMA="p02_cross_context_v2_case_spec_v1"
PROJECT="946d2f7b14840837a5b641150c9df9008c4be9eb"
TOOLCHAIN="leanprover/lean4:v4.14.0"
CLASSIFIER="75d0599c277806007b1f31db451dbbe1bec3962e"

def load_spec(path:Path)->dict[str,Any]:
    spec=json.loads(path.read_text(encoding="utf-8"))
    if spec.get("schema_version")!=CASE_SCHEMA: raise RuntimeError("unexpected case schema")
    if spec.get("pinned_project_sha")!=PROJECT: raise RuntimeError("unexpected pinned project")
    if spec.get("lean_toolchain")!=TOOLCHAIN: raise RuntimeError("unexpected toolchain")
    if spec.get("classifier_v2_blob_sha")!=CLASSIFIER: raise RuntimeError("unexpected classifier")
    if spec.get("collection_reads_expectations") is not False: raise RuntimeError("collection boundary absent")
    if len(spec.get("state_cases") or [])!=48 or len(spec.get("edge_cases") or [])!=96: raise RuntimeError("case cardinality mismatch")
    ids=[r["state_id"] for r in spec["state_cases"]]+[r["edge_id"] for r in spec["edge_cases"]]
    if len(ids)!=len(set(ids)): raise RuntimeError("duplicate execution ids")
    return spec

def as_case(row:dict[str,Any],case_id:str,role:str)->base.Case:
    return base.Case(case_id=case_id,role=role,mechanisms=(),source=str(row["source"]),target_statement=str(row["target_statement"]),theorem_name=str(row["theorem_name"]))

def main()->int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--case-spec",type=Path,required=True); p.add_argument("--pinned-project",type=Path,required=True); p.add_argument("--out",type=Path,required=True); p.add_argument("--prereg-commit",required=True); p.add_argument("--timeout-seconds",type=float,default=30.0); a=p.parse_args()
    spec=load_spec(a.case_spec.resolve())
    out=a.out.resolve()
    if out.exists() and any(out.iterdir()): raise RuntimeError(f"output nonempty: {out}")
    out.mkdir(parents=True,exist_ok=True)
    env=base.environment_snapshot(a.pinned_project.resolve()); base.json_dump(out/"ENVIRONMENT.json",env); errs=base.validate_environment(env)
    if errs: raise RuntimeError("; ".join(errs))
    base.json_dump(out/"CASE_SPEC_USED.json",spec)
    with tempfile.TemporaryDirectory(prefix="p02-cross-context-v2-") as tmp:
        scratch=Path(tmp)
        for row in spec["state_cases"]:
            case=as_case(row,row["state_id"],f"cross_context_state_{row['context_id']}")
            obs=base.collect_case(case,project=a.pinned_project.resolve(),scratch=scratch,timeout_seconds=a.timeout_seconds)
            base.write_case_bundle(out,case,obs)
        for row in spec["edge_cases"]:
            case=as_case(row,row["edge_id"],f"cross_context_edge_{row['context_id']}")
            obs=base.collect_case(case,project=a.pinned_project.resolve(),scratch=scratch,timeout_seconds=a.timeout_seconds)
            base.write_case_bundle(out,case,obs)
    post=base.successful_stdout(base.git_observation(a.pinned_project.resolve(),"status","--porcelain"))
    if post is None or post: raise RuntimeError(f"pinned project changed: {post!r}")
    run={"schema_version":SCHEMA,"status":"RAW_CROSS_CONTEXT_EXECUTED_NOT_CLASSIFIED","publication_claim_eligible":False,"classification_performed":False,"prereg_commit":a.prereg_commit,"case_spec_sha256":base.sha256_bytes(a.case_spec.read_bytes()),"expected_results_read_during_collection":False,"n_contexts":3,"n_state_cases":48,"n_edge_cases":96,"n_cases":144,"timeout_seconds":a.timeout_seconds,"expected_project_sha":PROJECT,"expected_toolchain":TOOLCHAIN,"expected_classifier_v2_blob_sha":CLASSIFIER,"toolchain_transport":os.environ.get("P02_TOOLCHAIN_TRANSPORT"),"toolchain_archive_sha256":os.environ.get("P02_TOOLCHAIN_ARCHIVE_SHA256") or None,"harness_branch_sha":os.environ.get("GITHUB_SHA"),"nonclaims":["This bundle contains raw observations only.","The collector does not receive expected results.","The three contexts are targeted constructions rather than a natural proof distribution.","The replication denominators stay separate from the primary study."]}
    base.json_dump(out/"RUN_MANIFEST.json",run); files=base.inventory(out); integ={"schema_version":"p02_cross_context_raw_integrity_v1","publication_claim_eligible":False,"n_files":len(files),"files":files,"bundle_digest":base.canonical_digest({"files":files})}; base.json_dump(out/"INTEGRITY_MANIFEST.json",integ); print(json.dumps({"run":run,"integrity":integ},indent=2,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
