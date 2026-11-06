#!/usr/bin/env python3
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "TOOLS" / "ARCHIGROW_COMPETITION_REPORT.py"
REGISTRY = ROOT / "DOMAIN" / "ARCHITECTURE_COMPETITION_REPRESENTATION_REGISTRY.json"

spec = importlib.util.spec_from_file_location("archcomp", TOOL)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class Args:
    project_type = "urban_civic"
    delivery = "A3_REPORT"
    focus = "도시 맥락과 진입 동선, 채광, 주차와 면적 검토"
    required_modes = ""
    brief_verified = False
    content_frozen = False
    brief_file = ""
    json = False

def main():
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert "SECTION" in reg["representation_modes"]
    assert "BRIEF" in reg["quality_gates"]

    package = mod.build_package(Args(), reg)
    modes = [item["mode"] for item in package["items"]]
    assert package["status"] == "BRIEF_UNVERIFIED"
    assert modes[0] in {"CONTEXT", "CIRCULATION", "PERFORMANCE", "TECHNICAL"}
    assert "CONTEXT" in modes
    assert "CIRCULATION" in modes
    assert "PERFORMANCE" in modes
    assert "TECHNICAL" in modes
    assert len(modes) == len(set(modes))

    Args.brief_verified = True
    Args.content_frozen = True
    package2 = mod.build_package(Args(), reg)
    assert package2["status"] == "CANDIDATE"
    assert "freeze_guard" in package2

    brief_path = Path(tempfile.gettempdir()) / "archcomp-brief-test.json"
    brief_path.write_text(json.dumps({
        "competition_name": "TEST",
        "verified": True,
        "delivery": "A1_BOARD",
        "mandatory_modes": ["PLAN", "SECTION", "ELEVATION"],
        "content_frozen": True,
        "mandatory_drawings": [{"name": "배치도", "mode": "CONTEXT", "scale": "1:500"}]
    }, ensure_ascii=False), encoding="utf-8")
    Args.brief_file = str(brief_path)
    Args.brief_verified = False
    Args.content_frozen = False
    package3 = mod.build_package(Args(), reg)
    modes3 = [item["mode"] for item in package3["items"]]
    assert package3["status"] == "CANDIDATE"
    assert package3["delivery"] == "A1_BOARD"
    assert all(mode in modes3 for mode in ["PLAN", "SECTION", "ELEVATION", "CONTEXT"])
    assert "freeze_guard" in package3

    Args.brief_file = ""
    md = mod.as_markdown(package2)
    assert "권장 도면/표현 순서" in md
    assert "최종 검증" in md
    assert "제출동결" in md

    print("PASS: architecture competition representation registry/recommender")

if __name__ == "__main__":
    raise SystemExit(main())
