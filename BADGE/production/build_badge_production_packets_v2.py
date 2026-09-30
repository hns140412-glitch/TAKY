#!/usr/bin/env python3
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load(rel,root=ROOT): return json.loads((Path(root)/rel).read_text(encoding="utf-8"))
def slot_for_badge_id(badge_id):
    m=re.search(r"(\d+)$",str(badge_id))
    if not m: raise ValueError("BADGE_ID_NUMERIC_SUFFIX_REQUIRED")
    return str(int(m.group(1))).zfill(3)
FORBIDDEN=[
 "invented character or crew identity in base art",
 "text or display copy baked into artwork",
 "shared rim baked into individual art",
 "star count or tier ornament baked into individual art",
 "lock state baked into individual art",
 "contact-sheet crop reused as an individual badge",
 "semantic replacement of the source motif",
 "automatic runtime activation or automatic award"
]
def classify(badge_id,baseline_ids,rework_ids):
    if badge_id in rework_ids:return "REWORK_REQUIRED"
    if badge_id in baseline_ids:return "KEEP_CANDIDATE"
    return "NEW_UNREVIEWED"
def action_for(kind):
    return {"REWORK_REQUIRED":"GENERATE_NEW_CANDIDATE","KEEP_CANDIDATE":"REVIEW_EXISTING_CANDIDATE_THEN_RETAIN_OR_REWORK","NEW_UNREVIEWED":"VISUAL_REVIEW_REQUIRED"}[kind]
def build(root=ROOT):
    source=load("BADGE/badge-60-story-20-history-working.json",root)
    direction=load("BADGE/assets/individual-art-direction-60.json",root)
    copydoc=load("BADGE/badge-wow-inspired-copyworking.json",root)
    baseline=load("BADGE/production/badge-production-baseline-v2.json",root)
    queue=load("BADGE/assets/visual-rework-queue-working.json",root)
    S={x["source_draft_id"]:x for x in source["presets"]}
    D={x["badge_id"]:x for x in direction["items"]}
    C={x["source_draft_id"]:x for x in copydoc["preset_copy"]}
    if set(S)!=set(D) or set(S)!=set(C): raise ValueError("SOURCE_DIRECTION_COPY_UNIVERSE_MISMATCH")
    base=set(baseline["reviewed_ids"]);rework=set(queue["correction_ids"])
    if not base.issubset(S) or not rework.issubset(base): raise ValueError("BASELINE_OR_REWORK_SCOPE_INVALID")
    items=[]
    for bid in S:
        s,d,c=S[bid],D[bid],C[bid];slot=slot_for_badge_id(bid);kind=classify(bid,base,rework);asset="BADGE/assets/individual/"+slot
        items.append({
          "badge_id":bid,"visual_id":d["visual_id"],"production_classification":kind,"generation_action":action_for(kind),
          "source_canonical_title":s["stable_name"],"display_item":c["display_title_proposal"],"core_detail":c["flavor_text_proposal"],
          "source_storyline":s["storyline"],"source_motif":s["motif"],"scene_brief":d["scene_brief"],
          "witty_key_detail":d["witty_key_detail"],"small_icon_read":d["small_icon_read"],"wordplay_device":c["wordplay_device"],
          "unlock_toast":c["unlock_toast_proposal"],"input_lock":"LOCKED_FROM_AUTHORITY",
          "allowed_delta":"STYLE_DEPTH_COMPOSITION_CORRECTION_ONLY_SOURCE_MEANING_LOCKED","forbidden_elements":FORBIDDEN,
          "layer_roles":{
            "base":"Per-badge recessed depth foundation only; no shared rim/star/tier/lock/text.",
            "bg":"Internal environmental/background motif; subordinate to the source motif.",
            "subject":"Primary readable motif: "+s["motif"],
            "fx":"Badge-local foreground light/particles/highlight only when semantically useful."
          },
          "asset_dir":asset,
          "asset_contract":{
            "individual_manifest":asset+"/manifest.json","base":asset+"/base.png","bg":asset+"/bg.png","subject":asset+"/subject.png","fx":asset+"/fx.png",
            "composite":asset+"/composite.png","previews":[asset+"/preview-"+str(n)+".png" for n in (64,120,200,320)],
            "depth_profile":asset+"/depth-profile.json","review":asset+"/review.json"
          },
          "depth_profile_template":"BADGE/production/badge-depth-profile-default-v1.json","detail_effect_scope":"BADGE_DETAIL_VIEW_ONLY",
          "unearned_policy":"APPROVED_ART_ONLY_STATIC_LOCKED_NO_DEPTH_NO_CHARACTER_NO_TIER_STAR_0",
          "first_award_policy":"SIGNED_AWARD_LEDGER_STAR_1_DETAIL_DEPTH_ALLOWED","approval_status":"NOT_APPROVED","runtime_binding":False
        })
    counts={k:sum(x["production_classification"]==k for x in items) for k in ("KEEP_CANDIDATE","REWORK_REQUIRED","NEW_UNREVIEWED")}
    return {"schema":"TAKY_BADGE_PRODUCTION_PACKETS_V2","status":"60_CURRENT_PACKETS_READY_FOR_CONTROLLED_PRODUCTION_NOT_ART_APPROVAL","owner":"TAKY/BADGE",
      "generated_from":{"source":"BADGE/badge-60-story-20-history-working.json","art_direction":"BADGE/assets/individual-art-direction-60.json",
      "copy":"BADGE/badge-wow-inspired-copyworking.json","reviewed_baseline":"BADGE/production/badge-production-baseline-v2.json",
      "rework_queue":"BADGE/assets/visual-rework-queue-working.json","standard":"BADGE/production/badge-production-standard-v2.json"},
      "item_count":len(items),"classification_counts":counts,"depth_profile_template":"BADGE/production/badge-depth-profile-default-v1.json","items":items}
def main():
    p=argparse.ArgumentParser();p.add_argument("--check",action="store_true");a=p.parse_args()
    built=build();path=ROOT/"BADGE/production/badge-production-packets-v2.json"
    if a.check:
        if json.loads(path.read_text(encoding="utf-8"))!=built: raise SystemExit("BADGE PRODUCTION PACKETS V2 DRIFT")
        print("BADGE PRODUCTION PACKETS V2 deterministic build: PASS")
    else:
        path.write_text(json.dumps(built,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");print("wrote",path)
if __name__=="__main__":main()
