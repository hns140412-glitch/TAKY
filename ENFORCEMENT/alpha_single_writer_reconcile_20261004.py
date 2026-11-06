from pathlib import Path
import json, hashlib

ROOT = Path(r"D:\Git PWA\TAKY_ALPHA_20261003")
ALPHA = ROOT / "ALPHA"
ENF = ROOT / "ENFORCEMENT"
REVIEW = ROOT / "ALPHA_REVIEW"
TODAY = "2026-10-04"
CLAIMS = ["DOCUMENTED","CODED","CI_VERIFIED","RUNTIME_VERIFIED","DEVICE_VERIFIED","DEPLOYED","PRODUCTION_VERIFIED"]
EXPECTED_RULE_BLOB = "b4ca9b367f08be37f358bad339900b5ea005fb56"

def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def save(rel, obj):
    p = ROOT / rel
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def code_ref(s):
    s = str(s).lower()
    return s.endswith((".js",".mjs",".cjs",".ts",".tsx",".py",".jsx"))

def claimset(owner=None, refs=None, owner_gap=False):
    refs = refs or []
    docs = ([owner] if owner else []) + list(refs)
    coded = [r for r in refs if code_ref(r)]
    return {
        "DOCUMENTED":{"state":"EVIDENCED" if docs else "UNVERIFIED","evidence":docs},
        "CODED":{"state":"EVIDENCED" if coded else "UNVERIFIED","evidence":coded},
        "CI_VERIFIED":{"state":"UNVERIFIED","evidence":[]},
        "RUNTIME_VERIFIED":{"state":"UNVERIFIED","evidence":[]},
        "DEVICE_VERIFIED":{"state":"UNVERIFIED","evidence":[]},
        "DEPLOYED":{"state":"HOLD","evidence":[]},
        "PRODUCTION_VERIFIED":{"state":"UNVERIFIED","evidence":[]},
    }

# 1) Reconcile routing aliases left by concurrent writers.
routing = load("ALPHA/TAKY_ALPHA_ROUTING_GRAPH_V0_1.json")
alias = {
    "TAKY_ASSETS":"TAKY_ASSETS_REPO",
    "TAKY_WORK_OS":"TAKY_WORK_OS_REPO",
    "SYNC_RUNTIME":"SYNC_CONTRACT",
    "AUTH_RUNTIME":"AUTH_SESSION",
    "PRIVATE_FAMILY_RUNTIME":"CHARACTER_ASSET_PIPELINE",
}
routing["schema"] = "TAKY_ALPHA_ROUTING_GRAPH_V0_1"
routing["status"] = "DRAFT_STRUCTURE_PENDING_DETERMINISTIC_VALIDATION"
routing["date"] = TODAY
routing["nodes"] = [n for n in routing.get("nodes",[]) if n.get("id") not in alias]
new_edges=[]
seen=set()
for e in routing.get("edges",[]):
    x=dict(e)
    x["from"]=alias.get(x.get("from"),x.get("from"))
    x["to"]=alias.get(x.get("to"),x.get("to"))
    key=(x.get("from"),x.get("to"),x.get("relation"))
    if key not in seen:
        seen.add(key); new_edges.append(x)
routing["edges"]=new_edges
for inv in [
    "POINTER_ONLY_NE_STRUCTURAL_COVERAGE",
    "LOCAL_INFRA_COMPLETE_NE_SYSTEM_ALPHA_COMPLETE",
    "POST_FREEZE_DELTA_NE_CANONICAL_AUTHORITY",
    "CURRENT_OR_HISTORY_PATH_IS_NEVER_A_NODE_OWNER",
    "READY_SET_PROJECTION_NE_PLANNER_AUTHORITY",
]:
    if inv not in routing.setdefault("invariants",[]): routing["invariants"].append(inv)
save("ALPHA/TAKY_ALPHA_ROUTING_GRAPH_V0_1.json", routing)

# 2) Conservative claim repair for app/engine coverage.
cov = load("ALPHA/TAKY_ALPHA_APP_ENGINE_COVERAGE_V0_1.json")
cov["status"] = "DRAFT_STRUCTURE_PENDING_DETERMINISTIC_VALIDATION"
cov["date"] = TODAY
for row in cov.get("rows",[]):
    owner = row.get("semantic_owner")
    refs = list(row.get("implementation_or_evidence_refs",[]))
    inherited = list(row.get("inherited_contracts",[]))
    doc_refs = ([owner] if owner else []) + inherited
    if row.get("id")=="SAVEY" and not doc_refs:
        doc_refs=["ALPHA_INPUT/FROZEN_BETA/BETA_FREEZE_MANIFEST_20261003.json#savey"]
    coded=[r for r in refs if code_ref(r)]
    row["claims"]={
        "DOCUMENTED":{"state":"EVIDENCED" if doc_refs else "UNVERIFIED","evidence":doc_refs},
        "CODED":{"state":"EVIDENCED" if coded else "UNVERIFIED","evidence":coded},
        "CI_VERIFIED":{"state":"UNVERIFIED","evidence":[]},
        "RUNTIME_VERIFIED":{"state":"UNVERIFIED","evidence":[]},
        "DEVICE_VERIFIED":{"state":"UNVERIFIED","evidence":[]},
        "DEPLOYED":{"state":"HOLD","evidence":[]},
        "PRODUCTION_VERIFIED":{"state":"UNVERIFIED","evidence":[]},
    }
cov["claim_dimensions"]=CLAIMS
save("ALPHA/TAKY_ALPHA_APP_ENGINE_COVERAGE_V0_1.json", cov)

# 3) Runtime claim repair.
runtime = load("ALPHA/TAKY_ALPHA_RUNTIME_CONTRACTS_V0_1.json")
runtime["status"]="DRAFT_STRUCTURE_PENDING_DETERMINISTIC_VALIDATION"
runtime["date"]=TODAY
for c in runtime.get("contracts",[]):
    c["claims"]=claimset(c.get("authority"), c.get("implementation_refs",[]))
runtime["claim_dimensions"]=CLAIMS
save("ALPHA/TAKY_ALPHA_RUNTIME_CONTRACTS_V0_1.json", runtime)

# 4) Pipeline claim dimensions + governance execution pipeline.
pipe = load("ALPHA/TAKY_ALPHA_PIPELINE_MAP_V0_1.json")
pipe["status"]="DRAFT_STRUCTURE_PENDING_DETERMINISTIC_VALIDATION"
pipe["date"]=TODAY
required_gov = {
  "id":"GOVERNANCE_EXECUTION_CONTINUITY",
  "stages":[
    {"id":"C2S_COMPILE","owner":"MASTER/CONVERSATION_TO_SYSTEM_PROTOCOL.md","owner_state":"MAPPED","implementation_or_evidence_refs":[]},
    {"id":"ENFORCEMENT_GATE","owner":"MASTER/ENFORCEMENT_PROTOCOL.md","owner_state":"MAPPED","implementation_or_evidence_refs":["ENFORCEMENT/taky_gate.py"]},
    {"id":"EXECUTOR_LIFECYCLE","owner":"MASTER/CODEX_TASK_CONTRACT.md","owner_state":"MAPPED","implementation_or_evidence_refs":[]},
    {"id":"CHECKPOINT_CURRENT","owner":"MASTER/EXECUTION_CHECKPOINT_PROTOCOL.md","owner_state":"MAPPED","implementation_or_evidence_refs":["ENFORCEMENT/execution_checkpoint.py"]},
    {"id":"HANDOFF_RESUME","owner":"MASTER/HANDOFF_PROTOCOL.md","owner_state":"MAPPED","implementation_or_evidence_refs":[]},
  ]
}
pipes=pipe.setdefault("pipelines",[])
if not any(x.get("id")==required_gov["id"] for x in pipes): pipes.append(required_gov)
for p in pipes:
    for s in p.get("stages",[]):
        refs=s.get("implementation_or_evidence_refs",[])
        s["claims"]=claimset(s.get("owner"), refs, s.get("owner_state")=="OPEN_OWNER_GAP")
pipe["claim_dimensions"]=CLAIMS
save("ALPHA/TAKY_ALPHA_PIPELINE_MAP_V0_1.json", pipe)

# 5) Lane registry comparison is content-equivalent after CRLF normalization.
lane = load("ALPHA/TAKY_ALPHA_LANE_IMPORT_LOCAL_INFRA_V0_1.json")
lane["canonical_rule_registry"]["normalization"]="CRLF_TO_LF_BEFORE_GIT_BLOB_HASH"
lane["canonical_rule_registry"]["expected_blob_sha"]=EXPECTED_RULE_BLOB
save("ALPHA/TAKY_ALPHA_LANE_IMPORT_LOCAL_INFRA_V0_1.json", lane)

# 6) Validation contract points to current validators.
val = load("ALPHA/TAKY_ALPHA_VALIDATION_CONTRACT_V0_1.json")
val["schema"]="TAKY_ALPHA_VALIDATION_CONTRACT_V0_1"
val["date"]=TODAY
val["current_validators"]=[
  "ENFORCEMENT/alpha_readonly_validator_v03.py",
  "ENFORCEMENT/alpha_coverage_depth_validator.py",
  "ENFORCEMENT/alpha_pipeline_validator.py",
  "ENFORCEMENT/alpha_lane_boundary_validator.py",
]
save("ALPHA/TAKY_ALPHA_VALIDATION_CONTRACT_V0_1.json", val)

# Validator source texts.
v03 = r'''from pathlib import Path
import json, hashlib, sys
ROOT=Path(r"D:\Git PWA\TAKY_ALPHA_20261003"); REVIEW=ROOT/"ALPHA_REVIEW"
def load(p): return json.loads((ROOT/p).read_text(encoding="utf-8"))
fail=[]
lock=load(Path("ALPHA_REVIEW/ALPHA_INPUT_LOCK_20261003.json"))
beta=load(Path("ALPHA_INPUT/FROZEN_BETA/BETA_FREEZE_MANIFEST_20261003.json"))
approval=load(Path("ALPHA_INPUT/FROZEN_BETA/BETA_FREEZE_APPROVAL_20261003.json"))
authority=load(Path("ALPHA/TAKY_ALPHA_AUTHORITY_MAP_V0_1.json"))
carry=load(Path("ALPHA/TAKY_ALPHA_CARRYOVER_OPEN_V0_1.json"))
validation=load(Path("ALPHA/TAKY_ALPHA_VALIDATION_CONTRACT_V0_1.json"))
routing=load(Path("ALPHA/TAKY_ALPHA_ROUTING_GRAPH_V0_1.json"))
compiled=load(Path("ALPHA/TAKY_ALPHA_RULE_COMPILE_V0_1.json"))
mreg=load(Path("MASTER/MASTER_FILE_REGISTRY.json"))
rreg=load(Path("MASTER/RULE_REGISTRY.json"))
layer=load(Path("MASTER/SYSTEM_LAYER_OWNERSHIP_MAP.json"))
master=(ROOT/"ALPHA/TAKY_ALPHA_MASTER_V0_1.md").read_text(encoding="utf-8")
# V0
if lock.get("frozen_beta_snapshot_identity_sha256")!=approval.get("frozen_beta_snapshot_identity_sha256"): fail.append("V0_APPROVAL_SNAPSHOT_MISMATCH")
if approval.get("status")!="APPROVED": fail.append("V0_FREEZE_NOT_APPROVED")
ap=ROOT/lock.get("freeze_approval_evidence","")
if not ap.exists() or hashlib.sha256(ap.read_bytes()).hexdigest()!=lock.get("freeze_approval_sha256"): fail.append("V0_APPROVAL_EVIDENCE_INVALID")
# V1
src=mreg.get("semantic_owners",[]); alp=authority.get("semantic_owners",[])
sns=[x.get("namespace") for x in src]; ans=[x.get("namespace") for x in alp]
if len(sns)!=len(set(sns)) or len(ans)!=len(set(ans)): fail.append("V1_DUPLICATE_NAMESPACE")
if set(sns)!=set(ans): fail.append("V1_NAMESPACE_SET_MISMATCH")
sb={x["namespace"]:x for x in src if x.get("namespace")}; ab={x["namespace"]:x for x in alp if x.get("namespace")}
for ns,row in sb.items():
    for k,v in row.get("paths",{}).items():
        if k in ("owner","current","change_ledger","verification_checkpoint") and ab.get(ns,{}).get(k)!=v: fail.append(f"V1_PATH_MISMATCH:{ns}:{k}")
# V2 canonical 21-rule owner-reference compile. scope is resolved from registry, never copied into compile.
sr=rreg.get("rules",[]); cr=compiled.get("rules",[])
if [x.get("rule_id") for x in sr] != [x.get("rule_id") for x in cr]: fail.append("V2_RULE_ID_ORDER_OR_SET_MISMATCH")
for s,c in zip(sr,cr):
    if (s.get("rule_id"),s.get("owner"))!=(c.get("rule_id"),c.get("owner")): fail.append("V2_RULE_OWNER_MISMATCH:"+str(s.get("rule_id")))
    if "scope" in c: fail.append("V2_COMPILED_SCOPE_MUST_BE_REFERENCE_ONLY:"+str(c.get("rule_id")))
    if s.get("owner") and not (ROOT/s["owner"]).exists(): fail.append("V2_RULE_OWNER_MISSING:"+str(s.get("rule_id")))
b=(ROOT/"MASTER/RULE_REGISTRY.json").read_bytes().replace(b"\r\n",b"\n")
blob=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
expected=(authority.get("canonical_rule_registry_live_read",{}) or authority.get("canonical_rule_registry",{})).get("blob_sha")
if expected and blob!=expected: fail.append("V2_CANONICAL_RULE_BLOB_MISMATCH")
# V3-6
if "CURRENT_IS_RESUME_POINTER_NOT_OWNER" not in authority.get("authority_rules",[]): fail.append("V3_CURRENT_BOUNDARY_MISSING")
if authority.get("input",{}).get("source_heads")!=beta.get("source_heads"): fail.append("V5_SOURCE_HEADS_NOT_FROZEN_MATCH")
if carry.get("exact_carry_over_open")!=beta.get("carry_over_open",{}): fail.append("V6_MANIFEST_OPEN_MISMATCH")
if carry.get("exact_contained_open")!=beta.get("freeze_gate",{}).get("contained_open",[]): fail.append("V6_CONTAINED_OPEN_MISMATCH")
# V7 routing
nodes=routing.get("nodes",[]); ids=[n.get("id") for n in nodes]
if len(ids)!=len(set(ids)): fail.append("V7_DUPLICATE_ROUTING_NODE")
required={"TAKY","WORK_OS","LEARNING_OS","LEARNING_APP_FAMILY","LEARNING_ENGINE","PLANNER","READY_SET","HIDE_SEEK","SNAP_POP","TAKY_MOBILE","EXPLORER_CREW","DESIGN_UI_ASSETS","TAKY_ASSETS_REPO","BADGE","SAVEY","TAKY_WORK_OS_REPO","SYNC_CONTRACT","AUTH_SESSION","FAMILY_PRIVATE_BOUNDARY","OFFLINE_QUEUE","DRIVE_GOOGLE_CANONICAL","LOCAL_HTTP_BRIDGE","ENFORCEMENT_ENGINE","EXECUTOR_LIFECYCLE","C2S_COMPILER","HANDOFF","CHECKPOINT","LOCAL_INFRA_ALPHA_LANE"}
if not required.issubset(set(ids)): fail.append("V7_REQUIRED_NODE_MISSING:"+",".join(sorted(required-set(ids))))
for stale in ("TAKY_ASSETS","TAKY_WORK_OS","SYNC_RUNTIME","AUTH_RUNTIME","PRIVATE_FAMILY_RUNTIME"):
    if stale in ids: fail.append("V7_STALE_ALIAS_NODE:"+stale)
nb={n["id"]:n for n in nodes if n.get("id")}
for x in ("PLANNER","BADGE","SAVEY"):
    if nb.get(x,{}).get("owner_state")!="OPEN_OWNER_GAP": fail.append("V7_OWNER_GAP_NOT_EXPLICIT:"+x)
if nb.get("PLANNER",{}).get("semantic_authority")!="LEARNING_OS": fail.append("V7_PLANNER_AUTHORITY_INVALID")
for e in routing.get("edges",[]):
    if e.get("from") not in nb or e.get("to") not in nb: fail.append("V7_EDGE_UNKNOWN_NODE")
# V8/V9/V11-13 declarations
if not validation.get("claim_dimensions"): fail.append("V8_CLAIM_DIMENSIONS_MISSING")
rb=validation.get("release_boundary",{})
for k in ("push","merge","deploy","paid_api"):
    if rb.get(k)!="HOLD": fail.append("V9_RELEASE_NOT_HOLD:"+k)
gids={x.get("id") for x in validation.get("validation_gates",[])}
for g in ("V11_PIPELINE_COMPLETENESS","V12_APP_COVERAGE_DEPTH","V13_LANE_BOUNDARY"):
    if g not in gids: fail.append("V10_REQUIRED_GATE_MISSING:"+g)
res={"schema":"TAKY_ALPHA_READONLY_VALIDATION_V0_3","date":"2026-10-04","status":"PASS" if not fail else "FAIL","failure_count":len(fail),"failures":fail}
(REVIEW/"ALPHA_READONLY_VALIDATION_20261004.json").write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(res,ensure_ascii=False)); sys.exit(0 if not fail else 1)
'''
(ENF/"alpha_readonly_validator_v03.py").write_text(v03,encoding="utf-8")

coverage_validator = r'''from pathlib import Path
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
'''
(ENF/"alpha_coverage_depth_validator.py").write_text(coverage_validator,encoding="utf-8")

pipeline_validator = r'''from pathlib import Path
import json,sys
ROOT=Path(r"D:\Git PWA\TAKY_ALPHA_20261003"); REVIEW=ROOT/"ALPHA_REVIEW"
CLAIMS=["DOCUMENTED","CODED","CI_VERIFIED","RUNTIME_VERIFIED","DEVICE_VERIFIED","DEPLOYED","PRODUCTION_VERIFIED"]
p=json.loads((ROOT/"ALPHA/TAKY_ALPHA_PIPELINE_MAP_V0_1.json").read_text(encoding="utf-8")); fail=[]
expected={
"LEARNING_DATA_TO_EXECUTION":["SOURCE_CAPTURE","MINING","ATOMIZE","INDEX_SEARCH","RELATE","LEARNING","GROW","PLANNER","APP_EXECUTION","RESULT_EVIDENCE","CARRYOVER_CURRENT"],
"WORK_OS_ARCHIGROW":["SOURCE_INTAKE","ANALYSIS","ARTIFACT_OUTPUT","VALIDATION","LEARNING_GROWTH"],
"DESIGN_UI_ASSET":["APPROVED_SOURCE","SCREEN_CONTRACT","ASSET_LAYERS_BINDING","UI_RUNTIME","VISUAL_REGRESSION"],
"BADGE_REWARD":["EVIDENCE_PRODUCER","VERIFIED_OBSERVATION","AWARD_POLICY","DURABLE_LEDGER","VISUAL_BINDING","REWARD_USE"],
"GOVERNANCE_EXECUTION_CONTINUITY":["C2S_COMPILE","ENFORCEMENT_GATE","EXECUTOR_LIFECYCLE","CHECKPOINT_CURRENT","HANDOFF_RESUME"],
}
by={x.get("id"):x for x in p.get("pipelines",[])}
for pid,seq in expected.items():
    if pid not in by: fail.append("PIPELINE_MISSING:"+pid); continue
    got=[s.get("id") for s in by[pid].get("stages",[])]
    if got!=seq: fail.append("PIPELINE_SEQUENCE_MISMATCH:"+pid)
    for s in by[pid].get("stages",[]):
        if not s.get("owner") and s.get("owner_state")!="OPEN_OWNER_GAP": fail.append(f"PIPELINE_OWNER_UNBOUNDED:{pid}:{s.get('id')}")
        if set(s.get("claims",{}))!=set(CLAIMS): fail.append(f"PIPELINE_CLAIM_SET_INVALID:{pid}:{s.get('id')}")
res={"schema":"TAKY_ALPHA_PIPELINE_VALIDATION_V1","date":"2026-10-04","status":"PASS" if not fail else "FAIL","failure_count":len(fail),"failures":fail}
(REVIEW/"ALPHA_PIPELINE_VALIDATION_20261004.json").write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(res,ensure_ascii=False)); sys.exit(0 if not fail else 1)
'''
(ENF/"alpha_pipeline_validator.py").write_text(pipeline_validator,encoding="utf-8")

lane_validator = r'''from pathlib import Path
import json,hashlib,sys
ROOT=Path(r"D:\Git PWA\TAKY_ALPHA_20261003"); REVIEW=ROOT/"ALPHA_REVIEW"; fail=[]
lane=json.loads((ROOT/"ALPHA/TAKY_ALPHA_LANE_IMPORT_LOCAL_INFRA_V0_1.json").read_text(encoding="utf-8"))
post=json.loads((ROOT/"ALPHA/TAKY_ALPHA_POST_FREEZE_DELTA_V0_1.json").read_text(encoding="utf-8"))
master=(ROOT/"ALPHA/TAKY_ALPHA_MASTER_V0_1.md").read_text(encoding="utf-8")
if lane.get("scope")!="LOCAL_INFRA_ONLY" or lane.get("implies_system_alpha") is not False: fail.append("LANE_SCOPE_LEAK")
if post.get("authority_transfer") is not False: fail.append("POST_FREEZE_AUTHORITY_TRANSFER")
expected=lane.get("canonical_rule_registry",{}).get("expected_blob_sha") or lane.get("canonical_rule_registry",{}).get("blob_sha")
b=(ROOT/"MASTER/RULE_REGISTRY.json").read_bytes().replace(b"\r\n",b"\n")
blob=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
if expected and blob!=expected: fail.append("LANE_CANONICAL_REGISTRY_BLOB_MISMATCH")
d=lane.get("local_candidate_registry_diff",{})
if not d.get("candidate_only") or not d.get("canonical_only") or "NO_AUTHORITY_TRANSFER" not in str(d.get("disposition")): fail.append("LANE_REGISTRY_DIFF_NOT_EXPLICIT")
if "LOCAL_ALPHA_COMPLETE != SYSTEM_ALPHA_COMPLETE" not in master: fail.append("MASTER_LANE_BOUNDARY_MISSING")
res={"schema":"TAKY_ALPHA_LANE_BOUNDARY_VALIDATION_V1","date":"2026-10-04","status":"PASS" if not fail else "FAIL","failure_count":len(fail),"failures":fail,"normalized_canonical_rule_blob":blob}
(REVIEW/"ALPHA_LANE_BOUNDARY_VALIDATION_20261004.json").write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(res,ensure_ascii=False)); sys.exit(0 if not fail else 1)
'''
(ENF/"alpha_lane_boundary_validator.py").write_text(lane_validator,encoding="utf-8")

save("ALPHA_REVIEW/ALPHA_SINGLE_WRITER_RECONCILIATION_20261004.json",{
    "schema":"TAKY_ALPHA_SINGLE_WRITER_RECONCILIATION_V1",
    "date":TODAY,
    "status":"APPLIED_AWAITING_VALIDATION",
    "reconciled_alias_nodes":alias,
    "added_pipeline":"GOVERNANCE_EXECUTION_CONTINUITY",
    "validator_set":[
        "ENFORCEMENT/alpha_readonly_validator_v03.py",
        "ENFORCEMENT/alpha_coverage_depth_validator.py",
        "ENFORCEMENT/alpha_pipeline_validator.py",
        "ENFORCEMENT/alpha_lane_boundary_validator.py"
    ],
    "claim_boundary":"STRUCTURAL_RECONCILIATION_NE_ALPHA_PASS"
})
print("RECONCILED")
