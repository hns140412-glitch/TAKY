#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "DOMAIN" / "ARCHITECTURE_COMPETITION_REPRESENTATION_REGISTRY.json"

KEYWORDS = {
    "CONTEXT": ["site", "context", "urban", "city", "landscape", "대지", "맥락", "도시", "입지"],
    "CONCEPT": ["concept", "mass", "form", "idea", "conceptual", "개념", "매스", "형태", "아이디어"],
    "PROGRAM": ["program", "zoning", "adjacency", "프로그램", "조닝", "용도"],
    "CIRCULATION": ["circulation", "arrival", "movement", "access", "flow", "동선", "진입", "접근"],
    "PLAN": ["plan", "function", "layout", "floor", "평면", "기능", "배치"],
    "SECTION": ["section", "level", "atrium", "topography", "vertical", "단면", "레벨", "아트리움", "고저차"],
    "ELEVATION": ["elevation", "facade", "frontage", "skin", "입면", "파사드", "외피"],
    "AXONOMETRIC": ["axon", "exploded", "assembly", "layer", "액소", "아이소", "분해"],
    "PERFORMANCE": ["sun", "daylight", "wind", "energy", "passive", "water", "환경", "채광", "일사", "바람", "에너지"],
    "EXPERIENCE": ["experience", "atmosphere", "interior", "public life", "경험", "분위기", "투시", "내부"],
    "TECHNICAL": ["structure", "parking", "area", "egress", "envelope", "feasibility", "구조", "주차", "면적", "피난", "기술"],
}

SOURCE_REQUIREMENTS = {
    "CONTEXT": "verified site/base map + context data",
    "CONCEPT": "approved design intent + mass/form source",
    "PROGRAM": "verified program schedule + plan/model",
    "CIRCULATION": "verified access/core/route geometry",
    "PLAN": "verified CAD/BIM plan",
    "SECTION": "verified section/levels/model",
    "ELEVATION": "verified facade/elevation/model",
    "AXONOMETRIC": "verified 3D/model or reconstructable geometry",
    "PERFORMANCE": "verified geometry + actual analysis inputs/results where numeric",
    "EXPERIENCE": "verified 3D/model + camera intent",
    "TECHNICAL": "verified structure/parking/area/code data",
}

PRODUCTION = {
    "CONTEXT": "GIS/CAD -> cleaned vector/SVG -> report",
    "CONCEPT": "CAD/3D -> diagram vector/SVG -> report",
    "PROGRAM": "plan/model -> semantic color overlay -> SVG",
    "CIRCULATION": "plan/section -> route hierarchy overlay -> SVG",
    "PLAN": "DWG/DXF -> clean layers/lineweights -> canonical SVG",
    "SECTION": "DWG/DXF/3D -> section vector -> optional rendered derivative",
    "ELEVATION": "DWG/DXF/3D -> elevation vector -> material/shadow derivative",
    "AXONOMETRIC": "verified 3D -> orthographic/cutaway -> vector/raster derivative",
    "PERFORMANCE": "analysis output -> normalized diagram -> report",
    "EXPERIENCE": "verified 3D -> render -> geometry-drift check",
    "TECHNICAL": "CAD/Excel/BIM -> verified metrics/diagram -> report",
}
def load_registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))

def load_brief(path):
    if not path:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    return json.loads(p.read_text(encoding="utf-8"))

def normalize_project_type(value):
    mapping = {
        "default": "DEFAULT_COMPETITION",
        "urban": "URBAN_CIVIC",
        "urban_civic": "URBAN_CIVIC",
        "civic": "URBAN_CIVIC",
        "housing": "HOUSING",
        "landscape": "LANDSCAPE",
        "technical": "TECHNICAL_FEASIBILITY",
        "technical_feasibility": "TECHNICAL_FEASIBILITY",
    }
    return mapping.get(value.lower(), "DEFAULT_COMPETITION")

def infer_modes(text):
    lower = (text or "").lower()
    scores = {}
    for mode, words in KEYWORDS.items():
        score = sum(1 for word in words if word.lower() in lower)
        if score:
            scores[mode] = score
    return [mode for mode, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))]

def unique(items):
    out = []
    for item in items:
        if item not in out:
            out.append(item)
    return out

def select_styles(sequence, delivery):
    styles = []
    if any(mode in sequence for mode in ("PLAN", "SECTION", "ELEVATION", "TECHNICAL")):
        styles.append("MONO_ACCENT")
    if any(mode in sequence for mode in ("CONCEPT", "PROGRAM", "CIRCULATION", "PERFORMANCE")):
        styles.append("DIAGRAM_SYSTEM")
    if any(mode in sequence for mode in ("SECTION", "EXPERIENCE")):
        styles.append("SOFT_RENDERED")
    if "CONCEPT" in sequence and delivery in {"A1_BOARD", "A3_REPORT", "PPT"}:
        styles.append("CONCEPT_COLLAGE")
    return unique(styles)

def build_package(args, registry):
    brief = load_brief(getattr(args, "brief_file", ""))
    sequence_key = normalize_project_type(args.project_type)
    sequence = list(registry["story_sequences"][sequence_key])
    inferred = infer_modes(args.focus)

    brief_delivery = brief.get("delivery") if brief else None
    delivery_key = brief_delivery or args.delivery

    if inferred:
        prioritized = [m for m in inferred if m in registry["representation_modes"]]
        sequence = unique(prioritized + sequence)

    required = []
    if args.required_modes:
        required.extend(x.strip().upper() for x in args.required_modes.split(",") if x.strip())
    if brief:
        required.extend(x.strip().upper() for x in brief.get("mandatory_modes", []) if isinstance(x, str))
        for drawing in brief.get("mandatory_drawings", []):
            mode = str(drawing.get("mode") or "").upper()
            if mode:
                required.append(mode)
    required = [x for x in required if x in registry["representation_modes"]]
    if required:
        sequence = unique(required + sequence)

    brief_verified = bool(brief.get("verified")) if brief is not None else bool(args.brief_verified)
    content_frozen = bool(args.content_frozen or (brief and brief.get("content_frozen")) or (brief and brief.get("no_post_submission_enhancement")))
    delivery = registry["delivery_profiles"].get(delivery_key, registry["delivery_profiles"]["A3_REPORT"])
    package = {
        "status": "CANDIDATE" if brief_verified else "BRIEF_UNVERIFIED",
        "project_type": sequence_key,
        "delivery": delivery_key,
        "focus": args.focus,
        "brief_verified": brief_verified,
        "content_frozen": content_frozen,
        "brief": brief,
        "delivery_profile": delivery,
        "hard_rules": registry["hard_rules"],
        "items": [],
    }

    for order, mode in enumerate(sequence, 1):
        spec = registry["representation_modes"][mode]
        package["items"].append({
            "order": order,
            "mode": mode,
            "question": spec["goal"],
            "recommended_techniques": spec["techniques"][:3],
            "best_for": spec["best_for"],
            "source_required": SOURCE_REQUIREMENTS.get(mode, "verified project source"),
            "production_path": PRODUCTION.get(mode, "verified source -> representation derivative"),
            "avoid": spec["avoid"],
        })

    if content_frozen:
        package["freeze_guard"] = "No post-freeze drawing/content enhancement unless the competition brief explicitly allows it."

    if brief:
        package["submission_constraints"] = {
            key: brief.get(key)
            for key in (
                "competition_name", "phase", "panel_size", "panel_count", "page_size", "page_count",
                "anonymity", "color_constraints", "file_constraints", "presentation_minutes", "mandatory_drawings"
            )
            if brief.get(key) is not None
        }

    package["style_profiles"] = [
        {"id": style_id, **registry["visual_styles"][style_id]}
        for style_id in select_styles(sequence, delivery_key)
        if style_id in registry.get("visual_styles", {})
    ]
    package["quality_gates"] = registry["quality_gates"]
    return package

def as_markdown(package):
    lines = []
    lines.append("# ArchiGrow 설계경기 보고서 표현 패키지")
    lines.append("")
    lines.append(f"- 상태: **{package['status']}**")
    lines.append(f"- 유형: {package['project_type']}")
    lines.append(f"- 결과물: {package['delivery']}")
    if package.get("focus"):
        lines.append(f"- 핵심 의도: {package['focus']}")
    lines.append("")
    if package["status"] == "BRIEF_UNVERIFIED":
        lines.append("> 공모 지침 미검증: 아래 구성은 후보안이며 제출 적합성 PASS가 아닙니다.")
        lines.append("")
    if package.get("freeze_guard"):
        lines.append(f"> 제출동결: {package['freeze_guard']}")
        lines.append("")
    if package.get("submission_constraints"):
        lines.append("## 공모 지침 반영")
        for key, value in package["submission_constraints"].items():
            lines.append(f"- {key}: {value}")
        lines.append("")

    if package.get("style_profiles"):
        lines.append("## 권장 그래픽 시스템")
        for style in package["style_profiles"]:
            lines.append(f"### {style['id']}")
            lines.append(f"- 목적: {style['goal']}")
            lines.append(f"- 베이스: {style['base']}")
            lines.append(f"- 강조: {style['accent']}")
            lines.append(f"- 선 체계: {', '.join(style['line_roles'])}")
            lines.append(f"- 깊이: {style['depth']}")
            lines.append(f"- 엔투라지: {style['entourage']}")
            lines.append(f"- 피하기: {', '.join(style['avoid'])}")
            lines.append("")

    lines.append("## 권장 도면/표현 순서")
    lines.append("")
    for item in package["items"]:
        tech = ", ".join(item["recommended_techniques"])
        lines.append(f"### {item['order']}. {item['mode']}")
        lines.append(f"- 질문: {item['question']}")
        lines.append(f"- 표현: {tech}")
        lines.append(f"- 원천: {item['source_required']}")
        lines.append(f"- 제작: {item['production_path']}")
        lines.append(f"- 피하기: {', '.join(item['avoid'])}")
        lines.append("")

    lines.append("## 최종 검증")
    for key, value in package["quality_gates"].items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)

def parse_args():
    parser = argparse.ArgumentParser(description="Deterministic architecture-competition report representation recommender.")
    parser.add_argument("--project-type", default="default")
    parser.add_argument("--delivery", default="A3_REPORT",
                        choices=["A1_BOARD", "A3_REPORT", "PPT", "PDF_DRAWING_BOOK"])
    parser.add_argument("--focus", default="")
    parser.add_argument("--required-modes", default="")
    parser.add_argument("--brief-verified", action="store_true")
    parser.add_argument("--content-frozen", action="store_true")
    parser.add_argument("--brief-file", default="", help="Normalized competition brief JSON.")
    parser.add_argument("--output", default="", help="Optional output file path.")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()

def main():
    args = parse_args()
    registry = load_registry()
    package = build_package(args, registry)
    rendered = json.dumps(package, ensure_ascii=False, indent=2) if args.json else as_markdown(package)
    if args.output:
        out = Path(args.output)
        if not out.is_absolute():
            out = (Path.cwd() / out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
        print(str(out))
    else:
        print(rendered)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
