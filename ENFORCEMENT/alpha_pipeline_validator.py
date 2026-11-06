from pathlib import Path
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
