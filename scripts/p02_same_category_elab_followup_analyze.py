#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,re
from pathlib import Path
import p02_classify_native_v2_raw as common
EXPECTED_SCHEMA='p02_same_category_elab_followup_expected_v1'

def main()->int:
 p=argparse.ArgumentParser(); p.add_argument('--raw',type=Path,required=True); p.add_argument('--classified',type=Path,required=True); p.add_argument('--expected',type=Path,required=True); p.add_argument('--out',type=Path,required=True); p.add_argument('--prereg-commit',required=True); a=p.parse_args()
 exp=json.loads(a.expected.read_text())
 if exp.get('schema_version')!=EXPECTED_SCHEMA: raise RuntimeError('expectation schema mismatch')
 obs={}
 for path in sorted((a.classified/'cases').glob('*/classification.json')):
  row=json.loads(path.read_text()); obs[row['case_id']]=row['derived_native_class']
 state_rows=[]
 for cid,ec in sorted(exp['state_expectations'].items()):
  raw=json.loads((a.raw/'cases'/cid/'observations.json').read_text()); cand=raw.get('candidate') or {}; text=(cand.get('stdout') or '')+'\n'+(cand.get('stderr') or ''); oc=obs.get(cid)
  state_rows.append({'case_id':cid,'expected_class':ec,'observed_class':oc,'match':oc==ec,'candidate_error_marker_count':len(re.findall(r'\berror:\s*',text,re.I))})
 edge_rows=[]
 for e in exp['edge_expectations']:
  fc,tc=obs.get(e['from']),obs.get(e['to']); change=fc!=tc
  edge_rows.append({'from':e['from'],'to':e['to'],'removed':e['removed'],'from_class':fc,'to_class':tc,'expected_change':bool(e['category_changes']),'observed_change':change,'match':change==bool(e['category_changes'])})
 sm=sum(r['match'] for r in state_rows); em=sum(r['match'] for r in edge_rows); changes=sum(r['observed_change'] for r in edge_rows); all_match=sm==4 and em==4
 out=a.out.resolve()
 if out.exists() and any(out.iterdir()): raise RuntimeError('analysis output nonempty')
 out.mkdir(parents=True,exist_ok=True)
 analysis={'schema_version':'p02_same_category_elab_followup_analysis_v1','status':'FOLLOWUP_EXPECTATIONS_MATCH' if all_match else 'FOLLOWUP_EXPECTATIONS_MISMATCH','publication_claim_eligible':False,'prereg_commit':a.prereg_commit,'expected_results_sha256':common.sha256_bytes(a.expected.read_bytes()),'design_status':'designed_after_v1_mapper_coverage_miss_before_followup_execution','n_states':4,'n_state_matches':sm,'n_active_edges':4,'n_edge_matches':em,'observed_category_changes':changes,'observed_category_preservations':4-changes,'state_rows':state_rows,'edge_rows':edge_rows,'non_claims':['This follow-up was designed after observing the v1 elaboration UNKNOWN outcome.','It does not erase or replace the v1 mismatch.','It tests same-category masking under two elaboration diagnostics already covered by the frozen mapper.']}
 common.json_dump(out/'FOLLOWUP_ANALYSIS.json',analysis)
 with (out/'STATE_TABLE.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(state_rows[0])); w.writeheader(); w.writerows(state_rows)
 with (out/'EDGE_TABLE.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(edge_rows[0])); w.writeheader(); w.writerows(edge_rows)
 files=common.inventory(out); integ={'schema_version':'p02_same_category_elab_followup_analysis_integrity_v1','publication_claim_eligible':False,'n_files':len(files),'files':files,'bundle_digest':common.canonical_digest({'files':files})}; common.json_dump(out/'INTEGRITY_MANIFEST.json',integ); print(json.dumps({'analysis':analysis,'integrity':integ},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
