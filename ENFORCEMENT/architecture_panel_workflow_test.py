#!/usr/bin/env python3
"""Tests for TOOLS/ARCHIGROW_PANEL_WORKFLOW.py (file-producing; no Chrome/PowerPoint/network needed).

Chrome PDF rendering and browser interaction are exercised separately via `demo --render` and Playwright.
PPTX checks are skipped (loudly) only when python-pptx is not installed.
"""
import hashlib
import importlib.util
import json
import re
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "TOOLS" / "ARCHIGROW_PANEL_WORKFLOW.py"
FIX = ROOT / "REFERENCE" / "ARCHCOMP_OUTPUT_BUILD_TEST"

spec = importlib.util.spec_from_file_location("archigrow_panel_workflow", TOOL)
pw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pw)

EXTRACT_TOOL = ROOT / "TOOLS" / "ARCHIGROW_PANEL_SOURCE_EXTRACT.py"
spec_se = importlib.util.spec_from_file_location("archigrow_panel_source_extract", EXTRACT_TOOL)
se = importlib.util.module_from_spec(spec_se)
spec_se.loader.exec_module(se)


def fitz_module():
    try:
        return se._load_fitz()
    except ImportError:
        return None


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fixture_boards(out):
    package = pw.load_package(FIX / "package-A1_BOARD.json")
    bindings, _ = pw.auto_bind(package, FIX / "QUALITY_SOURCES")
    assert len(bindings) == 9, f"expected 9 auto-bound sources, got {len(bindings)}"
    return package, bindings, pw.build_boards(package, bindings, out, demo=True, render=False)


def fake_blocks(n):
    modes = list(pw.NARR_ORDER)
    return [{"block_id": f"{modes[i % len(modes)]}:{i + 1}", "mode": modes[i % len(modes)]} for i in range(n)]


def test_layouts():
    ax, ay, aw, ah = pw.body_area()
    for style_id, fn in pw.LAYOUTS.items():
        for n in range(1, 12):
            seq, rects, labels = fn(fake_blocks(n))
            assert len(seq) == n == len(rects), (style_id, n)
            for (x, y, w, h) in rects:
                assert w > 20 and h > 40, (style_id, n, w, h)
                assert x >= ax - 1e-6 and y >= ay - 1e-6, (style_id, n)
                assert x + w <= ax + aw + 1e-6 and y + h <= ay + ah + 1e-6, (style_id, n)
            for i in range(n):
                for j in range(i + 1, n):
                    a, b = rects[i], rects[j]
                    overlap = a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]
                    assert not overlap, (style_id, n, i, j)
    seq_a, rects_a, _ = pw.layout_gallery(fake_blocks(9))
    seq_b, rects_b, labels_b = pw.layout_narrative(fake_blocks(9))
    assert [round(r[2]) for r in rects_a] != [round(r[2]) for r in rects_b], "styles must differ in composition"
    assert labels_b and {l["stage"] for l in labels_b} <= set(pw.STAGE_ORDER)
    print("layouts: PASS")


def test_boards_and_manifest(out):
    package, bindings, results = fixture_boards(out)
    assert [r["doc"]["board"]["style_id"] for r in results] == pw.STYLE_ORDER
    htmls = []
    for r in results:
        d = Path(r["dir"])
        doc = r["doc"]
        for name in ("board.html", "panel-blocks.json", "build-manifest.json", "validation.json"):
            assert (d / name).exists(), (d, name)
        assert doc["board"]["width_mm"] == 594.0 and doc["board"]["height_mm"] == 841.0
        assert doc["board"]["html_sha256"] == sha(d / "board.html")
        assert doc["source_gaps"] == [], doc["source_gaps"]
        assert len(doc["blocks"]) == 9
        ids = [b["block_id"] for b in doc["blocks"]]
        assert len(ids) == len(set(ids))
        html_text = (d / "board.html").read_text(encoding="utf-8")
        assert "@page{size:594mm 841mm" in html_text
        for b in doc["blocks"]:
            assert b["binding_status"] == "BOUND"
            assert b["source_sha256"] == sha(b["source_path"]), b["block_id"]
            n = b["board_rect_norm"]
            assert 0 <= n["x"] and 0 <= n["y"] and n["x"] + n["w"] <= 1.0001 and n["y"] + n["h"] <= 1.0001, b["block_id"]
            assert f'id="{b["board_anchor"]}"' in html_text
            assert f'data-block-id="{b["block_id"]}"' in html_text
            assert b["source_sha256"] in html_text
            assert b["rect_method"] == "LAYOUT_BY_CONSTRUCTION_EXACT"
        assert 'contenteditable="true"' in html_text  # layout/source text stays editable
        assert "DEMO" in html_text  # synthetic sources are labelled
        htmls.append(html_text)
    assert htmls[0] != htmls[1]
    assert "--accent:#c86435" in htmls[0] and "--accent:#1f7a8c" in htmls[1]
    # block rect sets differ between treatments
    r0 = {b["block_id"]: b["board_rect_norm"] for b in results[0]["doc"]["blocks"]}
    r1 = {b["block_id"]: b["board_rect_norm"] for b in results[1]["doc"]["blocks"]}
    assert r0 != r1
    print("boards+manifest: PASS")
    return package, bindings, results


def test_missing_source_is_gap(out):
    package = pw.load_package(FIX / "package-A1_BOARD.json")
    bindings, _ = pw.auto_bind(package, FIX / "QUALITY_SOURCES")
    dropped = sorted(bindings)[0]
    partial = {k: v for k, v in bindings.items() if k != dropped}
    res = pw.build_boards(package, partial, out, styles=["MONO_ACCENT_GALLERY"], demo=True)
    doc = res[0]["doc"]
    assert doc["source_gaps"] == [dropped]
    html_text = (Path(res[0]["dir"]) / "board.html").read_text(encoding="utf-8")
    assert "MISSING SOURCE" in html_text
    deck = pw.plan_deck(doc["blocks"], "jury", 15)
    assert dropped not in deck["selected_blocks"] and dropped in deck["unbound_blocks"]
    assert all((s.get("block_id") != dropped) for s in deck["slides"])
    print("missing-source gap handling: PASS")


def test_deck_planning(results):
    blocks = results[0]["doc"]["blocks"]
    raster = FIX / "TEST_SOURCES"
    decks = {}
    for aud in ("jury", "citizen"):
        for minutes in (15, 5):
            d = pw.plan_deck(blocks, aud, minutes, raster_dir=raster)
            decks[(aud, minutes)] = d
            assert d["audit_violations"] == [], d["audit_violations"]
            assert sum(s["seconds"] for s in d["slides"]) == minutes * 60
            assert d["slides"][0]["kind"] == "TITLE" and d["slides"][-1]["kind"] == "CLOSE"
            assert d["slide_count"] == len(d["slides"]) <= d["max_slides_by_density"]
            for s in d["slides"]:
                if s["kind"] == "BLOCK":
                    assert s["source_ref"]["source_sha256"] and s["source_ref"]["board_rect_norm"]
                    assert s["notes"] and s["seconds"] >= 15
    assert decks[("jury", 15)]["slide_count"] > decks[("jury", 5)]["slide_count"]
    assert set(decks[("jury", 5)]["selected_blocks"]) < set(decks[("jury", 15)]["selected_blocks"])
    assert decks[("jury", 5)]["selected_blocks"] != decks[("citizen", 5)]["selected_blocks"], "audience must change selection"
    jt = [s["bullets"][0]["text"] for s in decks[("jury", 15)]["slides"] if s["kind"] == "BLOCK"]
    ct = [s["bullets"][0]["text"] for s in decks[("citizen", 15)]["slides"] if s["kind"] == "BLOCK"]
    assert jt != ct, "audience must change wording"
    # density changes budget
    low = pw.plan_deck(blocks, "jury", 5, density="low")
    high = pw.plan_deck(blocks, "jury", 5, density="high")
    assert low["slide_count"] <= decks[("jury", 5)]["slide_count"] <= high["slide_count"]
    assert low["audit_violations"] == [] and high["audit_violations"] == []
    print("deck planning: PASS")
    return decks


def test_facts_and_audit(results, out):
    blocks = results[0]["doc"]["blocks"]
    ids = [b["block_id"] for b in blocks]
    target = next(i for i in ids if i.startswith("PLAN"))
    facts_path = Path(out) / "facts.json"
    area_src = Path(out) / "area-table-rev1.txt"
    area_src.write_text("연면적 12,345㎡\n주차 120대\n", encoding="utf-8")
    facts_path.write_text(json.dumps({"facts": [
        {"id": "F1", "text": "연면적 12,345㎡", "block_ids": [target], "source_ref": "area-table-rev1",
         "source_file": area_src.name, "source_sha256": sha(area_src)},
        {"id": "F2", "text": "근거 없는 주장 99%", "block_ids": [target]},
        {"id": "F3", "text": "존재하지 않는 블록", "block_ids": ["NOPE:1"], "source_ref": "x"},
    ]}, ensure_ascii=False), encoding="utf-8")
    accepted, held = pw.load_facts(facts_path, ids)
    assert [f["id"] for f in accepted] == ["F1"]
    assert accepted[0]["authority"] == "SOURCE_HASH_MATCHED" and accepted[0]["cross_check"] == "NUMBERS_FOUND_IN_TEXT_SOURCE"
    assert {h["id"] for h in held} == {"F2", "F3"}
    deck = pw.plan_deck(blocks, "jury", 15, facts=accepted)
    plan_slide = next(s for s in deck["slides"] if s["block_id"] == target)
    fact_bullets = [b for b in plan_slide["bullets"] if b["basis"] == "BOARD_STATED:F1"]
    assert fact_bullets and fact_bullets[0]["source_ref"] == "area-table-rev1" and fact_bullets[0]["authority"] == "UNVERIFIED"
    assert pw.BOARD_STATED_TAG in fact_bullets[0]["text"]
    assert deck["audit_violations"] == []
    all_text = " ".join(b["text"] for s in deck["slides"] for b in s["bullets"])
    assert "99%" not in all_text, "unsourced claim must be HOLD, never rendered"
    # a numeral without a fact basis must be flagged
    deck["slides"][1]["bullets"].append({"text": "연면적 777㎡", "basis": "ROLE_TEMPLATE"})
    assert any("NUMERAL_WITHOUT_FACT" in v for v in pw.audit_deck(deck))
    deck["slides"][1]["bullets"].append({"text": "무근거", "basis": ""})
    assert any("NO_BASIS" in v for v in pw.audit_deck(deck))
    print("facts + anti-hallucination audit: PASS")


def test_time_split():
    for total, weights in [(825, [3, 3, 3, 2, 2, 1.5, 1.5, 1.5, 1.5]), (265, [3, 3, 2, 2]), (100, [1, 1, 1])]:
        secs = pw._time_split(total, weights)
        assert sum(secs) == total and all(s >= 15 for s in secs), (total, secs)
    print("time split: PASS")


def test_pptx(results, decks, out):
    if not pw.pptx_available():
        print("pptx: SKIP (python-pptx not installed; deck plans still tested)")
        return
    blocks = results[0]["doc"]["blocks"]
    style_id = results[0]["doc"]["board"]["style_id"]
    for (aud, minutes), deck in decks.items():
        path = Path(out) / f"{deck['deck_id']}.pptx"
        pw.build_pptx(deck, path, blocks, style_id)
        rep = pw.inspect_pptx(path)
        assert rep["slide_count"] == deck["slide_count"], (deck["deck_id"], rep["slide_count"])
        assert rep["slide_width_in"] == 13.333 and rep["slide_height_in"] == 7.5
        for plan, got in zip(deck["slides"], rep["slides"]):
            assert got["title"] == plan["title"]
            assert got["notes"] == plan["notes"]
            assert got["body"] and all(b["text"] in got["body"] for b in plan["bullets"])
            if plan["kind"] == "BLOCK":
                assert got["active_block"] == plan["block_id"]
                assert got["locator_blocks"] == 9
                assert got["pictures"] == [f"SOURCE_IMAGE:{plan['block_id']}"], got["pictures"]
                assert plan["block_id"] in (got["locator_link"] or "").replace("%3A", ":")
                assert plan["source_ref"]["source_sha256"][:12] in got["footer"]
    # edit persistence: change a title, save, reopen
    deck = decks[("jury", 15)]
    src = Path(out) / f"{deck['deck_id']}.pptx"
    edited = Path(out) / "edited.pptx"
    pw.edit_pptx_title(src, 2, "수정된 제목 검증", edited)
    assert pw.inspect_pptx(edited)["slides"][1]["title"] == "수정된 제목 검증"
    assert pw.inspect_pptx(src)["slides"][1]["title"] == deck["slides"][1]["title"], "original deck must be untouched"
    print("pptx build/reopen/edit persistence: PASS")


def test_recompose_and_viewer(results, out):
    board_dirs = [r["dir"] for r in results]
    before = sha(Path(board_dirs[0]) / "board.html")
    rec_out = Path(out) / "recomposed"
    rec = pw.recompose(board_dirs, rec_out, raster_dir=FIX / "TEST_SOURCES")
    assert rec["original_board_unchanged"] is True
    assert sha(Path(board_dirs[0]) / "board.html") == before
    assert [d["deck_id"] for d in rec["decks"]] == ["jury_15min", "jury_5min", "citizen_15min", "citizen_5min"]
    assert (rec_out / "deck-plans.json").exists()
    viewer = Path(rec["viewer"])
    text = viewer.read_text(encoding="utf-8")
    m = re.search(r'<script id="data" type="application/json">(.*?)</script>', text, re.S)
    data = json.loads(m.group(1).replace("<\\/", "</"))
    assert len(data["boards"]) == 2 and len(data["decks"]) == 4
    for b in data["boards"]:
        assert len(b["rects"]) == 9
        assert (viewer.parent / b["html_rel"]).exists(), b["html_rel"]
    for d in data["decks"]:
        for s in d["slides"]:
            if s["kind"] == "BLOCK":
                assert s["block_id"] in data["boards"][0]["rects"]
                assert s["source_sha256"]
                assert s["image_rel"] and (viewer.parent / s["image_rel"]).exists(), s["image_rel"]
    assert "PANEL_VIEWER" in text and "selectBlock" in text
    if pw.pptx_available():
        assert rec["pptx_status"] == "READY"
        for deck_id, rel in rec["deck_files"].items():
            assert (rec_out / rel).exists()
    print("recompose + viewer + original-board preservation: PASS")


def test_legacy_board_loader():
    legacy = FIX / "QUALITY_A1_BOARD"
    if not (legacy / "build-manifest.json").exists() or not (legacy / "board.html").exists():
        print("legacy loader: SKIP (fixture board absent)")
        return
    doc = pw.load_board_blocks(legacy)
    assert doc["segmentation"]["method"] == "RULE_BASED_FROM_BUILD_MANIFEST"
    assert doc["board"]["html_sha256"] == sha(legacy / "board.html")
    visible = [b for b in doc["blocks"] if b.get("board_rect_norm")]
    assert 1 <= len(visible) <= 9
    for b in visible:
        assert b["rect_method"] == "CSS_GRID_ESTIMATE_UNVERIFIED"
        n = b["board_rect_norm"]
        assert n["x"] + n["w"] <= 1.0001 and n["y"] + n["h"] <= 1.0001
    deck = pw.plan_deck(doc["blocks"], "citizen", 5)
    assert deck["audit_violations"] == []
    print("legacy board loader (rule-based, estimated rects labelled): PASS")


# ---------------------------------------------------------------- B: numeric source authority

def write_json_file(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return Path(path)


def test_numeric_authority(results, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    blocks = results[0]["doc"]["blocks"]
    ids = [b["block_id"] for b in blocks]
    target = next(i for i in ids if i.startswith("PLAN"))
    info = pw.classify_numeric("주차 120대, 용적률 250%, 연면적 12,345.5㎡")
    assert info["is_numeric"] and info["numbers"] == ["120", "250", "12345.5"]
    assert {"COUNT", "RATIO", "AREA"} <= set(info["quantity_kinds"])
    assert not pw.classify_numeric("공공성을 높이는 계획")["is_numeric"]

    src = out / "program-rev3.txt"
    src.write_text("연면적 12,345㎡ / 주차 120대", encoding="utf-8")
    good_hash = sha(src)
    facts = [
        {"id": "OK", "text": "주차 120대", "block_ids": [target], "source_file": src.name, "source_sha256": good_hash},
        {"id": "FORGED_REF", "text": "연면적 99,999㎡", "block_ids": [target], "source_ref": "program-rev3 (사실 확인됨)"},
        {"id": "FORGED_DICT", "text": "주차 777대", "block_ids": [target],
         "source_ref": {"label": "구조도서 rev9", "source_file": "no-such-file.pdf", "source_sha256": "a" * 64}},
        {"id": "WRONG_HASH", "text": "주차 120대", "block_ids": [target], "source_file": src.name, "source_sha256": "b" * 64},
        {"id": "NO_HASH", "text": "주차 120대", "block_ids": [target], "source_file": src.name},
        {"id": "MISLABELED", "text": "주차 130대", "block_ids": [target], "source_file": src.name, "source_sha256": good_hash},
        {"id": "STATED", "text": "연면적 5,000㎡", "block_ids": [target], "source_ref": "보드 우하단 표", "claim_role": "BOARD_STATED"},
        {"id": "WORDS", "text": "남측 가로를 향해 열린 마당", "block_ids": [target], "source_ref": "보드 캡션"},
    ]
    fp = write_json_file(out / "facts-authority.json", {"facts": facts})
    accepted, held = pw.load_facts(fp, ids)
    by_id = {f["id"]: f for f in accepted}
    held_by_id = {h["id"]: h["reason"] for h in held}
    assert by_id["OK"]["authority"] == "SOURCE_HASH_MATCHED" and by_id["OK"]["claim_role"] == "BOARD_STATED"
    assert by_id["OK"]["authority_hold"] == "AUTHORITATIVE_PROJECT_BINDING_REQUIRED"
    assert held_by_id["FORGED_REF"].startswith("UNVERIFIED_NUMERIC_SOURCE_REF"), held_by_id
    assert held_by_id["FORGED_DICT"].startswith("UNVERIFIED_NUMERIC_SOURCE_REF"), held_by_id
    assert held_by_id["WRONG_HASH"] == "SOURCE_HASH_MISMATCH"
    assert held_by_id["NO_HASH"].startswith("UNVERIFIED_NUMERIC_SOURCE_REF:NO_REVISION_HASH")
    assert held_by_id["MISLABELED"].startswith("NUMBER_NOT_IN_SOURCE")
    assert by_id["STATED"]["authority"] == "UNVERIFIED" and by_id["STATED"]["claim_role"] == "BOARD_STATED"
    assert by_id["WORDS"]["authority"] == "UNVERIFIED"
    assert not any(f["authority"] == "VERIFIED" for f in accepted), "self-signed source cannot certify official facts"

    deck = pw.plan_deck(blocks, "jury", 15, facts=accepted)
    bullets = [b for s in deck["slides"] for b in s["bullets"] if b["basis"].startswith(("FACT:", "BOARD_STATED:"))]
    assert deck["audit_violations"] == [], deck["audit_violations"]
    assert all(b["authority"] == "VERIFIED" for b in bullets if b["basis"].startswith("FACT:"))
    stated = [b for b in bullets if b["basis"].startswith("BOARD_STATED:")]
    assert stated and all(pw.BOARD_STATED_TAG in b["text"] for b in stated)
    all_text = " ".join(b["text"] for s in deck["slides"] for b in s["bullets"])
    for forged in ("99,999", "777", "130대"):
        assert forged not in all_text, forged
    # a hand-forged FACT bullet without hash authority is an audit violation
    deck["slides"][1]["bullets"].append({"text": "주차 888대", "basis": "FACT:X", "source_ref": "nonblank"})
    assert any("FACT_NOT_HASH_VERIFIED" in v for v in pw.audit_deck(deck))
    deck["slides"][1]["bullets"][-1] = {"text": "연면적 5,000㎡", "basis": "BOARD_STATED:X", "source_ref": "x"}
    assert any("BOARD_STATED_UNTAGGED" in v for v in pw.audit_deck(deck))
    # revision change after declaring the hash invalidates the proof
    src.write_text("연면적 12,345㎡ / 주차 121대", encoding="utf-8")
    accepted2, held2 = pw.load_facts(fp, ids)
    assert "OK" not in {f["id"] for f in accepted2}
    assert {h["id"]: h["reason"] for h in held2}["OK"] == "SOURCE_HASH_MISMATCH"
    print("numeric source authority (hash-proven, forged ref held): PASS")


# ---------------------------------------------------------------- C: mandatory presentation

def test_must_show(results, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    blocks = results[0]["doc"]["blocks"]
    ids = [b["block_id"] for b in blocks]
    base = pw.plan_deck(blocks, "jury", 5)
    assert base["must_show_status"] == "NONE" and base["audit_violations"] == []
    assert len(base["omitted_blocks"]) >= 2, "fixture must omit blocks at 5 minutes for this test to mean anything"
    forced_a, forced_b = base["omitted_blocks"][0], base["omitted_blocks"][1]

    brief = out / "brief-rev2.txt"
    brief.write_text("필수 제시: 주차·피난 계획", encoding="utf-8")
    items = [
        {"id": "BRIEF-1", "label": "공모지침 필수 도면", "owner": "BRIEF", "block_id": forced_a,
         "source_file": brief.name, "source_sha256": sha(brief)},
        {"id": "USER-1", "label": "대표님 요청", "owner": "USER", "block_id": forced_b},
        {"id": "RULE-NOSRC", "label": "법정 주차 검토", "owner": "OFFICIAL_RULE", "block_id": "NOPE:1"},
    ]
    fp = write_json_file(out / "must-show.json", {"must_show": items})
    loaded, rejected = pw.load_must_show(fp)
    binding = {m["id"]: m["binding"] for m in loaded}
    assert binding == {"BRIEF-1": "CLAIMED_MANDATORY_UNVERIFIED", "USER-1": "USER_REQUEST", "RULE-NOSRC": "CLAIMED_MANDATORY_UNVERIFIED"}
    assert rejected == []
    # owner claim with a wrong hash is not verified; a bare user flag is never law
    bad = write_json_file(out / "must-show-bad.json", {"must_show": [
        {"id": "B2", "label": "x", "owner": "BRIEF", "block_id": forced_a, "source_file": brief.name, "source_sha256": "c" * 64},
        {"id": "", "label": "no id"}]})
    loaded_bad, rejected_bad = pw.load_must_show(bad)
    assert loaded_bad[0]["binding"] == "CLAIMED_MANDATORY_UNVERIFIED" and len(rejected_bad) == 1

    deck = pw.plan_deck(blocks, "jury", 5, must_show=loaded)
    assert deck["audit_violations"] == [], deck["audit_violations"]
    assert forced_a in deck["selected_blocks"] and forced_b in deck["selected_blocks"], "MUST_SHOW dropped"
    report = {r["id"]: r for r in deck["must_show_report"]}
    assert report["BRIEF-1"]["status"] == "PLACED" and report["USER-1"]["status"] == "PLACED"
    assert report["RULE-NOSRC"]["status"] == "PLACEHOLDER_SOURCE_UNVERIFIED"
    assert deck["must_show_status"] == "SATISFIED" and deck["must_show_omitted"] == []
    assert sum(s["seconds"] for s in deck["slides"]) == 300 and all(s["seconds"] >= 15 for s in deck["slides"])
    ph = next(s for s in deck["slides"] if s["kind"] == "PLACEHOLDER")
    assert ph["must_show"] == ["RULE-NOSRC"] and ph["block_id"] is None
    assert not any(re.search(r"\d", b["text"]) for b in ph["bullets"]), "placeholder must not carry invented numbers"
    # 15/5 variants and citizen variant stay intact
    d15 = pw.plan_deck(blocks, "citizen", 15, must_show=loaded)
    assert d15["must_show_status"] == "SATISFIED" and d15["audit_violations"] == []

    # arbitrary per-block boolean = user request, not binding
    flagged = [dict(b, must_show=True) if b["block_id"] == forced_a else b for b in blocks]
    dflag = pw.plan_deck(flagged, "jury", 5)
    r = dflag["must_show_report"][0]
    assert r["binding"] == "USER_REQUEST" and r["status"] == "PLACED" and forced_a in dflag["selected_blocks"]

    # infeasible: far more mandatory units than the hard 15s floor allows -> honest flag, verified items survive, nothing silent
    many = [{"id": f"M{i}", "label": f"요청 {i}", "owner": "USER", "block_id": f"NOPE:{i}", "binding": "USER_REQUEST",
             "evidence_status": "NO_SOURCE_FILE"} for i in range(30)]
    many.append(dict(loaded[0]))  # Claimed brief-mandatory item must be accounted for; no forged VERIFIED
    inf = pw.plan_deck(blocks, "citizen", 5, must_show=many)
    assert inf["must_show_status"] == "INFEASIBLE_AT_DURATION", inf["must_show_status"]
    assert inf["must_show_omitted"] and inf["suggested_minutes"] and inf["suggested_minutes"] > 5
    rep = {x["id"]: x for x in inf["must_show_report"]}
    assert set(rep) == {m["id"] for m in many}, "every mandatory item must be accounted for"
    assert rep["BRIEF-1"]["status"] == "PLACED"
    assert all(rep[i]["status"] == "INFEASIBLE_AT_DURATION" for i in inf["must_show_omitted"])
    assert inf["audit_violations"] == [], inf["audit_violations"]
    assert sum(s["seconds"] for s in inf["slides"]) == 300 and all(s["seconds"] >= 15 for s in inf["slides"])
    # silent drop is an audit violation
    tampered = dict(inf, must_show_status="SATISFIED")
    assert "MUST_SHOW_SILENT_DROP" in pw.audit_deck(tampered)
    tampered2 = dict(inf, must_show_report=[x for x in inf["must_show_report"] if x["id"] != "M1"])
    assert "MUST_SHOW_UNACCOUNTED" in pw.audit_deck(tampered2)

    if pw.pptx_available():
        style_id = results[0]["doc"]["board"]["style_id"]
        path = pw.build_pptx(inf, Path(out) / "infeasible.pptx", blocks, style_id)
        rep_p = pw.inspect_pptx(path)
        assert rep_p["slide_count"] == inf["slide_count"]
        assert all("권장" in (s.get("must_show_status") or "") for s in rep_p["slides"]), "status must be visible on every slide"
        ph_path = pw.build_pptx(deck, Path(out) / "placeholder.pptx", blocks, style_id)
        got = pw.inspect_pptx(ph_path)
        kinds = [s["kind"] for s in deck["slides"]]
        idx = kinds.index("PLACEHOLDER")
        assert "RULE-NOSRC" in got["slides"][idx]["must_show_status"] and got["slides"][idx]["pictures"] == []

    # recompose end-to-end: metadata + viewer banner + deck-plans.json
    board_dirs = [r["dir"] for r in results]
    facts_file = write_json_file(out / "facts-and-must.json", {"facts": [], "must_show": items})
    rec = pw.recompose(board_dirs, out / "rec", facts_path=facts_file, raster_dir=FIX / "TEST_SOURCES", make_pptx=False)
    assert rec["must_show_items"] == 3
    plans = json.loads((out / "rec" / "deck-plans.json").read_text(encoding="utf-8"))
    assert len(plans["must_show"]) == 3 and all("must_show_status" in d for d in plans["decks"])
    text = Path(rec["viewer"]).read_text(encoding="utf-8")
    assert "mustShowBanner" in text
    data = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', text, re.S).group(1).replace("<\\/", "</"))
    assert all(d["must_show_status"] == "SATISFIED" for d in data["decks"])
    assert any(s["must_show"] for d in data["decks"] for s in d["slides"])
    print("mandatory presentation (retain / placeholder / infeasible, visible status): PASS")


# ---------------------------------------------------------------- A: source extractor

def make_pdf(fitz, path, extra_text=None, image=None):
    doc = fitz.open()
    page = doc.new_page(width=600, height=800)
    page.insert_text((72, 100), "ALPHA PLAN LEGEND", fontsize=14)
    if image is not None:
        page.insert_image(fitz.Rect(50, 150, 350, 450), filename=str(image))
    page.draw_rect(fitz.Rect(380, 150, 560, 450), color=(0, 0, 0), fill=(0.9, 0.9, 0.9), width=1)
    page.draw_line((390, 200), (550, 200), color=(0, 0, 0), width=1)
    page.draw_line((390, 300), (550, 420), color=(0, 0, 0), width=1)
    page.insert_text((50, 470), "CAPTION BELOW IMAGE", fontsize=10)
    if extra_text:
        page.insert_text((300, 700), extra_text, fontsize=12)
    rotated = doc.new_page(width=600, height=800)
    rotated.insert_text((72, 100), "ROTATED TOKEN", fontsize=14)
    rotated.set_rotation(90)
    doc.save(str(path))
    doc.close()
    return Path(path)


def assert_regions_meaningful(doc):
    for page in doc["pages"]:
        assert page["regions"], page["page_no"]
        ids = [r["rect_id"] for r in page["regions"]]
        assert len(ids) == len(set(ids)), "rect ids must be unique"
        for r in page["regions"]:
            n = r["bbox_norm"]
            assert n["w"] > 0 and n["h"] > 0, (r["object_id"], n)
            assert -0.01 <= n["x"] and -0.01 <= n["y"] and n["x"] + n["w"] <= 1.01 and n["y"] + n["h"] <= 1.01, (r["object_id"], n)
            assert r["semantic_type"] == "UNKNOWN" and r["review_state"] == "PROPOSED"
            assert r["extractor"] and r["method"] and 0 <= r["confidence"]["geometry"] <= 1 and r["confidence"]["semantic"] == 0.0
            assert r["source_sha256"] == doc["source"]["sha256"]
            if r["kind"] == "TEXT":
                assert r["text"].strip()


def test_extract_pdf(tmp):
    fitz = fitz_module()
    if fitz is None:
        print("source extract pdf: SKIP (PyMuPDF not installed)")
        return None
    tmp = Path(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    png = tmp / "plate.png"
    from PIL import Image
    Image.new("RGB", (300, 300), (200, 120, 60)).save(png)
    pdf = make_pdf(fitz, tmp / "unfamiliar.pdf", image=png)
    before = sha(pdf)
    doc = se.import_source(pdf, tmp / "out", dpi=60)
    assert doc["source"]["sha256"] == before == sha(pdf) and doc["source"]["source_unchanged"] is True
    assert doc["extractor"]["name"] == "pymupdf"
    assert len(doc["pages"]) == 2
    assert_regions_meaningful(doc)

    p1 = doc["pages"][0]
    assert (p1["width"], p1["height"], p1["unit"], p1["rotation_deg"]) == (600.0, 800.0, "pt", 0)
    assert p1["mediabox"] and p1["cropbox"]
    by_kind = {}
    for r in p1["regions"]:
        by_kind.setdefault(r["kind"], []).append(r)
    assert {"TEXT", "IMAGE", "DRAWING"} <= set(by_kind), sorted(by_kind)
    img = by_kind["IMAGE"][0]
    b = img["bbox_native"]
    assert abs(b["x0"] - 50) < 2 and abs(b["y0"] - 150) < 2 and abs(b["x1"] - 350) < 2 and abs(b["y1"] - 450) < 2, b
    assert abs(img["bbox_norm"]["x"] - 50 / 600) < 0.005 and abs(img["bbox_norm"]["h"] - 300 / 800) < 0.005
    drw = by_kind["DRAWING"][0]
    assert drw["native_ref"]["primitive_count"] >= 2 and abs(drw["bbox_native"]["x0"] - 380) < 4 and abs(drw["bbox_native"]["y1"] - 450) < 4
    texts = {r["text"].strip(): r for r in by_kind["TEXT"]}
    assert "ALPHA PLAN LEGEND" in texts and "CAPTION BELOW IMAGE" in texts
    for r in p1["regions"]:  # rotation 0: visual and unrotated PDF frames coincide
        assert all(abs(r["bbox_unrotated_pdf_pt"][k] - r["bbox_native"][k]) < 0.01 for k in ("x0", "y0", "x1", "y1")), r["object_id"]

    # grouped caption: one semantic group references several primitives (image + caption)
    cap = texts["CAPTION BELOW IMAGE"]
    grp = next(g for g in doc["groups"] if img["object_id"] in g["member_object_ids"])
    assert cap["object_id"] in grp["member_object_ids"] and len(grp["member_object_ids"]) >= 2
    assert grp["semantic_type"] == "UNKNOWN" and grp["review_state"] == "PROPOSED"

    # rotation: visual frame vs unrotated PDF frame
    p2 = doc["pages"][1]
    assert p2["rotation_deg"] == 90 and (p2["width"], p2["height"]) == (800.0, 600.0)
    tok = next(r for r in p2["regions"] if r["kind"] == "TEXT" and "ROTATED TOKEN" in r["text"])
    ub = tok["bbox_unrotated_pdf_pt"]
    assert abs(ub["x0"] - 72) < 4 and 70 < ub["y0"] < 102, ub
    assert tok["bbox_native"] != ub, "rotated page: visual frame must differ from unrotated frame"
    reopened = fitz.open(str(pdf))
    try:
        mapped = fitz.Rect(ub["x0"], ub["y0"], ub["x1"], ub["y1"]) * reopened[1].rotation_matrix
    finally:
        reopened.close()
    vb = tok["bbox_native"]
    assert max(abs(mapped.x0 - vb["x0"]), abs(mapped.y0 - vb["y0"]), abs(mapped.x1 - vb["x1"]), abs(mapped.y1 - vb["y1"])) < 1.5
    assert 0 <= tok["bbox_norm"]["x"] <= 1 and 0 <= tok["bbox_norm"]["y"] <= 1

    # review overlay + backgrounds
    html_text = (tmp / "out" / "review.html").read_text(encoding="utf-8")
    assert "PANEL_SOURCE_REVIEW" in html_text and before in html_text and 'id="exportBtn"' in html_text
    assert (tmp / "out" / "pages" / "page-1.png").exists() and (tmp / "out" / "source-regions.json").exists()
    on_disk = json.loads((tmp / "out" / "source-regions.json").read_text(encoding="utf-8"))
    assert sum(len(p["regions"]) for p in on_disk["pages"]) == sum(len(p["regions"]) for p in doc["pages"])
    assert len(se.semantic_types()) >= 12 and {"PLAN", "SECTION", "UNKNOWN"} <= set(se.semantic_types())
    print("source extract pdf (regions, rotation, groups, overlay): PASS")
    return {"pdf": pdf, "png": png, "doc": doc, "fitz": fitz, "img": img, "cap": cap}


def test_corrections_and_stale(ctx, tmp):
    if ctx is None:
        print("corrections: SKIP (no PDF fixture)")
        return
    tmp = Path(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    doc, img, cap = ctx["doc"], ctx["img"], ctx["cap"]
    sha_now = doc["source"]["sha256"]
    corr = {"version": se.CORRECTIONS_VERSION, "source_sha256": sha_now, "source_name": "unfamiliar.pdf", "corrections": [
        {"rect_id": img["rect_id"], "semantic_type": "PLAN", "label": "1층 평면", "group_id": "plan-main", "ignored": False},
        {"rect_id": cap["rect_id"], "semantic_type": "UNKNOWN", "label": "평면 캡션", "group_id": "plan-main", "ignored": False},
        {"rect_id": "R-does-not-exist", "semantic_type": "PLAN", "label": "x", "group_id": "", "ignored": False},
        {"rect_id": img["rect_id"], "semantic_type": "NOT_A_MODE", "label": "bad", "group_id": "", "ignored": False},
    ]}
    cp = write_json_file(tmp / "corrections.json", corr)
    d1 = se.import_source(ctx["pdf"], tmp / "applied", corrections_path=cp, dpi=60)
    c = d1["corrections"]
    assert c["status"] == "APPLIED" and c["applied"] == 2 and c["orphaned"] == ["R-does-not-exist"] and len(c["rejected"]) == 1
    reg = {r["rect_id"]: r for p in d1["pages"] for r in p["regions"]}
    assert reg[img["rect_id"]]["semantic_type"] == "PLAN" and reg[img["rect_id"]]["review_state"] == "HUMAN_CORRECTED"
    human = [g for g in d1["groups"] if g["source"] == "HUMAN"]
    assert len(human) == 1 and set(human[0]["member_object_ids"]) == {img["object_id"], cap["object_id"]}
    assert human[0]["semantic_type"] == "PLAN" and human[0]["label"] == "1층 평면"
    assert any(g["review_state"] == "SUPERSEDED_BY_HUMAN" for g in d1["groups"] if g["source"] == "AUTO_PROXIMITY"), "regroup keeps provenance"
    # idempotent re-import of the same revision keeps the correction
    d1b = se.import_source(ctx["pdf"], tmp / "applied2", corrections_path=cp, dpi=60)
    assert d1b["corrections"]["applied"] == 2 and [g["member_object_ids"] for g in d1b["groups"] if g["source"] == "HUMAN"] == [human[0]["member_object_ids"]]
    assert "HUMAN_CORRECTED" in (tmp / "applied" / "review.html").read_text(encoding="utf-8")

    # bridge: human-labelled group -> panel blocks -> deck planning with crop image
    panel = se.export_panel_blocks(d1, tmp / "applied", page=1)
    assert [b["mode"] for b in panel["blocks"]] == ["PLAN"] and panel["blocks"][0]["source_sha256"] == sha_now
    assert Path(panel["blocks"][0]["crop_path"]).exists()
    loaded = pw.load_board_blocks(tmp / "applied")
    deck = pw.plan_deck(loaded["blocks"], "jury", 5)
    assert deck["audit_violations"] == [] and deck["selected_blocks"] == ["PLAN:1"]
    slide = next(s for s in deck["slides"] if s["kind"] == "BLOCK")
    assert slide["image_path"] and Path(slide["image_path"]).exists() and slide["source_ref"]["source_sha256"] == sha_now
    auto_only = se.export_panel_blocks(se.import_source(ctx["pdf"], tmp / "noedit", dpi=60), tmp / "noedit", page=1)
    assert auto_only["blocks"] == [], "auto proposals must never become blocks without a human label"

    # source revision change: corrections go STALE, nothing is applied
    changed = make_pdf(ctx["fitz"], tmp / "unfamiliar_rev2.pdf", extra_text="REVISION TWO", image=ctx["png"])
    assert sha(changed) != sha_now
    d2 = se.import_source(changed, tmp / "stale", corrections_path=cp, dpi=60)
    c2 = d2["corrections"]
    assert c2["status"] == "STALE" and c2["applied"] == 0 and c2["stale"] == len(corr["corrections"])
    assert img["rect_id"] in c2["remap_candidates"], "unchanged geometry keeps its stable rect id as remap candidate"
    assert all(r["semantic_type"] == "UNKNOWN" for p in d2["pages"] for r in p["regions"])
    assert not [g for g in d2["groups"] if g["source"] == "HUMAN"]
    assert "STALE" in (tmp / "stale" / "review.html").read_text(encoding="utf-8")
    # original untouched by every import above
    assert sha(ctx["pdf"]) == sha_now
    # wrong format / unsupported source
    bad = write_json_file(tmp / "bad-corr.json", {"version": "OLD", "corrections": []})
    assert se.import_source(ctx["pdf"], tmp / "badver", corrections_path=bad, dpi=60)["corrections"]["status"] == "INVALID"
    try:
        se.import_source(tmp / "corrections.json", tmp / "x")
        raise AssertionError("unsupported kind accepted")
    except SystemExit as exc:
        assert "UNSUPPORTED_SOURCE_KIND" in str(exc)
    print("corrections (apply / regroup / STALE on revision / invalid) + panel-block bridge: PASS")


def test_extract_pptx(results, decks, tmp):
    if not pw.pptx_available():
        print("source extract pptx: SKIP (python-pptx not installed)")
        return
    from pptx import Presentation
    from pptx.util import Inches
    tmp = Path(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    # (1) an existing generated deck as unfamiliar native content
    deck = decks[("jury", 15)]
    gen = tmp / "generated.pptx"
    pw.build_pptx(deck, gen, results[0]["doc"]["blocks"], results[0]["doc"]["board"]["style_id"])
    before = sha(gen)
    doc = se.import_source(gen, tmp / "gen_out")
    assert doc["extractor"]["name"] == "python-pptx" and doc["source"]["sha256"] == before == sha(gen)
    assert len(doc["pages"]) == deck["slide_count"]
    assert_regions_meaningful(doc)
    slide2 = doc["pages"][1]
    assert slide2["unit"] == "EMU" and slide2["width"] == float(Presentation(str(gen)).slide_width)
    title = next(r for r in slide2["regions"] if r["native_ref"]["name"] == "TITLE")
    assert title["text"] == deck["slides"][1]["title"] and title["kind"] == "TEXT"
    assert abs(title["bbox_native"]["x0"] - Inches(0.6)) <= 2 and abs(title["bbox_native"]["y0"] - Inches(0.62)) <= 2
    assert abs(title["bbox_norm"]["x"] - 0.6 / 13.333) < 0.001
    pic = next(r for r in slide2["regions"] if r["kind"] == "IMAGE")
    assert pic["native_ref"]["image_sha1"] and (tmp / "gen_out" / "assets" / pic["native_ref"]["asset"]).exists()
    locator_shapes = [r for r in slide2["regions"] if r["native_ref"]["name"].startswith("LOCATOR")]
    assert len(locator_shapes) >= 9, "locator mini-board shapes are native shapes with measured geometry"
    # (2) rotation + native group transforms
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    rot = sl.shapes.add_textbox(Inches(2), Inches(2), Inches(3), Inches(1))
    rot.text_frame.text = "ROTATED BOX"
    rot.rotation = 90
    grp = sl.shapes.add_group_shape()
    inner = grp.shapes.add_textbox(Inches(8), Inches(1), Inches(2), Inches(1))
    inner.text_frame.text = "GROUPED CAPTION"
    cap2 = grp.shapes.add_textbox(Inches(8), Inches(2.2), Inches(2), Inches(0.5))
    cap2.text_frame.text = "SECOND MEMBER"
    synth = tmp / "synthetic.pptx"
    prs.save(str(synth))
    d2 = se.import_source(synth, tmp / "syn_out")
    assert_regions_meaningful(d2)
    regs = {r["text"]: r for r in d2["pages"][0]["regions"] if r["kind"] == "TEXT"}
    rb = regs["ROTATED BOX"]
    assert rb["rotation_deg"] == 90.0
    assert abs(rb["bbox_native"]["x0"] - Inches(3)) <= 3 and abs(rb["bbox_native"]["y0"] - Inches(1)) <= 3
    assert abs(rb["bbox_native"]["x1"] - Inches(4)) <= 3 and abs(rb["bbox_native"]["y1"] - Inches(4)) <= 3
    assert rb["unrotated_frame_emu"]["w"] == Inches(3), "native unrotated frame preserved next to rotated AABB"
    gi = regs["GROUPED CAPTION"]
    assert abs(gi["bbox_native"]["x0"] - Inches(8)) <= 3 and abs(gi["bbox_native"]["y0"] - Inches(1)) <= 3
    native = [g for g in d2["groups"] if g["source"] == "NATIVE_GROUP"]
    assert len(native) == 1 and set(native[0]["member_object_ids"]) == {gi["object_id"], regs["SECOND MEMBER"]["object_id"]}
    print("source extract pptx (generated deck, rotation, native group): PASS")


def test_extract_raster_and_existing_pdf(tmp):
    tmp = Path(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    # Use a known fully decodable raster for the success path. Old TEST_SOURCES
    # contain some header-readable yet truncated files; do not silently enable
    # PIL.LOAD_TRUNCATED_IMAGES to manufacture a passing result.
    from PIL import Image
    valid = tmp / "valid_unknown_board.png"
    Image.new("RGB", (880, 620), (240, 235, 226)).save(valid)
    before = sha(valid)
    doc = se.import_source(valid, tmp / "png_out")
    assert sha(valid) == before and doc["source"]["kind"] == "IMAGE"
    (region,) = doc["pages"][0]["regions"]
    assert region["kind"] == "IMAGE_PAGE_UNKNOWN" and region["needs_review"] is True and region["semantic_type"] == "UNKNOWN"
    assert "OCR_VISION_HOLD" in region["needs_review_reason"] and doc["pages"][0]["unit"] == "px"
    assert (tmp / "png_out" / "pages" / "page-1.png").exists() and any("OCR" in h for h in doc["hold"])
    # Corrupted old fixture must never be reported as a successfully rendered
    # image. Mark the background as unavailable and preserve the evidence.
    pngs = sorted((FIX / "TEST_SOURCES").glob("*.png"))
    if pngs:
        candidate = pngs[0]
        try:
            degraded = se.import_source(candidate, tmp / "legacy_raster_out")
        except (OSError, ValueError) as exc:
            assert type(exc).__name__ in {"OSError", "UnidentifiedImageError", "ValueError"}
        else:
            bg = degraded["backgrounds"]
            if bg.get("error"):
                assert any("BACKGROUND_RENDER_UNAVAILABLE" in h for h in degraded["hold"])
                assert not (tmp / "legacy_raster_out" / "pages" / "page-1.png").exists()
            else:
                assert (tmp / "legacy_raster_out" / "pages" / "page-1.png").exists()
    if fitz_module() is not None:
        existing = sorted(FIX.glob("**/board.pdf"))
        if existing:
            doc = se.import_source(existing[0], tmp / "existing_out", dpi=40)
            assert_regions_meaningful(doc)
            assert any(r["kind"] != "PAGE_UNKNOWN" for p in doc["pages"] for r in p["regions"]), "real board PDF produced no native regions"
        else:
            print("existing board.pdf: SKIP (not rendered in this checkout)")
    print("source extract raster route + existing PDF: PASS")


def main():
    test_time_split()
    test_layouts()
    with tempfile.TemporaryDirectory(prefix="panel-workflow-test-") as tmp:
        tmp = Path(tmp)
        _, _, results = test_boards_and_manifest(tmp / "a")
        test_missing_source_is_gap(tmp / "gap")
        decks = test_deck_planning(results)
        test_facts_and_audit(results, tmp)
        test_numeric_authority(results, tmp / "authority")
        test_must_show(results, tmp / "must")
        test_pptx(results, decks, tmp / "pptx")
        test_recompose_and_viewer(results, tmp / "viewer")
        ctx = test_extract_pdf(tmp / "extract_pdf")
        test_corrections_and_stale(ctx, tmp / "corr")
        test_extract_pptx(results, decks, tmp / "extract_pptx")
        test_extract_raster_and_existing_pdf(tmp / "extract_misc")
    test_legacy_board_loader()
    print("architecture_panel_workflow: PASS")


if __name__ == "__main__":
    main()
