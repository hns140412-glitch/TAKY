from pathlib import Path
import json, sys
ROOT=Path(r"D:\Git PWA\TAKY_ALPHA_20261003")
def load(p): return json.loads((ROOT/p).read_text(encoding="utf-8"))
fail=[]
master=(ROOT/"ALPHA/TAKY_ALPHA_MASTER_V0_1.md").read_text(encoding="utf-8")
current=load("ALPHA/TAKY_ALPHA_CURRENT_V0_1.json")
authority=load("ALPHA/TAKY_ALPHA_AUTHORITY_MAP_V0_1.json")
validation=load("ALPHA/TAKY_ALPHA_VALIDATION_CONTRACT_V0_1.json")
open_plan=load("ALPHA/TAKY_ALPHA_OPEN_CLOSURE_PLAN_V0_1.json")
receipt=load("ALPHA/TAKY_ALPHA_LOCAL_CANONICAL_PROMOTION_20261004.json")
main_refresh=load("ALPHA_REVIEW/ALPHA_MAIN_REFRESH_EVIDENCE_20261004.json")
if "LOCAL CANONICAL ORCHESTRATION / GITHUB MAIN UNCHANGED" not in master: fail.append("MASTER_PROMOTION_STATUS_MISSING")
for stale in ("DRAFT / NON-CANONICAL / LOCAL ONLY","SYSTEM_ALPHA_STRUCTURAL_COMPLETE_LOCAL / NON-CANONICAL","A10 human canonical-promotion gate remains PENDING"):
    if stale in master: fail.append("MASTER_STALE_PROMOTION_TEXT:"+stale)
if current.get("status")!="SYSTEM_ALPHA_LOCAL_CANONICAL_ORCHESTRATION": fail.append("CURRENT_STATUS")
if current.get("a10")!="PASS_LOCAL_CANONICAL_HUMAN_APPROVED": fail.append("CURRENT_A10")
if current.get("semantic_owner_transfer") is not False: fail.append("SEMANTIC_OWNER_TRANSFER")
if current.get("github_main_mutated") is not False: fail.append("GITHUB_MAIN_MUTATION_CLAIM")
if authority.get("status")!="LOCAL_CANONICAL_ORCHESTRATION": fail.append("AUTHORITY_STATUS")
if authority.get("promotion",{}).get("state")!="A10_PASS_LOCAL_CANONICAL": fail.append("AUTHORITY_PROMOTION")
if validation.get("status")!="LOCAL_CANONICAL_PROMOTION_PASS": fail.append("VALIDATION_STATUS")
if validation.get("latest_structural_evidence",{}).get("A10")!="ALPHA/TAKY_ALPHA_LOCAL_CANONICAL_PROMOTION_20261004.json": fail.append("A10_EVIDENCE_REF")
a10=next((x for x in open_plan.get("items",[]) if x.get("id")=="A10_HUMAN_PROMOTION"),{})
if a10.get("state")!="CLOSED_PASS_LOCAL_CANONICAL": fail.append("OPEN_PLAN_A10")
if receipt.get("status")!="LOCAL_CANONICAL_ORCHESTRATION_PROMOTED": fail.append("RECEIPT_STATUS")
if receipt.get("human_approval",{}).get("approved") is not True: fail.append("HUMAN_APPROVAL_MISSING")
if receipt.get("scope",{}).get("semantic_owner_transfer") is not False: fail.append("RECEIPT_OWNER_TRANSFER")
if main_refresh.get("compare_status")!="identical" or main_refresh.get("ahead_by")!=0 or main_refresh.get("behind_by")!=0: fail.append("MAIN_REFRESH_DIVERGED")
for src in (current.get("release_boundary",{}), validation.get("promotion_boundary",{}), receipt.get("release_boundary",{})):
    for k in ("push","merge","deploy","paid_api"):
        if src.get(k)!="HOLD": fail.append("RELEASE_BOUNDARY:"+k)
if current.get("release_boundary",{}).get("netlify")!="HOLD": fail.append("NETLIFY_BOUNDARY")
for gap in ("PLANNER","BADGE","SAVEY"):
    if gap not in current.get("explicit_owner_gaps",[]): fail.append("OWNER_GAP_LOST:"+gap)
res={"schema":"TAKY_ALPHA_A10_PROMOTION_VALIDATION_V1","date":"2026-10-04","status":"PASS" if not fail else "FAIL","failure_count":len(fail),"failures":fail}
(ROOT/"ALPHA_REVIEW/ALPHA_A10_PROMOTION_VALIDATION_20261004.json").write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(res,ensure_ascii=False)); sys.exit(0 if not fail else 1)
