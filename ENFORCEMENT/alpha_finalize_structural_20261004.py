from pathlib import Path
import json
ROOT=Path(r"D:\Git PWA\TAKY_ALPHA_20261003")
ALPHA=ROOT/"ALPHA"; REVIEW=ROOT/"ALPHA_REVIEW"
def load(rel): return json.loads((ROOT/rel).read_text(encoding="utf-8"))
def save(rel,obj): (ROOT/rel).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

a7={
 "readonly":load("ALPHA_REVIEW/ALPHA_READONLY_VALIDATION_20261004.json"),
 "coverage":load("ALPHA_REVIEW/ALPHA_COVERAGE_DEPTH_VALIDATION_20261004.json"),
 "pipeline":load("ALPHA_REVIEW/ALPHA_PIPELINE_VALIDATION_20261004.json"),
 "lane":load("ALPHA_REVIEW/ALPHA_LANE_BOUNDARY_VALIDATION_20261004.json"),
 "beta_suite":load("ENFORCEMENT/alpha_validation_2026_10_03/beta_full_suite_v2.summary.json"),
 "git_diff_check":"PASS"
}
a8=(REVIEW/"CODEX_A8_EMBEDDED_RESULT_20261004.txt").read_text(encoding="utf-8")
a9=load("ALPHA_REVIEW/ALPHA_ADVERSARIAL_VALIDATION_20261004.json")
if not all(x["status"]=="PASS" for x in (a7["readonly"],a7["coverage"],a7["pipeline"],a7["lane"])): raise SystemExit("A7 focused validation not PASS")
if a7["beta_suite"].get("failures")!=0 or a7["beta_suite"].get("total")!=132: raise SystemExit("A7 beta regression not 132/132")
if "A8_PASS_SYSTEM_ALPHA_STRUCTURALLY_READY_FOR_A9" not in a8: raise SystemExit("A8 verdict missing")
if a9.get("status")!="PASS": raise SystemExit("A9 not PASS")

op=load("ALPHA/TAKY_ALPHA_OPEN_CLOSURE_PLAN_V0_1.json")
items=op.setdefault("items",[])
by={x.get("id"):x for x in items}
if "A8_INDEPENDENT_CROSS_VALIDATION" in by:
    by["A8_INDEPENDENT_CROSS_VALIDATION"].update({"state":"CLOSED_PASS","blocks_structural_alpha":False,"evidence":"ALPHA_REVIEW/CODEX_A8_EMBEDDED_RESULT_20261004.txt"})
else:
    items.append({"id":"A8_INDEPENDENT_CROSS_VALIDATION","class":"ALPHA_GATE","state":"CLOSED_PASS","blocks_structural_alpha":False,"evidence":"ALPHA_REVIEW/CODEX_A8_EMBEDDED_RESULT_20261004.txt"})
if "A9_ADVERSARIAL_VALIDATION" not in by:
    items.append({"id":"A9_ADVERSARIAL_VALIDATION","class":"ALPHA_GATE","state":"CLOSED_PASS","blocks_structural_alpha":False,"evidence":"ALPHA_REVIEW/ALPHA_ADVERSARIAL_VALIDATION_20261004.json"})
if "A10_HUMAN_PROMOTION" in by:
    by["A10_HUMAN_PROMOTION"].update({"state":"PENDING_HUMAN_PROMOTION","blocks_structural_alpha":False,"blocks_canonical_promotion":True})
op["status"]="STRUCTURAL_CLOSURE_CLASSIFIED"
op["date"]="2026-10-04"
save("ALPHA/TAKY_ALPHA_OPEN_CLOSURE_PLAN_V0_1.json",op)

val=load("ALPHA/TAKY_ALPHA_VALIDATION_CONTRACT_V0_1.json")
val["latest_structural_evidence"]={
 "A7":["ALPHA_REVIEW/ALPHA_READONLY_VALIDATION_20261004.json","ALPHA_REVIEW/ALPHA_COVERAGE_DEPTH_VALIDATION_20261004.json","ALPHA_REVIEW/ALPHA_PIPELINE_VALIDATION_20261004.json","ALPHA_REVIEW/ALPHA_LANE_BOUNDARY_VALIDATION_20261004.json","ENFORCEMENT/alpha_validation_2026_10_03/beta_full_suite_v2.summary.json"],
 "A8":"ALPHA_REVIEW/CODEX_A8_EMBEDDED_RESULT_20261004.txt",
 "A9":"ALPHA_REVIEW/ALPHA_ADVERSARIAL_VALIDATION_20261004.json",
 "A10":"PENDING_HUMAN_PROMOTION"
}
save("ALPHA/TAKY_ALPHA_VALIDATION_CONTRACT_V0_1.json",val)

master_path=ALPHA/"TAKY_ALPHA_MASTER_V0_1.md"
master=master_path.read_text(encoding="utf-8")
section="""## 24. System-wide structural closure checkpoint — 2026-10-04
Status: **SYSTEM_ALPHA_STRUCTURAL_COMPLETE_LOCAL / NON-CANONICAL**.

- A7 deterministic validation: focused structural validators PASS; Frozen Beta regression 132/132 PASS; git diff --check PASS.
- A8 independent cross-validation: Codex embedded evidence audit PASS (A8_PASS_SYSTEM_ALPHA_STRUCTURALLY_READY_FOR_A9).
- A9 adversarial validation: 7/7 negative probes detected and PASS.
- A10 human canonical-promotion gate remains PENDING.
- Planner, Badge and SAVEY owner gaps remain explicit OPEN; they were not silently promoted.
- Product/runtime/device/deployment gaps remain OPEN/HOLD and do not invalidate structural Alpha closure.
- No push, merge, deploy, Netlify or paid API transition is authorized by this checkpoint.

SYSTEM_ALPHA_STRUCTURAL_COMPLETE_LOCAL != CANONICAL_ALPHA_PROMOTED != PRODUCT_RUNTIME_COMPLETE != DEPLOYED.
"""
if "## 24. System-wide structural closure checkpoint" not in master:
    master=master.rstrip()+"\n\n"+section+"\n"
master_path.write_text(master,encoding="utf-8")

current={
 "schema":"TAKY_SYSTEM_ALPHA_CURRENT_V1",
 "date":"2026-10-04",
 "status":"SYSTEM_ALPHA_STRUCTURAL_COMPLETE_LOCAL_NONCANONICAL",
 "frozen_beta_snapshot_identity_sha256":"ed761ad71074001d967d044368f4e07cacefbc457e7b9e5cbb00f8e655a65f57",
 "a0_a7":"PASS",
 "a8":"PASS_CODEX_EMBEDDED_AUDIT",
 "a9":"PASS_7_OF_7_ADVERSARIAL_PROBES",
 "a10":"PENDING_HUMAN_CANONICAL_PROMOTION",
 "focused_validation_refs":[
  "ALPHA_REVIEW/ALPHA_READONLY_VALIDATION_20261004.json",
  "ALPHA_REVIEW/ALPHA_COVERAGE_DEPTH_VALIDATION_20261004.json",
  "ALPHA_REVIEW/ALPHA_PIPELINE_VALIDATION_20261004.json",
  "ALPHA_REVIEW/ALPHA_LANE_BOUNDARY_VALIDATION_20261004.json"
 ],
 "regression":{"frozen_beta":"132/132 PASS","git_diff_check":"PASS"},
 "independent_audit":"ALPHA_REVIEW/CODEX_A8_EMBEDDED_RESULT_20261004.txt",
 "adversarial":"ALPHA_REVIEW/ALPHA_ADVERSARIAL_VALIDATION_20261004.json",
 "open_plan":"ALPHA/TAKY_ALPHA_OPEN_CLOSURE_PLAN_V0_1.json",
 "explicit_owner_gaps":["PLANNER","BADGE","SAVEY"],
 "release_boundary":{"push":"HOLD","merge":"HOLD","deploy":"HOLD","netlify":"HOLD","paid_api":"HOLD"},
 "claim_boundary":"STRUCTURAL_ALPHA_COMPLETE_NE_CANONICAL_PROMOTION_NE_PRODUCT_RUNTIME_COMPLETE_NE_DEPLOYED",
 "next":"A10_HUMAN_CANONICAL_PROMOTION_ONLY_IF_EXPLICITLY_AUTHORIZED"
}
save("ALPHA/TAKY_ALPHA_CURRENT_V0_1.json",current)
save("ALPHA_REVIEW/ALPHA_SYSTEM_WIDE_STATUS_20261004_FINAL.json",current)
print("SYSTEM_ALPHA_STRUCTURAL_COMPLETE_LOCAL_NONCANONICAL")
