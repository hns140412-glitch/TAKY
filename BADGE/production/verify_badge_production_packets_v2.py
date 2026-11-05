#!/usr/bin/env python3
import json
from pathlib import Path
from build_badge_production_packets_v2 import ROOT,build,slot_for_badge_id,classify
PACKETS="BADGE/production/badge-production-packets-v2.json"
REQUIRED_FILES=("manifest.json","base.png","bg.png","subject.png","fx.png","composite.png","preview-64.png","preview-120.png","preview-200.png","preview-320.png","depth-profile.json","review.json")
def verify(root=ROOT,document=None):
    root=Path(root);errors=[];expected=build(root)
    doc=document if document is not None else json.loads((root/PACKETS).read_text(encoding="utf-8"))
    standard=json.loads((root/"BADGE/production/badge-production-standard-v2.json").read_text(encoding="utf-8"))
    if doc.get("schema")!="TAKY_BADGE_PRODUCTION_PACKETS_V2":errors.append("PACKET_SCHEMA")
    if doc!=expected:errors.append("PACKET_BUILD_DRIFT")
    items=doc.get("items")
    if not isinstance(items,list):return ["PACKET_ITEMS_REQUIRED"]
    if doc.get("item_count")!=len(items):errors.append("PACKET_COUNT_DRIFT")
    ids=[x.get("badge_id") for x in items];dirs=[x.get("asset_dir") for x in items]
    if len(ids)!=len(set(ids)):errors.append("PACKET_DUPLICATE_ID")
    if len(dirs)!=len(set(dirs)):errors.append("PACKET_ASSET_DIR_COLLISION")
    required=set(standard.get("production_packet_required_fields",[]))
    for x in items:
        bid=x.get("badge_id","")
        if any(k not in x or x.get(k) in ("",None) for k in required):errors.append("PACKET_REQUIRED_FIELD_MISSING_"+bid)
        rootpath="BADGE/assets/individual/"+slot_for_badge_id(bid)
        if x.get("asset_dir")!=rootpath:errors.append("PACKET_ASSET_DIR_"+bid)
        c=x.get("asset_contract",{})
        delivered=set(Path(v).name for v in c.values() if isinstance(v,str))
        delivered.update(Path(v).name for v in c.get("previews",[]) if isinstance(v,str))
        if delivered!=set(REQUIRED_FILES):errors.append("PACKET_DELIVERY_SET_"+bid)
        if x.get("detail_effect_scope")!="BADGE_DETAIL_VIEW_ONLY":errors.append("PACKET_DEPTH_SCOPE_"+bid)
        if x.get("approval_status")!="NOT_APPROVED" or x.get("runtime_binding") is not False:errors.append("PACKET_FALSE_APPROVAL_"+bid)
        if x.get("production_classification")=="NEW_UNREVIEWED" and x.get("generation_action")!="VISUAL_REVIEW_REQUIRED":errors.append("NEW_BADGE_AUTO_KEEP_FORBIDDEN_"+bid)
    counts=doc.get("classification_counts",{})
    if sum(counts.values())!=len(items):errors.append("PACKET_CLASSIFICATION_COUNT")
    if slot_for_badge_id("BDG-DRAFT-1000")!="1000":errors.append("ASSET_SLOT_TRUNCATION_REGRESSION")
    if classify("BDG-DRAFT-9999",set(),set())!="NEW_UNREVIEWED":errors.append("FUTURE_BADGE_CLASSIFICATION")
    return sorted(set(errors))
if __name__=="__main__":
    p=verify()
    if p:raise SystemExit("BADGE PRODUCTION PACKETS V2 BLOCKED: "+", ".join(p))
    print("BADGE PRODUCTION PACKETS V2 PASS: current 60 deterministic packets; future IDs NEW_UNREVIEWED; detail-only depth delivery locked.")
