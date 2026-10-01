#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, tempfile
from pathlib import Path
import p02_native_v2_raw as base

SCHEMA='p02_same_category_elab_followup_raw_v1'
CASE_SCHEMA='p02_same_category_elab_followup_case_spec_v1'
PROJECT='946d2f7b14840837a5b641150c9df9008c4be9eb'
TOOLCHAIN='leanprover/lean4:v4.14.0'
CLASSIFIER='75d0599c277806007b1f31db451dbbe1bec3962e'

def main()->int:
 p=argparse.ArgumentParser(); p.add_argument('--case-spec',type=Path,required=True); p.add_argument('--pinned-project',type=Path,required=True); p.add_argument('--out',type=Path,required=True); p.add_argument('--prereg-commit',required=True); p.add_argument('--timeout-seconds',type=float,default=30.0); a=p.parse_args()
 spec=json.loads(a.case_spec.read_text(encoding='utf-8'))
 if spec.get('schema_version')!=CASE_SCHEMA or spec.get('pinned_project_sha')!=PROJECT or spec.get('lean_toolchain')!=TOOLCHAIN or spec.get('classifier_v2_blob_sha')!=CLASSIFIER or spec.get('collection_reads_expectations') is not False: raise RuntimeError('follow-up spec invariant failed')
 rows=spec['pair']['states']
 if len(rows)!=4 or {r['state'] for r in rows}!={'clean','a','b','ab'}: raise RuntimeError('follow-up states invalid')
 out=a.out.resolve()
 if out.exists() and any(out.iterdir()): raise RuntimeError('output nonempty')
 out.mkdir(parents=True,exist_ok=True)
 env=base.environment_snapshot(a.pinned_project.resolve()); base.json_dump(out/'ENVIRONMENT.json',env); errs=base.validate_environment(env)
 if errs: raise RuntimeError('; '.join(errs))
 base.json_dump(out/'CASE_SPEC_USED.json',spec)
 with tempfile.TemporaryDirectory(prefix='p02-sc-elab-followup-') as tmp:
  scratch=Path(tmp)
  for r in rows:
   case=base.Case(case_id=r['state_id'],role=f"same_category_elab_followup_{r['state']}",mechanisms=(),source=r['source'],target_statement=r['target_statement'],theorem_name=r['theorem_name'])
   obs=base.collect_case(case,project=a.pinned_project.resolve(),scratch=scratch,timeout_seconds=a.timeout_seconds)
   base.write_case_bundle(out,case,obs)
 post=base.successful_stdout(base.git_observation(a.pinned_project.resolve(),'status','--porcelain'))
 if post is None or post: raise RuntimeError(f'pinned project changed: {post!r}')
 run={'schema_version':SCHEMA,'status':'RAW_ELAB_FOLLOWUP_EXECUTED_NOT_CLASSIFIED','publication_claim_eligible':False,'classification_performed':False,'prereg_commit':a.prereg_commit,'case_spec_sha256':base.sha256_bytes(a.case_spec.read_bytes()),'expected_results_read_during_collection':False,'n_cases':4,'expected_project_sha':PROJECT,'expected_toolchain':TOOLCHAIN,'expected_classifier_v2_blob_sha':CLASSIFIER,'toolchain_transport':os.environ.get('P02_TOOLCHAIN_TRANSPORT'),'toolchain_archive_sha256':os.environ.get('P02_TOOLCHAIN_ARCHIVE_SHA256') or None,'non_claims':['This is a follow-up designed after the v1 elaboration mapper-coverage miss.','The collector does not receive expected results.','No category claim is assigned during raw collection.']}
 base.json_dump(out/'RUN_MANIFEST.json',run); files=base.inventory(out); integ={'schema_version':'p02_same_category_elab_followup_raw_integrity_v1','publication_claim_eligible':False,'n_files':len(files),'files':files,'bundle_digest':base.canonical_digest({'files':files})}; base.json_dump(out/'INTEGRITY_MANIFEST.json',integ); print(json.dumps({'run':run,'integrity':integ},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
