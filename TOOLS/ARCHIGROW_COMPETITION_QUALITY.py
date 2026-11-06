#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
QUALITY=ROOT/"DOMAIN"/"ARCHITECTURE_COMPETITION_VISUAL_QUALITY_REGISTRY.json"

MEASURED_MODES={"PLAN","SECTION","ELEVATION","TECHNICAL"}

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

HTML_NAMES={"A1_BOARD":"board.html","A3_REPORT":"report.html","PDF_DRAWING_BOOK":"drawing-book.html"}
def html_min_font_pt(html):
    """Smallest absolute text size in generated print HTML (em resolved against the html/body base size)."""
    base=re.search(r"html,body\{[^}]*font-size:([\d.]+)pt",html)
    base_pt=float(base.group(1)) if base else 12.0
    unit={"pt":1.0,"px":0.75,"mm":72/25.4}
    sizes=[]
    for v,u in re.findall(r"font-size:\s*([\d.]+)(em|pt|px|mm)",html):
        sizes.append(float(v)*base_pt if u=="em" else float(v)*unit[u])
    return min(sizes) if sizes else None

def legibility(build_dir,delivery,spec):
    """Learned gate PRINT_LEGIBILITY_FAIL (ArchiGrow review mining 2026-09-30 M13/AC-05): ~5pt A3 text failed real review."""
    name=HTML_NAMES.get(delivery)
    mins=[v*72/25.4 for v in (spec.get("type_mm") or {}).values()]+[float(v) for v in (spec.get("type_pt") or {}).values()]
    if not name or not mins or not (Path(build_dir)/name).exists():
        return None,None
    return html_min_font_pt((Path(build_dir)/name).read_text(encoding="utf-8")),min(mins)

def evaluate(build_dir):
    build_dir=Path(build_dir)
    manifest=load(build_dir/"build-manifest.json")
    validation=load(build_dir/"validation.json")
    quality=load(QUALITY)
    delivery=manifest["delivery"]
    spec=quality.get(delivery,{})
    errors=[]
    warnings=[]
    ppt_claims={}
    slides_path=build_dir/"slides.json"
    if delivery=="PPT" and slides_path.exists():
        try:
            slides=load(slides_path).get("slides",[])
            ppt_claims={int(s.get("slide_no")):str(s.get("claim") or "") for s in slides}
        except Exception:
            ppt_claims={}

    metrics={
        "source_count":len(manifest.get("items",[])),
        "source_gap_count":len(validation.get("source_gaps",[])),
        "vector_count":0,
        "raster_count":0,
        "low_resolution_count":0,
        "overlong_claim_count":0
    }

    if validation.get("source_gaps"):
        errors.append("SOURCE_GAPS_PRESENT")
    render=(validation.get("render_evidence") or {})
    if render and render.get("mechanical_render_pass") is not True:
        errors.append("MECHANICAL_RENDER_NOT_PASS")
    if not render:
        errors.append("RENDER_EVIDENCE_MISSING")

    for item in manifest.get("items",[]):
        meta=item.get("source_meta") or {}
        kind=meta.get("kind")
        if kind=="VECTOR":
            metrics["vector_count"]+=1
        elif kind=="RASTER":
            metrics["raster_count"]+=1

        claim=(ppt_claims.get(int(item.get("order") or 0)) if delivery=="PPT" else None) or str(item.get("question") or "")
        if delivery=="PPT" and len(claim)>int(spec.get("claim_max_chars",80)):
            warnings.append(f"OVERLONG_CLAIM:{item['id']}")
            metrics["overlong_claim_count"]+=1
        if delivery=="A3_REPORT" and len(claim)>160:
            warnings.append(f"OVERLONG_PAGE_TITLE:{item['id']}")
            metrics["overlong_claim_count"]+=1

        if kind=="RASTER":
            w=meta.get("width_px") or 0
            h=meta.get("height_px") or 0
            role=item.get("layout_role")
            minimum=0
            if delivery=="A1_BOARD":
                minimum=(spec.get("raster_min_px") or {}).get("hero_width" if role=="HERO" else "standard_width",0)
            elif delivery=="A3_REPORT":
                minimum=(spec.get("raster_min_px") or {}).get("primary_width",0)
            elif delivery=="PPT":
                minimum=(spec.get("raster_min_px") or {}).get("primary_width",0)
                min_h=(spec.get("raster_min_px") or {}).get("primary_height",0)
                if min_h and h<min_h:
                    warnings.append(f"RASTER_HEIGHT_LOW:{item['id']}:{h}<{min_h}")
            if minimum and w<minimum:
                errors.append(f"RASTER_WIDTH_LOW:{item['id']}:{w}<{minimum}")
                metrics["low_resolution_count"]+=1

        if delivery=="PDF_DRAWING_BOOK" and item.get("mode") in MEASURED_MODES and kind=="RASTER":
            warnings.append(f"MEASURED_DRAWING_RASTER:{item['id']}")
        if kind=="RASTER_UNINSPECTED":
            errors.append(f"RASTER_UNVERIFIABLE:{item['id']}:{meta.get('reason')}")
        if kind in {"NONE","OTHER"} and item.get("source_exists"):
            warnings.append(f"SOURCE_KIND_UNVERIFIED:{item['id']}")

    min_pt,floor_pt=legibility(build_dir,delivery,spec)
    metrics["min_font_pt"]=round(min_pt,2) if min_pt else None
    if min_pt is not None and min_pt+0.05<floor_pt:
        errors.append(f"PRINT_LEGIBILITY_FAIL:min_font_{min_pt:.2f}pt<{floor_pt:.2f}pt")

    if delivery=="A1_BOARD":
        primary=sum(1 for x in manifest.get("items",[]) if x.get("layout_role") in {"HERO","TECHNICAL_LARGE","HERO_SECONDARY","WIDE"})
        max_primary=int((spec.get("density") or {}).get("max_primary_blocks",6))
        if primary>max_primary:
            warnings.append(f"A1_PRIMARY_BLOCK_DENSITY:{primary}>{max_primary}")

    hard_pass=not errors
    status="QUALITY_GATE_PASS" if hard_pass and not warnings else ("QUALITY_GATE_WARN" if hard_pass else "QUALITY_GATE_FAIL")
    result={
        "version":"ARCHCOMP_VISUAL_QUALITY_GATE_V1",
        "delivery":delivery,
        "status":status,
        "hard_pass":hard_pass,
        "errors":errors,
        "warnings":warnings,
        "metrics":metrics,
        "visual_review_required":True,
        "rule":"Mechanical quality checks cannot replace final visual/source comparison of the rendered artifact."
    }
    (build_dir/"quality-report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--build-dir",required=True)
    args=p.parse_args()
    result=evaluate(args.build_dir)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result["hard_pass"] else 2

if __name__=="__main__":
    raise SystemExit(main())
