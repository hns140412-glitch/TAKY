
from pathlib import Path
import json

ROOT = Path(r"D:\Git PWA\TAKY_ALPHA_20261003")
ALPHA = ROOT / "ALPHA"
REVIEW = ROOT / "ALPHA_REVIEW"
TODAY = "2026-10-04"
FROZEN = "ed761ad71074001d967d044368f4e07cacefbc457e7b9e5cbb00f8e655a65f57"
CANONICAL_RULE_BLOB = "b4ca9b367f08be37f358bad339900b5ea005fb56"
CLAIMS = ["DOCUMENTED","CODED","CI_VERIFIED","RUNTIME_VERIFIED","DEVICE_VERIFIED","DEPLOYED","PRODUCTION_VERIFIED"]

def load(name):
    return json.loads((ALPHA/name).read_text(encoding="utf-8"))

def save(name, obj):
    (ALPHA/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

def add_unique(rows, row, key="id"):
    value=row.get(key)
    for i, old in enumerate(rows):
        if old.get(key)==value:
            rows[i]=row
            return
    rows.append(row)

def claimset(documented=True, coded=False, ci=False, runtime=False, evidence=None):
    evidence=evidence or []
    return {
        "DOCUMENTED":{"state":"EVIDENCED" if documented else "UNVERIFIED","evidence":evidence if documented else []},
        "CODED":{"state":"EVIDENCED" if coded else "UNVERIFIED","evidence":evidence if coded else []},
        "CI_VERIFIED":{"state":"EVIDENCED" if ci else "UNVERIFIED","evidence":[]},
        "RUNTIME_VERIFIED":{"state":"EVIDENCED" if runtime else "UNVERIFIED","evidence":[]},
        "DEVICE_VERIFIED":{"state":"UNVERIFIED","evidence":[]},
        "DEPLOYED":{"state":"HOLD","evidence":[]},
        "PRODUCTION_VERIFIED":{"state":"UNVERIFIED","evidence":[]}
    }

post = {
  "schema":"TAKY_ALPHA_POST_FREEZE_DELTA_V0_1","status":"VOLATILE_CANDIDATE_SNAPSHOT","date":TODAY,
  "authority_transfer":False,"frozen_beta_snapshot_identity_sha256":FROZEN,
  "rule":"POST_FREEZE_WORKING_STATE_NE_CANONICAL_MAIN; this layer never mutates Frozen Beta.",
  "repos":[
    {"id":"TAKY","head":"fee09fa8cdd0b863fc08d4fa6d84d72a182cbc0e","branch":"character-asset-behavior-separation-2026-09-30","dirty_count":242,"frozen_head":"e7ca5c7f94f6721a8f399d8deb49f7f01d73f6a2"},
    {"id":"Ready-Set","head":"16026f41149dae5faed1c4ca2d1f2933a40ced7a","branch":"user-character-generator-adapter-2026-09-30","dirty_count":6,"frozen_head":"0c49a2d607c7c26f3ad6ea4ca6fcee4c5b2ad915"},
    {"id":"Hide-Seek","head":"5b29db8299237d41f9ce6d054256dda765f9cd09","branch":"family-character-profile-consumer-2026-09-30","dirty_count":5,"frozen_head":"5da6594510cc89341054aafef66d5f4ea47a0210"},
    {"id":"Snap-Pop","head":"94d548545b3c4bd04008d767a27c9cc9e0bcf28c","branch":"family-character-profile-consumer-2026-09-30","dirty_count":5,"frozen_head":"a77e65b383df170e1124d3b9e01ca37eef334d6c"},
    {"id":"TAKY-MOBILE","head":"9bcb7d9660834818457704db2c0a5b16c9964c95","branch":"main","dirty_count":2,"frozen_head":"6c90045d1bc1f957325b7daef0c6079b29338f1e"},
    {"id":"SAVEY","head":"939b229e2b55bd4bf92b33bc0884872015b145bc","branch":"main","dirty_count":0,"frozen_head":"5a196080b8f8ce50d188b0181d9bec5e5477a265"},
    {"id":"TAKY-WORK-OS","head":"74f47452d6bfd2d7b68f568c2f9d147040cefd10","branch":"runtime-hub-unification-2026-09-11","dirty_count":0,"frozen_head":"c82a99bd7fbd7ab979907d038e8f948d3792de90"}
  ],
  "claim_boundary":["LOCAL_HEAD_NE_GITHUB_MAIN","DIRTY_WORKTREE_NE_VALIDATED_CANDIDATE","POST_FREEZE_DELTA_NE_FROZEN_INPUT","NO_SILENT_PROMOTION"]
}
save("TAKY_ALPHA_POST_FREEZE_DELTA_V0_1.json", post)

lane = {
  "schema":"TAKY_ALPHA_LANE_IMPORT_LOCAL_INFRA_V0_1","status":"BOUNDED_LANE_IMPORTED","date":TODAY,
  "scope":"LOCAL_INFRA_ONLY","implies_system_alpha":False,
  "source":{"handoff":r"D:\Git PWA\TAKY\HANDOFF\TAKY_ALPHA_FINAL_2026-10-03.md",
            "current":r"D:\Git PWA\TAKY\CURRENT\TAKY\TAKY_ALPHA_2026-10-03.json",
            "checkpoint_hash":"sha256:1d556eecafcec340c0a7fd1d9237e529717a9e30478b6cc0bf7b69d60d6542f4",
            "source_status":"LOCAL_ALPHA_COMPLETE"},
  "canonical_rule_registry":{"source":"GitHub main MASTER/RULE_REGISTRY.json","blob_sha":CANONICAL_RULE_BLOB,"rule_count":21,"includes":"TKY-CHECKPOINT-001"},
  "local_candidate_registry_diff":{"candidate_rule_count":25,
      "candidate_only":["TKY-CONNECTION-001","TKY-SAVEY-001","TKY-WORKSTATION-001","TKY-ARCHIPIPE-001","TKY-AICOLLAB-001"],
      "canonical_only":["TKY-CHECKPOINT-001"],"disposition":"POST_FREEZE_CANDIDATE_ONLY__NO_AUTHORITY_TRANSFER"},
  "open":["HOST_PROVIDER_AUTHENTICATED_HUMAN_IDENTITY","HOSTED_CHATGPT_CLAUDE_AUTOMATIC_INTERCEPTION","CAD_EXCEL_HWP_REPRESENTATIVE_TASK_VERIFICATION"],
  "invariants":["LANE_COMPLETE_NE_SYSTEM_COMPLETE","LOCAL_REGISTRY_NE_CANONICAL_REGISTRY","NO_PUSH_MERGE_DEPLOY_PAID_API"]
}
save("TAKY_ALPHA_LANE_IMPORT_LOCAL_INFRA_V0_1.json", lane)

authority=load("TAKY_ALPHA_AUTHORITY_MAP_V0_1.json")
authority["date"]=TODAY
shared=authority.setdefault("shared_contracts",[])
for row in [
  {"id":"sync","path":"TAKY_SYNC_CONTRACT_V1.md"},
  {"id":"family_learning","path":"MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md"},
  {"id":"family_private_character","path":"OS/CHARACTER_ASSET_BEHAVIOR_PIPELINE.md"},
  {"id":"auth_runtime_candidate","path":"SHARED/runtime/taky-google-account-auth-v1.js","authority_class":"IMPLEMENTATION_EVIDENCE_ONLY"},
  {"id":"family_session_runtime_candidate","path":"LEARNING/transport/family-session-http-endpoint.js","authority_class":"IMPLEMENTATION_EVIDENCE_ONLY"}]:
    if not any(x.get("id")==row["id"] for x in shared): shared.append(row)
authority["lanes"]=[{"id":"LOCAL_INFRA_ALPHA","path":"ALPHA/TAKY_ALPHA_LANE_IMPORT_LOCAL_INFRA_V0_1.json","authority_transfer":False}]
authority["post_freeze_delta"]="ALPHA/TAKY_ALPHA_POST_FREEZE_DELTA_V0_1.json"
authority["canonical_rule_registry_live_read"]={"blob_sha":CANONICAL_RULE_BLOB,"rule_count":21,"includes_checkpoint_rule":True}
save("TAKY_ALPHA_AUTHORITY_MAP_V0_1.json", authority)

routing=load("TAKY_ALPHA_ROUTING_GRAPH_V0_1.json")
routing["schema"]="TAKY_ALPHA_ROUTING_GRAPH_V0_1"; routing["date"]=TODAY
nodes=routing.setdefault("nodes",[])
for row in [
 {"id":"TAKY_MOBILE","class":"MOBILE_ROUTING_APP","owner_state":"OPEN_OWNER_GAP","registry_ref":"OS/MOBILE_APP_DEVELOPMENT_REGISTRY.json"},
 {"id":"TAKY_ASSETS","class":"SHARED_ASSET_REPOSITORY","authority_ref":"MASTER/DESIGN_UI_ASSET_SOURCE_PROTOCOL.md"},
 {"id":"TAKY_WORK_OS","class":"WORK_OS_IMPLEMENTATION_REPOSITORY","authority_ref":"OS/WORK_OS.md"},
 {"id":"SYNC_RUNTIME","class":"SHARED_RUNTIME_CONTRACT","owner":"TAKY_SYNC_CONTRACT_V1.md"},
 {"id":"AUTH_RUNTIME","class":"SHARED_TECHNICAL_CAPABILITY","owner_state":"IMPLEMENTATION_BOUND","authority_ref":"MASTER/SHARED_TECHNICAL_CAPABILITY_REGISTRY.json"},
 {"id":"PRIVATE_FAMILY_RUNTIME","class":"SHARED_TECHNICAL_CAPABILITY","owner_state":"IMPLEMENTATION_BOUND","authority_ref":"OS/CHARACTER_ASSET_BEHAVIOR_PIPELINE.md"}]:
    add_unique(nodes,row)
for id_ in ("PLANNER","BADGE","SAVEY"):
    n=next((x for x in nodes if x.get("id")==id_),None)
    if n:
        n.pop("owner",None); n["owner_state"]="OPEN_OWNER_GAP"
        if id_=="PLANNER":
            n["semantic_authority"]="LEARNING_OS"; n["implementation_ref"]="PROJECTS/READY_WHOLE_IMPLEMENTATION_CONTRACT.md#Planner / MAIN"
        elif id_=="BADGE":
            n["evidence_refs"]=["CURRENT/BADGE_SYSTEM_RECOVERY_CURRENT_2026-09-26.json","BADGE/BADGE_60_PLUS_HISTORY_20_STORY_SYSTEM_2026-09-26.md"]
        else:
            n["implementation_repo"]="SAVEY"
edges=routing.setdefault("edges",[])
for row in [
 {"from":"TAKY","to":"TAKY_MOBILE","relation":"ROUTE_MOBILE_INSTALL_AND_SHARED_ENTRY"},
 {"from":"DESIGN_UI_ASSETS","to":"TAKY_ASSETS","relation":"GOVERN_APPROVED_ASSET_SOURCE"},
 {"from":"WORK_OS","to":"TAKY_WORK_OS","relation":"IMPLEMENT_WORK_OS_RUNTIME"},
 {"from":"SHARED_TECHNICAL_CAPABILITY","to":"AUTH_RUNTIME","relation":"IMPLEMENT_AUTH_MECHANISM"},
 {"from":"SHARED_TECHNICAL_CAPABILITY","to":"PRIVATE_FAMILY_RUNTIME","relation":"IMPLEMENT_PRIVATE_FAMILY_MECHANISM"},
 {"from":"LEARNING_APP_FAMILY","to":"SYNC_RUNTIME","relation":"CONSUME_SHARED_SYNC_CONTRACT"},
 {"from":"SYNC_RUNTIME","to":"READY_SET","relation":"SYNC_CONSUMER"},{"from":"SYNC_RUNTIME","to":"HIDE_SEEK","relation":"SYNC_CONSUMER"},{"from":"SYNC_RUNTIME","to":"SNAP_POP","relation":"SYNC_CONSUMER"},
 {"from":"AUTH_RUNTIME","to":"READY_SET","relation":"AUTH_CONSUMER"},{"from":"AUTH_RUNTIME","to":"HIDE_SEEK","relation":"AUTH_CONSUMER"},{"from":"AUTH_RUNTIME","to":"SNAP_POP","relation":"AUTH_CONSUMER"},
 {"from":"READY_SET","to":"LEARNING_ENGINE","relation":"SESSION_RESULT_EVIDENCE"},{"from":"SNAP_POP","to":"LEARNING_ENGINE","relation":"EXPRESSION_EVIDENCE_SIGNALS"}]:
    key=(row["from"],row["to"],row["relation"])
    if not any((x.get("from"),x.get("to"),x.get("relation"))==key for x in edges): edges.append(row)
for inv in ["POINTER_ONLY_NE_STRUCTURAL_COVERAGE","LOCAL_INFRA_COMPLETE_NE_SYSTEM_ALPHA_COMPLETE","POST_FREEZE_DELTA_NE_CANONICAL_AUTHORITY"]:
    if inv not in routing.setdefault("invariants",[]): routing["invariants"].append(inv)
save("TAKY_ALPHA_ROUTING_GRAPH_V0_1.json", routing)

migration=load("TAKY_ALPHA_MIGRATION_COVERAGE_V0_1.json"); migration["date"]=TODAY
node_ids={x.get("id") for x in nodes}; aliases={"TAKY_CORE":"TAKY","EXPLORATION_CREW":"EXPLORER_CREW","LEARNING_ENGINE_CORE":"LEARNING_ENGINE"}
for row in migration.get("rows",[]):
    if row.get("status")=="COVERED_OR_EXPLICITLY_NON_ROUTING":
        target=aliases.get(row.get("identity"),row.get("identity"))
        row["status"]="COVERED_ROUTING_REFERENCE" if target in node_ids else "EXPLICIT_NON_ROUTING_REFERENCE"
    if row.get("mode")=="POINTER_ONLY" and row.get("status")=="COVERED":
        row["status"]="SEMANTIC_POINTER_COVERED__DEPTH_TRACKED_SEPARATELY"
for ident,rep in [("WHOLE_SYSTEM_APP_ENGINE_DEPTH","ALPHA/TAKY_ALPHA_APP_ENGINE_COVERAGE_V0_1.json"),("WHOLE_SYSTEM_PIPELINES","ALPHA/TAKY_ALPHA_PIPELINE_MAP_V0_1.json"),("WHOLE_SYSTEM_RUNTIME_CONTRACTS","ALPHA/TAKY_ALPHA_RUNTIME_CONTRACTS_V0_1.json"),("LOCAL_INFRA_LANE","ALPHA/TAKY_ALPHA_LANE_IMPORT_LOCAL_INFRA_V0_1.json"),("POST_FREEZE_DELTA","ALPHA/TAKY_ALPHA_POST_FREEZE_DELTA_V0_1.json")]:
    if not any(x.get("identity")==ident for x in migration.get("rows",[])):
        migration["rows"].append({"source_type":"ALPHA_DEPTH_LAYER","source":"Frozen Beta + bounded post-freeze evidence","identity":ident,"alpha_representation":rep,"mode":"DEPTH_EVIDENCE","authority_transfer":False,"status":"COVERED_BY_EXPLICIT_ARTIFACT"})
save("TAKY_ALPHA_MIGRATION_COVERAGE_V0_1.json", migration)

carry=load("TAKY_ALPHA_CARRYOVER_OPEN_V0_1.json"); carry["date"]=TODAY
classes=carry.setdefault("classes",[])
for row in [
 {"id":"LOCAL_INFRA_HOST_IDENTITY","state":"OPEN_EXTERNAL_BOUNDARY","source":"ALPHA/TAKY_ALPHA_LANE_IMPORT_LOCAL_INFRA_V0_1.json"},
 {"id":"LOCAL_INFRA_CAD_EXCEL_HWP_TASKS","state":"OPEN_OPTIONAL_REPRESENTATIVE_TASK","source":"ALPHA/TAKY_ALPHA_LANE_IMPORT_LOCAL_INFRA_V0_1.json"},
 {"id":"ALPHA_INDEPENDENT_CROSS_VALIDATION","state":"OPEN_A8","source":"ALPHA/TAKY_ALPHA_VALIDATION_CONTRACT_V0_1.json"},
 {"id":"ALPHA_HUMAN_PROMOTION","state":"HOLD_A10","source":"ALPHA/TAKY_ALPHA_VALIDATION_CONTRACT_V0_1.json"}]:
    add_unique(classes,row)
save("TAKY_ALPHA_CARRYOVER_OPEN_V0_1.json", carry)

validation=load("TAKY_ALPHA_VALIDATION_CONTRACT_V0_1.json"); validation["schema"]="TAKY_ALPHA_VALIDATION_CONTRACT_V0_1"; validation["date"]=TODAY
vg=validation.setdefault("validation_gates",[])
for row in [
 {"id":"V11_PIPELINE_COMPLETENESS","rule":"Required whole-system pipelines have contiguous owner-bounded stage maps; POINTER_ONLY cannot satisfy areas A-F","required":"PASS"},
 {"id":"V12_APP_COVERAGE_DEPTH","rule":"Every app/engine row has owner or explicit owner gap, source, implementation/evidence refs, OPEN refs and independent claim dimensions","required":"PASS"},
 {"id":"V13_LANE_BOUNDARY","rule":"LOCAL infrastructure lane and post-freeze working deltas cannot imply whole-system or canonical completion","required":"PASS"}]:
    add_unique(vg,row)
save("TAKY_ALPHA_VALIDATION_CONTRACT_V0_1.json", validation)

trace=load("TAKY_ALPHA_SOURCE_TRACE_V0_1.json"); trace["date"]=TODAY; items=trace.setdefault("items",[])
for row in [
 {"alpha_concept":"Whole-system app/engine depth","classification":"STRUCTURAL_COVERAGE_LAYER","sources":["MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md","OS/LEARNING_ENGINE_CORE.md","OS/EXPLORATION_CREW_CANONICAL.md","TAKY_SYNC_CONTRACT_V1.md"],"authority_transfer":False},
 {"alpha_concept":"Whole-system pipeline map","classification":"ALPHA_ROUTING_SYNTHESIS","sources":["MASTER/CONVERSATION_TO_SYSTEM_PROTOCOL.md","OS/LEARNING_ENGINE_CORE.md","MASTER/GROWTH_INTELLIGENCE_PROTOCOL.md","OS/WORK_OS.md","MASTER/DESIGN_UI_ASSET_SOURCE_PROTOCOL.md"],"authority_transfer":False},
 {"alpha_concept":"LOCAL infrastructure Alpha lane","classification":"BOUNDED_IMPORTED_LANE","sources":[r"D:\Git PWA\TAKY\HANDOFF\TAKY_ALPHA_FINAL_2026-10-03.md"],"authority_transfer":False},
 {"alpha_concept":"Post-freeze working deltas","classification":"VOLATILE_CANDIDATE_EVIDENCE","sources":["ALPHA/TAKY_ALPHA_POST_FREEZE_DELTA_V0_1.json"],"authority_transfer":False}]:
    if not any(x.get("alpha_concept")==row["alpha_concept"] for x in items): items.append(row)
save("TAKY_ALPHA_SOURCE_TRACE_V0_1.json", trace)

apps=[
 ("READY_SET","APP","Ready-Set","0c49a2d607c7c26f3ad6ea4ca6fcee4c5b2ad915","PROJECTS/READY_WHOLE_IMPLEMENTATION_CONTRACT.md",["MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md","TAKY_SYNC_CONTRACT_V1.md"],["ready-runtime-v07.js","app.js"],["BADGE_CENTRAL"]),
 ("HIDE_SEEK","APP","Hide-Seek","5da6594510cc89341054aafef66d5f4ea47a0210","hns140412-glitch/Hide-Seek:Hide_Seek_UI_MASTER_LOGIC_REV_04.md",["MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md","OS/LEARNING_ENGINE_CORE.md","TAKY_SYNC_CONTRACT_V1.md"],["hide-bridge.js"],["HIDE_CREW_V2","BADGE_CENTRAL"]),
 ("SNAP_POP","APP","Snap-Pop","a77e65b383df170e1124d3b9e01ca37eef334d6c","hns140412-glitch/Snap-Pop:Snap_Pop_UI_MASTER_LOGIC_REV_12.md",["MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md","TAKY_SYNC_CONTRACT_V1.md"],["snap-bridge.js","app.js"],["SNAP_CREW_V2","SNAP_LEGACY_BROWSER_CLOSURE","BADGE_CENTRAL"]),
 ("TAKY_MOBILE","APP","TAKY-MOBILE","6c90045d1bc1f957325b7daef0c6079b29338f1e","OPEN_OWNER_GAP",["OS/MOBILE_APP_DEVELOPMENT_REGISTRY.json"],[],[]),
 ("LEARNING_ENGINE","ENGINE","TAKY","e7ca5c7f94f6721a8f399d8deb49f7f01d73f6a2","OS/LEARNING_ENGINE_CORE.md",[],["CURRENT/LEARNING_ENGINE_DATA_READINESS_CURRENT.json"],[]),
 ("PLANNER","ENGINE","TAKY","e7ca5c7f94f6721a8f399d8deb49f7f01d73f6a2","OPEN_OWNER_GAP",["OS/GUIDE_FAMILY_LEARNING_OS.md"],["PROJECTS/READY_WHOLE_IMPLEMENTATION_CONTRACT.md#Planner / MAIN"],["PLANNER_OWNER_GAP"]),
 ("EXPLORER_CREW","ENGINE","TAKY","e7ca5c7f94f6721a8f399d8deb49f7f01d73f6a2","OS/EXPLORATION_CREW_CANONICAL.md",["MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md"],["LEARNING/transport/central-learning-production-host.js"],["EXPLORER_CREW_CENTRAL_RUNTIME","HIDE_CREW_V2","SNAP_CREW_V2"]),
 ("BADGE","ENGINE","TAKY","e7ca5c7f94f6721a8f399d8deb49f7f01d73f6a2","OPEN_OWNER_GAP",["MASTER/DESIGN_UI_ASSET_SOURCE_PROTOCOL.md"],["BADGE/badge-award-ledger-store.js"],["BADGE_CENTRAL","BADGE_OWNER_GAP"]),
 ("SAVEY","ENGINE","SAVEY","5a196080b8f8ce50d188b0181d9bec5e5477a265","OPEN_OWNER_GAP",[],[],["SAVEY_LIVE_GOOGLE_BINDING_AND_DATA_POPULATION","SAVEY_OWNER_GAP"])]
coverage={"schema":"TAKY_ALPHA_APP_ENGINE_COVERAGE_V0_1","status":"STRUCTURAL_COVERAGE","date":TODAY,"frozen_beta_snapshot_identity_sha256":FROZEN,"rows":[],"claim_dimensions":CLAIMS,"rule":"POINTER_ONLY_NE_STRUCTURAL_COVERAGE"}
for ident,kind,repo,sha,owner,inherit,impl,opens in apps:
    ev=[x for x in [owner if owner!="OPEN_OWNER_GAP" else None,*inherit,*impl] if x]
    coverage["rows"].append({"id":ident,"kind":kind,"source_repo":repo,"frozen_sha":sha,"semantic_owner":None if owner=="OPEN_OWNER_GAP" else owner,"owner_state":"OPEN_OWNER_GAP" if owner=="OPEN_OWNER_GAP" else "RESOLVED","inherited_contracts":inherit,"implementation_or_evidence_refs":impl,"open_refs":opens,"claims":claimset(True,bool(impl),False,False,ev)})
save("TAKY_ALPHA_APP_ENGINE_COVERAGE_V0_1.json", coverage)

def stage(id_,owner,refs=None,state="MAPPED"):
    return {"id":id_,"owner":owner if owner!="OPEN_OWNER_GAP" else None,"owner_state":"OPEN_OWNER_GAP" if owner=="OPEN_OWNER_GAP" else state,"implementation_or_evidence_refs":refs or []}
pipeline={"schema":"TAKY_ALPHA_PIPELINE_MAP_V0_1","status":"STRUCTURAL_MAP","date":TODAY,"pipelines":[
 {"id":"LEARNING_DATA_TO_EXECUTION","stages":[stage("SOURCE_CAPTURE","MASTER/CONVERSATION_TO_SYSTEM_PROTOCOL.md",["OS/DRIVE_C2S_DIRECT.md"]),stage("MINING","OPEN_OWNER_GAP",["CURRENT/DATA/DATA_INDEX_SEARCH_PROJECTION.json"]),stage("ATOMIZE","MASTER/CONVERSATION_TO_SYSTEM_PROTOCOL.md"),stage("INDEX_SEARCH","OS/LEARNING_ENGINE_CORE.md",["CURRENT/DATA/DATA_INDEX_SEARCH_PROJECTION.json"]),stage("RELATE","OS/LEARNING_ENGINE_CORE.md"),stage("LEARNING","OS/LEARNING_ENGINE_CORE.md",["CURRENT/LEARNING_ENGINE_DATA_READINESS_CURRENT.json"]),stage("GROW","MASTER/GROWTH_INTELLIGENCE_PROTOCOL.md"),stage("PLANNER","OPEN_OWNER_GAP",["PROJECTS/READY_WHOLE_IMPLEMENTATION_CONTRACT.md#Planner / MAIN"]),stage("APP_EXECUTION","MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md",["ALPHA/TAKY_ALPHA_APP_ENGINE_COVERAGE_V0_1.json"]),stage("RESULT_EVIDENCE","MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md"),stage("CARRYOVER_CURRENT","MASTER/EXECUTION_CHECKPOINT_PROTOCOL.md")]},
 {"id":"WORK_OS_ARCHIGROW","stages":[stage("SOURCE_INTAKE","OS/WORK_OS.md",["MASTER/OPERATIONAL_WORKSPACE_PROTOCOL.md"]),stage("ANALYSIS","DOMAIN/ARCHITECTURE_WORK_OS.md"),stage("ARTIFACT_OUTPUT","DOMAIN/ARCHITECTURE_WORK_OS.md"),stage("VALIDATION","MASTER/VALIDATION_RULES.md"),stage("LEARNING_GROWTH","DOMAIN/ARCHITECTURE_GROWTH_MAP.md",["MASTER/GROWTH_INTELLIGENCE_PROTOCOL.md"])]},
 {"id":"DESIGN_UI_ASSET","stages":[stage("APPROVED_SOURCE","MASTER/DESIGN_UI_ASSET_SOURCE_PROTOCOL.md"),stage("SCREEN_CONTRACT","MASTER/DESIGN_UI_ASSET_SOURCE_PROTOCOL.md"),stage("ASSET_LAYERS_BINDING","MASTER/DESIGN_UI_ASSET_SOURCE_PROTOCOL.md",["TAKY-ASSETS"]),stage("UI_RUNTIME","MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md",["ALPHA/TAKY_ALPHA_APP_ENGINE_COVERAGE_V0_1.json"]),stage("VISUAL_REGRESSION","MASTER/VALIDATION_RULES.md")]},
 {"id":"BADGE_REWARD","stages":[stage("EVIDENCE_PRODUCER","MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md"),stage("VERIFIED_OBSERVATION","OPEN_OWNER_GAP",["CURRENT/BADGE_SYSTEM_RECOVERY_CURRENT_2026-09-26.json"]),stage("AWARD_POLICY","OPEN_OWNER_GAP",["BADGE/BADGE_60_PLUS_HISTORY_20_STORY_SYSTEM_2026-09-26.md"]),stage("DURABLE_LEDGER","OPEN_OWNER_GAP",["BADGE/badge-award-ledger-store.js"]),stage("VISUAL_BINDING","MASTER/DESIGN_UI_ASSET_SOURCE_PROTOCOL.md"),stage("REWARD_USE","OPEN_OWNER_GAP")]}]}
save("TAKY_ALPHA_PIPELINE_MAP_V0_1.json", pipeline)

runtime={"schema":"TAKY_ALPHA_RUNTIME_CONTRACTS_V0_1","status":"STRUCTURAL_MAP","date":TODAY,"contracts":[
 {"id":"SYNC_OFFLINE","authority":"TAKY_SYNC_CONTRACT_V1.md","implementation_refs":[],"claims":claimset(True,False)},
 {"id":"ACCOUNT_AUTH","authority":"MASTER/SHARED_TECHNICAL_CAPABILITY_REGISTRY.json","implementation_refs":["SHARED/runtime/taky-account-auth-public-config-v1.js","SHARED/runtime/taky-google-account-auth-v1.js"],"claims":claimset(True,True)},
 {"id":"FAMILY_SESSION","authority":"OS/CHARACTER_ASSET_BEHAVIOR_PIPELINE.md","implementation_refs":["LEARNING/transport/family-session-http-endpoint.js","LEARNING/transport/family-character-profile-http-endpoint.js"],"claims":claimset(True,True)},
 {"id":"PRIVATE_CHARACTER_BINARY","authority":"OS/CHARACTER_ASSET_BEHAVIOR_PIPELINE.md","implementation_refs":["LEARNING/transport/private-character-object-store-adapter.js","LEARNING/transport/local-character-object-store.js"],"claims":claimset(True,True)},
 {"id":"DRIVE_GOOGLE_CANONICAL_DATA","authority":"TAKY_SYNC_CONTRACT_V1.md","implementation_refs":[],"claims":claimset(True,False)},
 {"id":"LOCAL_HTTP_BRIDGE","authority":"MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md","implementation_refs":["LEARNING/transport/node-http-learning-bridge.js","LEARNING/transport/central-learning-production-host.js"],"claims":claimset(True,True)}],"claim_rule":"CODE_EXISTS_NE_RUNTIME_VERIFIED_NE_DEVICE_VERIFIED_NE_PRODUCTION_VERIFIED"}
save("TAKY_ALPHA_RUNTIME_CONTRACTS_V0_1.json", runtime)

rule_compile=load("TAKY_ALPHA_RULE_COMPILE_V0_1.json")
known={"TKY-ENFORCEMENT-001":["ENFORCEMENT/taky_gate.py","MASTER/ENFORCEMENT_PROTOCOL.md"],"TKY-CHECKPOINT-001":["ENFORCEMENT/execution_checkpoint.py","MASTER/EXECUTION_CHECKPOINT_PROTOCOL.md"],"TKY-C2S-001":["MASTER/CONVERSATION_TO_SYSTEM_PROTOCOL.md"],"TKY-CODEX-001":["MASTER/CODEX_TASK_CONTRACT.md"]}
gate_rows=[]
for rr in rule_compile.get("rules",[]):
    rid=rr.get("rule_id"); refs=known.get(rid,[])
    gate_rows.append({"rule_id":rid,"owner":rr.get("owner"),"gate_state":"EXECUTABLE_OR_CONTRACT_BOUND" if refs else "NO_EXECUTABLE_GATE_RECORDED","gate_refs":refs})
save("TAKY_ALPHA_GATE_MAP_V0_1.json",{"schema":"TAKY_ALPHA_GATE_MAP_V0_1","status":"A2B_EXPLICIT_MAP","date":TODAY,"canonical_rule_registry_blob_sha":CANONICAL_RULE_BLOB,"rows":gate_rows,"rule":"NO_EXECUTABLE_GATE_RECORDED is explicit and must not be treated as PASS-through."})
save("TAKY_ALPHA_EVIDENCE_GRAPH_V0_1.json",{"schema":"TAKY_ALPHA_EVIDENCE_GRAPH_V0_1","status":"A4_STRUCTURAL_GRAPH","date":TODAY,"nodes":[{"id":"FROZEN_BETA","ref":"ALPHA_INPUT/FROZEN_BETA/BETA_FREEZE_MANIFEST_20261003.json","class":"IMMUTABLE_INPUT"},{"id":"AUTHORITY","ref":"ALPHA/TAKY_ALPHA_AUTHORITY_MAP_V0_1.json","class":"AUTHORITY_MAP"},{"id":"ROUTING","ref":"ALPHA/TAKY_ALPHA_ROUTING_GRAPH_V0_1.json","class":"ROUTING"},{"id":"APP_ENGINE","ref":"ALPHA/TAKY_ALPHA_APP_ENGINE_COVERAGE_V0_1.json","class":"DEPTH_COVERAGE"},{"id":"PIPELINES","ref":"ALPHA/TAKY_ALPHA_PIPELINE_MAP_V0_1.json","class":"PIPELINE"},{"id":"RUNTIME","ref":"ALPHA/TAKY_ALPHA_RUNTIME_CONTRACTS_V0_1.json","class":"RUNTIME_CONTRACT"},{"id":"OPEN","ref":"ALPHA/TAKY_ALPHA_OPEN_CLOSURE_PLAN_V0_1.json","class":"OPEN_DISPOSITION"},{"id":"POST_FREEZE","ref":"ALPHA/TAKY_ALPHA_POST_FREEZE_DELTA_V0_1.json","class":"VOLATILE_CANDIDATE"}],"edges":[{"from":"FROZEN_BETA","to":"AUTHORITY","relation":"SEEDS"},{"from":"AUTHORITY","to":"ROUTING","relation":"BOUNDS"},{"from":"ROUTING","to":"APP_ENGINE","relation":"ROUTES"},{"from":"APP_ENGINE","to":"PIPELINES","relation":"PARTICIPATES_IN"},{"from":"PIPELINES","to":"RUNTIME","relation":"USES"},{"from":"APP_ENGINE","to":"OPEN","relation":"PRESERVES_GAPS"},{"from":"POST_FREEZE","to":"OPEN","relation":"CANDIDATE_DELTA_ONLY"}],"rule":"TRACEABLE_STRUCTURE_NE_RUNTIME_PROOF"})
save("TAKY_ALPHA_OPEN_CLOSURE_PLAN_V0_1.json",{"schema":"TAKY_ALPHA_OPEN_CLOSURE_PLAN_V0_1","status":"A6_CLASSIFIED","date":TODAY,"items":[{"id":"EXPLORER_CREW_CENTRAL_RUNTIME","class":"PRODUCT_GAP","blocks_structural_alpha":False},{"id":"HIDE_CREW_V2","class":"PRODUCT_GAP","blocks_structural_alpha":False},{"id":"SNAP_CREW_V2","class":"PRODUCT_GAP","blocks_structural_alpha":False},{"id":"BADGE_CENTRAL","class":"PRODUCT_GAP","blocks_structural_alpha":False,"detail":"47 producer-QA PASS / 13 OPEN / 0 active frozen snapshot"},{"id":"DESIGN_TO_UI","class":"CANDIDATE","blocks_structural_alpha":False},{"id":"ASSET_POINTER_CONTRACT","class":"CANDIDATE_HOLD","blocks_structural_alpha":False},{"id":"FAMILY_PROFILE_RADIO_UX","class":"PRODUCT_GAP","blocks_structural_alpha":False,"detail":"tap-vs-hold remains unresolved"},{"id":"SNAP_LEGACY_BROWSER_CLOSURE","class":"UNVERIFIED_CONTAINED","blocks_structural_alpha":False},{"id":"SAVEY_LIVE_GOOGLE_BINDING_AND_DATA_POPULATION","class":"RUNTIME_GAP","blocks_structural_alpha":False},{"id":"SHARED_AUTH_IDENTITY_FEDERATION","class":"HOLD","blocks_structural_alpha":False},{"id":"HOSTED_RUNTIME_INTERCEPTION","class":"UNVERIFIED_CONTAINED","blocks_structural_alpha":False},{"id":"DEPLOYMENT","class":"HOLD","blocks_structural_alpha":False},{"id":"LOCAL_INFRA_HOST_IDENTITY","class":"EXTERNAL_BOUNDARY","blocks_structural_alpha":False},{"id":"LOCAL_INFRA_CAD_EXCEL_HWP_TASKS","class":"FUTURE_LANE","blocks_structural_alpha":False},{"id":"A8_INDEPENDENT_CROSS_VALIDATION","class":"ALPHA_GATE","blocks_structural_alpha":True},{"id":"A10_HUMAN_PROMOTION","class":"HUMAN_GATE","blocks_structural_alpha":True}],"rule":"PRODUCT_RUNTIME_GAP_NE_ALPHA_STRUCTURAL_BLOCKER_UNLESS_MARKED"})

master_path=ALPHA/"TAKY_ALPHA_MASTER_V0_1.md"; master=master_path.read_text(encoding="utf-8")
append = """## 21. Whole-system depth closure — 2026-10-04
Alpha structural coverage is not satisfied by owner pointers alone. Machine-readable depth surfaces are the app/engine coverage, pipeline map, runtime contracts, gate map, evidence graph, OPEN closure plan, bounded local-infrastructure lane, and post-freeze delta artifacts.
Areas A-F retain owner/owner-gap, implementation/evidence references, explicit OPEN refs and independent claim dimensions.

## 22. Bounded lanes and post-freeze deltas
The D:\\Git PWA\\TAKY local Alpha completion is imported only as LOCAL_INFRA_ONLY.
LOCAL_ALPHA_COMPLETE != SYSTEM_ALPHA_COMPLETE.
Frozen Beta remains immutable. Later working heads and dirty worktrees are captured only as volatile candidate evidence and do not self-promote to canonical authority.

## 23. Current system-wide Alpha gate
Structural completion requires V11 pipeline completeness, V12 app/engine depth and V13 lane-boundary PASS in addition to the earlier gates.
A8 independent cross-validation and A10 human promotion remain separate mandatory gates.
"""
if "## 21. Whole-system depth closure" not in master: master=master.rstrip()+"\n\n"+append
master_path.write_text(master,encoding="utf-8")

(REVIEW/"ALPHA_SYSTEM_CLOSURE_APPLY_20261004.json").write_text(json.dumps({"schema":"TAKY_ALPHA_SYSTEM_CLOSURE_APPLY_20261004","status":"APPLIED_AWAITING_VALIDATION","date":TODAY,"canonical_rule_registry_blob_sha":CANONICAL_RULE_BLOB,"frozen_beta_snapshot_identity_sha256":FROZEN,"next":"RUN_DETERMINISTIC_VALIDATION"},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("APPLIED")
