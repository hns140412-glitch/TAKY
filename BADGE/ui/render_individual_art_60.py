#!/usr/bin/env python3
"""Raster integration QA for sixty *separate* independent illustration candidates.
Renders backgrounds+interiors into one PNG per badge. Never paints shared rim/stars/tier/lock,
never infers awards, never mutates the asset approval registry. No contact sheet.
"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path

import cairosvg
from PIL import Image, ImageStat

UI = Path(__file__).resolve().parent
MANIFEST = json.loads((UI / "badge-individual-art-60-candidates.json").read_text(encoding="utf-8"))
OUT = UI / "rendered-individual-candidates"
OUT.mkdir(parents=True, exist_ok=True)
seen = set()
for n, item in enumerate(MANIFEST["items"], 1):
    code = f"{n:03d}"
    layers = []
    for name in ("background", "interior"):
        ref = item["base_layers"][name]
        path = UI / ref.removeprefix("./")
        raster = cairosvg.svg2png(url=str(path), output_width=1024, output_height=1024)
        im = Image.open(io.BytesIO(raster)).convert("RGBA")
        assert im.size == (1024, 1024), (code, name)
        layers.append(im)
    bg, front = layers
    main = front.crop((140, 170, 840, 850)).getchannel("A")
    main_alpha = ImageStat.Stat(main).mean[0]
    assert main_alpha > 8, (code, "interior invisible in focal area", main_alpha)
    composite = Image.alpha_composite(bg, front)
    assert composite.getchannel("A").getextrema() == (255, 255), (code, "background should be opaque")
    png = OUT / f"{code}.png"
    composite.save(png, optimize=True)
    digest = hashlib.sha256(png.read_bytes()).hexdigest()
    assert digest not in seen, (code, "duplicate composite")
    seen.add(digest)
    for size in (64, 120, 200, 320):
        scaled = composite.resize((size, size), Image.Resampling.LANCZOS).convert("RGB")
        colors = scaled.getcolors(maxcolors=1_000_000)
        assert colors and len(colors) > 48, (code, size, "lost detail / flattened image")
print("BADGE ART RASTER QA: PASS — 60 distinct 1024x1024 per-badge PNG composites")
print("All 60 rasterized successfully; 64/120/200/320 size checks passed.")
print("No contact sheet; no shared rim/star/lock/effect or Crew injected; no runtime activation.")
print("Original six-screen pixel/style comparison remains OPEN and is not certified by this script.")
