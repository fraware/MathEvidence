#!/usr/bin/env python3
"""Audit cross-context state and repair executions against sealed expectations."""
from __future__ import annotations
import argparse, csv, json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import p02_classify_native_v2_raw as common

EXPECTED_SCHEMA="p02_cross_context_v2_expected_results_v1"

def load_classes(root:Path)->dict[str,str]:
    out={}
    for p in sorted((root/"cases").glob("*/classification.json")):
        row=json.loads(p.read_text(encoding="utf-8")); cid=str(row["case_id"])
        if cid in out: raise RuntimeError(f"duplicate classification {cid}")
        out[cid]=str(row["derived_native_class"])
    return out

def write_csv(path:Path,fields:list[str],rows:list[dict[str,Any]])->None:
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--raw",type=Path,required=True); p.add_argument("--classified",type=Path,required=True); p.add_argument("--expected",type=Path,required=True); p.add_argument("--out",type=Path,required=True); p.add_argument("--prereg-commit",required=True); a=p.parse_args()
    exp=json.loads(a.expected.read_text(encoding="utf-8"))
    if exp.get("schema_version")!=EXPECTED_SCHEMA: raise RuntimeError("unexpected expectation schema")
    obs=load_classes(a.classified.resolve())
    state_rows=[]; state_class={}
    for row in exp["state_expectations"]:
        cid=row["state_id"]; oc=obs.get(cid); ec=row["expected_class"]; state_class[cid]=oc
        state_rows.append({"context_id":row["context_id"],"state_id":cid,"expected_class":ec,"observed_class":oc,"match":oc==ec})
    edge_rows=[]
    for row in exp["edge_expectations"]:
        edge_id=row["edge_id"]; edge_class=obs.get(edge_id); origin_class=state_class.get(row["from_state_id"]); destination_state_class=state_class.get(row["to_state_id"])
        observed_change=origin_class!=edge_class
        edge_rows.append({"context_id":row["context_id"],"edge_id":edge_id,"from_state_id":row["from_state_id"],"to_state_id":row["to_state_id"],"removed_mechanism":row["removed_mechanism"],"expected_from_class":row["expected_from_class"],"observed_from_class":origin_class,"expected_to_class":row["expected_to_class"],"observed_edge_class":edge_class,"destination_state_class":destination_state_class,"edge_class_match":edge_class==row["expected_to_class"],"independent_rerun_match":edge_class==destination_state_class,"expected_change":bool(row["expected_change"]),"observed_change":observed_change,"movement_match":observed_change==bool(row["expected_change"])})
    per=defaultdict(lambda:{"state_matches":0,"state_total":0,"edge_class_matches":0,"edge_total":0,"independent_rerun_matches":0,"movement_matches":0,"category_changes":0,"category_preservations":0})
    for r in state_rows:
        q=per[r["context_id"]]; q["state_total"]+=1; q["state_matches"]+=int(r["match"])
    for r in edge_rows:
        q=per[r["context_id"]]; q["edge_total"]+=1; q["edge_class_matches"]+=int(r["edge_class_match"]); q["independent_rerun_matches"]+=int(r["independent_rerun_match"]); q["movement_matches"]+=int(r["movement_match"]); q["category_changes"]+=int(r["observed_change"]); q["category_preservations"]+=int(not r["observed_change"])
    sm=sum(r["match"] for r in state_rows); ecm=sum(r["edge_class_match"] for r in edge_rows); irm=sum(r["independent_rerun_match"] for r in edge_rows); mm=sum(r["movement_match"] for r in edge_rows); changes=sum(r["observed_change"] for r in edge_rows)
    all_match=sm==48 and ecm==96 and irm==96 and mm==96
    analysis={"schema_version":"p02_cross_context_v2_analysis_v1","status":"CROSS_CONTEXT_EXPECTATIONS_MATCH" if all_match else "CROSS_CONTEXT_EXPECTATIONS_MISMATCH","publication_claim_eligible":False,"prereg_commit":a.prereg_commit,"expected_results_sha256":common.sha256_bytes(a.expected.read_bytes()),"n_contexts":3,"n_state_cases":48,"n_state_matches":sm,"n_edge_cases":96,"n_edge_class_matches":ecm,"n_independent_rerun_matches":irm,"n_movement_matches":mm,"observed_category_changes":changes,"observed_category_preservations":96-changes,"per_context":dict(sorted(per.items())),"observed_class_counts":dict(sorted(Counter(obs.values()).items())),"state_mismatches":[r for r in state_rows if not r["match"]],"edge_mismatches":[r for r in edge_rows if not (r["edge_class_match"] and r["independent_rerun_match"] and r["movement_match"])],"nonclaims":["The three theorem contexts are targeted constructions, not a natural corpus.","The replication reuses the same four mechanism families under changed propositions and proof shapes.","Its counts are reported separately from the primary factorial study.","Agreement tests transfer of the declared mechanism, not prevalence or autonomous-agent performance."]}
    out=a.out.resolve()
    if out.exists() and any(out.iterdir()): raise RuntimeError("analysis output nonempty")
    out.mkdir(parents=True,exist_ok=True); common.json_dump(out/"CROSS_CONTEXT_ANALYSIS.json",analysis); write_csv(out/"STATE_TABLE.csv",list(state_rows[0]),state_rows); write_csv(out/"EDGE_TABLE.csv",list(edge_rows[0]),edge_rows)
    files=common.inventory(out); integ={"schema_version":"p02_cross_context_v2_analysis_integrity_v1","publication_claim_eligible":False,"n_files":len(files),"files":files,"bundle_digest":common.canonical_digest({"files":files})}; common.json_dump(out/"INTEGRITY_MANIFEST.json",integ); print(json.dumps({"analysis":analysis,"integrity":integ},indent=2,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
