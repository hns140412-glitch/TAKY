from pathlib import Path
import json, copy, hashlib, sys
ROOT=Path(r"D:\Git PWA\TAKY_ALPHA_20261003"); REVIEW=ROOT/"ALPHA_REVIEW"
def load(p): return json.loads((ROOT/p).read_text(encoding="utf-8"))
CLAIMS={"DOCUMENTED","CODED","CI_VERIFIED","RUNTIME_VERIFIED","DEVICE_VERIFIED","DEPLOYED","PRODUCTION_VERIFIED"}
routing=load(Path("ALPHA/TAKY_ALPHA_ROUTING_GRAPH_V0_1.json"))
cov=load(Path("ALPHA/TAKY_ALPHA_APP_ENGINE_COVERAGE_V0_1.json"))
pipe=load(Path("ALPHA/TAKY_ALPHA_PIPELINE_MAP_V0_1.json"))
runtime=load(Path("ALPHA/TAKY_ALPHA_RUNTIME_CONTRACTS_V0_1.json"))
lane=load(Path("ALPHA/TAKY_ALPHA_LANE_IMPORT_LOCAL_INFRA_V0_1.json"))

def routing_err(r):
    e=[]; ids=[x.get("id") for x in r.get("nodes",[])]
    if len(ids)!=len(set(ids)): e.append("DUPLICATE_NODE")
    for stale in ("TAKY_ASSETS","TAKY_WORK_OS","SYNC_RUNTIME","AUTH_RUNTIME","PRIVATE_FAMILY_RUNTIME"):
        if stale in ids: e.append("STALE_ALIAS")
    by={x.get("id"):x for x in r.get("nodes",[])}
    for k in ("PLANNER","BADGE","SAVEY"):
        n=by.get(k,{})
        if n.get("owner_state")=="RESOLVED" and not (n.get("owner") or n.get("semantic_owner")): e.append("SILENT_OWNER_PROMOTION")
    return e

def cov_err(c):
    e=[]
    for r in c.get("rows",[]):
        if r.get("owner_state")=="RESOLVED" and not r.get("semantic_owner"): e.append("OWNER_MISSING")
        if set(r.get("claims",{}))!=CLAIMS: e.append("CLAIM_SET")
        for v in r.get("claims",{}).values():
            if v.get("state")=="EVIDENCED" and not v.get("evidence"): e.append("EMPTY_EVIDENCE")
    return e

expected={
"LEARNING_DATA_TO_EXECUTION":["SOURCE_CAPTURE","MINING","ATOMIZE","INDEX_SEARCH","RELATE","LEARNING","GROW","PLANNER","APP_EXECUTION","RESULT_EVIDENCE","CARRYOVER_CURRENT"],
"WORK_OS_ARCHIGROW":["SOURCE_INTAKE","ANALYSIS","ARTIFACT_OUTPUT","VALIDATION","LEARNING_GROWTH"],
"DESIGN_UI_ASSET":["APPROVED_SOURCE","SCREEN_CONTRACT","ASSET_LAYERS_BINDING","UI_RUNTIME","VISUAL_REGRESSION"],
"BADGE_REWARD":["EVIDENCE_PRODUCER","VERIFIED_OBSERVATION","AWARD_POLICY","DURABLE_LEDGER","VISUAL_BINDING","REWARD_USE"],
"GOVERNANCE_EXECUTION_CONTINUITY":["C2S_COMPILE","ENFORCEMENT_GATE","EXECUTOR_LIFECYCLE","CHECKPOINT_CURRENT","HANDOFF_RESUME"],
}
def pipe_err(p):
    e=[]; by={x.get("id"):x for x in p.get("pipelines",[])}
    for k,seq in expected.items():
        if [s.get("id") for s in by.get(k,{}).get("stages",[])]!=seq: e.append("SEQUENCE")
    return e

def runtime_err(r):
    e=[]
    for c in r.get("contracts",[]):
        for v in c.get("claims",{}).values():
            if v.get("state")=="EVIDENCED" and not v.get("evidence"): e.append("EMPTY_EVIDENCE")
    return e

def lane_err(l):
    e=[]
    if l.get("scope")!="LOCAL_INFRA_ONLY" or l.get("implies_system_alpha") is not False: e.append("LANE_SCOPE_LEAK")
    expected_blob=l.get("canonical_rule_registry",{}).get("expected_blob_sha")
    b=(ROOT/"MASTER/RULE_REGISTRY.json").read_bytes().replace(b"\r\n",b"\n")
    blob=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
    if expected_blob and blob!=expected_blob: e.append("REGISTRY_DRIFT")
    return e

baseline=bool(not routing_err(routing) and not cov_err(cov) and not pipe_err(pipe) and not runtime_err(runtime) and not lane_err(lane))
cases=[]

x=copy.deepcopy(routing); x["nodes"].append({"id":"SYNC_RUNTIME"})
cases.append({"id":"STALE_ALIAS_INJECTION","detected":"STALE_ALIAS" in routing_err(x)})
x=copy.deepcopy(routing); b=next(n for n in x["nodes"] if n["id"]=="BADGE"); b["owner_state"]="RESOLVED"; b.pop("owner",None); b.pop("semantic_owner",None)
cases.append({"id":"SILENT_OWNER_PROMOTION","detected":"SILENT_OWNER_PROMOTION" in routing_err(x)})
x=copy.deepcopy(cov); x["rows"][0]["claims"]["RUNTIME_VERIFIED"]={"state":"EVIDENCED","evidence":[]}
cases.append({"id":"RUNTIME_OVERCLAIM_EMPTY_EVIDENCE","detected":"EMPTY_EVIDENCE" in cov_err(x)})
x=copy.deepcopy(pipe); next(p for p in x["pipelines"] if p["id"]=="LEARNING_DATA_TO_EXECUTION")["stages"].pop(3)
cases.append({"id":"PIPELINE_STAGE_LOSS","detected":"SEQUENCE" in pipe_err(x)})
x=copy.deepcopy(runtime); x["contracts"][0]["claims"]["PRODUCTION_VERIFIED"]={"state":"EVIDENCED","evidence":[]}
cases.append({"id":"PRODUCTION_OVERCLAIM","detected":"EMPTY_EVIDENCE" in runtime_err(x)})
x=copy.deepcopy(lane); x["implies_system_alpha"]=True
cases.append({"id":"LANE_TO_SYSTEM_ESCALATION","detected":"LANE_SCOPE_LEAK" in lane_err(x)})
x=copy.deepcopy(lane); x["canonical_rule_registry"]["expected_blob_sha"]="0"*40
cases.append({"id":"CANONICAL_REGISTRY_DRIFT","detected":"REGISTRY_DRIFT" in lane_err(x)})

failed=[c["id"] for c in cases if not c["detected"]]
status="PASS" if baseline and not failed else "FAIL"
res={"schema":"TAKY_ALPHA_ADVERSARIAL_VALIDATION_V1","date":"2026-10-04","status":status,"baseline_pass":baseline,"case_count":len(cases),"cases":cases,"failed_cases":failed}
(REVIEW/"ALPHA_ADVERSARIAL_VALIDATION_20261004.json").write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(res,ensure_ascii=False))
sys.exit(0 if status=="PASS" else 1)
