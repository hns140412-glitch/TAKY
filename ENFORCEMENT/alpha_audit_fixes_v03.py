from pathlib import Path
import json, hashlib

ROOT=Path(r"D:\Git PWA\TAKY_ALPHA_20261003")
ALPHA=ROOT/"ALPHA"
REVIEW=ROOT/"ALPHA_REVIEW"

def load(rel):
    return json.loads((ROOT/rel).read_text(encoding="utf-8"))

def dump(rel,obj):
    p=ROOT/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# 1) Rule compile: reference-only, registry-hash bound, no copied scope semantics.
rule_path=ROOT/"MASTER/RULE_REGISTRY.json"
rules=load("MASTER/RULE_REGISTRY.json")
rule_sha=hashlib.sha256(rule_path.read_bytes()).hexdigest()
compiled={
  "schema":"TAKY_ALPHA_RULE_OWNER_REFERENCE_COMPILE_V0_2",
  "status":"OWNER_REFERENCE_COMPILE_PASS",
  "date":"2026-10-03",
  "source_registry":"MASTER/RULE_REGISTRY.json",
  "source_registry_version":rules.get("registry_version"),
  "source_registry_sha256":rule_sha,
  "rule_count":len(rules.get("rules",[])),
  "rules":[
    {
      "rule_id":r.get("rule_id"),
      "owner":r.get("owner"),
      "owner_exists":bool(r.get("owner") and (ROOT/r["owner"]).exists()),
      "semantics":"RESOLVE_FROM_SOURCE_REGISTRY_AND_OWNER_AT_USE_TIME"
    }
    for r in rules.get("rules",[])
  ],
  "activation_gate_mapping":"NOT_RUN__A2B_PENDING",
  "invariants":[
    "ONE_RULE_ID_ONE_DECLARED_OWNER",
    "ALPHA_DOES_NOT_COPY_RULE_SCOPE_TEXT",
    "ALPHA_DOES_NOT_REDEFINE_RULE_SEMANTICS",
    "EXECUTABLE_GATE_MAPPING_REQUIRES_SEPARATE_A2B_VALIDATION"
  ]
}
dump("ALPHA/TAKY_ALPHA_RULE_COMPILE_V0_1.json",compiled)

# 2) Carry-over source IDs + registry coverage gaps.
carry=load("ALPHA/TAKY_ALPHA_CARRYOVER_OPEN_V0_1.json")
source_map={
 "EXPLORER_CREW_CENTRAL_RUNTIME":"exploration_crew_central_runtime",
 "HIDE_CREW_V2":"exploration_crew_hide_consumer_v2",
 "SNAP_CREW_V2":"exploration_crew_snap_consumer_v2",
 "BADGE_CENTRAL":"badge_central",
 "DESIGN_TO_UI":"design_to_ui",
 "ASSET_POINTER_CONTRACT":"assets_approved_results_pointer_contract",
 "FAMILY_PROFILE_RADIO_UX":"recent_family_profile_radio_ux",
 "SNAP_LEGACY_BROWSER_CLOSURE":"snap_legacy_browser_closure",
 "HOSTED_RUNTIME_INTERCEPTION":"hosted_runtime_interception",
 "DEPLOYMENT":"deployment_netlify"
}
for row in carry.get("classes",[]):
    if row.get("id") in source_map:
        row["source_scope_id"]=source_map[row["id"]]
        row["source_current"]="CURRENT/SYSTEM_WIDE_REVIEW.json"
    elif row.get("id")=="SAVEY_LIVE_GOOGLE_BINDING_AND_DATA_POPULATION":
        row["source_scope_id"]=None
        row["source"]="ALPHA_INPUT/FROZEN_BETA/BETA_FREEZE_MANIFEST_20261003.json#carry_over_open.savey"

mf=load("MASTER/MASTER_FILE_REGISTRY.json")
rule_owners={r.get("owner") for r in rules.get("rules",[])}
semantic_paths={x.get("paths",{}).get("owner") for x in mf.get("semantic_owners",[])}
active=[p for p,v in mf.get("files",{}).items() if v.get("class")=="ACTIVE_OWNER"]
coverage=[]
for p in sorted(set(active)-rule_owners):
    if p in semantic_paths:
        coverage.append({
          "path":p,
          "state":"COVERED_BY_SEMANTIC_OWNER_REGISTRY",
          "rule_id":None,
          "alpha_disposition":"PRESERVE_OWNER_POINTER__NO_RULE_ID_INVENTED"
        })
    else:
        coverage.append({
          "path":p,
          "state":"OPEN_RULE_REGISTRY_COVERAGE_GAP",
          "rule_id":None,
          "alpha_disposition":"PRESERVE_AS_OPEN__DO_NOT_INVENT_RULE_ID"
        })
carry["active_owner_rule_registry_coverage"]=coverage
dump("ALPHA/TAKY_ALPHA_CARRYOVER_OPEN_V0_1.json",carry)

# 3) Frozen path remap + approval binding stays in input lock.
lock=load("ALPHA_REVIEW/ALPHA_INPUT_LOCK_20261003.json")
lock["frozen_path_remap"]={
 "BETA_REVIEW/BETA_FREEZE_MANIFEST_20261003.json":"ALPHA_INPUT/FROZEN_BETA/BETA_FREEZE_MANIFEST_20261003.json",
 "BETA_REVIEW/BETA_FREEZE_READINESS_20261003.json":"ALPHA_INPUT/FROZEN_BETA/BETA_FREEZE_READINESS_20261003.json",
 "BETA_REVIEW/BETA_FINAL_ADVERSARIAL_CLOSURE_20261003.json":"ALPHA_INPUT/FROZEN_BETA/BETA_FINAL_ADVERSARIAL_CLOSURE_20261003.json",
 "TAKY_BETA_FROZEN_20261003.lock.json":"ALPHA_INPUT/FROZEN_BETA/TAKY_BETA_FROZEN_20261003.lock.json",
 "TAKY_BETA_FREEZE_APPROVAL_20261003.json":"ALPHA_INPUT/FROZEN_BETA/BETA_FREEZE_APPROVAL_20261003.json"
}
lock["path_remap_rule"]="Frozen artifact contents remain immutable; Alpha resolves their original Beta-local pointers only through this explicit remap."
dump("ALPHA_REVIEW/ALPHA_INPUT_LOCK_20261003.json",lock)

# 4) Local dirty/candidate boundary from exact Frozen manifest.
beta=load("ALPHA_INPUT/FROZEN_BETA/BETA_FREEZE_MANIFEST_20261003.json")
local=beta.get("local_snapshot",{})
candidate_boundary={
 "schema":"TAKY_ALPHA_FROZEN_LOCAL_CANDIDATE_BOUNDARY_V0_1",
 "status":"FROZEN_INPUT_CANDIDATE_SCOPE",
 "date":"2026-10-03",
 "frozen_beta_snapshot_identity_sha256":lock.get("frozen_beta_snapshot_identity_sha256"),
 "head":local.get("head"),
 "index_tree":local.get("index_tree"),
 "tracked_patch_sha256":local.get("tracked_patch_sha256"),
 "staged_files":local.get("staged_files",[]),
 "unstaged_files":local.get("unstaged_files",[]),
 "source_untracked_sha256":local.get("source_untracked_sha256",{}),
 "authority":"NONE__FROZEN_LOCAL_IMPLEMENTATION_EVIDENCE_ONLY",
 "promotion_rule":"Each item requires owner-aware validation and explicit promotion; presence in Frozen Beta seed does not make it canonical.",
 "mutation_rule":"Alpha may analyze/restructure these inputs but must not rewrite Frozen Beta evidence."
}
dump("ALPHA/TAKY_ALPHA_FROZEN_LOCAL_CANDIDATE_BOUNDARY_V0_1.json",candidate_boundary)

# 5) Source trace for Alpha-only summaries/synthesis.
trace={
 "schema":"TAKY_ALPHA_SOURCE_TRACE_V0_1",
 "status":"DRAFT_TRACE",
 "date":"2026-10-03",
 "items":[
  {
   "alpha_concept":"Human Key / Global Cycle",
   "classification":"VERBATIM_DISPLAY_REFERENCE__NO_REDEFINITION",
   "sources":["MASTER/MASTER_LOGIC.md","TAKY.md","MASTER/RULE_REGISTRY.json#TKY-GUIDING-001"]
  },
  {
   "alpha_concept":"DEEP MEMORY — LIGHT EXECUTION",
   "classification":"EXISTING_FROZEN_PRINCIPLE",
   "sources":["MASTER/EXECUTION_CHECKPOINT_PROTOCOL.md"]
  },
  {
   "alpha_concept":"RAW / INDEX / DETAIL / CURRENT",
   "classification":"ALPHA_DRAFT_SYNTHESIS_FROM_FROZEN_STORAGE_AND_CURRENT_BOUNDARIES",
   "sources":["MASTER/CONVERSATION_TO_SYSTEM_PROTOCOL.md","MASTER/EXECUTION_CHECKPOINT_PROTOCOL.md","CURRENT/SYSTEM_WIDE_REVIEW.json"],
   "authority_transfer":False
  },
  {
   "alpha_concept":"LearningGrow",
   "classification":"ALPHA_DRAFT_UMBRELLA_LABEL",
   "sources":["OS/LEARNING_ENGINE_CORE.md","MASTER/GROWTH_INTELLIGENCE_PROTOCOL.md"],
   "authority_transfer":False
  },
  {
   "alpha_concept":"ArchiGrow",
   "classification":"ALPHA_DRAFT_UMBRELLA_LABEL",
   "sources":["DOMAIN/ARCHITECTURE_GROWTH_MAP.md","DOMAIN/ARCHITECTURE_WORK_OS.md","MASTER/GROWTH_INTELLIGENCE_PROTOCOL.md"],
   "authority_transfer":False
  },
  {
   "alpha_concept":"Independent evidence claim dimensions",
   "classification":"NORMALIZATION_OF_EXISTING_NON_EQUIVALENCE_BOUNDARY",
   "sources":["MASTER/MASTER_LOGIC.md","CURRENT/SYSTEM_WIDE_REVIEW.json"],
   "authority_transfer":False
  }
 ],
 "rule":"ALPHA_DRAFT_SYNTHESIS may organize Frozen Beta concepts but cannot become canonical semantics without migration coverage, validation, and human promotion."
}
dump("ALPHA/TAKY_ALPHA_SOURCE_TRACE_V0_1.json",trace)

# 6) Migration + decision coverage matrix.
layer=load("MASTER/SYSTEM_LAYER_OWNERSHIP_MAP.json")
rows=[]
for ns in mf.get("semantic_owners",[]):
    rows.append({
      "source_type":"SEMANTIC_OWNER",
      "source":ns["paths"]["owner"],
      "identity":ns["namespace"],
      "alpha_representation":"ALPHA/TAKY_ALPHA_AUTHORITY_MAP_V0_1.json",
      "mode":"POINTER_ONLY",
      "authority_transfer":False,
      "status":"COVERED"
    })
for r in rules.get("rules",[]):
    rows.append({
      "source_type":"RULE_ID",
      "source":"MASTER/RULE_REGISTRY.json",
      "identity":r["rule_id"],
      "alpha_representation":"ALPHA/TAKY_ALPHA_RULE_COMPILE_V0_1.json",
      "mode":"REGISTRY_HASHED_REFERENCE",
      "authority_transfer":False,
      "status":"COVERED_A2A__A2B_PENDING"
    })
for lid,lrow in layer.get("layers",{}).items():
    rows.append({
      "source_type":"SYSTEM_LAYER",
      "source":"MASTER/SYSTEM_LAYER_OWNERSHIP_MAP.json",
      "identity":lid,
      "alpha_representation":"ALPHA/TAKY_ALPHA_ROUTING_GRAPH_V0_1.json",
      "mode":"ROUTING_REFERENCE",
      "authority_transfer":False,
      "status":"COVERED_OR_EXPLICITLY_NON_ROUTING"
    })
rows.append({
 "source_type":"FROZEN_OPEN_SET",
 "source":"ALPHA_INPUT/FROZEN_BETA/BETA_FREEZE_MANIFEST_20261003.json",
 "identity":"carry_over_open + contained_open",
 "alpha_representation":"ALPHA/TAKY_ALPHA_CARRYOVER_OPEN_V0_1.json",
 "mode":"LOSSLESS_COPY_PLUS_SOURCE_MAPPING",
 "authority_transfer":False,
 "status":"COVERED"
})
rows.append({
 "source_type":"FROZEN_LOCAL_CANDIDATE",
 "source":"ALPHA_INPUT/FROZEN_BETA/BETA_FREEZE_MANIFEST_20261003.json#local_snapshot",
 "identity":"staged + unstaged + source_untracked",
 "alpha_representation":"ALPHA/TAKY_ALPHA_FROZEN_LOCAL_CANDIDATE_BOUNDARY_V0_1.json",
 "mode":"FROZEN_INPUT_BOUNDARY",
 "authority_transfer":False,
 "status":"COVERED"
})
migration={
 "schema":"TAKY_ALPHA_MIGRATION_DECISION_COVERAGE_V0_1",
 "status":"DRAFT_COVERAGE_MATRIX",
 "date":"2026-10-03",
 "purpose":"Required old→new coverage evidence before any canonical replacement. This matrix does not authorize replacement.",
 "rows":rows,
 "unresolved":[
   x for x in coverage if x.get("state")=="OPEN_RULE_REGISTRY_COVERAGE_GAP"
 ],
 "canonical_replacement":"NOT_AUTHORIZED"
}
dump("ALPHA/TAKY_ALPHA_MIGRATION_COVERAGE_V0_1.json",migration)

print(json.dumps({
 "rule_count":compiled["rule_count"],
 "rule_registry_sha256":rule_sha,
 "active_owner_coverage":coverage,
 "migration_rows":len(rows)
},ensure_ascii=False))
