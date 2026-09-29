#!/usr/bin/env python3
"""Fail-closed source and truth guard for 60 badge art candidates.

This checks queue integrity and activation state. It does NOT certify illustration quality.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def verify(queue, source, registry, visual):
    errors=[]
    ids=[p["source_draft_id"] for p in source["presets"]]
    correction=queue.get("correction_ids",[])
    approved=set(ids)-set(correction)
    if len(ids)!=60 or len(set(ids))!=60: errors.append("SOURCE_60_ID_INTEGRITY")
    if len(correction)!=31 or len(set(correction))!=31 or not set(correction)<=set(ids) or len(approved)!=29:
        errors.append("REWORK_31_29_PARTITION")
    if queue.get("special_state")!={"BDG-DRAFT-012":"USER_SELECTED_CANDIDATE_QA_OPEN",
                                    "BDG-DRAFT-040":"LATEST_REJECTED_REWORK_OPEN"}:
        errors.append("012_040_CORRECTION_LOST")
    if queue.get("authority")!="CANDIDATE_QA_ONLY_NOT_APPROVAL":
        errors.append("FALSE_ART_AUTHORITY")
    for k in ("final_approved_count","production_png_binding_count","active_count","automatic_award_count"):
        if queue.get(k)!=0: errors.append("FALSE_PROGRESS_"+k.upper())
    if queue.get("activation")!="HOLD" or queue.get("netlify")!="HOLD":
        errors.append("RELEASE_HOLD_BYPASS")
    items=registry["items"]; visuals=visual["items"]
    if len(items)!=60 or len(visuals)!=60: errors.append("REGISTRY_60_INTEGRITY")
    else:
        for s,a,v in zip(source["presets"],items,visuals):
            if s["source_draft_id"]!=a["badge_id"] or s["source_draft_id"]!=v["draft_id"]:
                errors.append("SOURCE_ID_MAPPING")
            if s["stable_name"]!=a["source_title"] or s["motif"]!=a["scene_motif"] or s["storyline"]!=a["storyline"]:
                errors.append("SOURCE_SEMANTIC_DRIFT")
            if a.get("runtime_approved") is not False or a.get("runtime_bound") is not False or a.get("active") is not False:
                errors.append("PREMATURE_CANDIDATE_PROMOTION")
            if v.get("active") is not False or v.get("renderer_binding") is not False or v.get("approval_status")!="NOT_APPROVED":
                errors.append("PREMATURE_VISUAL_PROMOTION")
    if registry.get("live_binding") is not False or registry.get("automatic_approval") is not False:
        errors.append("REGISTRY_GLOBAL_ACTIVATION")
    return sorted(set(errors))

def main():
    q=read("BADGE/assets/visual-rework-queue-working.json")
    s=read("BADGE/badge-60-story-20-history-working.json")
    r=read("BADGE/assets/asset-registry-working.json")
    v=read("BADGE/badge-visual-registry-working.json")
    errors=verify(q,s,r,v)
    if errors:
        raise SystemExit("BADGE REWORK GATE FAIL: "+", ".join(errors))
    print("BADGE REWORK GATE PASS: 31 correction / 29 conditional candidates; 012 selected-not-approved, 040 rejected; zero final approvals, runtime bindings, active awards or deployment. This is structural truth, NOT visual quality approval.")

if __name__=="__main__":
    main()
