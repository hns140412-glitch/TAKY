#!/usr/bin/env python3
"""Audit only the 60 isolated development-preview bindings. Never grant art approval."""
import json,re
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[2]
ui=ROOT/"BADGE"/"ui"
source=json.loads((ROOT/"BADGE"/"badge-60-story-20-history-working.json").read_text(encoding="utf-8"))["presets"]
brief=json.loads((ROOT/"BADGE"/"assets"/"individual-art-direction-60.json").read_text(encoding="utf-8"))["items"]
catalog=json.loads((ROOT/"BADGE"/"assets"/"asset-registry-working.json").read_text(encoding="utf-8"))["items"]
slots=json.loads((ROOT/"BADGE"/"assets"/"overlays"/"slots-working.json").read_text(encoding="utf-8"))["items"]
manifest=json.loads((ui/"badge-dev-preview-bindings-60.json").read_text(encoding="utf-8"))
assert manifest["contract"]=="VISUAL_DRAFT_BINDING_NOT_PRODUCTION_RUNTIME"
assert manifest["preview_only"] is True and manifest["may_promote_to_runtime"] is False
assert len(manifest["items"])==len(source)==len(brief)==len(catalog)==len(slots)==60
for n,(m,s,d,c,o) in enumerate(zip(manifest["items"],source,brief,catalog,slots),1):
    code=f"{n:03d}"
    assert m["slot"]==n
    assert m["badge_id"]==s["source_draft_id"]==d["badge_id"]==c["badge_id"]==o["badge_id"]
    assert m["visual_id"]==s["visual_id"]==d["visual_id"]==c["visual_id"]==o["visual_id"]
    assert m["source_title"]==s["stable_name"]==c["source_title"]
    assert m["scene_brief"]==d["scene_brief"]
    assert m["small_icon_read"]==d["small_icon_read"]
    assert m["witty_key_detail"]==d["witty_key_detail"]
    assert m["qa_state"] in ("VISUAL_STYLE_FAIL","STYLE_NOT_YET_CERTIFIED")
    assert m["preview_bound"] is True and m["production_bound"] is False
    assert m["production_approved"] is False and m["active"] is False
    assert m["optional_character_overlay"] is None and m["optional_crew_overlay"] is None
    assert m["overlay_placement_status"]=="PROVISIONAL_UNTIL_FINAL_INDIVIDUAL_ART"
    assert m["layers"]["foreground"] is None
    for key in ("background","interior"):
        relative=f"./assets/individual/{code}/{key}.svg"
        assert m["layers"][key]==relative
        assert (ui/relative).is_file()
class Extract(HTMLParser):
    def __init__(self):
        super().__init__();self.on=False;self.value=""
    def handle_starttag(self,tag,attrs):
        if tag=="script" and ("id","source") in attrs:self.on=True
    def handle_endtag(self,tag):
        if tag=="script" and self.on:self.on=False
    def handle_data(self,text):
        if self.on:self.value+=text
page=(ui/"badge-dev-binding-inspector.html").read_text(encoding="utf-8")
e=Extract();e.feed(page)
assert e.value,"offline inspector must embed actual manifest"
embedded=json.loads(e.value)
assert len(embedded["items"])==60
for m,entry in zip(manifest["items"],embedded["items"]):
    assert m["badge_id"]==entry["id"]
    assert m["layers"]["background"]==entry["background"]
    assert m["layers"]["interior"]==entry["interior"]
    assert m["scene_brief"]==entry["scene"]
    assert m["small_icon_read"]==entry["small"]
assert page.count("id=\"stars\"")==1
assert all(label in page for label in ("320","200","120","64"))
assert all(t in page for t in ("green","blue","red","gold","platinum"))
assert "PRODUCTION APPROVAL: NO" in page and "RUNTIME BIND: NO" in page
assert "assets/shared/rim.svg" in (ui/"badge-atlas.css").read_text(encoding="utf-8")
assert "data-stars" in page
print("BADGE 60 DEVELOPMENT BINDINGS: PASS — each unique source ID points to 2 real independent files and single-scene offline inspector")
print("60 candidate preview bindings; 0 formal production bindings, 0 art approvals, no invented character overlay or fake ledger.")
