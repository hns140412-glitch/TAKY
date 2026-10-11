#!/usr/bin/env python3
"""TAKY evidence -> relation -> execution -> outcome -> growth lineage.

This engine is intentionally conservative:
- discovery is never authority;
- relations are typed and provenance-bound;
- failure can create a regression candidate but never auto-promote policy;
- CURRENT_BEST requires independent/repeated outcome evidence + regression safety.
"""
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone

STAGES=("RAW","INDEX","LEARNING","RELATION","EXECUTION","OUTCOME","GROWTH")
PROMOTABLE={"FRONTIER","CURRENT_BEST"}
RELATION_TYPES={
    "SUPPORTS","CONTRADICTS","REFINES","DEPENDS_ON","DERIVED_FROM",
    "APPLIES_TO","FAILED_UNDER","SUCCEEDED_UNDER","SUPERSEDES","SAME_ENTITY"
}

def _s(v): return str(v or "").strip()
def _truthy(v):
    if v is None or v is False:
        return False
    if isinstance(v,(int,float)):
        return v != 0
    text=_s(v).lower()
    if text in {"","0","false","no","n","off","none","null"}:
        return False
    return True
def _id(prefix,payload):
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    return prefix+"-"+hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]

def validate_node(node:dict)->list[str]:
    errors=[]
    stage=_s(node.get("stage")).upper()
    if stage not in STAGES: errors.append("LINEAGE_STAGE_INVALID")
    if not _s(node.get("node_id")): errors.append("LINEAGE_NODE_ID_MISSING")
    if not _s(node.get("source_ref")): errors.append("LINEAGE_SOURCE_REF_MISSING")
    if stage in {"LEARNING","RELATION","EXECUTION","OUTCOME","GROWTH"} and not node.get("parent_refs"):
        errors.append("LINEAGE_PARENT_REQUIRED")
    if stage=="OUTCOME" and _s(node.get("verification_state")).upper() not in {"VERIFIED","FAILED_CONFIRMED","UNVERIFIED","PARTIAL"}:
        errors.append("OUTCOME_VERIFICATION_STATE_INVALID")
    return errors

def relation(src:str,dst:str,kind:str,evidence_refs:list[str],confidence:float|None=None)->dict:
    kind=_s(kind).upper()
    if kind not in RELATION_TYPES: raise ValueError("RELATION_TYPE_INVALID")
    payload={"src":src,"dst":dst,"kind":kind,"evidence_refs":sorted(set(evidence_refs or []))}
    return {
        "relation_id":_id("REL",payload),"src":src,"dst":dst,"kind":kind,
        "evidence_refs":payload["evidence_refs"],"confidence":confidence,
        "created_at":datetime.now(timezone.utc).isoformat()
    }

def growth_decision(candidate:dict,outcomes:list[dict],regressions:list[dict])->dict:
    target=_s(candidate.get("target_state")).upper()
    evidence_refs=sorted(set(candidate.get("evidence_refs") or []))
    verified=[]
    seen_verified=set()
    failures=[]
    for o in outcomes:
        if _truthy(o.get("synthetic")):
            continue
        state=_s(o.get("verification_state")).upper()
        if state=="VERIFIED":
            workflow_run=_s(o.get("workflow_run"))
            key=("WORKFLOW_RUN",workflow_run) if workflow_run else (
                "FALLBACK",
                _s(o.get("verification_authority")).upper(),
                _s(o.get("context_key")),
                _s(o.get("evidence_ref")),
            )
            if key not in seen_verified:
                seen_verified.add(key)
                verified.append(o)
        elif state=="FAILED_CONFIRMED":
            failures.append(o)
    independent={_s(o.get("verification_authority")).upper() for o in verified if _s(o.get("verification_authority"))}
    contexts={_s(o.get("context_key")) for o in verified if _s(o.get("context_key"))}
    bound_evidence_refs={_s(o.get("evidence_ref")) for o in verified if _s(o.get("evidence_ref"))}
    missing_outcome_evidence_ref=[o for o in verified if not _s(o.get("evidence_ref"))]
    outcome_workflow_runs={_s(o.get("workflow_run")) for o in verified if _s(o.get("workflow_run"))}

    regression_pass=[]
    regression_fail=[]
    regression_status_missing=[]
    regression_status_unrecognized=[]
    regression_status_conflict=[]
    regression_missing_authority=[]
    regression_missing_workflow_run=[]
    regression_overlap=[]
    seen_regressions={}
    for r in regressions:
        if _truthy(r.get("synthetic")):
            continue
        status=_s(r.get("status")).upper()
        pass_statuses={"PASS","PASSED","REGRESSION_PASS","SUCCESS"}
        fail_statuses={
            "FAIL","FAILED","FAILURE","REGRESSION_FAIL","ERROR",
            "CANCELLED","CANCELED","TIMED_OUT","TIMEOUT",
            "ACTION_REQUIRED","STARTUP_FAILURE","STALE","NEUTRAL","SKIPPED"
        }
        if not status:
            regression_status_missing.append(r)
            continue
        if status not in pass_statuses and status not in fail_statuses:
            regression_status_unrecognized.append(r)
            continue
        authority=_s(r.get("verification_authority")).upper()
        if not authority:
            regression_missing_authority.append(r)
            continue
        workflow_run=_s(r.get("workflow_run"))
        if not workflow_run:
            regression_missing_workflow_run.append(r)
            continue
        if workflow_run in outcome_workflow_runs:
            regression_overlap.append(r)
            continue
        key=("WORKFLOW_RUN",workflow_run)
        normalized_status="PASS" if status in pass_statuses else "FAIL"
        prior_status=seen_regressions.get(key)
        if prior_status:
            if prior_status != normalized_status:
                regression_status_conflict.append(r)
            continue
        seen_regressions[key]=normalized_status
        if normalized_status=="PASS":
            regression_pass.append(r)
        else:
            regression_fail.append(r)

    blockers=[]
    if target not in PROMOTABLE: blockers.append("GROWTH_TARGET_INVALID")
    if not evidence_refs: blockers.append("GROWTH_EVIDENCE_MISSING")
    if target=="CURRENT_BEST":
        if len(verified)<2: blockers.append("CURRENT_BEST_REQUIRES_REPEATED_VERIFIED_OUTCOMES")
        if len(contexts)<2: blockers.append("CURRENT_BEST_REQUIRES_CONTEXT_DIVERSITY")
        if len(independent)<1: blockers.append("CURRENT_BEST_REQUIRES_VERIFICATION_AUTHORITY")
        if missing_outcome_evidence_ref:
            blockers.append("CURRENT_BEST_OUTCOME_EVIDENCE_REF_MISSING")
        if not set(evidence_refs).issubset(bound_evidence_refs):
            blockers.append("CURRENT_BEST_EVIDENCE_REFS_UNBOUND")
        if failures: blockers.append("CURRENT_BEST_HAS_CONFIRMED_FAILURE")
        if regression_status_missing:
            blockers.append("CURRENT_BEST_REGRESSION_STATUS_MISSING")
        if regression_status_unrecognized:
            blockers.append("CURRENT_BEST_REGRESSION_STATUS_UNRECOGNIZED")
        if regression_status_conflict:
            blockers.append("CURRENT_BEST_REGRESSION_STATUS_CONFLICT")
        if regression_missing_authority:
            blockers.append("CURRENT_BEST_REGRESSION_AUTHORITY_MISSING")
        if regression_missing_workflow_run:
            blockers.append("CURRENT_BEST_REGRESSION_WORKFLOW_RUN_MISSING")
        if regression_overlap:
            blockers.append("CURRENT_BEST_REGRESSION_NOT_INDEPENDENT")
        if not regression_pass: blockers.append("CURRENT_BEST_REQUIRES_CLEAN_REGRESSION_EVIDENCE")
        if regression_fail: blockers.append("CURRENT_BEST_REGRESSION_NOT_CLEAN")
        design_signoff=_s(candidate.get("design_user_signoff_ref"))
        if _truthy(candidate.get("design_parity_claim")) and not design_signoff.startswith("USER_SIGNOFF:"):
            blockers.append("CURRENT_BEST_DESIGN_PARITY_REQUIRES_USER_SIGNOFF")
    elif target=="FRONTIER":
        if not verified and not candidate.get("external_evidence_verified"):
            blockers.append("FRONTIER_REQUIRES_VERIFIED_EVIDENCE")

    return {
        "pass":not blockers,
        "target_state":target,
        "decision":"PROMOTION_ELIGIBLE" if not blockers else "HOLD",
        "blockers":blockers,
        "metrics":{
            "verified_outcomes":len(verified),"confirmed_failures":len(failures),
            "context_diversity":len(contexts),"verification_authorities":len(independent),
            "bound_evidence_refs":len(bound_evidence_refs),
            "missing_outcome_evidence_refs":len(missing_outcome_evidence_ref),
            "regression_passes":len(regression_pass),"regression_failures":len(regression_fail),
            "regression_status_missing":len(regression_status_missing),
            "regression_status_unrecognized":len(regression_status_unrecognized),
            "regression_status_conflict":len(regression_status_conflict),
            "regression_missing_authority":len(regression_missing_authority),
            "regression_missing_workflow_run":len(regression_missing_workflow_run),
            "regression_overlap":len(regression_overlap)
        },
        "auto_promote":False,
        "human_review_required": target=="CURRENT_BEST"
    }

def compile_lineage(nodes:list[dict],relations:list[dict])->dict:
    errors=[]
    ids=set()
    for n in nodes:
        errors.extend(validate_node(n))
        nid=_s(n.get("node_id"))
        if nid in ids: errors.append("LINEAGE_DUPLICATE_NODE:"+nid)
        ids.add(nid)
    for r in relations:
        if _s(r.get("kind")).upper() not in RELATION_TYPES: errors.append("RELATION_TYPE_INVALID")
        if r.get("src") not in ids or r.get("dst") not in ids: errors.append("RELATION_DANGLING_REF")
        if not r.get("evidence_refs"): errors.append("RELATION_EVIDENCE_MISSING")
    stage_counts={s:sum(1 for n in nodes if _s(n.get("stage")).upper()==s) for s in STAGES}
    return {"pass":not errors,"errors":sorted(set(errors)),"stage_counts":stage_counts,
            "complete_loop":all(stage_counts[s]>0 for s in STAGES),
            "node_count":len(nodes),"relation_count":len(relations)}

if __name__=="__main__":
    print(json.dumps({"module":"TAKY_GROWTH_LINEAGE_ENGINE_V1","stages":STAGES},ensure_ascii=False))
