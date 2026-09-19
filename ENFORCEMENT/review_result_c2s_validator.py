#!/usr/bin/env python3
"""Validate that a review-result artifact is consumed by C2S instead of merely archived."""
from __future__ import annotations
import argparse, json
from pathlib import Path

FINAL_OR_ROUTED={
    "APPLIED_CANONICAL","APPLIED_RUNTIME","IMPLEMENTED_MINIMUM","PARTIAL",
    "PLANNED","HOLD","REJECTED","SUPERSEDED","OPEN"
}

def validate(data:dict)->list[str]:
    failures=[]
    policy=data.get("compile_policy") or {}
    if policy.get("result_artifact_is_c2s_source") is not True:
        failures.append("REVIEW_RESULT_NOT_C2S_SOURCE")
    if policy.get("no_record_only") is not True:
        failures.append("RECORD_ONLY_PATH_NOT_BLOCKED")
    items=data.get("items") or []
    if not items:
        failures.append("REVIEW_RESULT_ITEMS_MISSING")
    seen=set()
    for item in items:
        iid=str(item.get("id","")).strip()
        if not iid: failures.append("ITEM_ID_MISSING"); continue
        if iid in seen: failures.append(f"DUPLICATE_ITEM:{iid}")
        seen.add(iid)
        for k in ("owner","disposition","utilization_state","action_ref","next_action"):
            if not str(item.get(k,"")).strip():
                failures.append(f"{iid}:MISSING:{k}")
        state=str(item.get("utilization_state","")).strip()
        if state not in FINAL_OR_ROUTED:
            failures.append(f"{iid}:INVALID_UTILIZATION_STATE:{state or 'MISSING'}")
        if state=="PLANNED" and str(item.get("next_action","")).upper() in {"","NONE"}:
            failures.append(f"{iid}:PLANNED_WITHOUT_NEXT_ACTION")
    cov=data.get("coverage") or {}
    if cov.get("material_item_count")!=len(items):
        failures.append("COVERAGE_MATERIAL_COUNT_MISMATCH")
    if cov.get("mapped_material_item_count")!=len(items):
        failures.append("COVERAGE_MAPPED_COUNT_MISMATCH")
    if cov.get("unmapped_material_item_count")!=0:
        failures.append("UNMAPPED_MATERIAL_NONZERO")
    if cov.get("silent_loss_count")!=0:
        failures.append("SILENT_LOSS_NONZERO")
    return failures

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("ledger",type=Path); a=ap.parse_args()
    data=json.loads(a.ledger.read_text(encoding="utf-8"))
    failures=validate(data)
    print(json.dumps({"pass":not failures,"detected":failures},ensure_ascii=False,indent=2))
    return 0 if not failures else 1

if __name__=="__main__":
    raise SystemExit(main())
