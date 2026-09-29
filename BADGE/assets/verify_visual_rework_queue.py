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
    batch_path=ROOT/"BADGE/assets/rework-batch-01-source-locked.json"
    if not batch_path.is_file():
        errors.append("REWORK_BATCH_01_MISSING")
    else:
        batch=json.loads(batch_path.read_text(encoding="utf-8"))
        expected=correction[:10]
        if [x.get("badge_id") for x in batch.get("items",[])]!=expected:
            errors.append("REWORK_BATCH_01_ID_ORDER_DRIFT")
        direction=json.loads((ROOT/"BADGE/assets/individual-art-direction-60.json").read_text(encoding="utf-8"))["items"]
        originals={p["source_draft_id"]:p for p in source["presets"]}
        proposals={p["badge_id"]:p for p in direction}
        for item in batch.get("items",[]):
            bid=item.get("badge_id")
            if bid not in originals or bid not in proposals:
                errors.append("REWORK_BATCH_UNKNOWN_ID")
                continue
            original=originals[bid]; proposal=proposals[bid]
            if (item.get("canonical_source_title")!=original["stable_name"] or
                item.get("source_motif")!=original["motif"] or
                item.get("source_storyline")!=original["storyline"] or
                item.get("proposed_display_title")!=proposal["display_title_proposal"]):
                errors.append("REWORK_BATCH_SOURCE_DRIFT")
            if item.get("final_approved") is not False or item.get("source_file_verified") is not False:
                errors.append("REWORK_BATCH_FALSE_COMPLETION")
            if not item.get("fix") or not item.get("small_size_witness") or item.get("required_layers")!=["background","interior"]:
                errors.append("REWORK_BATCH_ACCEPTANCE_INCOMPLETE")
            if bid=="BDG-DRAFT-012" and item.get("status")!="USER_SELECTED_CANDIDATE_QA_OPEN":
                errors.append("REWORK_BATCH_012_APPROVAL_DRIFT")
    # Recovered witty copy is an input contract, not an optional editorial note.
    # Fail closed if any of the 60 source-specific art briefs loses its title,
    # substantive detail, reveal line, or provenance / expression technique.
    copy=read("BADGE/badge-wow-inspired-copyworking.json")
    direction_document=read("BADGE/assets/individual-art-direction-60.json")
    all_copy=copy.get("preset_copy", [])
    all_briefs=direction_document.get("items", [])
    if len(all_copy)!=60 or len(all_briefs)!=60 or len(copy.get("discovery_copy", []))!=20:
        errors.append("WITTY_COPY_60_PLUS_20_INTEGRITY")
    copy_by_id={x.get("source_draft_id"):x for x in all_copy}
    source_by_id={x["source_draft_id"]:x for x in source["presets"]}
    if len(copy_by_id)!=60:
        errors.append("WITTY_COPY_ID_DUPLICATION")
    if direction_document.get("copy_authority")!="BADGE/badge-wow-inspired-copyworking.json" or direction_document.get("copy_status")!="COPY_PROPOSAL_NOT_RUNTIME_APPROVED":
        errors.append("ART_DIRECTION_COPY_AUTHORITY")
    brief_by_id={}
    for brief in all_briefs:
        bid=brief.get("badge_id")
        if bid in brief_by_id: errors.append("ART_DIRECTION_ID_DUPLICATION")
        brief_by_id[bid]=brief
        original=source_by_id.get(bid)
        authored=copy_by_id.get(bid)
        if not original or not authored:
            errors.append("ART_DIRECTION_UNKNOWN_SOURCE_OR_COPY")
            continue
        required_pairs=(
            ("canonical_title",original["stable_name"]),
            ("source_motif",original["motif"]),
            ("source_storyline",original["storyline"]),
            ("display_title_proposal",authored["display_title_proposal"]),
            ("core_detail_proposal",authored["flavor_text_proposal"]),
            ("unlock_toast_proposal",authored["unlock_toast_proposal"]),
            ("wordplay_device",authored["wordplay_device"]),
            ("copy_status","COPY_PROPOSAL_NOT_RUNTIME_APPROVED"),
            ("copy_source_ref","BADGE/badge-wow-inspired-copyworking.json#"+bid),
            ("artwork_text_policy","NO_TEXT_BAKED_IN_SCENE; DISPLAY_TITLE_AND_CORE_DETAIL_ARE_SEPARATE_UI_TEXT")
        )
        if authored.get("canonical_title")!=original["stable_name"] or any(brief.get(k)!=v or not v for k,v in required_pairs):
            errors.append("ART_DIRECTION_WITTY_COPY_DRIFT")
    if [x.get("badge_id") for x in all_briefs]!=ids or set(copy_by_id)!=set(ids):
        errors.append("ART_DIRECTION_COPY_ORDER_OR_SET")
    if batch_path.is_file():
        batch=json.loads(batch_path.read_text(encoding="utf-8"))
        if batch.get("copy_authority")!="BADGE/badge-wow-inspired-copyworking.json" or batch.get("copy_status")!="COPY_PROPOSAL_NOT_RUNTIME_APPROVED":
            errors.append("REWORK_BATCH_COPY_AUTHORITY")
        for entry in batch.get("items", []):
            brief=brief_by_id.get(entry.get("badge_id"))
            if brief and any(entry.get(k)!=brief.get(k) for k in ("core_detail_proposal","unlock_toast_proposal","wordplay_device","artwork_text_policy")):
                errors.append("REWORK_BATCH_WITTY_COPY_DRIFT")
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
