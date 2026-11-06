#!/usr/bin/env python3
import argparse
import html
import json
import os
import re
from pathlib import Path

try:
    from PIL import Image
except Exception:
    Image = None

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "DOMAIN" / "ARCHITECTURE_COMPETITION_OUTPUT_PROFILE_REGISTRY.json"
QUALITY = ROOT / "DOMAIN" / "ARCHITECTURE_COMPETITION_VISUAL_QUALITY_REGISTRY.json"

MODE_TITLES_KO={
    "CONTEXT":"대지와 도시맥락",
    "CONCEPT":"설계개념과 매스",
    "PROGRAM":"프로그램 구성",
    "CIRCULATION":"진입과 동선체계",
    "PLAN":"평면과 공간조직",
    "SECTION":"단면과 수직관계",
    "ELEVATION":"입면과 외피",
    "AXONOMETRIC":"공간구성과 레이어",
    "PERFORMANCE":"환경·성능 전략",
    "EXPERIENCE":"핵심 공간경험",
    "TECHNICAL":"구조·주차·면적·피난"
}

def short_title(mode, fallback=""):
    return MODE_TITLES_KO.get(str(mode or "").upper(), str(fallback or mode or ""))

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def slug(value):
    s = re.sub(r"[^A-Za-z0-9_-]+", "-", str(value or "").strip()).strip("-")
    return s.lower() or "item"

def esc(value):
    return html.escape(str(value or ""), quote=True)

def source_key(item):
    return f"{item.get('mode','UNKNOWN')}:{item.get('order',0)}"

def load_sources(path):
    if not path:
        return {}
    data = read_json(path)
    if isinstance(data, dict) and "bindings" in data:
        return data["bindings"]
    return data if isinstance(data, dict) else {}

def inspect_source(path):
    if not path:
        return {"kind":"NONE","width_px":None,"height_px":None,"aspect":None}
    p=Path(path)
    suffix=p.suffix.lower()
    if suffix in {".svg",".emf",".dxf",".dwg"}:
        return {"kind":"VECTOR","width_px":None,"height_px":None,"aspect":None}
    if suffix==".pdf":
        return {"kind":"PDF","width_px":None,"height_px":None,"aspect":None}
    if suffix in {".png",".jpg",".jpeg",".webp",".gif"} and Image is not None and p.exists():
        try:
            with Image.open(p) as im:
                w,h=im.size
            return {"kind":"RASTER","width_px":w,"height_px":h,"aspect":round(w/h,4) if h else None}
        except Exception:
            pass
    return {"kind":"OTHER","width_px":None,"height_px":None,"aspect":None}

def layout_role(mode, index):
    if index==0:
        return "HERO"
    if mode in {"PLAN","SECTION"}:
        return "TECHNICAL_LARGE"
    if mode in {"CONTEXT","ELEVATION"}:
        return "WIDE"
    if mode in {"EXPERIENCE","AXONOMETRIC"}:
        return "HERO_SECONDARY"
    if mode in {"CONCEPT","PROGRAM","CIRCULATION","PERFORMANCE"}:
        return "DIAGRAM"
    return "TECHNICAL"

def build_manifest(package, profile, sources, quality=None):
    items=[]
    for item in package.get("items", []):
        key=source_key(item)
        bound=sources.get(key)
        exists=False
        source_path=None
        if isinstance(bound, str):
            source_path=bound
        elif isinstance(bound, dict):
            source_path=bound.get("path")
        if source_path:
            exists=Path(source_path).exists()
        meta=inspect_source(source_path) if exists else inspect_source(None)
        items.append({
            "id": key,
            "order": item.get("order"),
            "mode": item.get("mode"),
            "layout_role": layout_role(item.get("mode"), len(items)),
            "question": item.get("question"),
            "source_required": item.get("source_required"),
            "production_path": item.get("production_path"),
            "source_path": source_path,
            "source_exists": exists,
            "source_meta": meta,
            "binding_status": "BOUND" if exists else "MISSING_SOURCE",
            "recommended_techniques": item.get("recommended_techniques", [])
        })
    return {
        "version":"ARCHCOMP_BUILD_MANIFEST_V1",
        "delivery":package.get("delivery"),
        "status":"READY_TO_RENDER" if items and all(x["source_exists"] for x in items) else "SOURCE_GAPS",
        "brief_verified":bool(package.get("brief_verified")),
        "content_frozen":bool(package.get("content_frozen")),
        "profile":profile,
        "quality":quality or {},
        "items":items
    }

def source_view(item):
    p=item.get("source_path")
    if item.get("source_exists") and p:
        suffix=Path(p).suffix.lower()
        uri=Path(p).resolve().as_uri()
        if suffix in {".png",".jpg",".jpeg",".webp",".gif",".svg"}:
            return f'<img class="source-img" src="{esc(uri)}" alt="{esc(item["id"])}">'
        return f'<div class="bound-file">BOUND SOURCE<br><small>{esc(p)}</small></div>'
    return (
        '<div class="missing">'
        '<strong>MISSING SOURCE</strong>'
        f'<span>{esc(item.get("source_required"))}</span>'
        '</div>'
    )
def css_for(delivery):
    if delivery=="A1_BOARD":
        page="@page { size: 594mm 841mm; margin: 0; }"
        frame="width:594mm;min-height:841mm;padding:16mm;grid-template-columns:repeat(12,1fr);gap:7mm;"
        body="font-size:10pt;"
        footer_lr="16mm"
    elif delivery in {"A3_REPORT","PDF_DRAWING_BOOK"}:
        page="@page { size: A3 portrait; margin: 0; }"
        frame="width:297mm;min-height:420mm;padding:14mm;grid-template-columns:repeat(12,1fr);gap:5mm;"
        body="font-size:9pt;"
        footer_lr="14mm"
    else:
        page="@page { size: 13.333in 7.5in; margin: 0; }"
        frame="width:338.66mm;min-height:190.5mm;padding:12mm;grid-template-columns:repeat(12,1fr);gap:5mm;"
        body="font-size:12pt;"
        footer_lr="12mm"
    return f"""
{page}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;font-family:'Noto Sans KR','Malgun Gothic',Arial,sans-serif;background:#e9e7e1;color:#151515;{body};-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.page{{{frame}display:grid;background:#f8f7f2;page-break-after:always;position:relative;overflow:hidden;align-content:start}}
.page:last-child{{page-break-after:auto}}
.header{{grid-column:1/-1;min-height:28mm;border-top:1.1mm solid #151515;border-bottom:.25mm solid #b6b1a6;padding:4mm 0 4.5mm;display:flex;justify-content:space-between;align-items:end}}
.header-left{{max-width:80%}}
.kicker{{font-size:.70em;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:#c86435}}
.title{{font-size:2.15em;font-weight:700;letter-spacing:-.035em;line-height:1.15;margin:1.3mm 0 0;max-width:100%}}
.subtitle{{font-size:.9em;color:#555;margin-top:1.2mm}}
.meta{{font-size:.70em;line-height:1.45;text-align:right;color:#777;white-space:nowrap}}
.mode-chip{{display:inline-block;background:#151515;color:#fff;padding:1.2mm 2.2mm;font-size:.66em;font-weight:700;letter-spacing:.10em}}
.argument-line{{grid-column:1/-1;margin-top:1.5mm;font-size:.72em;color:#555;letter-spacing:.01em}}
.primary{{grid-column:1/10;min-height:255mm}}
.support{{grid-column:10/-1;display:flex;flex-direction:column;gap:5mm;padding-top:1mm}}
.card{{border-top:.35mm solid #151515;padding-top:3mm}}
.card.soft{{border-top:.25mm solid #b6b1a6}}
.card-label{{font-size:.66em;font-weight:700;letter-spacing:.10em;color:#c86435;margin-bottom:1.2mm}}
.card-body{{font-size:.82em;line-height:1.55;color:#444}}
.source-frame{{width:100%;height:100%;min-height:120mm;background:#fff;border:.22mm solid #d7d4cb;display:flex;align-items:center;justify-content:center;overflow:hidden;position:relative}}
.source-frame::after{{content:'';position:absolute;inset:0;pointer-events:none;box-shadow:inset 0 0 0 .15mm rgba(21,21,21,.025)}}
.source-img{{width:100%;height:100%;object-fit:contain;display:block}}
.missing{{width:100%;height:100%;min-height:80mm;background:#f4e8e4;border:.45mm dashed #9b4b42;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3mm;color:#7d4d48;text-align:center;padding:8mm}}
.missing strong{{font-size:.9em;letter-spacing:.10em;color:#9b4b42}}
.missing span{{font-size:.72em;line-height:1.45;max-width:70%}}
.bound-file{{padding:10mm;text-align:center;font-size:.78em;color:#555}}
.question{{font-size:1.15em;font-weight:700;letter-spacing:-.02em;line-height:1.25;margin:0 0 2mm}}
.tech{{font-size:.70em;line-height:1.45;color:#666;margin-top:1.5mm}}
.footer{{position:absolute;bottom:6mm;left:{footer_lr};right:{footer_lr};border-top:.2mm solid #b6b1a6;padding-top:2mm;font-size:.60em;color:#777;display:flex;justify-content:space-between}}
.page-no{{font-weight:700;color:#151515}}
.a3-body{{grid-column:1/-1;display:grid;grid-template-columns:repeat(12,1fr);gap:5mm;margin-top:7mm}}
.a3-body.layout-hero .visual{{grid-column:1/-1;min-height:270mm}}
.a3-body.layout-hero .notes{{grid-column:1/-1;display:grid;grid-template-columns:repeat(3,1fr);gap:5mm}}
.a3-body.layout-wide .visual{{grid-column:1/-1;min-height:245mm}}
.a3-body.layout-wide .notes{{grid-column:1/-1;display:grid;grid-template-columns:2fr 1fr 1fr;gap:5mm}}
.a3-body.layout-technical_large .visual{{grid-column:1/10;min-height:300mm}}
.a3-body.layout-technical_large .notes{{grid-column:10/-1;display:flex;flex-direction:column;gap:5mm}}
.a3-body.layout-diagram .visual{{grid-column:1/9;min-height:275mm}}
.a3-body.layout-diagram .notes{{grid-column:9/-1;display:flex;flex-direction:column;gap:5mm}}
.a3-body.layout-technical .visual{{grid-column:1/10;min-height:285mm}}
.a3-body.layout-technical .notes{{grid-column:10/-1;display:flex;flex-direction:column;gap:5mm}}
.board-grid{{grid-column:1/-1;display:grid;grid-template-columns:repeat(12,1fr);grid-template-rows:176mm 102mm 126mm 126mm;gap:6mm;align-content:start;margin-top:6mm}}
.board-item{{display:flex;flex-direction:column;min-width:0;min-height:0}}
.board-item.slot-1{{grid-column:1/9;grid-row:1}}
.board-item.slot-2{{grid-column:9/13;grid-row:1}}
.board-item.slot-3{{grid-column:1/5;grid-row:2}}
.board-item.slot-4{{grid-column:5/9;grid-row:2}}
.board-item.slot-5{{grid-column:9/13;grid-row:2}}
.board-item.slot-6{{grid-column:1/7;grid-row:3}}
.board-item.slot-7{{grid-column:7/13;grid-row:3}}
.board-item.slot-8{{grid-column:1/7;grid-row:4}}
.board-item.slot-9{{grid-column:7/13;grid-row:4}}
.board-item:nth-child(n+10){{display:none}}
.board-item .source-frame{{flex:1;min-height:0}}
.board-item.slot-1 .source-frame{{min-height:135mm}}
.board-caption{{display:flex;justify-content:space-between;gap:4mm;align-items:flex-start;margin-top:2mm}}
.board-caption .mode{{font-size:.65em;font-weight:700;letter-spacing:.08em;color:#c86435}}
.board-caption .claim{{font-size:.78em;font-weight:600;line-height:1.35;max-width:76%}}
.sheet-index{{grid-column:1/-1;margin-top:10mm}}
.sheet-titlebar{{grid-column:1/-1;display:grid;grid-template-columns:1fr auto;align-items:end;border-bottom:.35mm solid #151515;padding-bottom:3mm;margin-bottom:5mm}}
.sheet-title{{font-size:1.55em;font-weight:700;letter-spacing:-.03em}}
.sheet-meta{{font-size:.68em;color:#666;text-align:right}}
table{{border-collapse:collapse;width:100%;font-size:.78em;background:#fff}}
th{{font-size:.72em;letter-spacing:.08em;text-transform:uppercase;color:#666}}
th,td{{border-bottom:.2mm solid #d7d4cb;padding:3mm 2mm;text-align:left;vertical-align:top}}
tr:first-child th{{border-top:.35mm solid #151515}}
"""
def render_a3_report(package, manifest, outdir):
    pages=[]
    total=len(manifest["items"])
    for item in manifest["items"]:
        tech=", ".join(item.get("recommended_techniques") or [])
        role=str(item.get("layout_role") or "TECHNICAL").lower()
        source_meta=item.get("source_meta") or {}
        source_note=source_meta.get("kind") or "NONE"
        if source_meta.get("width_px"):
            source_note += f" · {source_meta.get('width_px')}×{source_meta.get('height_px')} px"
        pages.append(f"""
<section class="page">
  <header class="header">
    <div class="header-left">
      <div class="kicker">ARCHITECTURE COMPETITION · {esc(item["mode"])}</div>
      <div class="title">{esc(short_title(item["mode"],item["question"]))}</div>
      <div class="subtitle">{esc(item["question"])}</div>
    </div>
    <div class="meta"><span class="page-no">{item["order"]:02d}</span> / {total:02d}<br>A3 REPORT</div>
  </header>
  <div class="a3-body layout-{esc(role)}">
    <div class="visual"><div class="source-frame">{source_view(item)}</div></div>
    <div class="notes">
      <div class="card">
        <div class="card-label">REPRESENTATION</div>
        <div class="card-body">{esc(tech)}</div>
      </div>
      <div class="card soft">
        <div class="card-label">SOURCE</div>
        <div class="card-body">{esc(item.get("source_required"))}<br><span style="color:#8a8a8a">{esc(source_note)}</span></div>
      </div>
      <div class="card soft">
        <div class="card-label">PRODUCTION</div>
        <div class="card-body">{esc(item.get("production_path"))}</div>
      </div>
    </div>
  </div>
  <footer class="footer">
    <span>{esc(item["id"])} · {esc(item["binding_status"])}</span>
    <span>{esc(manifest.get("status"))}</span>
  </footer>
</section>""")
    write_html(outdir/"report.html", package, "\n".join(pages), "A3_REPORT")
def render_a1_board(package, manifest, outdir):
    cards=[]
    for idx,item in enumerate(manifest["items"],1):
        role=str(item.get("layout_role") or "TECHNICAL").lower()
        claim=short_title(item.get("mode"),item.get("question") or "")
        cards.append(f"""
<div class="board-item role-{esc(role)} slot-{idx}">
  <div class="source-frame">{source_view(item)}</div>
  <div class="board-caption">
    <span class="mode">{esc(item["mode"])}</span>
    <span class="claim">{esc(claim)}</span>
  </div>
  <div class="tech">{esc(" · ".join(item.get("recommended_techniques") or []))}</div>
</div>""")
    title=package.get("focus") or "DESIGN ARGUMENT"
    competition=(package.get("brief") or {}).get("competition_name") or "ARCHITECTURE COMPETITION"
    body=f"""
<section class="page">
<header class="header">
 <div class="header-left">
   <div class="kicker">{esc(competition)}</div>
   <div class="title">{esc(title)}</div>
   <div class="subtitle">SITE → IDEA → SPATIAL PROOF → EXPERIENCE</div>
 </div>
 <div class="meta">A1 BOARD<br>{len(manifest["items"])} VISUAL ARGUMENTS</div>
</header>
<div class="argument-line">Drawing hierarchy is source-bound; measured geometry remains authoritative.</div>
<div class="board-grid">{''.join(cards)}</div>
<footer class="footer"><span>ARCHIGROW · SOURCE-BOUND REPRESENTATION</span><span>{esc(manifest["status"])}</span></footer>
</section>"""
    write_html(outdir/"board.html",package,body,"A1_BOARD")
def render_drawing_book(package, manifest, outdir):
    rows=[]
    for item in manifest["items"]:
        meta=item.get("source_meta") or {}
        source_desc=meta.get("kind") or "NONE"
        rows.append(
            f"<tr><td>{item['order']:02d}</td><td><strong>{esc(item['mode'])}</strong><br><span style='color:#777'>{esc(item['question'])}</span></td>"
            f"<td>{esc(item['id'])}</td><td>{esc(source_desc)}</td><td>{esc(item['binding_status'])}</td></tr>"
        )
    index=f"""
<section class="page">
<header class="header">
  <div class="header-left"><div class="kicker">PDF DRAWING BOOK</div><div class="title">도면 목록 / Drawing Index</div></div>
  <div class="meta">{len(manifest["items"])} SHEETS</div>
</header>
<div class="sheet-index"><table><thead><tr><th>No.</th><th>Drawing</th><th>ID</th><th>Source</th><th>Status</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<footer class="footer"><span>Measured drawing first · vector preferred</span><span>{esc(manifest["status"])}</span></footer>
</section>"""
    sheets=[index]
    total=len(manifest["items"])
    for item in manifest["items"]:
        meta=item.get("source_meta") or {}
        source_desc=meta.get("kind") or "NONE"
        if meta.get("width_px"):
            source_desc+=f" · {meta.get('width_px')}×{meta.get('height_px')} px"
        sheets.append(f"""
<section class="page">
<div class="sheet-titlebar">
  <div>
    <div class="kicker">{esc(item['mode'])} · {esc(item['id'])}</div>
    <div class="sheet-title">{esc(short_title(item['mode'],item['question']))}</div>
  </div>
  <div class="sheet-meta">SHEET {item['order']:02d}/{total:02d}<br>{esc(source_desc)}</div>
</div>
<main style="grid-column:1/-1;min-height:330mm"><div class="source-frame">{source_view(item)}</div></main>
<footer class="footer"><span>{esc(item['binding_status'])} · {esc(item['question'])}</span><span>{item['order']:02d}</span></footer>
</section>""")
    write_html(outdir/"drawing-book.html",package,"\n".join(sheets),"PDF_DRAWING_BOOK")
def render_ppt_plan(package, manifest, outdir):
    minutes=((package.get("brief") or {}).get("presentation_minutes"))
    default_seconds=45
    slide_count=len(manifest["items"])
    seconds=(float(minutes)*60/slide_count) if minutes and slide_count else default_seconds
    slides=[]
    for item in manifest["items"]:
        slides.append({
            "slide_no":item["order"],
            "claim":short_title(item["mode"],item["question"]),
            "detail":item["question"],
            "mode":item["mode"],
            "primary_visual_source":item["source_path"],
            "binding_status":item["binding_status"],
            "recommended_techniques":item["recommended_techniques"],
            "speaker_note_evidence":item["source_required"],
            "time_seconds":round(seconds,1)
        })
    (outdir/"slides.json").write_text(json.dumps({"slides":slides},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    ps = make_ppt_ps(slides, outdir/"competition-report.pptx")
    (outdir/"BUILD_PPTX.ps1").write_text(ps,encoding="utf-8-sig")

def make_ppt_ps(slides, pptx_path):
    data=json.dumps(slides,ensure_ascii=False).replace("'", "''")
    target=str(pptx_path).replace("'","''")
    return f"""$ErrorActionPreference='Stop'
$slides = @'
{data}
'@ | ConvertFrom-Json
function RGBi([int]$r,[int]$g,[int]$b) {{ return $r + (256*$g) + (65536*$b) }}
function AddText($slide,$x,$y,$w,$h,$text,$size,$bold,$color,$font='Noto Sans KR') {{
  $tb=$slide.Shapes.AddTextbox(1,$x,$y,$w,$h)
  $tb.TextFrame.MarginLeft=0; $tb.TextFrame.MarginRight=0; $tb.TextFrame.MarginTop=0; $tb.TextFrame.MarginBottom=0
  $tb.TextFrame.TextRange.Text=[string]$text
  $tb.TextFrame.TextRange.Font.Name=$font
  $tb.TextFrame.TextRange.Font.Size=$size
  $tb.TextFrame.TextRange.Font.Bold=($(if($bold){{-1}}else{{0}}))
  $tb.TextFrame.TextRange.Font.Color.RGB=$color
  return $tb
}}
$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = [Microsoft.Office.Core.MsoTriState]::msoTrue
$pres = $ppt.Presentations.Add()
$pres.PageSetup.SlideWidth = 960
$pres.PageSetup.SlideHeight = 540
$total=@($slides).Count
foreach($s in $slides) {{
  $slide = $pres.Slides.Add($pres.Slides.Count+1, 12)

  $bg=$slide.Shapes.AddShape(1,0,0,960,540)
  $bg.Fill.Solid(); $bg.Fill.ForeColor.RGB=(RGBi 248 247 242)
  $bg.Line.Visible=0
  $bg.ZOrder(1)

  $accent=$slide.Shapes.AddShape(1,48,34,42,5)
  $accent.Fill.Solid(); $accent.Fill.ForeColor.RGB=(RGBi 200 100 53)
  $accent.Line.Visible=0

  AddText $slide 104 27 300 20 ([string]$s.mode) 11 $true (RGBi 200 100 53) | Out-Null
  $title=AddText $slide 48 58 864 66 ([string]$s.claim) 27 $true (RGBi 21 21 21)

  $visualFrame=$slide.Shapes.AddShape(1,48,142,690,318)
  $visualFrame.Fill.Solid(); $visualFrame.Fill.ForeColor.RGB=(RGBi 255 255 255)
  $visualFrame.Line.ForeColor.RGB=(RGBi 215 212 203)
  $visualFrame.Line.Weight=0.75

  $sourceOk=$false
  if($s.binding_status -eq 'BOUND' -and $s.primary_visual_source -and (Test-Path $s.primary_visual_source)) {{
    try {{
      $pic=$slide.Shapes.AddPicture($s.primary_visual_source,0,-1,0,0,-1,-1)
      $maxW=684; $maxH=312
      $scale=[Math]::Min($maxW/$pic.Width,$maxH/$pic.Height)
      if($scale -gt 1) {{ $scale=1 }}
      $pic.Width=$pic.Width*$scale
      $pic.Height=$pic.Height*$scale
      $pic.Left=48+(690-$pic.Width)/2
      $pic.Top=142+(318-$pic.Height)/2
      $sourceOk=$true
    }} catch {{
      $sourceOk=$false
    }}
  }}
  if(-not $sourceOk) {{
    $visualFrame.Fill.ForeColor.RGB=(RGBi 244 232 228)
    $visualFrame.Line.ForeColor.RGB=(RGBi 155 75 66)
    AddText $slide 88 270 610 40 ('MISSING / UNSUPPORTED SOURCE · '+[string]$s.mode) 16 $true (RGBi 155 75 66) | Out-Null
  }}

  $sideLine=$slide.Shapes.AddShape(1,765,142,1,318)
  $sideLine.Fill.Solid(); $sideLine.Fill.ForeColor.RGB=(RGBi 182 177 166); $sideLine.Line.Visible=0
  AddText $slide 786 146 126 18 'REPRESENTATION' 9 $true (RGBi 200 100 53) | Out-Null
  $tech=([string]::Join(' · ',@($s.recommended_techniques)))
  AddText $slide 786 169 126 88 $tech 12 $false (RGBi 68 68 68) | Out-Null
  AddText $slide 786 270 126 18 'WHY / EVIDENCE' 9 $true (RGBi 200 100 53) | Out-Null
  AddText $slide 786 293 126 62 ([string]$s.detail) 10 $false (RGBi 68 68 68) | Out-Null
  AddText $slide 786 370 126 18 'SOURCE' 9 $true (RGBi 200 100 53) | Out-Null
  AddText $slide 786 393 126 55 ([string]$s.speaker_note_evidence) 9 $false (RGBi 85 85 85) | Out-Null

  $footer=$slide.Shapes.AddShape(1,48,496,864,1)
  $footer.Fill.Solid(); $footer.Fill.ForeColor.RGB=(RGBi 182 177 166); $footer.Line.Visible=0
  AddText $slide 48 505 250 16 ('ARCHIGROW · '+[string]$s.binding_status) 9 $false (RGBi 119 119 119) | Out-Null
  AddText $slide 720 505 130 16 (([string]$s.time_seconds)+' sec') 9 $false (RGBi 119 119 119) | Out-Null
  AddText $slide 866 503 46 18 (([string]$s.slide_no).PadLeft(2,'0')+'/'+([string]$total).PadLeft(2,'0')) 10 $true (RGBi 21 21 21) | Out-Null
}}
$pres.SaveAs('{target}')
$pres.Close()
$ppt.Quit()
"""
def write_html(path, package, body, delivery):
    title=esc((package.get("brief") or {}).get("competition_name") or "ArchiGrow Competition Output")
    doc=f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{css_for(delivery)}</style></head><body>{body}</body></html>"""
    path.write_text(doc,encoding="utf-8")

def write_common(package, manifest, outdir):
    (outdir/"build-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    template={"bindings":{x["id"]:{"path":"","source_role":x["source_required"]} for x in manifest["items"]}}
    (outdir/"source-bindings.template.json").write_text(json.dumps(template,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    validation={
        "delivery":manifest["delivery"],
        "required_checks":manifest["profile"].get("validation",[]),
        "source_gaps":[x["id"] for x in manifest["items"] if not x["source_exists"]],
        "verified":False,
        "rule":"Actual rendered output must be inspected; this manifest alone is never a PASS."
    }
    (outdir/"validation.json").write_text(json.dumps(validation,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def main():
    p=argparse.ArgumentParser(description="Build result-specific architecture competition output shells from a recommendation package.")
    p.add_argument("--package",required=True,help="JSON package emitted by ARCHIGROW_COMPETITION_REPORT.py --json")
    p.add_argument("--sources",default="",help="Optional source binding JSON.")
    p.add_argument("--out-dir",required=True)
    args=p.parse_args()

    package=read_json(args.package)
    profiles=read_json(PROFILES)["profiles"]
    quality_registry=read_json(QUALITY)
    delivery=package.get("delivery")
    if delivery not in profiles:
        raise SystemExit(f"Unsupported delivery: {delivery}")
    outdir=Path(args.out_dir).resolve()
    outdir.mkdir(parents=True,exist_ok=True)
    quality={
        "registry_id":quality_registry.get("registry_id"),
        "tokens":quality_registry.get("tokens",{}),
        "delivery":quality_registry.get(delivery,{}),
        "mode_emphasis":quality_registry.get("mode_emphasis",{})
    }
    manifest=build_manifest(package,profiles[delivery],load_sources(args.sources),quality=quality)
    write_common(package,manifest,outdir)
    if delivery=="A1_BOARD":
        render_a1_board(package,manifest,outdir)
    elif delivery=="A3_REPORT":
        render_a3_report(package,manifest,outdir)
    elif delivery=="PPT":
        render_ppt_plan(package,manifest,outdir)
    elif delivery=="PDF_DRAWING_BOOK":
        render_drawing_book(package,manifest,outdir)
    print(json.dumps({"ok":True,"delivery":delivery,"status":manifest["status"],"out_dir":str(outdir)},ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
