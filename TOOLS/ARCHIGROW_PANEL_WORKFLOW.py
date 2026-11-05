#!/usr/bin/env python3
"""ARCHIGROW panel workflow adapter (thin integration over the ARCHIGROW_COMPETITION_* tools).

Workflow A  design assets -> source-bound A1 board in two style treatments (HTML + PDF via existing renderer).
Workflow B  existing board -> semantic block manifest -> audience/time specific decks (editable PPTX)
            -> browser viewer that links every slide back to its source block on the board.

Honesty contract: segmentation and recomposition are deterministic, rule-based and evidence-bound.
No live LLM, no paid API, no network. Sample sources are synthetic DEMO assets, not project facts.
Nothing here is promoted to CURRENT; runtime results stay UNVERIFIED until executed and inspected.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "TOOLS"
FIXTURE_ROOT = ROOT / "REFERENCE" / "ARCHCOMP_OUTPUT_BUILD_TEST"
DEFAULT_OUT = FIXTURE_ROOT / "PANEL_REPLICA_20261019"

BLOCKS_VERSION = "ARCHIGROW_PANEL_BLOCKS_V1"
DECK_VERSION = "ARCHIGROW_PANEL_DECK_V1"

AI_DISCLOSURE = (
    "RULE_BASED_DETERMINISTIC: block segmentation, audience selection and Korean editorial text come from "
    "registry roles and explicit user-supplied facts. This is NOT a live LLM and NOT vision-based discovery "
    "of blocks in an arbitrary image. Role-template text is not a project fact."
)

BOARD_W_MM = 594.0
BOARD_H_MM = 841.0
SHEET_H_MM = 840.0  # one mm slack so Chrome never spills a blank second page
MARGIN_MM = 16.0
HEADER_H_MM = 40.0
FOOTER_H_MM = 12.0
GAP_MM = 6.0
CAPTION_H_MM = 16.0
STAGE_LABEL_W_MM = 26.0


def _load_tool(alias, filename):
    spec = importlib.util.spec_from_file_location(alias, TOOLS / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BUILD = _load_tool("archigrow_comp_build_for_panel", "ARCHIGROW_COMPETITION_BUILD.py")
BIND = _load_tool("archigrow_comp_bind_for_panel", "ARCHIGROW_COMPETITION_BIND.py")
RENDER = _load_tool("archigrow_comp_render_for_panel", "ARCHIGROW_COMPETITION_RENDER.py")

# ---------------------------------------------------------------- semantics

STAGE_OF = {
    "CONTEXT": "SITE", "CIRCULATION": "SITE",
    "CONCEPT": "IDEA", "PROGRAM": "IDEA", "PERFORMANCE": "IDEA",
    "PLAN": "PROOF", "SECTION": "PROOF", "ELEVATION": "PROOF", "AXONOMETRIC": "PROOF", "TECHNICAL": "PROOF",
    "EXPERIENCE": "EXPERIENCE",
}
STAGE_ORDER = ["SITE", "IDEA", "PROOF", "EXPERIENCE"]
STAGE_KO = {"SITE": "대지·접근", "IDEA": "개념·구성", "PROOF": "공간 증명", "EXPERIENCE": "경험"}
NARR_ORDER = ["CONTEXT", "CIRCULATION", "CONCEPT", "PROGRAM", "PERFORMANCE", "PLAN", "SECTION",
              "ELEVATION", "AXONOMETRIC", "TECHNICAL", "EXPERIENCE"]
MODE_WEIGHT = {"PLAN": 3.0, "SECTION": 3.0, "EXPERIENCE": 3.0, "CONTEXT": 2.0, "CONCEPT": 2.0,
               "ELEVATION": 2.0, "AXONOMETRIC": 2.0}
HERO_PREFERENCE = ["EXPERIENCE", "CONCEPT", "CONTEXT"]

# Priority = which blocks survive when time is short (earlier = kept first).
AUDIENCE_PRIORITY = {
    "jury": ["CONCEPT", "CONTEXT", "PLAN", "SECTION", "EXPERIENCE", "PROGRAM", "CIRCULATION",
             "PERFORMANCE", "TECHNICAL", "ELEVATION", "AXONOMETRIC"],
    "citizen": ["CONTEXT", "CIRCULATION", "PROGRAM", "EXPERIENCE", "PERFORMANCE", "CONCEPT", "PLAN",
                "SECTION", "ELEVATION", "AXONOMETRIC", "TECHNICAL"],
}
AUDIENCE_LABEL_KO = {"jury": "심사위원", "citizen": "시민 공청회"}
DENSITY_MIN_SEC = {"low": 60, "standard": 45, "high": 30}
DENSITY_BULLETS = {"low": 1, "standard": 2, "high": 3}
DENSITY_FACTS = {"low": 1, "standard": 2, "high": 3}

# Role-template editorial text (NO project facts, NO numerals). jury / citizen register differs.
ROLE_KO = {
    "CONTEXT": {
        "headline": "이 대지에 왜 이 계획인가",
        "jury": ["대지와 도시 맥락이 배치 판단의 출발점입니다", "맥락 읽기와 계획의 대응을 한 장에서 확인합니다"],
        "citizen": ["이 건물이 동네의 어느 자리에 놓이는지 보여 드립니다", "주변 길과 이웃 건물과의 관계를 먼저 살펴봅니다"],
    },
    "CONCEPT": {
        "headline": "핵심 아이디어를 한 장으로",
        "jury": ["설계 개념이 매스와 공간 구성으로 이어지는 과정을 보여 줍니다", "개념은 이후 모든 도면의 판단 기준이 됩니다"],
        "citizen": ["이 건물의 기본 생각을 쉬운 그림으로 설명합니다", "왜 이런 모양이 되었는지 이어서 보여 드립니다"],
    },
    "PROGRAM": {
        "headline": "어떤 공간이 어떻게 놓이는가",
        "jury": ["프로그램의 배치와 공공·사적 위계를 확인합니다", "기능 간 관계가 평면과 단면에 어떻게 반영되는지 봅니다"],
        "citizen": ["어떤 시설이 어디에 들어오는지 한눈에 봅니다", "이웃이 이용할 공간이 어디인지 확인합니다"],
    },
    "CIRCULATION": {
        "headline": "어떻게 들어오고 움직이는가",
        "jury": ["진입 위계와 동선 체계를 주 동선 중심으로 설명합니다", "보행과 서비스 흐름의 분리를 확인합니다"],
        "citizen": ["어느 길로 어떻게 들어오는지 보여 드립니다", "걸어서 이용하는 길이 어떻게 이어지는지 살펴봅니다"],
    },
    "PLAN": {
        "headline": "공간의 조직과 쓰임",
        "jury": ["측정된 도면 기하를 유지한 평면으로 공간 조직을 설명합니다", "실의 구성과 규모는 원본 도면 블록에서 확인합니다"],
        "citizen": ["건물 안이 어떻게 나뉘고 쓰이는지 평면으로 봅니다", "자세한 크기는 원본 도면에서 확인할 수 있습니다"],
    },
    "SECTION": {
        "headline": "수직 관계와 공간 경험",
        "jury": ["단면으로 층간 관계와 빛의 깊이를 설명합니다", "공공성과 인간 척도가 단면에서 드러나는 지점을 봅니다"],
        "citizen": ["건물을 세로로 잘랐을 때의 모습을 보여 드립니다", "높이와 열린 공간이 어떤 느낌인지 살펴봅니다"],
    },
    "ELEVATION": {
        "headline": "외관과 거리의 얼굴",
        "jury": ["입면으로 외피의 구성과 거리 대응을 확인합니다", "재료와 비례는 원본 도면 기준으로 판단합니다"],
        "citizen": ["길에서 보이는 건물의 모습을 보여 드립니다", "이웃 건물과 어울리는 방식을 살펴봅니다"],
    },
    "AXONOMETRIC": {
        "headline": "공간 구성과 층의 겹침",
        "jury": ["레이어를 분리해 공간 구성의 논리를 보여 줍니다", "구조와 기능의 중첩 관계를 읽어 냅니다"],
        "citizen": ["건물이 어떻게 층층이 쌓이는지 입체로 보여 드립니다", "각 층의 역할을 쉽게 구분해 봅니다"],
    },
    "PERFORMANCE": {
        "headline": "빛과 바람을 읽는 계획",
        "jury": ["환경·성능 전략을 단면과 다이어그램으로 설명합니다", "수치 주장은 검증된 분석 입력이 있을 때만 사용합니다"],
        "citizen": ["햇빛과 바람이 건물과 주변에 미치는 방식을 보여 드립니다", "쾌적함과 관련된 계획 의도를 설명합니다"],
    },
    "EXPERIENCE": {
        "headline": "이곳에서의 경험",
        "jury": ["핵심 공간의 분위기와 이용 장면을 보여 줍니다", "경험 이미지는 앞선 도면의 기하와 일치합니다"],
        "citizen": ["완성되었을 때 이곳을 걷는 장면을 보여 드립니다", "머물고 모이는 공간의 느낌을 전해 드립니다"],
    },
    "TECHNICAL": {
        "headline": "실현 가능성과 계획 관리",
        "jury": ["구조·주차·피난 등 실현 가능성의 근거를 제시합니다", "면적과 법규 수치는 출처가 있는 항목만 인용합니다"],
        "citizen": ["안전과 주차 같은 생활 문제를 어떻게 다루는지 설명합니다", "세부 수치는 원본 자료에서 확인할 수 있습니다"],
    },
}
WATCH_BULLET = "보드의 해당 블록에서 원본 도면을 확인할 수 있습니다"

STYLES = {
    "MONO_ACCENT_GALLERY": {
        "label": "스타일 A · 모노 액센트 갤러리",
        "intent": "Technical clarity with one semantic accent; one hero drawing leads, supporting drawings follow in an even gallery.",
        "paper": "#f8f7f2", "ink": "#151515", "accent": "#c86435", "muted": "#6b675f", "line": "#b6b1a6",
        "frame": "#ffffff", "dark_header": False,
    },
    "DIAGRAM_SYSTEM_NARRATIVE": {
        "label": "스타일 B · 다이어그램 시스템 내러티브",
        "intent": "Fast narrative read: SITE -> IDEA -> PROOF -> EXPERIENCE stage bands, fixed semantic colour, proof drawings widest.",
        "paper": "#eef2f4", "ink": "#0f2a3a", "accent": "#1f7a8c", "muted": "#4d6573", "line": "#9fb3be",
        "frame": "#ffffff", "dark_header": True,
    },
}
STYLE_ORDER = ["MONO_ACCENT_GALLERY", "DIAGRAM_SYSTEM_NARRATIVE"]

# ---------------------------------------------------------------- helpers


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel_uri(path, base_dir):
    """Relative forward-slash path for portable links; absolute file URI if no relative path exists."""
    try:
        return Path(os.path.relpath(str(path), str(base_dir))).as_posix()
    except ValueError:
        return Path(path).resolve().as_uri()


def narr_key(block):
    mode = block.get("mode")
    return NARR_ORDER.index(mode) if mode in NARR_ORDER else len(NARR_ORDER)


def block_weight(block):
    return MODE_WEIGHT.get(block.get("mode"), 1.5)


def even_chunks(n, per=3):
    if n <= 0:
        return []
    rows = -(-n // per)
    base, extra = divmod(n, rows)
    return [base + (1 if i < extra else 0) for i in range(rows)]


def body_area():
    x = MARGIN_MM
    y = MARGIN_MM + HEADER_H_MM + GAP_MM
    w = BOARD_W_MM - 2 * MARGIN_MM
    h = BOARD_H_MM - MARGIN_MM - FOOTER_H_MM - GAP_MM - y
    return x, y, w, h


def pack_rows(rows, x, y, w, h, gap):
    """rows = [(row_weight, [item_weights])] -> [[(x, y, w, h)]] in mm."""
    out = []
    if not rows:
        return out
    avail_h = h - gap * (len(rows) - 1)
    total_h = sum(r[0] for r in rows)
    cy = y
    for row_weight, widths in rows:
        rh = avail_h * row_weight / total_h
        avail_w = w - gap * (len(widths) - 1)
        total_w = sum(widths)
        cx = x
        rects = []
        for item_weight in widths:
            cw = avail_w * item_weight / total_w
            rects.append((cx, cy, cw, rh))
            cx += cw + gap
        out.append(rects)
        cy += rh + gap
    return out


def pick_hero(blocks):
    for mode in HERO_PREFERENCE:
        for b in blocks:
            if b.get("mode") == mode:
                return b
    return blocks[0]


def layout_gallery(blocks):
    """Style A: hero + heaviest drawing on the first row, remaining blocks in balanced rows of up to three."""
    if not blocks:
        return [], [], []
    x, y, w, h = body_area()
    hero = pick_hero(blocks)
    rest = sorted([b for b in blocks if b is not hero], key=narr_key)
    seq = [hero]
    if rest:
        second = max(rest, key=block_weight)
        rest.remove(second)
        seq.append(second)
    seq.extend(rest)
    rows = [(1.0, [1.0])] if len(seq) == 1 else [(2.2, [2.0, 1.0])]
    for size in even_chunks(len(seq) - 2, 3):
        rows.append((1.0, [1.0] * size))
    packed = pack_rows(rows, x, y, w, h, GAP_MM)
    rects = [r for row in packed for r in row]
    return seq, rects, []


def layout_narrative(blocks):
    """Style B: stage bands SITE/IDEA/PROOF/EXPERIENCE; row item widths follow drawing weight."""
    if not blocks:
        return [], [], []
    x, y, w, h = body_area()
    groups = []
    for stage in STAGE_ORDER:
        members = sorted([b for b in blocks if STAGE_OF.get(b.get("mode"), "PROOF") == stage], key=narr_key)
        if members:
            groups.append((stage, members))
    rows = []
    row_layout = []  # (stage, [blocks in row])
    for stage, members in groups:
        idx = 0
        for size in even_chunks(len(members), 3):
            chunk = members[idx:idx + size]
            idx += size
            rows.append((0.5 + max(block_weight(b) for b in chunk) / 2.0, [block_weight(b) for b in chunk]))
            row_layout.append((stage, chunk))
    cx = x + STAGE_LABEL_W_MM + GAP_MM
    packed = pack_rows(rows, cx, y, w - STAGE_LABEL_W_MM - GAP_MM, h, GAP_MM)
    seq, rects, labels = [], [], []
    for (stage, chunk), row_rects in zip(row_layout, packed):
        seq.extend(chunk)
        rects.extend(row_rects)
        top, bottom = row_rects[0][1], row_rects[0][1] + row_rects[0][3]
        if labels and labels[-1]["stage"] == stage:
            labels[-1]["h"] = bottom - labels[-1]["y"]
        else:
            labels.append({"stage": stage, "ko": STAGE_KO[stage], "x": x, "y": top, "w": STAGE_LABEL_W_MM, "h": bottom - top})
    return seq, rects, labels


LAYOUTS = {"MONO_ACCENT_GALLERY": layout_gallery, "DIAGRAM_SYSTEM_NARRATIVE": layout_narrative}

# ---------------------------------------------------------------- workflow A: assets -> board


def load_package(path):
    package = read_json(path)
    if package.get("delivery") != "A1_BOARD":
        raise SystemExit(f"PACKAGE_DELIVERY_NOT_A1_BOARD:{package.get('delivery')}")
    return package


def auto_bind(package, asset_dir):
    """Reuse BIND heuristics; only unique high-confidence matches bind (never guess)."""
    result = BIND.build(package, asset_dir)
    return result["bindings"], result["suggestions"]


def make_manifest(package, bindings):
    profiles = read_json(BUILD.PROFILES)["profiles"]
    quality_registry = read_json(BUILD.QUALITY)
    quality = {
        "registry_id": quality_registry.get("registry_id"),
        "tokens": quality_registry.get("tokens", {}),
        "delivery": quality_registry.get("A1_BOARD", {}),
        "mode_emphasis": quality_registry.get("mode_emphasis", {}),
    }
    return BUILD.build_manifest(package, profiles["A1_BOARD"], bindings, quality=quality)


def make_blocks(manifest):
    blocks = []
    for it in manifest["items"]:
        exists = bool(it.get("source_exists"))
        path = it.get("source_path")
        blocks.append({
            "block_id": it["id"],
            "order": it.get("order"),
            "mode": it["mode"],
            "stage": STAGE_OF.get(it["mode"], "PROOF"),
            "role": it.get("layout_role"),
            "title_ko": BUILD.short_title(it["mode"], it.get("question")),
            "question": it.get("question"),
            "source_required": it.get("source_required"),
            "source_path": path,
            "source_exists": exists,
            "source_kind": (it.get("source_meta") or {}).get("kind"),
            "source_sha256": sha256_file(path) if exists else None,
            "binding_status": it.get("binding_status"),
            "board_anchor": "blk-" + BUILD.slug(it["id"]),
        })
    return blocks


def _rect_record(rect):
    x, y, w, h = rect
    return {
        "board_rect_mm": {"x": round(x, 3), "y": round(y, 3), "w": round(w, 3), "h": round(h, 3)},
        "board_rect_norm": {"x": round(x / BOARD_W_MM, 5), "y": round(y / BOARD_H_MM, 5),
                            "w": round(w / BOARD_W_MM, 5), "h": round(h / BOARD_H_MM, 5)},
    }


STYLE_CSS = """
@page{size:594mm 841mm;margin:0}
*{box-sizing:border-box}
html,body{margin:0;padding:0;width:594mm;height:840mm;overflow:hidden;font-family:'Noto Sans KR','Malgun Gothic',Arial,sans-serif;font-size:10pt;background:var(--paper);color:var(--ink);-webkit-print-color-adjust:exact;print-color-adjust:exact}
.sheet{position:relative;width:594mm;height:840mm;overflow:hidden;background:var(--paper)}
.hdr{position:absolute;left:16mm;right:16mm;top:16mm;height:40mm;border-top:1.1mm solid var(--ink);border-bottom:.25mm solid var(--line);padding:4mm 0 4mm;display:flex;justify-content:space-between;align-items:flex-end}
.hdr.dark{background:var(--ink);color:#fff;border:0;padding:5mm 7mm}
.hdr-left{max-width:78%}
.kicker{font-size:11pt;font-weight:700;letter-spacing:.16em;color:var(--accent)}
.hdr.dark .kicker{color:#bfe3ea}
.title{font-size:30pt;font-weight:700;letter-spacing:-.03em;line-height:1.15;margin:1.5mm 0 0}
.subtitle{font-size:12pt;color:var(--muted);margin-top:1.5mm}
.hdr.dark .subtitle{color:#d4e2e8}
.meta{font-size:9pt;line-height:1.5;text-align:right;color:var(--muted)}
.hdr.dark .meta{color:#d4e2e8}
.stage{position:absolute;background:var(--accent);color:#fff;padding:3mm 2.5mm;font-size:11pt;font-weight:700;line-height:1.3}
.stage small{display:block;font-size:8pt;font-weight:400;letter-spacing:.08em;margin-top:1mm}
.blk{position:absolute;margin:0;display:block}
.blk .frame{position:absolute;left:0;right:0;top:0;bottom:16mm;background:var(--frame);border:.22mm solid var(--line);overflow:hidden;display:flex;align-items:center;justify-content:center}
.blk .source-img{width:100%;height:100%;object-fit:contain;display:block}
.blk .missing{width:100%;height:100%;background:#f4e8e4;border:.45mm dashed #9b4b42;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3mm;color:#7d4d48;text-align:center;padding:8mm;font-size:10pt}
.blk .bound-file{padding:10mm;text-align:center;font-size:10pt;color:#555}
.cap{position:absolute;left:0;right:0;bottom:0;height:16mm;display:flex;align-items:center;gap:3mm;overflow:hidden;border-top:.35mm solid var(--ink);padding-top:1mm}
.cap .no{font-size:11pt;font-weight:700;color:var(--accent)}
.cap .mode{font-size:8pt;font-weight:700;letter-spacing:.1em;color:var(--muted)}
.cap .claim{font-size:11pt;font-weight:700;line-height:1.25}
.footer{position:absolute;left:16mm;right:16mm;bottom:12mm;height:8mm;border-top:.2mm solid var(--line);padding-top:2mm;font-size:8pt;color:var(--muted);display:flex;justify-content:space-between}
body.style-b .blk .frame{border-left:1.2mm solid var(--accent)}
body.style-b .cap{border-top:.35mm solid var(--accent)}
[contenteditable]:hover{outline:.3mm dashed var(--accent)}
"""


def _board_html(package, blocks_by_id, ordered, rects, labels, style_id, board_title, demo, manifest_status):
    style = STYLES[style_id]
    sheet = []
    for lab in labels:
        sheet.append(
            f'<div class="stage" data-stage="{BUILD.esc(lab["stage"])}" style="left:{lab["x"]:.2f}mm;top:{lab["y"]:.2f}mm;'
            f'width:{lab["w"]:.2f}mm;height:{lab["h"]:.2f}mm">{BUILD.esc(lab["ko"])}<small>{BUILD.esc(lab["stage"])}</small></div>')
    for idx, (b, rect) in enumerate(zip(ordered, rects), 1):
        x, y, w, h = rect
        item = b["_item"]
        sheet.append(
            f'<figure class="blk" id="{BUILD.esc(b["board_anchor"])}" data-block-id="{BUILD.esc(b["block_id"])}" '
            f'data-mode="{BUILD.esc(b["mode"])}" data-source-sha256="{BUILD.esc(b["source_sha256"] or "")}" '
            f'style="left:{x:.2f}mm;top:{y:.2f}mm;width:{w:.2f}mm;height:{h:.2f}mm">'
            f'<div class="frame">{BUILD.source_view(item)}</div>'
            f'<figcaption class="cap"><span class="no">{idx:02d}</span><span class="mode">{BUILD.esc(b["mode"])}</span>'
            f'<b class="claim" contenteditable="true" data-edit-id="cap-{BUILD.esc(b["board_anchor"])}">{BUILD.esc(b["title_ko"])}</b></figcaption>'
            f'</figure>')
    competition = (package.get("brief") or {}).get("competition_name") or "ARCHITECTURE DESIGN BOARD"
    demo_line = "DEMO · 합성 테스트 소스 · 프로젝트 사실 아님" if demo else "SOURCE-BOUND"
    header_cls = "hdr dark" if style["dark_header"] else "hdr"
    body_cls = "style-b" if style["dark_header"] else "style-a"
    theme = (f":root{{--paper:{style['paper']};--ink:{style['ink']};--accent:{style['accent']};--muted:{style['muted']};"
             f"--line:{style['line']};--frame:{style['frame']}}}")
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{BUILD.esc(board_title)} · {BUILD.esc(style_id)}</title>
<style>{theme}{STYLE_CSS}</style></head>
<body class="{body_cls}" data-board-style="{BUILD.esc(style_id)}">
<section class="sheet" data-board-width-mm="594" data-board-height-mm="841">
<header class="{header_cls}">
 <div class="hdr-left">
  <div class="kicker">{BUILD.esc(competition)}</div>
  <div class="title" contenteditable="true" data-edit-id="board-title">{BUILD.esc(board_title)}</div>
  <div class="subtitle" contenteditable="true" data-edit-id="board-subtitle">SITE → IDEA → SPATIAL PROOF → EXPERIENCE</div>
 </div>
 <div class="meta">A1 BOARD · 594×841mm<br>{len(ordered)} BLOCKS<br>{BUILD.esc(demo_line)}</div>
</header>
{''.join(sheet)}
<footer class="footer"><span>ARCHIGROW PANEL WORKFLOW · {BUILD.esc(STYLES[style_id]['label'])} · 소스 SHA 결합</span><span>{BUILD.esc(manifest_status)}</span></footer>
</section></body></html>
"""


def write_board(package, bindings, style_id, out_dir, board_title=None, demo=True, render=False):
    """Build one A1 board treatment. Returns (blocks_doc, render_evidence_or_None)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = make_manifest(package, bindings)
    BUILD.write_common(package, manifest, out_dir)  # build-manifest.json / source-bindings.template.json / validation.json
    blocks = make_blocks(manifest)
    items = {it["id"]: it for it in manifest["items"]}
    for b in blocks:
        b["_item"] = items[b["block_id"]]
    ordered, rects, labels = LAYOUTS[style_id](blocks)
    title = board_title or package.get("focus") or "DESIGN ARGUMENT"
    html_doc = _board_html(package, {b["block_id"]: b for b in blocks}, ordered, rects, labels,
                           style_id, title, demo, manifest["status"])
    html_path = out_dir / "board.html"
    html_path.write_text(html_doc, encoding="utf-8")
    rect_by_id = {b["block_id"]: _rect_record(r) for b, r in zip(ordered, rects)}
    out_blocks = []
    for pos, b in enumerate(ordered, 1):
        rec = {k: v for k, v in b.items() if not k.startswith("_")}
        rec.update(rect_by_id[b["block_id"]])
        rec["board_position"] = pos
        rec["board_link"] = f"board.html#{b['board_anchor']}"
        rec["rect_method"] = "LAYOUT_BY_CONSTRUCTION_EXACT"
        out_blocks.append(rec)
    doc = {
        "version": BLOCKS_VERSION,
        "board": {
            "style_id": style_id, "style_label": STYLES[style_id]["label"], "style_intent": STYLES[style_id]["intent"],
            "title": title, "delivery": "A1_BOARD", "width_mm": BOARD_W_MM, "height_mm": BOARD_H_MM,
            "html": "board.html", "html_sha256": sha256_file(html_path),
            "pdf": None, "pdf_sha256": None,
            "manifest_status": manifest["status"], "demo_sources": bool(demo),
            "stage_labels": [{"stage": lab["stage"], "ko": lab["ko"]} for lab in labels],
        },
        "segmentation": {"method": "BY_CONSTRUCTION", "note": "Blocks are placed by this generator, so rects are exact; no image analysis."},
        "ai_disclosure": AI_DISCLOSURE,
        "source_gaps": [b["block_id"] for b in out_blocks if b["binding_status"] != "BOUND"],
        "blocks": out_blocks,
    }
    evidence = None
    if render:
        evidence = render_board_pdf(out_dir)
        pdf_path = out_dir / "board.pdf"
        if pdf_path.exists():
            doc["board"]["pdf"] = "board.pdf"
            doc["board"]["pdf_sha256"] = sha256_file(pdf_path)
    write_json(out_dir / "panel-blocks.json", doc)
    return doc, evidence


def render_board_pdf(build_dir):
    """Existing renderer + mechanical 594x841mm / single-page check. Errors are reported, never raised."""
    build_dir = Path(build_dir)
    evidence = {"delivery": "A1_BOARD", "outputs": []}
    try:
        pdf = RENDER.render_html(build_dir, "A1_BOARD")
        probe = RENDER.pdf_probe(pdf)
        expected = RENDER.EXPECTED_PT["A1_BOARD"]
        size_ok = RENDER.size_match(probe.get("first_media_box_pt"), expected)
        pages_ok = probe["page_count"] == 1
        evidence["outputs"].append({
            "path": str(pdf), "bytes": pdf.stat().st_size, "sha256": RENDER.sha256(pdf), "kind": "PDF",
            "page_count": probe["page_count"], "expected_page_count": 1, "page_count_match": pages_ok,
            "first_media_box_pt": probe["first_media_box_pt"], "expected_media_box_pt": expected,
            "physical_size_match": size_ok,
        })
        evidence["mechanical_render_pass"] = bool(pdf.stat().st_size > 1000 and size_ok and pages_ok)
    except Exception as exc:  # BLOCKED != FAILED: keep the exact blocker visible
        evidence["mechanical_render_pass"] = False
        evidence["render_error"] = f"{type(exc).__name__}: {str(exc)[-600:]}"
    RENDER.update_validation(build_dir, evidence)
    return evidence


def build_boards(package, bindings, out_dir, styles=None, board_title=None, demo=True, render=False):
    styles = styles or STYLE_ORDER
    results = []
    for style_id in styles:
        d = Path(out_dir) / "boards" / style_id
        doc, evidence = write_board(package, bindings, style_id, d, board_title=board_title, demo=demo, render=render)
        results.append({"dir": d, "doc": doc, "render": evidence})
    return results

# ---------------------------------------------------------------- workflow B: existing board -> blocks

# CSS grid slots of the legacy BUILD A1 board: slot -> (col_start, col_end_exclusive, row)
LEGACY_SLOTS = {1: (1, 9, 0), 2: (9, 13, 0), 3: (1, 5, 1), 4: (5, 9, 1), 5: (9, 13, 1),
                6: (1, 7, 2), 7: (7, 13, 2), 8: (1, 7, 3), 9: (7, 13, 3)}
LEGACY_ROW_H = [176.0, 102.0, 126.0, 126.0]
LEGACY_GRID_TOP_MM = 69.0  # estimate: padding + header + argument line + grid gaps


def legacy_rect(slot):
    start, end, row = LEGACY_SLOTS[slot]
    inner_w = BOARD_W_MM - 2 * MARGIN_MM
    col_w = (inner_w - 11 * GAP_MM) / 12.0
    x = MARGIN_MM + (start - 1) * (col_w + GAP_MM)
    w = (end - start) * col_w + (end - start - 1) * GAP_MM
    y = LEGACY_GRID_TOP_MM + sum(LEGACY_ROW_H[:row]) + GAP_MM * row
    return (x, y, w, LEGACY_ROW_H[row])


def load_board_blocks(board_dir):
    """Return the panel block document for an existing board directory.

    Preferred: panel-blocks.json written by this tool (exact rects).
    Fallback: a legacy ARCHIGROW_COMPETITION_BUILD A1 board -> rule-based block derivation with ESTIMATED rects.
    """
    board_dir = Path(board_dir)
    native = board_dir / "panel-blocks.json"
    if native.exists():
        doc = read_json(native)
        html_path = board_dir / doc["board"]["html"]
        doc["board"]["html_sha256_current"] = sha256_file(html_path) if html_path.exists() else None
        doc["board"]["dir"] = str(board_dir)
        return doc
    manifest_path = board_dir / "build-manifest.json"
    html_path = board_dir / "board.html"
    if not manifest_path.exists() or not html_path.exists():
        raise SystemExit(f"BOARD_NOT_FOUND: need panel-blocks.json or build-manifest.json+board.html in {board_dir}")
    manifest = read_json(manifest_path)
    if manifest.get("delivery") != "A1_BOARD":
        raise SystemExit(f"BOARD_DELIVERY_NOT_A1_BOARD:{manifest.get('delivery')}")
    blocks = []
    for idx, it in enumerate(manifest.get("items", []), 1):
        path = it.get("source_path")
        exists = bool(path) and Path(path).exists()
        hidden = idx not in LEGACY_SLOTS
        rec = {
            "block_id": it["id"], "order": it.get("order"), "mode": it["mode"],
            "stage": STAGE_OF.get(it["mode"], "PROOF"), "role": it.get("layout_role"),
            "title_ko": BUILD.short_title(it["mode"], it.get("question")),
            "question": it.get("question"), "source_required": it.get("source_required"),
            "source_path": path, "source_exists": exists,
            "source_kind": (it.get("source_meta") or {}).get("kind"),
            "source_sha256": sha256_file(path) if exists else None,
            "binding_status": "BOUND" if (exists and not hidden) else ("HIDDEN_BY_BOARD_CSS" if hidden else "MISSING_SOURCE"),
            "board_anchor": f"slot-{idx}", "board_position": idx,
            "board_link": f"board.html (grid slot {idx})",
        }
        if not hidden:
            rec.update(_rect_record(legacy_rect(idx)))
            rec["rect_method"] = "CSS_GRID_ESTIMATE_UNVERIFIED"
        blocks.append(rec)
    doc = {
        "version": BLOCKS_VERSION,
        "board": {
            "style_id": "LEGACY_COMPETITION_BUILD", "style_label": "기존 생성 보드(레거시)", "style_intent": "Pre-existing generated board.",
            "title": "Existing A1 board", "delivery": "A1_BOARD", "width_mm": BOARD_W_MM, "height_mm": BOARD_H_MM,
            "html": "board.html", "html_sha256": sha256_file(html_path),
            "pdf": "board.pdf" if (board_dir / "board.pdf").exists() else None,
            "pdf_sha256": sha256_file(board_dir / "board.pdf") if (board_dir / "board.pdf").exists() else None,
            "manifest_status": manifest.get("status"), "demo_sources": None,
            "stage_labels": [], "html_sha256_current": sha256_file(html_path), "dir": str(board_dir),
        },
        "segmentation": {"method": "RULE_BASED_FROM_BUILD_MANIFEST",
                         "note": "Blocks follow the builder's grid slots; rects are CSS-grid estimates, not measured. Not vision-based."},
        "ai_disclosure": AI_DISCLOSURE,
        "source_gaps": [b["block_id"] for b in blocks if b["binding_status"] != "BOUND"],
        "blocks": blocks,
    }
    return doc

# ---------------------------------------------------------------- facts (anti-hallucination)


NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
TEXT_SOURCE_SUFFIX = {".txt", ".md", ".csv", ".tsv", ".json"}
QUANTITY_KINDS = [("AREA", r"㎡|m²|m2|평"), ("RATIO", r"%|퍼센트|배"), ("COUNT", r"대|세대|호|층|개|명|실"),
                  ("LENGTH", r"mm|cm|km|m(?![a-z²2])")]
FACT_ROLES = {"PROJECT_FACT", "DERIVED", "BOARD_STATED", "INTERPRETATION", "EDITORIAL", "UNKNOWN"}
BOARD_STATED_TAG = " (보드 기재·미검증)"
MUST_OWNERS = {"BRIEF", "OFFICIAL_RULE", "USER"}


def classify_numeric(text):
    """Numeric claim classification: which numbers a statement carries and what kind of quantity they look like."""
    text = str(text or "")
    numbers = [n.replace(",", "") for n in NUMBER_RE.findall(text)]
    kinds = [k for k, pattern in QUANTITY_KINDS if re.search(pattern, text)]
    return {"is_numeric": bool(numbers), "numbers": numbers, "quantity_kinds": kinds}


def verify_source_proof(entry, base_dir=None):
    """A source_ref label proves nothing. Proof = an existing file whose sha256 equals the declared revision hash."""
    ref = entry.get("source_file")
    if not ref:
        return {"status": "NO_SOURCE_FILE"}
    path = Path(str(ref))
    if not path.is_absolute() and base_dir:
        path = Path(base_dir) / path
    if not path.is_file():
        return {"status": "SOURCE_FILE_MISSING", "path": str(path)}
    actual = sha256_file(path)
    declared = str(entry.get("source_sha256") or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", declared):
        return {"status": "NO_REVISION_HASH", "path": str(path), "actual_sha256": actual}
    if declared != actual:
        return {"status": "SOURCE_HASH_MISMATCH", "path": str(path), "declared_sha256": declared, "actual_sha256": actual}
    return {"status": "HASH_VERIFIED", "path": str(path), "sha256": actual}


def _cross_check_numbers(proof, numbers):
    """Text-like sources must literally contain every number the claim states. Binary sources are not checked."""
    path = Path(proof["path"])
    if path.suffix.lower() not in TEXT_SOURCE_SUFFIX:
        return "NOT_CHECKED_BINARY_SOURCE", []
    source_text = path.read_text(encoding="utf-8", errors="replace")
    present = {n.replace(",", "") for n in NUMBER_RE.findall(source_text)}
    missing = [n for n in numbers if n not in present]
    return ("NUMBERS_FOUND_IN_TEXT_SOURCE" if not missing else "NUMBER_NOT_IN_SOURCE"), missing


def _fact_entry(f):
    entry = dict(f)
    if isinstance(f.get("source_ref"), dict):
        entry.update(f["source_ref"])
    label = entry.get("label") or (f.get("source_ref") if isinstance(f.get("source_ref"), str) else None) or entry.get("source_file")
    return entry, (str(label) if label else "")


def load_facts(path, valid_block_ids):
    """Fact authority is proven, never assumed.

    SOURCE_HASH_MATCHED = byte integrity only; it does NOT prove approval, legal status or authoritative design facts.
    BOARD_STATED (UNVERIFIED) = labelled or explicitly board-stated claim without proof; numeric ones are accepted only when
                 the author declares claim_role BOARD_STATED, and they are always rendered with a visible tag.
    Everything else is HOLD with an explicit reason. A non-blank source_ref string alone NEVER grants VERIFIED.
    """
    accepted, held = [], []
    if not path:
        return accepted, held
    data = read_json(path)
    items = data.get("facts", []) if isinstance(data, dict) else data
    valid = set(valid_block_ids)
    base_dir = Path(path).parent
    for f in items:
        fid, text = f.get("id"), f.get("text")
        ids = [b for b in (f.get("block_ids") or []) if b in valid]
        entry, label = _fact_entry(f)
        if not (fid and text):
            held.append({"id": fid, "text": text, "reason": "INCOMPLETE"})
            continue
        if not ids:
            held.append({"id": fid, "text": text, "reason": "NO_KNOWN_BLOCK"})
            continue
        numeric = classify_numeric(text)
        proof = verify_source_proof(entry, base_dir)
        role_in = str(f.get("claim_role") or "").upper()
        record = {"id": str(fid), "text": str(text), "source_ref": label, "block_ids": ids, "numeric": numeric,
                  "source_proof": {k: v for k, v in proof.items() if k != "path"}}
        if proof["status"] == "HASH_VERIFIED":
            cross, missing = _cross_check_numbers(proof, numeric["numbers"]) if numeric["is_numeric"] else ("NO_NUMBERS", [])
            if missing:
                held.append({"id": fid, "text": text, "reason": "NUMBER_NOT_IN_SOURCE:" + ",".join(missing)})
                continue
            # A caller can create any text file and compute its SHA. Such a
            # match proves bytes/revision integrity, NEVER that the data is an
            # approved project fact. Keep the sentence usable, but visibly
            # attributed as board-stated until a canonical authority binding
            # (project ID, approval/revision, issuer) is independently checked.
            record.update({"claim_role": "BOARD_STATED",
                           "authority": "SOURCE_HASH_MATCHED", "cross_check": cross,
                           "authority_hold": "AUTHORITATIVE_PROJECT_BINDING_REQUIRED"})
            accepted.append(record)
            continue
        if proof["status"] == "SOURCE_HASH_MISMATCH":
            held.append({"id": fid, "text": text, "reason": "SOURCE_HASH_MISMATCH"})
        elif not label:
            held.append({"id": fid, "text": text, "reason": "NO_SOURCE_REF"})
        elif numeric["is_numeric"] and role_in != "BOARD_STATED":
            held.append({"id": fid, "text": text, "reason": "UNVERIFIED_NUMERIC_SOURCE_REF:" + proof["status"]})
        else:
            record.update({"claim_role": "BOARD_STATED", "authority": "UNVERIFIED", "cross_check": "NOT_CHECKED"})
            accepted.append(record)
    return accepted, held


def load_must_show(path):
    """MUST_SHOW items from the same JSON file (key must_show). Owner decides binding; a bare user flag is not law.

    binding: VERIFIED_MANDATORY (BRIEF/OFFICIAL_RULE owner with hash-verified evidence)
             CLAIMED_MANDATORY_UNVERIFIED (BRIEF/OFFICIAL_RULE owner, evidence not proven)
             USER_REQUEST (everything else)
    """
    items, rejected = [], []
    if not path:
        return items, rejected
    data = read_json(path)
    raw = data.get("must_show", []) if isinstance(data, dict) else []
    base_dir = Path(path).parent
    for m in raw:
        mid = m.get("id")
        if not mid or not (m.get("block_id") or m.get("mode") or m.get("label")):
            rejected.append({"id": mid, "reason": "INCOMPLETE"})
            continue
        owner = str(m.get("owner") or "USER").upper()
        if owner not in MUST_OWNERS:
            owner = "USER"
        entry, _ = _fact_entry(m)
        proof = verify_source_proof(entry, base_dir)
        if owner != "USER":
            # A self-hashed brief or rule-text file is not authenticated as an
            # applicable official submission rule. Preserve as a visible
            # claimed mandatory item, pending issuer/revision/applicability.
            binding = "CLAIMED_MANDATORY_UNVERIFIED"
        else:
            binding = "USER_REQUEST"
        items.append({"id": str(mid), "label": str(m.get("label") or m.get("block_id") or m.get("mode")), "owner": owner,
                      "binding": binding, "block_id": m.get("block_id"), "mode": m.get("mode"),
                      "evidence_status": proof["status"], "version": m.get("version")})
    return items, rejected


BINDING_RANK = {"VERIFIED_MANDATORY": 0, "CLAIMED_MANDATORY_UNVERIFIED": 1, "USER_REQUEST": 2}
BINDING_LABEL_KO = {"VERIFIED_MANDATORY": "공식·검증 필수", "CLAIMED_MANDATORY_UNVERIFIED": "필수 주장(증빙 미검증)",
                    "USER_REQUEST": "사용자 요청(법적 구속 아님)"}
HARD_FLOOR_SEC = 15


def plan_must_show(blocks, bound, must_show, content_budget_sec):
    """Decide which MUST_SHOW units get a slide. Nothing is silently dropped.

    A unit is a bound block (items sharing a block merge) or a PLACEHOLDER (no bound source block: shown, no numbers).
    Capacity is the hard per-slide floor, not the density target; units beyond it are INFEASIBLE_AT_DURATION.
    """
    items = [dict(m) for m in (must_show or [])]
    known = {m["id"] for m in items}
    for b in blocks:  # an arbitrary per-block boolean is a user request, never binding law
        if b.get("must_show") is True and ("BLOCKFLAG:" + b["block_id"]) not in known:
            items.append({"id": "BLOCKFLAG:" + b["block_id"], "label": b.get("title_ko") or b["block_id"], "owner": "USER",
                          "binding": "USER_REQUEST", "block_id": b["block_id"], "mode": None, "evidence_status": "NO_SOURCE_FILE",
                          "version": None})
    items.sort(key=lambda m: BINDING_RANK.get(m.get("binding"), 2))
    units, by_block = [], {}
    for it in items:
        cand = None
        if it.get("block_id"):
            cand = next((b for b in bound if b["block_id"] == it["block_id"]), None)
        elif it.get("mode"):
            cand = next((b for b in bound if b.get("mode") == it["mode"]), None)
        if cand is not None:
            if cand["block_id"] in by_block:
                by_block[cand["block_id"]]["items"].append(it)
            else:
                unit = {"kind": "BLOCK", "block": cand, "items": [it]}
                by_block[cand["block_id"]] = unit
                units.append(unit)
        else:
            units.append({"kind": "PLACEHOLDER", "block": None, "items": [it]})
    capacity = max(0, int(content_budget_sec // HARD_FLOOR_SEC))
    kept, dropped = units[:capacity], units[capacity:]
    report = []
    for unit, status in [(u, None) for u in kept] + [(u, "INFEASIBLE_AT_DURATION") for u in dropped]:
        for it in unit["items"]:
            report.append({"id": it["id"], "label": it["label"], "owner": it["owner"], "binding": it["binding"],
                           "binding_label_ko": BINDING_LABEL_KO.get(it["binding"], ""), "block_id": unit["block"]["block_id"] if unit["block"] else None,
                           "status": status or ("PLACED" if unit["kind"] == "BLOCK" else "PLACEHOLDER_SOURCE_UNVERIFIED")})
    return {
        "input_ids": [it["id"] for it in items],
        "forced_blocks": [u["block"] for u in kept if u["kind"] == "BLOCK"],
        "tags": {u["block"]["block_id"]: [it["id"] for it in u["items"]] for u in kept if u["kind"] == "BLOCK"},
        "placeholders": [u["items"] for u in kept if u["kind"] == "PLACEHOLDER"],
        "report": report,
        "omitted_ids": [it["id"] for u in dropped for it in u["items"]],
        "unit_count": len(units),
    }

# ---------------------------------------------------------------- deck planning


def find_slide_image(block, raster_dir=None):
    """PPTX can embed PNG/JPEG only. Returns (path, sha256, hold_reason)."""
    crop = block.get("crop_path")  # region crop written by ARCHIGROW_PANEL_SOURCE_EXTRACT.py
    if crop and Path(crop).exists():
        return str(crop), sha256_file(crop), None
    src = block.get("source_path")
    if src and Path(src).suffix.lower() in {".png", ".jpg", ".jpeg"} and Path(src).exists():
        return str(src), sha256_file(src), None
    if src and raster_dir:
        stem = Path(src).stem
        for ext in (".png", ".jpg", ".jpeg"):
            cand = Path(raster_dir) / (stem + ext)
            if cand.exists():
                return str(cand), sha256_file(cand), None
    return None, None, "NO_PNG_JPEG_DERIVATIVE_FOR_PPTX"


def _time_split(total, weights, floor=15):
    """Integer seconds in steps of 5 that sum exactly to total."""
    if not weights:
        return []
    raw = [max(floor, int(round(total * w / sum(weights) / 5.0)) * 5) for w in weights]
    diff = total - sum(raw)
    order = sorted(range(len(raw)), key=lambda i: -weights[i])
    i = 0
    while diff != 0 and i < 1000:
        k = order[i % len(order)]
        step = 5 if diff > 0 else -5
        if raw[k] + step >= floor:
            raw[k] += step
            diff -= step
        i += 1
    if diff != 0:  # total not representable in 5s steps (e.g. tiny totals): last slide absorbs the remainder
        raw[order[0]] += diff
    return raw


def plan_deck(blocks, audience, minutes, density="standard", facts=None, raster_dir=None, board_title="설계 보드",
              must_show=None):
    if audience not in AUDIENCE_PRIORITY:
        raise ValueError(f"UNKNOWN_AUDIENCE:{audience}")
    if density not in DENSITY_MIN_SEC:
        raise ValueError(f"UNKNOWN_DENSITY:{density}")
    facts = facts or []
    total = int(round(float(minutes) * 60))
    bound = [b for b in blocks if b.get("binding_status") == "BOUND" and b.get("board_rect_norm")]
    skipped_unbound = [b["block_id"] for b in blocks if b not in bound]
    min_sec = DENSITY_MIN_SEC[density]
    max_slides = max(3, total // min_sec)
    n_blocks = max(0, min(len(bound), max_slides - 2))
    prio = AUDIENCE_PRIORITY[audience]
    title_sec = 15 if minutes <= 5 else 30
    close_sec = 20 if minutes <= 5 else 45
    ms = plan_must_show(blocks, bound, must_show, total - title_sec - close_sec)
    forced = ms["forced_blocks"]
    placeholders = ms["placeholders"]
    others = sorted([b for b in bound if b not in forced],
                    key=lambda b: (prio.index(b["mode"]) if b["mode"] in prio else len(prio), narr_key(b)))
    room = max(0, max_slides - 2 - len(forced) - len(placeholders))
    selected = sorted(forced + others[:room], key=narr_key)
    omitted = [b["block_id"] for b in bound if b not in selected]
    n_units = len(selected) + len(placeholders)
    if not n_units:
        title_sec, close_sec = total // 2, total - total // 2
        content_secs = []
    else:
        content_secs = _time_split(total - title_sec - close_sec,
                                   [block_weight(b) for b in selected] + [1.0] * len(placeholders))
        residual = total - title_sec - close_sec - sum(content_secs)
        if residual:
            close_sec += residual  # impossible-to-split remainder lands on the close slide

    n_bullets = DENSITY_BULLETS[density]
    n_facts = DENSITY_FACTS[density]
    aud_ko = AUDIENCE_LABEL_KO[audience]
    slides = []
    slides.append({
        "no": 1, "kind": "TITLE", "title": board_title,
        "bullets": [
            {"text": f"{aud_ko} 대상 · {int(minutes)}분 발표", "basis": "STRUCTURE"},
            {"text": f"보드 블록 {len(selected)}개를 선별해 구성했습니다", "basis": "STRUCTURE"},
        ],
        "seconds": title_sec, "block_id": None, "source_ref": None,
        "notes": f"[{title_sec}초] {aud_ko}에게 인사하고 발표 순서를 안내합니다. 발표 내용은 보드의 원본 블록에 연결되어 있습니다.",
    })
    for idx, b in enumerate(selected):
        role = ROLE_KO.get(b["mode"], {"headline": b["title_ko"], "jury": [b["title_ko"]], "citizen": [b["title_ko"]]})
        pool = [{"text": t, "basis": "ROLE_TEMPLATE"} for t in role[audience]] + [{"text": WATCH_BULLET, "basis": "ROLE_TEMPLATE"}]
        bullets = pool[:n_bullets]
        attached = [f for f in facts if b["block_id"] in f["block_ids"]][:n_facts]
        for f in attached:
            if f.get("authority") == "VERIFIED":
                bullets.append({"text": f["text"], "basis": "FACT:" + f["id"], "source_ref": f["source_ref"],
                                "authority": "VERIFIED", "claim_role": f.get("claim_role")})
            else:  # no hash proof -> visibly board-stated, never presented as a verified project fact
                bullets.append({"text": f["text"] + BOARD_STATED_TAG, "basis": "BOARD_STATED:" + f["id"],
                                "source_ref": f.get("source_ref"), "authority": "UNVERIFIED", "claim_role": "BOARD_STATED"})
        img, img_sha, img_hold = find_slide_image(b, raster_dir)
        sec = content_secs[idx]
        script = " ".join(x["text"] + "." for x in bullets)
        slides.append({
            "no": len(slides) + 1, "kind": "BLOCK", "title": role["headline"], "mode": b["mode"],
            "bullets": bullets, "seconds": sec, "block_id": b["block_id"],
            "source_ref": {
                "block_id": b["block_id"], "source_path": b.get("source_path"), "source_sha256": b.get("source_sha256"),
                "board_rect_norm": b["board_rect_norm"], "board_link": b.get("board_link"),
                "rect_method": b.get("rect_method"),
            },
            "image_path": img, "image_sha256": img_sha, "image_hold_reason": img_hold,
            "must_show": ms["tags"].get(b["block_id"], []),
            "notes": (f"[{sec}초] {role['headline']}. {script} "
                      f"근거 블록 {b['block_id']} (원본 SHA {str(b.get('source_sha256'))[:12]}). "
                      f"사실·수치 주장은 출처가 연결된 항목만 사용합니다."
                      + (f" 필수 제시 항목: {', '.join(ms['tags'][b['block_id']])}." if ms["tags"].get(b["block_id"]) else "")),
        })
    for k, item_group in enumerate(placeholders):
        sec = content_secs[len(selected) + k]
        label = item_group[0]["label"]
        slides.append({
            "no": len(slides) + 1, "kind": "PLACEHOLDER", "title": label, "mode": None,
            "bullets": [{"text": "필수 제시 항목 — 원본 소스 확인 필요", "basis": "STRUCTURE"},
                        {"text": "소스가 연결되기 전까지 수치·사실 주장을 표기하지 않습니다", "basis": "STRUCTURE"}],
            "seconds": sec, "block_id": None, "source_ref": None, "must_show": [it["id"] for it in item_group],
            "notes": f"[{sec}초] 필수 항목 '{label}'의 근거 소스가 확인되지 않았습니다. 수치는 말하지 않고 소스 확인 후 보완합니다.",
        })
    close_bullets = [{"text": ROLE_KO.get(b["mode"], {"headline": b["title_ko"]})["headline"], "basis": "ROLE_TEMPLATE"}
                     for b in selected[:4]]
    close_bullets.append({"text": "질문과 의견을 받습니다", "basis": "STRUCTURE"})
    slides.append({
        "no": len(slides) + 1, "kind": "CLOSE", "title": "정리와 질의", "bullets": close_bullets,
        "seconds": close_sec, "block_id": None, "source_ref": None,
        "notes": f"[{close_sec}초] 핵심 흐름을 되짚고 질의를 받습니다. 정량 근거는 원본 도면 블록에서 다시 확인합니다.",
    })
    deck = {
        "version": DECK_VERSION, "deck_id": f"{audience}_{int(minutes)}min", "audience": audience, "audience_ko": aud_ko,
        "minutes": minutes, "total_seconds": total, "density": density,
        "slide_count": len(slides), "max_slides_by_density": max_slides,
        "selected_blocks": [b["block_id"] for b in selected], "omitted_blocks": omitted,
        "unbound_blocks": skipped_unbound,
        "selection_rule": "MUST_SHOW first (hard floor 15s/slide), then AUDIENCE_PRIORITY and narrative order; "
                          "optional slide budget = floor(total/min_sec_per_slide)",
        "must_show_status": ("NONE" if not ms["input_ids"] else
                             ("INFEASIBLE_AT_DURATION" if ms["omitted_ids"] else "SATISFIED")),
        "must_show_input_ids": ms["input_ids"], "must_show_report": ms["report"], "must_show_omitted": ms["omitted_ids"],
        "must_show_compressed": bool(ms["input_ids"]) and len(selected) + len(placeholders) > max_slides - 2,
        "suggested_minutes": (max(int(minutes) + 5, -(-(title_sec + close_sec + ms["unit_count"] * 30) // 300) * 5)
                              if ms["omitted_ids"] else None),
        "ai_disclosure": AI_DISCLOSURE, "slides": slides,
    }
    deck["audit_violations"] = audit_deck(deck)
    return deck


def audit_deck(deck):
    """Anti-hallucination audit: every claim has a basis; numerals only from FACT/STRUCTURE; blocks carry a source SHA."""
    violations = []
    for s in deck["slides"]:
        for b in s["bullets"]:
            basis = b.get("basis")
            if not basis:
                violations.append(f"S{s['no']}:NO_BASIS")
            elif re.search(r"\d", b["text"]) and not (basis.startswith(("FACT:", "BOARD_STATED:")) or basis == "STRUCTURE"):
                violations.append(f"S{s['no']}:NUMERAL_WITHOUT_FACT:{b['text'][:20]}")
            if basis and basis.startswith("FACT:") and not b.get("source_ref"):
                violations.append(f"S{s['no']}:FACT_WITHOUT_SOURCE_REF")
            if basis and basis.startswith("FACT:") and b.get("authority") != "VERIFIED":
                violations.append(f"S{s['no']}:FACT_NOT_HASH_VERIFIED")
            if basis and basis.startswith("BOARD_STATED:") and BOARD_STATED_TAG not in b["text"]:
                violations.append(f"S{s['no']}:BOARD_STATED_UNTAGGED")
        if s["kind"] == "BLOCK":
            ref = s.get("source_ref") or {}
            if not ref.get("source_sha256") or not ref.get("board_rect_norm"):
                violations.append(f"S{s['no']}:BLOCK_WITHOUT_SOURCE_SHA_OR_RECT")
    total = sum(s["seconds"] for s in deck["slides"])
    if total != deck["total_seconds"]:
        violations.append(f"TIME_SUM_MISMATCH:{total}!={deck['total_seconds']}")
    reported = {r["id"] for r in deck.get("must_show_report", [])}
    if set(deck.get("must_show_input_ids", [])) != reported:
        violations.append("MUST_SHOW_UNACCOUNTED")
    placed = {i for s in deck["slides"] for i in (s.get("must_show") or [])}
    for r in deck.get("must_show_report", []):
        if r["status"] in ("PLACED", "PLACEHOLDER_SOURCE_UNVERIFIED") and r["id"] not in placed:
            violations.append(f"MUST_SHOW_CLAIMED_BUT_NOT_ON_SLIDE:{r['id']}")
    if deck.get("must_show_omitted") and deck.get("must_show_status") != "INFEASIBLE_AT_DURATION":
        violations.append("MUST_SHOW_SILENT_DROP")
    return violations

# ---------------------------------------------------------------- PPTX (python-pptx)

FONT_KO = "Malgun Gothic"


def pptx_available():
    return importlib.util.find_spec("pptx") is not None


def _hex(color):
    return color.lstrip("#").upper()


def _set_ea(run, font):
    from pptx.oxml.ns import qn
    rpr = run._r.get_or_add_rPr()
    for old in rpr.findall(qn("a:ea")):
        rpr.remove(old)
    rpr.append(rpr.makeelement(qn("a:ea"), {"typeface": font}))


def _add_text(slide, name, x, y, w, h, paragraphs, size, bold=False, color="151515"):
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    for i, text in enumerate(paragraphs):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        run = para.add_run()
        run.text = text
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.name = FONT_KO
        run.font.color.rgb = RGBColor.from_string(_hex(color))
        _set_ea(run, FONT_KO)
        if i:
            para.space_before = Pt(8)
    return tb


def _add_rect(slide, name, x, y, w, h, fill, line=None, line_w=0.75):
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.name = name
    if fill:
        shp.fill.solid()
        shp.fill.fore_color.rgb = RGBColor.from_string(_hex(fill))
    else:
        shp.fill.background()
    if line:
        shp.line.color.rgb = RGBColor.from_string(_hex(line))
        shp.line.width = Pt(line_w)
    else:
        shp.line.fill.background()
    return shp


def build_pptx(deck, out_path, locator_blocks, style_id, viewer_name="compare.html"):
    """Real editable PPTX: native text boxes, notes, source image, clickable board locator per slide."""
    from pptx import Presentation
    from pptx.util import Inches
    style = STYLES[style_id] if style_id in STYLES else STYLES[STYLE_ORDER[0]]
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    total = len(deck["slides"])
    loc_w, loc_h = 1.4, 1.4 * BOARD_H_MM / BOARD_W_MM
    loc_x, loc_y = 11.3, 6.75 - loc_h
    from pptx.dml.color import RGBColor
    for s in deck["slides"]:
        slide = prs.slides.add_slide(blank)
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = RGBColor.from_string(_hex(style["paper"]))
        _add_rect(slide, "ACCENT_BAR", 0.6, 0.38, 0.6, 0.07, style["accent"])
        kicker = s.get("mode") or s["kind"]
        _add_text(slide, "KICKER", 1.35, 0.28, 6.0, 0.3, [f"{kicker} · {deck['audience_ko']} {int(deck['minutes'])}분"], 11, True, style["accent"])
        if s["kind"] == "TITLE":
            _add_text(slide, "TITLE", 0.6, 2.2, 12.0, 1.6, [s["title"]], 38, True, style["ink"])
            _add_text(slide, "BODY", 0.6, 4.3, 12.0, 1.6, ["• " + b["text"] for b in s["bullets"]], 20, False, style["muted"])
        elif s["kind"] in ("CLOSE", "PLACEHOLDER"):
            _add_text(slide, "TITLE", 0.6, 0.7, 12.0, 0.9, [s["title"]], 32, True, style["ink"])
            _add_text(slide, "BODY", 0.6, 1.9, 10.5, 4.2, ["• " + b["text"] for b in s["bullets"]], 22, False, style["ink"])
        else:
            _add_text(slide, "TITLE", 0.6, 0.62, 12.1, 0.9, [s["title"]], 30, True, style["ink"])
            _place_image(slide, s, 0.6, 1.65, 7.9, 4.9, style)
            _add_text(slide, "BODY", 8.8, 1.65, 4.0, 3.0, ["• " + b["text"] for b in s["bullets"]], 16, False, style["ink"])
            _add_locator(slide, s, locator_blocks, loc_x, loc_y, loc_w, loc_h, style, deck, viewer_name)
            _add_text(slide, "LOCATOR_CAPTION", loc_x - 0.2, loc_y + loc_h + 0.04, loc_w + 0.4, 0.22, ["보드 위치 (클릭: 비교 뷰어)"], 9, False, style["muted"])
        ref = s.get("source_ref") or {}
        sha12 = str(ref.get("source_sha256") or "")[:12]
        foot = f"ARCHIGROW · 데모 · {s['seconds']}초 · {s['no']:02d}/{total:02d}"
        if s["block_id"]:
            foot = f"블록 {s['block_id']} · SHA {sha12} · " + foot
        _add_text(slide, "FOOTER", 0.6, 7.02, 12.1, 0.3, [foot], 9, False, style["muted"])
        if s.get("must_show") or deck.get("must_show_status") == "INFEASIBLE_AT_DURATION":
            status = ("필수 항목 · " + ", ".join(s["must_show"])) if s.get("must_show") else ""
            if deck.get("must_show_status") == "INFEASIBLE_AT_DURATION":
                status += (" · " if status else "") + (
                    f"발표시간 내 수용 불가 항목 {len(deck['must_show_omitted'])}건 — {deck['suggested_minutes']}분 이상 권장")
            _add_text(slide, "MUST_SHOW_STATUS", 0.6, 6.7, 10.5, 0.3, [status], 10, True, "#9B4B42")
        slide.notes_slide.notes_text_frame.text = s["notes"]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))
    return str(out_path)


def _place_image(slide, s, x, y, w, h, style):
    from pptx.util import Inches
    _add_rect(slide, "IMAGE_FRAME", x, y, w, h, "#FFFFFF", style["line"])
    path = s.get("image_path")
    if path and Path(path).exists():
        try:
            from PIL import Image
            with Image.open(path) as im:
                iw, ih = im.size
            scale = min(w / iw, h / ih)
            pw, ph = iw * scale, ih * scale
            pic = slide.shapes.add_picture(path, Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2), Inches(pw), Inches(ph))
            pic.name = f"SOURCE_IMAGE:{s['block_id']}"
            return
        except Exception as exc:
            s["image_hold_reason"] = f"IMAGE_EMBED_FAILED:{type(exc).__name__}"
    _add_text(slide, "IMAGE_HOLD", x + 0.4, y + h / 2 - 0.3, w - 0.8, 0.6,
              [f"원본 이미지 HOLD: {s.get('image_hold_reason') or 'UNKNOWN'} — 보드 블록에서 확인"], 14, True, "#9B4B42")


def _add_locator(slide, s, blocks, x, y, w, h, style, deck, viewer_name):
    outline = _add_rect(slide, "LOCATOR_BOARD", x, y, w, h, "#FFFFFF", style["ink"], 1.0)
    outline.click_action.hyperlink.address = (
        f"{viewer_name}?deck={quote(deck['deck_id'])}&slide={s['no']}&block={quote(s['block_id'] or '')}")
    for b in blocks:
        r = b.get("board_rect_norm")
        if not r or b.get("binding_status") != "BOUND":
            continue
        active = b["block_id"] == s["block_id"]
        name = ("LOCATOR_ACTIVE:" if active else "LOCATOR_BLOCK:") + b["block_id"]
        _add_rect(slide, name, x + r["x"] * w, y + r["y"] * h, r["w"] * w, r["h"] * h,
                  style["accent"] if active else "#D9DEE1", style["ink"] if active else "#FFFFFF", 0.5)


def inspect_pptx(path):
    """Reopen a PPTX and report what is actually stored (text, notes, picture and locator shapes)."""
    from pptx import Presentation
    prs = Presentation(str(path))
    slides = []
    for idx, slide in enumerate(prs.slides, 1):
        info = {"no": idx, "title": None, "body": None, "notes": None, "pictures": [], "locator_blocks": 0,
                "active_block": None, "footer": None, "locator_link": None}
        for shp in slide.shapes:
            name = shp.name
            if name == "TITLE":
                info["title"] = shp.text_frame.text
            elif name == "BODY":
                info["body"] = shp.text_frame.text
            elif name == "FOOTER":
                info["footer"] = shp.text_frame.text
            elif name == "MUST_SHOW_STATUS":
                info["must_show_status"] = shp.text_frame.text
            elif name.startswith("SOURCE_IMAGE:"):
                info["pictures"].append(name)
            elif name.startswith("LOCATOR_ACTIVE:"):
                info["active_block"] = name.split(":", 1)[1]
                info["locator_blocks"] += 1
            elif name.startswith("LOCATOR_BLOCK:"):
                info["locator_blocks"] += 1
            elif name == "LOCATOR_BOARD":
                try:
                    info["locator_link"] = shp.click_action.hyperlink.address
                except Exception:
                    info["locator_link"] = None
        if slide.has_notes_slide:
            info["notes"] = slide.notes_slide.notes_text_frame.text
        slides.append(info)
    return {"slide_count": len(slides), "slide_width_in": round(prs.slide_width / 914400, 3),
            "slide_height_in": round(prs.slide_height / 914400, 3), "slides": slides}


def edit_pptx_title(path, slide_no, new_text, out_path):
    """Edit a slide title in place (keeps run formatting), save to out_path. Used to prove edits persist."""
    from pptx import Presentation
    prs = Presentation(str(path))
    slide = prs.slides[slide_no - 1]
    for shp in slide.shapes:
        if shp.name == "TITLE":
            shp.text_frame.paragraphs[0].runs[0].text = new_text
            break
    else:
        raise ValueError("TITLE_SHAPE_NOT_FOUND")
    prs.save(str(out_path))
    return str(out_path)

# ---------------------------------------------------------------- viewer

VIEWER_TEMPLATE = r"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ARCHIGROW 패널 ↔ 발표 비교 뷰어 (DEMO)</title>
<style>
*{box-sizing:border-box}
body{margin:0;font-family:'Noto Sans KR','Malgun Gothic',Arial,sans-serif;background:#e9e7e1;color:#151515;font-size:14px}
header.top{padding:10px 16px;background:#151515;color:#fff;display:flex;justify-content:space-between;align-items:center;gap:12px}
header.top h1{font-size:16px;margin:0}
header.top small{color:#cfcab8}
main{display:grid;grid-template-columns:260px minmax(380px,1fr) 480px;gap:12px;padding:12px;align-items:start}
section{background:#fff;border:1px solid #d7d4cb;padding:10px}
.tabs{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}
.tabs button{border:1px solid #151515;background:#fff;padding:5px 9px;cursor:pointer;font-size:12px}
.tabs button.on{background:#c86435;color:#fff;border-color:#c86435}
ol#slideList{list-style:none;margin:0;padding:0}
ol#slideList li{padding:7px 8px;border-bottom:1px solid #eee;cursor:pointer;font-size:13px}
ol#slideList li.on{background:#fbe9df;font-weight:700}
ol#slideList li small{display:block;color:#777;font-weight:400}
#slideCard h2{margin:0 0 8px;font-size:22px}
#slideCard ul{padding-left:18px;margin:8px 0}
#slideCard img{max-width:100%;max-height:340px;border:1px solid #d7d4cb;background:#fff;display:block}
.note{background:#f5f3ec;border-left:3px solid #c86435;padding:8px;font-size:12px;margin-top:8px;white-space:pre-wrap}
.src{font-size:11px;color:#555;word-break:break-all;margin-top:6px}
#stage{position:relative;overflow:hidden;border:1px solid #bbb;background:#fff}
#boardFrame{position:absolute;left:0;top:0;border:0;transform-origin:0 0;pointer-events:none}
#overlay{position:absolute;inset:0}
.hit{position:absolute;border:1px solid rgba(21,21,21,.35);cursor:pointer}
.hit:hover{background:rgba(200,100,53,.15)}
.hit.on{border:3px solid #c86435;background:rgba(200,100,53,.28)}
.hit.off{border-style:dashed}
#blockInfo{font-size:12px;margin-top:8px;word-break:break-all}
</style></head><body>
<header class="top"><h1>ARCHIGROW 패널 ↔ 발표 비교 뷰어</h1><small id="disc"></small></header>
<main>
<section><div class="tabs" id="deckTabs"></div><ol id="slideList"></ol></section>
<section id="slideCard"></section>
<section><div class="tabs" id="styleTabs"></div><div id="stage"><iframe id="boardFrame" title="board"></iframe><div id="overlay"></div></div><div id="blockInfo"></div></section>
</main>
<script id="data" type="application/json">__DATA__</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent);
const BW=594*96/25.4, BH=841*96/25.4;
const st={style:D.boards[0].style_id,deck:D.decks[0].deck_id,idx:0,block:null,frameStyle:null};
const $=id=>document.getElementById(id);
function el(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e}
const curDeck=()=>D.decks.find(d=>d.deck_id===st.deck);
const curBoard=()=>D.boards.find(b=>b.style_id===st.style);
function selectSlide(i){const s=curDeck().slides[i];st.idx=i;st.block=s.block_id;render()}
function selectBlock(bid){
  const d=curDeck();const i=d.slides.findIndex(s=>s.block_id===bid);
  if(i>=0){selectSlide(i)}else{st.block=bid;render()}
}
function render(){
  $('disc').textContent=D.ai_disclosure;
  const dt=$('deckTabs');dt.textContent='';
  D.decks.forEach(d=>{const b=el('button',d.deck_id===st.deck?'on':'',d.audience_ko+' '+d.minutes+'분 ('+d.slide_count+'장)');
    b.dataset.deck=d.deck_id;b.onclick=()=>{st.deck=d.deck_id;st.idx=0;st.block=null;render()};dt.appendChild(b)});
  const sl=$('slideList');sl.textContent='';
  const d=curDeck();
  d.slides.forEach((s,i)=>{const li=el('li',i===st.idx?'on':'',s.no+'. '+s.title);li.dataset.slide=s.no;
    li.appendChild(el('small',null,(s.block_id||s.kind)+' · '+s.seconds+'초'));li.onclick=()=>selectSlide(i);sl.appendChild(li)});
  const s=d.slides[st.idx];const card=$('slideCard');card.textContent='';
  card.appendChild(el('h2',null,s.title));
  if(d.must_show_status&&d.must_show_status!=='NONE'){
    const rep=(d.must_show_report||[]).map(r=>r.id+':'+r.status).join(' · ');
    const ban=el('div','note','필수 항목 상태: '+d.must_show_status+(d.suggested_minutes?' · 권장 '+d.suggested_minutes+'분 이상':'')+'\n'+rep);
    ban.id='mustShowBanner';ban.dataset.status=d.must_show_status;card.appendChild(ban)}
  if(s.must_show&&s.must_show.length){const t=el('div','src','이 슬라이드의 필수 항목: '+s.must_show.join(', '));t.id='slideMustShow';card.appendChild(t)}
  const ul=el('ul');s.bullets.forEach(b=>{ul.appendChild(el('li',null,b.text+(b.basis&&(b.basis.startsWith('FACT:')||b.basis.startsWith('BOARD_STATED:'))?'  ['+b.source_ref+']':'')))});card.appendChild(ul);
  if(s.image_rel){const im=el('img');im.src=s.image_rel;im.alt=s.block_id;card.appendChild(im)}
  else if(s.kind==='BLOCK'){card.appendChild(el('div','note','원본 이미지 HOLD: '+(s.image_hold_reason||'')))}
  card.appendChild(el('div','note','발표 노트\n'+s.notes));
  if(s.block_id)card.appendChild(el('div','src','블록 '+s.block_id+' · 원본 SHA256 '+(s.source_sha256||'-')));
  const sb=$('styleTabs');sb.textContent='';
  D.boards.forEach(b=>{const bt=el('button',b.style_id===st.style?'on':'',b.style_label);bt.dataset.style=b.style_id;
    bt.onclick=()=>{st.style=b.style_id;render()};sb.appendChild(bt)});
  const board=curBoard();const W=$('stage').clientWidth||440;const k=W/BW;
  const stage=$('stage');stage.style.height=(BH*k)+'px';
  const fr=$('boardFrame');
  if(st.frameStyle!==board.style_id){fr.src=board.html_rel;st.frameStyle=board.style_id}
  fr.style.width=BW+'px';fr.style.height=BH+'px';fr.style.transform='scale('+k+')';
  const ov=$('overlay');ov.textContent='';
  Object.keys(board.rects).forEach(bid=>{const r=board.rects[bid];const h=el('div','hit'+(bid===st.block?' on':'')+(d.selected_blocks.includes(bid)?'':' off'));
    h.dataset.blockId=bid;h.title=bid;
    h.style.left=(r.x*100)+'%';h.style.top=(r.y*100)+'%';h.style.width=(r.w*100)+'%';h.style.height=(r.h*100)+'%';
    h.onclick=()=>selectBlock(bid);ov.appendChild(h)});
  const info=$('blockInfo');info.textContent='';
  if(st.block){const bi=board.blocks[st.block]||{};
    const inDeck=d.selected_blocks.includes(st.block);
    info.textContent='선택 블록: '+st.block+(inDeck?'':' (이 발표본에서는 생략됨)')+' · 위치 방식: '+(bi.rect_method||'-')+' · 보드 링크: '+(bi.board_link||'-')}
  else info.textContent='보드 블록을 클릭하면 해당 슬라이드로 이동하고, 슬라이드를 선택하면 보드 위치가 강조됩니다.';
}
(function init(){
  const q=new URLSearchParams(location.search);
  if(q.get('deck')&&D.decks.some(d=>d.deck_id===q.get('deck')))st.deck=q.get('deck');
  const d=curDeck();
  if(q.get('slide')){const i=d.slides.findIndex(s=>String(s.no)===q.get('slide'));if(i>=0){st.idx=i;st.block=d.slides[i].block_id}}
  if(q.get('block')){st.block=q.get('block')}
  window.PANEL_VIEWER={state:st,data:D,selectBlock,selectSlide};
  window.addEventListener('resize',render);
  render();
})();
</script></body></html>
"""


def write_viewer(out_dir, board_results, decks, deck_files):
    """compare.html: slide <-> board block cross-highlighting. board_results = [{'dir','doc'}]."""
    out_dir = Path(out_dir)
    asset_dir = out_dir / "viewer-assets"
    asset_dir.mkdir(parents=True, exist_ok=True)

    def local_image(path_value):
        """Package source slide images for a portable local comparison viewer."""
        import shutil
        source = Path(path_value)
        if not source.is_file():
            return None
        digest = sha256_file(source)
        destination = asset_dir / (digest[:16] + "_" + source.name)
        if not destination.exists():
            shutil.copyfile(source, destination)
        elif sha256_file(destination) != digest:
            raise ValueError("VIEWER_ASSET_HASH_MISMATCH")
        return "viewer-assets/" + destination.name

    boards = []
    for br in board_results:
        doc = br["doc"]
        boards.append({
            "style_id": doc["board"]["style_id"], "style_label": doc["board"]["style_label"],
            "html_rel": rel_uri(Path(br["dir"]) / doc["board"]["html"], out_dir),
            "rects": {b["block_id"]: b["board_rect_norm"] for b in doc["blocks"] if b.get("board_rect_norm")},
            "blocks": {b["block_id"]: {"rect_method": b.get("rect_method"), "board_link": b.get("board_link")} for b in doc["blocks"]},
        })
    deck_data = []
    for deck in decks:
        slides = []
        for s in deck["slides"]:
            ref = s.get("source_ref") or {}
            slides.append({
                "no": s["no"], "kind": s["kind"], "title": s["title"], "seconds": s["seconds"], "block_id": s["block_id"],
                "bullets": s["bullets"], "notes": s["notes"], "source_sha256": ref.get("source_sha256"),
                "image_rel": local_image(s["image_path"]) if s.get("image_path") else None,
                "image_hold_reason": s.get("image_hold_reason"), "must_show": s.get("must_show") or [],
            })
        deck_data.append({
            "deck_id": deck["deck_id"], "audience_ko": deck["audience_ko"], "minutes": deck["minutes"],
            "slide_count": deck["slide_count"], "selected_blocks": deck["selected_blocks"],
            "must_show_status": deck.get("must_show_status", "NONE"), "must_show_report": deck.get("must_show_report", []),
            "must_show_omitted": deck.get("must_show_omitted", []), "suggested_minutes": deck.get("suggested_minutes"),
            "pptx_rel": deck_files.get(deck["deck_id"]), "slides": slides,
        })
    payload = {"boards": boards, "decks": deck_data, "ai_disclosure": "규칙 기반(비-LLM) 재구성 · 데모 소스 · 미검증"}
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    path = out_dir / "compare.html"
    path.write_text(VIEWER_TEMPLATE.replace("__DATA__", data), encoding="utf-8")
    return path

# ---------------------------------------------------------------- orchestration


def recompose(board_dirs, out_dir, audiences=("jury", "citizen"), minutes_list=(15, 5), density="standard",
              facts_path=None, raster_dir=None, make_pptx=True, board_results=None, must_show_path=None):
    """Workflow B over one or more existing board dirs. The first board is the deck/locator reference."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if board_results is None:
        board_results = []
        for d in board_dirs:
            board_results.append({"dir": Path(d), "doc": load_board_blocks(d)})
    primary = board_results[0]
    pdoc = primary["doc"]
    html_before = pdoc["board"]["html_sha256"]
    facts, held_facts = load_facts(facts_path, [b["block_id"] for b in pdoc["blocks"]])
    must_show, must_show_rejected = load_must_show(must_show_path or facts_path)
    decks, deck_files, pptx_reports = [], {}, {}
    pptx_status = "SKIPPED"
    if make_pptx:
        pptx_status = "READY" if pptx_available() else "HOLD_PYTHON_PPTX_MISSING"
    for aud in audiences:
        for minutes in minutes_list:
            deck = plan_deck(pdoc["blocks"], aud, minutes, density=density, facts=facts, raster_dir=raster_dir,
                             board_title=pdoc["board"].get("title") or "설계 보드", must_show=must_show)
            decks.append(deck)
            if pptx_status == "READY":
                fname = f"decks/{deck['deck_id']}.pptx"
                build_pptx(deck, out_dir / fname, pdoc["blocks"], pdoc["board"]["style_id"], viewer_name="../compare.html")
                deck_files[deck["deck_id"]] = fname
                rep = inspect_pptx(out_dir / fname)
                rep["sha256"] = sha256_file(out_dir / fname)
                pptx_reports[deck["deck_id"]] = rep
    write_json(out_dir / "deck-plans.json", {"version": DECK_VERSION, "ai_disclosure": AI_DISCLOSURE,
                                             "facts_accepted": facts, "facts_held": held_facts,
                                             "must_show": must_show, "must_show_rejected": must_show_rejected, "decks": decks})
    viewer = write_viewer(out_dir, board_results, decks, deck_files)
    html_path = Path(primary["dir"]) / pdoc["board"]["html"]
    html_after = sha256_file(html_path) if html_path.exists() else None
    return {
        "decks": decks, "deck_files": deck_files, "pptx_status": pptx_status, "pptx_reports": pptx_reports,
        "viewer": str(viewer), "facts_accepted": len(facts), "facts_held": held_facts,
        "must_show_items": len(must_show), "must_show_rejected": must_show_rejected,
        "original_board_unchanged": html_before == html_after, "original_board_html_sha256": html_before,
    }


def run_demo(out_dir=DEFAULT_OUT, render=False, make_pptx=True, facts_path=None):
    out_dir = Path(out_dir)
    package_path = FIXTURE_ROOT / "package-A1_BOARD.json"
    asset_dir = FIXTURE_ROOT / "QUALITY_SOURCES"
    raster_dir = FIXTURE_ROOT / "TEST_SOURCES"
    package = load_package(package_path)
    bindings, suggestions = auto_bind(package, asset_dir)
    write_json(out_dir / "inputs" / "bindings.json", {"bindings": bindings, "suggestions": suggestions})
    boards = build_boards(package, bindings, out_dir, demo=True, render=render)
    rec = recompose([], out_dir, facts_path=facts_path, raster_dir=raster_dir, make_pptx=make_pptx, board_results=boards)
    summary = {
        "version": "ARCHIGROW_PANEL_WORKFLOW_SUMMARY_V1",
        "status": "IMPLEMENTED_UNVERIFIED_UNTIL_TESTS_AND_VISUAL_INSPECTION",
        "ai_disclosure": AI_DISCLOSURE,
        "inputs": {"package": str(package_path), "assets": str(asset_dir), "raster_derivatives": str(raster_dir),
                   "demo_synthetic_sources": True},
        "boards": [{
            "style_id": b["doc"]["board"]["style_id"], "dir": str(b["dir"]), "html_sha256": b["doc"]["board"]["html_sha256"],
            "pdf_sha256": b["doc"]["board"].get("pdf_sha256"), "block_count": len(b["doc"]["blocks"]),
            "source_gaps": b["doc"]["source_gaps"],
            "render": (b["render"] or {}).get("mechanical_render_pass") if b["render"] else "NOT_REQUESTED",
            "render_error": (b["render"] or {}).get("render_error") if b["render"] else None,
        } for b in boards],
        "decks": [{
            "deck_id": d["deck_id"], "slide_count": d["slide_count"], "total_seconds": d["total_seconds"],
            "selected_blocks": d["selected_blocks"], "omitted_blocks": d["omitted_blocks"],
            "audit_violations": d["audit_violations"], "pptx": rec["deck_files"].get(d["deck_id"]),
        } for d in rec["decks"]],
        "pptx_status": rec["pptx_status"], "viewer": rec["viewer"],
        "original_board_unchanged": rec["original_board_unchanged"],
        "facts_accepted": rec["facts_accepted"], "facts_held": rec["facts_held"],
        "hold": [
            "Block discovery is rule-based/by-construction, not a live AI parse of arbitrary boards.",
            "Slide counts follow time budget and available bound blocks; the demo's 18-block/16->7 numbers are not forced.",
            "No project facts supplied: slide text is role-template editorial; numerals/claims need --facts with source_ref.",
            "Browser/screenshot and PowerPoint-open verification are not performed by this command.",
        ],
    }
    write_json(out_dir / "panel-workflow-summary.json", summary)
    return summary


def main():
    p = argparse.ArgumentParser(description="ARCHIGROW panel workflow: assets->A1 board (2 styles) and board->audience decks.")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("demo", help="Run both workflows on the bundled synthetic A1 fixture.")
    d.add_argument("--out-dir", default=str(DEFAULT_OUT))
    d.add_argument("--render", action="store_true", help="Also print boards to PDF with the existing renderer (needs Chrome/Edge).")
    d.add_argument("--no-pptx", action="store_true")
    d.add_argument("--facts", default="")
    b = sub.add_parser("board", help="Workflow A: package + source bindings (or asset dir) -> two-style A1 boards.")
    b.add_argument("--package", required=True)
    b.add_argument("--sources", default="", help="bindings JSON from ARCHIGROW_COMPETITION_BIND.py")
    b.add_argument("--asset-dir", default="", help="auto-bind from a directory (unique high-confidence only)")
    b.add_argument("--title", default="")
    b.add_argument("--out-dir", required=True)
    b.add_argument("--render", action="store_true")
    r = sub.add_parser("recompose", help="Workflow B: existing board dir(s) -> decks + viewer.")
    r.add_argument("--board-dir", action="append", required=True)
    r.add_argument("--out-dir", required=True)
    r.add_argument("--audiences", default="jury,citizen")
    r.add_argument("--minutes", default="15,5")
    r.add_argument("--density", default="standard", choices=sorted(DENSITY_MIN_SEC))
    r.add_argument("--facts", default="", help="JSON with facts[] (hash-proven source_file+source_sha256) and must_show[]")
    r.add_argument("--must-show", default="", help="separate JSON with must_show[] (default: the --facts file)")
    r.add_argument("--raster-dir", default="")
    r.add_argument("--no-pptx", action="store_true")
    args = p.parse_args()
    if args.cmd == "demo":
        s = run_demo(args.out_dir, render=args.render, make_pptx=not args.no_pptx, facts_path=args.facts or None)
        print(json.dumps(s, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "board":
        package = load_package(args.package)
        if args.sources:
            bindings = BUILD.load_sources(args.sources)
        elif args.asset_dir:
            bindings, _ = auto_bind(package, args.asset_dir)
        else:
            bindings = {}
        res = build_boards(package, bindings, args.out_dir, board_title=args.title or None, demo=False, render=args.render)
        print(json.dumps([{"style": x["doc"]["board"]["style_id"], "dir": str(x["dir"]), "source_gaps": x["doc"]["source_gaps"]}
                          for x in res], ensure_ascii=False, indent=2))
        return 0
    rec = recompose(args.board_dir, args.out_dir, audiences=tuple(x for x in args.audiences.split(",") if x),
                    minutes_list=tuple(float(x) if "." in x else int(x) for x in args.minutes.split(",") if x),
                    density=args.density, facts_path=args.facts or None, raster_dir=args.raster_dir or None,
                    make_pptx=not args.no_pptx, must_show_path=args.must_show or None)
    print(json.dumps({"decks": [{"deck_id": x["deck_id"], "slides": x["slide_count"]} for x in rec["decks"]],
                      "pptx_status": rec["pptx_status"], "viewer": rec["viewer"],
                      "original_board_unchanged": rec["original_board_unchanged"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
