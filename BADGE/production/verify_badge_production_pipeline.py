#!/usr/bin/env python3
"""TAKY Badge production pipeline gate.

This is a PRE-GENERATION + admission integrity gate. It does not claim visual taste approval.
It fails closed if display item, core detail or source motif drift from authority, if character
policy is weakened, or if failed/unreviewed art is allowed to count as production progress.
"""
import copy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def load(rel,root=ROOT):
    return json.loads((Path(root)/rel).read_text(encoding="utf-8"))

def verify(root=ROOT, pipeline=None):
    root=Path(root)
    errors=[]
    p=pipeline if pipeline is not None else load("BADGE/production/badge-production-pipeline.json",root)
    direction=load("BADGE/assets/individual-art-direction-60.json",root)
    source=load("BADGE/badge-60-story-20-history-working.json",root)
    copydoc=load("BADGE/badge-wow-inspired-copyworking.json",root)
    queue=load("BADGE/assets/visual-rework-queue-working.json",root)
    admission=load("BADGE/assets/production-art-admission.json",root)
    D={x["badge_id"]:x for x in direction["items"]}
    S={x["source_draft_id"]:x for x in source["presets"]}
    C={x["source_draft_id"]:x for x in copydoc["preset_copy"]}
    ids=queue["correction_ids"]
    if p.get("schema")!="TAKY_BADGE_PRODUCTION_PIPELINE_V1": errors.append("PIPELINE_SCHEMA")
    if p.get("correction_count")!=len(ids) or len(p.get("items",[]))!=len(ids): errors.append("CORRECTION_COUNT")
    if [x.get("badge_id") for x in p.get("items",[])]!=ids: errors.append("CORRECTION_ORDER_OR_SET")
    inv=p.get("invariants",{})
    required_inv={
      "fixed_inputs":["display_item","core_detail","source_motif"],
      "no_generation_when_any_fixed_input_missing":True,
      "no_user_debug_loop":True,
      "no_character_in_base":True,
      "character_overlay_must_be_separate":True,
      "no_shared_ui_baked_into_art":True,
      "no_text_baked_into_art":True,
      "circular_outside_transparent":True,
      "one_badge_one_individual_file_set":True,
      "failed_candidate_never_counts_as_progress":True,
      "admission_does_not_equal_runtime_approval":True,
      "netlify":"HOLD"
    }
    if inv!=required_inv: errors.append("PIPELINE_INVARIANTS_DRIFT")
    for x in p.get("items",[]):
        bid=x.get("badge_id")
        if bid not in D or bid not in S or bid not in C:
            errors.append("UNKNOWN_BADGE_ID"); continue
        d,s,c=D[bid],S[bid],C[bid]
        expected={
          "visual_id":d["visual_id"],
          "display_item":d["display_title_proposal"],
          "core_detail":d["core_detail_proposal"],
          "source_motif":d["source_motif"],
          "source_storyline":d["source_storyline"],
          "scene_brief":d["scene_brief"],
          "witty_key_detail":d["witty_key_detail"],
          "wordplay_device":d["wordplay_device"],
          "unlock_toast":d["unlock_toast_proposal"],
          "source_canonical_title":s["stable_name"],
          "input_lock":"LOCKED_FROM_AUTHORITY",
          "base_art_policy":"NO_CHARACTER_OR_CREW_IN_BASE",
          "character_overlay_policy":"OPTIONAL_SEPARATE_APPROVED_OVERLAY_ONLY",
          "shared_ui_policy":"RIM_STAR_TIER_LOCK_SHADOW_TYPOGRAPHY_SEPARATE",
          "alpha_policy":"CIRCULAR_ART_OUTSIDE_TRANSPARENT",
          "layer_policy":["background","interior","composite"],
          "preview_sizes":[64,120,200,320],
          "pre_generation_status":"LOCKED_READY_FOR_CANDIDATE_GENERATION",
          "approval_status":"NOT_APPROVED"
        }
        for k,v in expected.items():
            if x.get(k)!=v or (k in ("display_item","core_detail","source_motif") and not x.get(k)):
                errors.append("LOCK_DRIFT_"+bid+"_"+k.upper())
        # Copy authority must also agree; this catches a direction file silently drifting from recovered copy.
        if c.get("display_title_proposal")!=d.get("display_title_proposal") or c.get("flavor_text_proposal")!=d.get("core_detail_proposal"):
            errors.append("COPY_DIRECTION_DRIFT_"+bid)
        if x.get("base_art_policy")!="NO_CHARACTER_OR_CREW_IN_BASE":
            errors.append("CHARACTER_BAKED_POLICY_"+bid)
    if admission.get("deployment")!="HOLD": errors.append("ADMISSION_DEPLOYMENT_NOT_HOLD")
    if queue.get("netlify")!="HOLD": errors.append("QUEUE_NETLIFY_NOT_HOLD")
    if queue.get("final_approved_count",0)!=0 and admission.get("status")=="HOLD_NO_ART_ADMITTED":
        errors.append("FALSE_PROGRESS_WITH_NO_ADMITTED_ART")
    return sorted(set(errors))

if __name__=="__main__":
    problems=verify()
    if problems:
        raise SystemExit("BADGE PRODUCTION PIPELINE BLOCKED: "+", ".join(problems))
    print("BADGE PRODUCTION PIPELINE PASS: correction inputs are locked; character/base/shared UI separation enforced; Netlify HOLD. This is not visual approval.")
