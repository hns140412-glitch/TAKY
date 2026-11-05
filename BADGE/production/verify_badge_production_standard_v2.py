#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def load(rel,root=ROOT):
    return json.loads((Path(root)/rel).read_text(encoding="utf-8"))

def classify(current_ids, correction_ids, baseline_ids):
    correction=set(correction_ids)
    baseline=set(baseline_ids)
    return {
      bid: ("REWORK_REQUIRED" if bid in correction else "KEEP_CANDIDATE" if bid in baseline else "NEW_UNREVIEWED")
      for bid in current_ids
    }

def verify(root=ROOT, standard=None):
    root=Path(root)
    s=standard if standard is not None else load("BADGE/production/badge-production-standard-v2.json",root)
    source=load("BADGE/badge-60-story-20-history-working.json",root)
    direction=load("BADGE/assets/individual-art-direction-60.json",root)
    copydoc=load("BADGE/badge-wow-inspired-copyworking.json",root)
    queue=load("BADGE/assets/visual-rework-queue-working.json",root)
    errors=[]
    if s.get("schema")!="TAKY_BADGE_PRODUCTION_STANDARD_V2": errors.append("STANDARD_SCHEMA")
    src=[x.get("source_draft_id") for x in source.get("presets",[])]
    art=[x.get("badge_id") for x in direction.get("items",[])]
    cpy=[x.get("source_draft_id") for x in copydoc.get("preset_copy",[])]
    if len(src)!=len(set(src)) or len(art)!=len(set(art)) or len(cpy)!=len(set(cpy)):
        errors.append("DUPLICATE_BADGE_ID")
    if set(src)!=set(art) or set(src)!=set(cpy):
        errors.append("SOURCE_DIRECTION_COPY_UNIVERSE_MISMATCH")
    corrections=queue.get("correction_ids",[])
    if not set(corrections).issubset(set(src)): errors.append("REWORK_ID_OUTSIDE_BADGE_UNIVERSE")
    baseline=s.get("current_baseline",{})
    if baseline.get("badge_count")!=len(src): errors.append("BASELINE_BADGE_COUNT_DRIFT")
    if baseline.get("rework_required")!=len(corrections): errors.append("BASELINE_REWORK_COUNT_DRIFT")
    if baseline.get("keep_candidate")!=len(src)-len(corrections): errors.append("BASELINE_KEEP_COUNT_DRIFT")
    classes=classify(src,corrections,src)
    if sum(v=="REWORK_REQUIRED" for v in classes.values())!=31: errors.append("CURRENT_REWORK_31_REQUIRED")
    if sum(v=="KEEP_CANDIDATE" for v in classes.values())!=29: errors.append("CURRENT_KEEP_29_REQUIRED")
    ext=s.get("extensibility",{})
    if ext.get("badge_count_hardcoded_in_pipeline") is not False or ext.get("new_badge_must_not_inherit_keep_status") is not True:
        errors.append("EXTENSIBILITY_RULE_DRIFT")
    artc=s.get("art_contract",{})
    if artc.get("required_depth_layers")!=["base","bg","subject","fx"]:
        errors.append("DEPTH_LAYER_CONTRACT_DRIFT")
    required_delivery={"manifest.json","base.png","bg.png","subject.png","fx.png","composite.png",
                       "preview-64.png","preview-120.png","preview-200.png","preview-320.png",
                       "depth-profile.json","review.json"}
    if set(artc.get("required_delivery",[]))!=required_delivery:
        errors.append("DELIVERY_CONTRACT_DRIFT")
    if not s.get("extensibility",{}).get("reviewed_baseline"):
        errors.append("REVIEWED_BASELINE_REQUIRED")
    depth=s.get("depth_detail_only",{})
    if depth.get("enabled_surface")!="BADGE_DETAIL_VIEW_ONLY":
        errors.append("DEPTH_SCOPE_DRIFT")
    required_static={"BADGE_ATLAS","BADGE_LIST","READY_WEEK","READY_DAY","CALENDAR","HISTORY_LIST","UNLOCK_SUMMARY"}
    if not required_static.issubset(set(depth.get("static_surfaces",[]))):
        errors.append("STATIC_SURFACE_COVERAGE_DRIFT")
    states=s.get("ownership_visual_states",{})
    if states.get("UNAPPROVED_ART",{}).get("render") is not False:
        errors.append("UNAPPROVED_ART_RENDER_FORBIDDEN")
    if states.get("UNEARNED",{}).get("star_count")!=0 or states.get("UNEARNED",{}).get("detail_depth") is not False:
        errors.append("UNEARNED_VISUAL_RULE_DRIFT")
    if states.get("FIRST_AWARD",{}).get("star_count")!=1 or states.get("FIRST_AWARD",{}).get("detail_depth") is not True:
        errors.append("FIRST_AWARD_ONE_STAR_RULE_DRIFT")
    if states.get("REAWARD",{}).get("star_increment")!=1 or states.get("REAWARD",{}).get("telemetry_cannot_increment") is not True:
        errors.append("REAWARD_RULE_DRIFT")
    release=s.get("release_gates",{})
    if release.get("main_merge")!="HOLD" or release.get("netlify")!="HOLD":
        errors.append("RELEASE_HOLD_DRIFT")
    return sorted(set(errors))

if __name__=="__main__":
    problems=verify()
    if problems:
        raise SystemExit("BADGE PRODUCTION STANDARD V2 BLOCKED: "+", ".join(problems))
    print("BADGE PRODUCTION STANDARD V2 PASS: 60 baseline classified 29 KEEP / 31 REWORK; future complete IDs default NEW_UNREVIEWED; detail-only depth and UNEARNED/FIRST_AWARD rules locked.")
