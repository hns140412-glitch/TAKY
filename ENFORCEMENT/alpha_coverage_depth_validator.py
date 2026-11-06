from pathlib import Path
import json,sys
ROOT=Path(r"D:\Git PWA\TAKY_ALPHA_20261003"); REVIEW=ROOT/"ALPHA_REVIEW"
def load(p): return json.loads((ROOT/p).read_text(encoding="utf-8"))
CLAIMS=["DOCUMENTED","CODED","CI_VERIFIED","RUNTIME_VERIFIED","DEVICE_VERIFIED","DEPLOYED","PRODUCTION_VERIFIED"]
fail=[]
cov=load(Path("ALPHA/TAKY_ALPHA_APP_ENGINE_COVERAGE_V0_1.json"))
runtime=load(Path("ALPHA/TAKY_ALPHA_RUNTIME_CONTRACTS_V0_1.json"))
mig=load(Path("ALPHA/TAKY_ALPHA_MIGRATION_COVERAGE_V0_1.json"))
rows=cov.get("rows",[]); ids=[r.get("id") for r in rows]
req={"READY_SET","HIDE_SEEK","SNAP_POP","TAKY_MOBILE","LEARNING_ENGINE","PLANNER","EXPLORER_CREW","BADGE","SAVEY"}
if len(ids)!=len(set(ids)): fail.append("COV_DUPLICATE_ID")
if not req.issubset(set(ids)): fail.append("COV_REQUIRED_ID_MISSING:"+",".join(sorted(req-set(ids))))
for r in rows:
    if not r.get("source_repo") or not r.get("frozen_sha"): fail.append("COV_SOURCE_IDENTITY_MISSING:"+str(r.get("id")))
    if r.get("owner_state")=="RESOLVED" and not r.get("semantic_owner"): fail.append("COV_OWNER_MISSING:"+str(r.get("id")))
    if r.get("owner_state") not in ("RESOLVED","OPEN_OWNER_GAP"): fail.append("COV_OWNER_STATE_INVALID:"+str(r.get("id")))
    claims=r.get("claims",{})
    if set(claims)!=set(CLAIMS): fail.append("COV_CLAIM_SET_INVALID:"+str(r.get("id")))
    for k,c in claims.items():
        if c.get("state")=="EVIDENCED" and not c.get("evidence"): fail.append(f"COV_EVIDENCE_EMPTY:{r.get('id')}:{k}")
contracts=runtime.get("contracts",[]); cids={c.get("id") for c in contracts}
rreq={"SYNC_OFFLINE","ACCOUNT_AUTH","FAMILY_SESSION","PRIVATE_CHARACTER_BINARY","DRIVE_GOOGLE_CANONICAL_DATA","LOCAL_HTTP_BRIDGE"}
if not rreq.issubset(cids): fail.append("RUNTIME_CONTRACT_MISSING:"+",".join(sorted(rreq-cids)))
for c in contracts:
    claims=c.get("claims",{})
    if set(claims)!=set(CLAIMS): fail.append("RUNTIME_CLAIM_SET_INVALID:"+str(c.get("id")))
    for k,v in claims.items():
        if v.get("state")=="EVIDENCED" and not v.get("evidence"): fail.append(f"RUNTIME_EVIDENCE_EMPTY:{c.get('id')}:{k}")
depth={r.get("identity") for r in mig.get("rows",[]) if r.get("source_type")=="ALPHA_DEPTH_LAYER"}
for x in ("WHOLE_SYSTEM_APP_ENGINE_DEPTH","WHOLE_SYSTEM_PIPELINES","WHOLE_SYSTEM_RUNTIME_CONTRACTS","LOCAL_INFRA_LANE","POST_FREEZE_DELTA"):
    if x not in depth: fail.append("MIGRATION_DEPTH_ROW_MISSING:"+x)
res={"schema":"TAKY_ALPHA_COVERAGE_DEPTH_VALIDATION_V1","date":"2026-10-04","status":"PASS" if not fail else "FAIL","failure_count":len(fail),"failures":fail}
(REVIEW/"ALPHA_COVERAGE_DEPTH_VALIDATION_20261004.json").write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(res,ensure_ascii=False)); sys.exit(0 if not fail else 1)
