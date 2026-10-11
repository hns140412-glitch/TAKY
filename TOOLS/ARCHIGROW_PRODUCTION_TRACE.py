#!/usr/bin/env python3
import json, hashlib
from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parents[1]
SCHEMA=json.loads((ROOT/"DOMAIN"/"ARCHITECTURE_PRODUCTION_TRACE_SCHEMA.json").read_text(encoding="utf-8"))
STAGE_INDEX={s:i for i,s in enumerate(SCHEMA["stages"])}

def clean(v): return str(v or "").strip()
def nonempty_list(v): return isinstance(v,list) and any(clean(x) for x in v)
def iso_ok(v):
    try: datetime.fromisoformat(clean(v).replace("Z","+00:00")); return True
    except Exception: return False
def digest(v):
    raw=json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def validate_stage(s):
    issues=[]
    for k in SCHEMA["required_stage_fields"]:
        v=s.get(k)
        if k in {"input_refs","output_refs","checks","object_ids"}:
            if not nonempty_list(v): issues.append("MISSING_"+k.upper())
        elif not clean(v): issues.append("MISSING_"+k.upper())
    if clean(s.get("stage")) not in STAGE_INDEX: issues.append("STAGE_INVALID")
    if clean(s.get("status")) not in SCHEMA["statuses"]: issues.append("STATUS_INVALID")
    if clean(s.get("recorded_at")) and not iso_ok(s.get("recorded_at")): issues.append("RECORDED_AT_INVALID")
    if clean(s.get("status"))=="PASS" and not all(isinstance(x,dict) and clean(x.get("check_id")) and x.get("pass") is True for x in (s.get("checks") or [])):
        issues.append("PASS_REQUIRES_ALL_CHECKS_TRUE")
    if clean(s.get("stage"))=="QTO_COST":
        if not nonempty_list(s.get("quantity_refs")): issues.append("QTO_QUANTITY_REF_REQUIRED")
        if not nonempty_list(s.get("cost_source_refs")): issues.append("COST_SOURCE_REF_REQUIRED")
        if not clean(s.get("cost_as_of")): issues.append("COST_AS_OF_REQUIRED")
    if clean(s.get("stage"))=="REVIEW_PERMIT" and clean(s.get("status"))=="PASS":
        if not nonempty_list(s.get("authority_evidence_refs")): issues.append("PERMIT_AUTHORITY_EVIDENCE_REQUIRED")
    if clean(s.get("stage"))=="FIELD_RFI":
        if not (nonempty_list(s.get("rfi_refs")) or nonempty_list(s.get("field_change_refs"))):
            issues.append("RFI_OR_FIELD_CHANGE_REF_REQUIRED")
    if clean(s.get("stage"))=="AS_BUILT_LESSON":
        if not nonempty_list(s.get("result_evidence_refs")): issues.append("RESULT_EVIDENCE_REQUIRED")
        if not clean(s.get("lesson")): issues.append("LESSON_REQUIRED")
    return {"ok":not issues,"issues":issues}

def validate_trace(trace):
    issues=[]
    project=clean(trace.get("project_id"))
    option=clean(trace.get("selected_option_id"))
    if not project: issues.append("PROJECT_ID_REQUIRED")
    if not option: issues.append("SELECTED_OPTION_ID_REQUIRED")
    stages=trace.get("stages") or []
    if not stages: issues.append("STAGES_REQUIRED"); return {"ok":False,"issues":issues}
    seen=set(); last_index=-1; failed=False; prior_outputs=set(); prior_objects=set()
    normalized=[]
    for raw in stages:
        s=json.loads(json.dumps(raw,ensure_ascii=False))
        c=validate_stage(s)
        sid=clean(s.get("stage"))
        if sid in seen: issues.append("DUPLICATE_STAGE:"+sid)
        seen.add(sid)
        idx=STAGE_INDEX.get(sid,-1)
        if idx<last_index: issues.append("STAGE_ORDER_INVALID:"+sid)
        last_index=max(last_index,idx)
        if failed: issues.append("DOWNSTREAM_AFTER_FAIL_FORBIDDEN:"+sid)
        if clean(s.get("status")) in {"FAIL","BLOCKED"}: failed=True
        if clean(s.get("project_id") or project)!=project: issues.append("PROJECT_ID_DRIFT:"+sid)
        if clean(s.get("selected_option_id") or option)!=option: issues.append("SELECTED_OPTION_DRIFT:"+sid)
        if prior_outputs and not (prior_outputs & set(map(clean,s.get("input_refs") or []))):
            issues.append("PREVIOUS_OUTPUT_NOT_CONSUMED:"+sid)
        objs=set(map(clean,s.get("object_ids") or []))
        new_objs={x for x in objs-prior_objects if x}
        if prior_objects and new_objs:
            change_refs=set(map(clean,s.get("object_change_refs") or []))
            if not change_refs: issues.append("NEW_OBJECT_WITHOUT_CHANGE_EVIDENCE:"+sid)
        if not c["ok"]: issues.extend(sid+":"+x for x in c["issues"])
        prior_outputs=set(map(clean,s.get("output_refs") or []))
        prior_objects=objs or prior_objects
        s["stage_digest_sha256"]=digest({k:v for k,v in s.items() if k!="stage_digest_sha256"})
        normalized.append(s)
    return {
      "ok":not issues,
      "issues":issues,
      "project_id":project or None,
      "selected_option_id":option or None,
      "stages":normalized,
      "last_stage":clean(normalized[-1].get("stage")) if normalized else None,
      "production_complete":bool(normalized and clean(normalized[-1].get("stage"))=="AS_BUILT_LESSON" and clean(normalized[-1].get("status"))=="PASS" and not issues),
      "legal_feasibility_authorized":False,
      "cost_truth_authorized":False,
      "rule":"PRODUCTION TRACE PASS PROVES TRACE/CHAIN INTEGRITY ONLY; DOMAIN/LEGAL/COST AUTHORITIES REMAIN EXTERNAL"
    }

def learning_candidate(trace_result):
    if not trace_result.get("ok") or not trace_result.get("production_complete"):
        return {"ok":False,"reason":"COMPLETE_VERIFIED_TRACE_REQUIRED"}
    last=trace_result["stages"][-1]
    return {
      "ok":True,
      "grow_domain":"ARCHI_GROW",
      "state":"CASE",
      "project_id":trace_result["project_id"],
      "selected_option_id":trace_result["selected_option_id"],
      "result_evidence_refs":list(last.get("result_evidence_refs") or []),
      "lesson":clean(last.get("lesson")),
      "promotion_authorized":False,
      "authority_transfer":False
    }

if __name__=="__main__":
    print(json.dumps({"schema":SCHEMA["schema"],"ok":True},ensure_ascii=False))
