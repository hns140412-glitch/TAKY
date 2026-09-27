#!/usr/bin/env python3
"""Candidate-only asset management and overlay-slot registry audit (no approval authority)."""
import json
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
assets=ROOT/"BADGE"/"assets"
catalog=json.loads((assets/"asset-registry-working.json").read_text(encoding="utf-8"))
slots=json.loads((assets/"overlays"/"slots-working.json").read_text(encoding="utf-8"))
source=json.loads((ROOT/"BADGE"/"badge-60-story-20-history-working.json").read_text(encoding="utf-8"))
visual=json.loads((ROOT/"BADGE"/"badge-visual-registry-working.json").read_text(encoding="utf-8"))
assert len(source["presets"])==len(visual["items"])==len(catalog["items"])==len(slots["items"])==60
assert catalog["live_binding"] is False and catalog["automatic_approval"] is False
assert catalog["type"]=="CANDIDATE_ASSET_INDEX_NOT_ACTIVE_CATALOG"
assert slots["status"]=="PROVISIONAL_GEOMETRY_NOT_RUNTIME_APPROVAL"
for shared in ("rim.svg","shadow.svg","star-mask.svg","lock.svg"):
    path=assets/"shared"/shared
    assert path.is_file(), shared
    svg=ET.fromstring(path.read_text(encoding="utf-8"))
    assert svg.tag=="{http://www.w3.org/2000/svg}svg"
    assert "0 0 512 512"==svg.attrib["viewBox"]
for i,(entry,source_entry,slot,reg) in enumerate(zip(catalog["items"],source["presets"],slots["items"],visual["items"]),1):
    code=f"{i:03d}"
    assert entry["badge_id"]==source_entry["source_draft_id"]==slot["badge_id"]==reg["draft_id"]
    assert entry["visual_id"]==source_entry["visual_id"]==slot["visual_id"]==reg["visual_id"]
    assert entry["source_title"]==source_entry["stable_name"]==reg["name"]
    assert entry["storyline"]==source_entry["storyline"] and entry["scene_motif"]==source_entry["motif"]
    assert entry["runtime_approved"] is False and entry["runtime_bound"] is False and entry["active"] is False
    assert entry["character_asset_ref"] is None and entry["crew_asset_ref"] is None
    assert reg["active"] is False and reg["renderer_binding"] is False and reg["asset_path"] is None
    assert reg["approval_evidence_refs"]==[] and reg["approval_status"]=="NOT_APPROVED"
    assert entry["layers"]["foreground"] is None
    for name in ("background","interior"):
        path=ROOT/entry["layers"][name]
        assert path.is_file(), (code,name)
        assert path.resolve().is_relative_to(ROOT.resolve()), (code,name)
        assert path.name==name+".svg" and path.parent.name==code
    assert entry["overlay_slot_id"]==entry["visual_id"]
    assert slot["approved_character_id"] is None and slot["approved_crew_id"] is None
    assert slot["review_status"]=="PROVISIONAL_UNTIL_FINAL_INDIVIDUAL_ART"
    for kind in ("profile","crew"):
        layout=slot[kind]
        lower,upper=(15,40) if kind=="profile" else (60,85)
        assert lower<=layout["x"]<=upper and 55<=layout["y"]<=83
        assert 15<=layout["scale"]<=42
        assert layout["depth"] in ("BEHIND_FOREGROUND","ABOVE_FOREGROUND")
print("BADGE ASSET REGISTRY PASS: 60 source-preserved scene pointers, 120 distinct individual layer paths, four shared SVG assets, 60 optional unbound profile/Crew slots.")
print("Zero fake identities, zero auto-approvals, zero active visual bindings and zero award issuance.")
