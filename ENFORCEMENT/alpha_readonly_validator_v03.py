from pathlib import Path
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
