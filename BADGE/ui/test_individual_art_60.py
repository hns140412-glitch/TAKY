#!/usr/bin/env python3
"""Fail-closed structural audit of independent 60 badge illustration candidates.
This does NOT establish pixel matching, editorial acceptance, Crew approval or runtime activation.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "BADGE" / "ui"
manifest = json.loads((UI / "badge-individual-art-60-candidates.json").read_text(encoding="utf-8"))
source = json.loads((ROOT / "BADGE" / "badge-60-story-20-history-working.json").read_text(encoding="utf-8"))
copy = json.loads((ROOT / "BADGE" / "badge-wow-inspired-copyworking.json").read_text(encoding="utf-8"))
registry = json.loads((ROOT / "BADGE" / "badge-visual-registry-working.json").read_text(encoding="utf-8"))
assert len(source["presets"]) == len(copy["preset_copy"]) == len(registry["items"]) == len(manifest["items"]) == 60
assert Counter(x["moment_rank"] for x in source["presets"]) == Counter(
    {"POCKET": 20, "FIELD": 20, "EXPEDITION": 14, "SECRET": 6}
)
assert manifest["status"] == "INDEPENDENT_ART_CANDIDATES_NO_AUTO_BINDING"
seen = {"background": set(), "interior": set()}
for i, (src, cp, candidate, reg) in enumerate(zip(
    source["presets"], copy["preset_copy"], manifest["items"], registry["items"]
), 1):
    code = f"{i:03d}"
    assert src["slot"] == i
    assert candidate["id"] == cp["source_draft_id"] == src["source_draft_id"] == reg["draft_id"]
    assert candidate["visual_id"] == src["visual_id"] == reg["visual_id"]
    assert candidate["canonical_title"] == src["stable_name"] == reg["name"]
    assert candidate["copy_proposal"] == cp["display_title_proposal"]
    assert candidate["source_motif"] == src["motif"]
    assert candidate["source_storyline"] == src["storyline"]
    assert candidate["approved"] is False and candidate["runtime_bound"] is False and candidate["active"] is False
    assert reg["active"] is False and reg["asset_state"] == "UNBOUND"
    assert reg["approval_status"] == "NOT_APPROVED" and reg["renderer_binding"] is False
    assert reg["asset_path"] is None
    assert candidate["crew"] is None
    for layer in ("background", "interior"):
        expected = f"./assets/individual/{code}/{layer}.svg"
        assert candidate["base_layers"][layer] == expected
        path = UI / expected[2:]
        raw = path.read_bytes()
        assert len(raw) > 800, (code, layer, "placeholder-sized asset")
        sha = hashlib.sha256(raw).hexdigest()
        assert sha not in seen[layer], (code, layer, "duplicate artwork")
        seen[layer].add(sha)
        node = ET.fromstring(raw)
        assert node.tag == "{http://www.w3.org/2000/svg}svg"
        assert node.attrib["viewBox"] == "0 0 512 512"
        assert node.attrib["width"] == node.attrib["height"] == "512"
        ids = [e.attrib["id"] for e in node.iter() if "id" in e.attrib]
        assert ("background" if layer == "background" else "interior") in ids
        assert "foreground" in ids if layer == "interior" else "foreground" not in ids
        for e in node.iter():
            tag = e.tag.split("}")[-1].lower()
            assert tag not in {"text", "image", "script", "foreignobject", "a"}, (code, layer, tag)
        low = raw.decode("utf-8").lower()
        assert "badge-star" not in low and "badge-rim" not in low
        assert "guide" not in low and "http://" not in low.replace('http://www.w3.org/2000/svg', '')
assert len(seen["background"]) == len(seen["interior"]) == 60
assert len(list((UI / "assets" / "individual").glob("*/*.svg"))) == 120
print("BADGE INDIVIDUAL ART STRUCTURAL QA: PASS")
print("60 source-preserved badges / 60 unique backgrounds / 60 unique interior SVG layers / 120 files")
print("No copied sheet, baked rim/stars/text, unauthorized Crew, registry binding, award or activation.")
print("Visual comparison against six approved screens remains a separate OPEN check.")
