#!/usr/bin/env python3
"""Focused tests for TOOLS/ARCHIGROW_CIRCULATION_VERTICAL.py (P9A). Prints PASS or raises."""
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "TOOLS" / "ARCHIGROW_CIRCULATION_VERTICAL.py"
SCRATCH = Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\10_PROJECTS\TAKY_ARCHI-GROW\_scratch")
P8_MODEL = SCRATCH / "TOPOGENESIS_P8_SEMANTIC_SYNC_20261028" / "live_root" / "T1950_d8b5092c28b6" / "model" / "massing_result.json"
GEO_PY = Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\.venv_archigrow_geo\Scripts\python.exe")
PROJECT = "SYNTHETIC_TOPO_P1"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")

spec = importlib.util.spec_from_file_location("p9", TOOL)
p9 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p9)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def raises(fn, label):
    try:
        fn()
    except p9.P9Error:
        return
    raise AssertionError(f"{label}: expected P9Error (fail closed)")


def make_fixture(tmp, mutate=None, name="fixture.json"):
    model, model_sha, source_sha = p9.load_source(P8_MODEL, PROJECT)
    fx = p9.sample_fixture(model_sha, source_sha, PROJECT, sorted(o["strategy"] for o in model["options"]))
    if mutate:
        mutate(fx)
    path = Path(tmp) / name
    path.write_text(json.dumps(fx), encoding="utf-8")
    return path


def balanced(fx):
    return next(o for o in fx["options"] if o["strategy"] == "BALANCED")


def run_to(tmp, fixture, sub, source=P8_MODEL):
    return p9.run(source, fixture, Path(tmp) / sub, PROJECT)


def main():
    assert P8_MODEL.exists(), f"BLOCKED: P8 model missing {P8_MODEL}"
    baseline = sha(P8_MODEL)
    with tempfile.TemporaryDirectory() as tmp:
        fx = make_fixture(tmp)
        model, receipt = run_to(tmp, fx, "ok")
        out = Path(tmp) / "ok"

        # status: partial pass, never total
        assert receipt["status"] == "PARTIAL_PASS_WITH_SCULPTURAL_HOLD", receipt["status"]
        assert receipt["total_pass_claimed"] is False and receipt["native_dwg"] == "NOT_DONE"
        assert all(v is False for v in receipt["claims"].values())
        strat = {s["strategy"]: s for s in model["strategies"]}
        bal, scu = strat["BALANCED"], strat["SCULPTURAL"]

        # BALANCED: two levels, no overlap with rooms, containment, pairwise
        assert bal["status"] == "PASS" and [l["level"] for l in bal["levels"]] == ["L01", "L02"]
        assert not bal["rejections"]
        for c in bal["checks"]:
            if c["check"].startswith(("NO_ROOM_OVERLAP", "CONTAINED", "PAIRWISE")):
                assert c["measured"] <= 1e-4, c
        assert any(c["check"] == "NO_ROOM_OVERLAP_AREA_M2" and c["room"] == "OFFICE" for c in bal["checks"])

        # corridor openings exactly 1 m on each level, real wall gap with wall pieces
        for lv in bal["levels"]:
            assert len(lv["openings"]) == 2
            for op in lv["openings"]:
                assert op["width_m"] == 1.0 and op["mode"] == "EXPLICIT_FIXTURE_OPENING"
                (x1, y1), (x2, y2) = op["segment"]
                assert abs(((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5 - 1.0) < 1e-9
            by = {s["id"]: s for s in lv["spaces"]}
            assert len(by["STAIR"]["walls"]) == 5 and len(by["LIFT"]["walls"]) == 5 and not by["CORRIDOR"]["walls"]
            assert {t["a"] + t["b"] for t in lv["touching_without_opening"]} == set()
            assert lv["programmed_room_openings"] == 0
            assert lv["unprogrammed_ref"]["classified_as_corridor"] is False
            assert {s["id"] for s in lv["spaces"]} == {"STAIR", "LIFT", "CORRIDOR"}  # residual never becomes a space

        # vertical edge pairs: typed stair/lift, footprint alignment only
        links = {l["kind"]: l for l in bal["vertical_links"]}
        assert set(links) == {"STAIR", "LIFT"}
        for l in links.values():
            assert (l["from_level"], l["to_level"]) == ("L01", "L02")
            assert l["mode"] == "SHAFT_FOOTPRINT_ALIGNMENT" and l["provenance"] == "EXPLICIT_FIXTURE"
        g = bal["graph"]
        assert g["network_status"] == "UNCONNECTED_TO_PROGRAMMED_ROOMS" and len(g["components"]) == 1
        assert len(g["edges"]) == 6 and g["vertical_meaning"] == "SHAFT_FOOTPRINT_ALIGNMENT_ONLY"

        # SCULPTURAL: HOLD, precise evidence, no DXF, no walls/openings/graph
        assert scu["status"] == "HOLD" and not scu["cad_published"] and scu["graph"] is None
        assert receipt["strategies"]["SCULPTURAL"]["dxf"] is None
        assert sorted(p.name for p in out.glob("*.dxf")) == ["P9_CIRCULATION_VERTICAL_BALANCED.dxf"]
        ev = {(r["level"], r["subject"], r["check"], r.get("room")): r["measured"] for r in scu["rejections"]}
        assert abs(ev[("L01", "STAIR", "NO_ROOM_OVERLAP_AREA_M2", "OFFICE")] - 12.0) < 1e-3
        assert abs(ev[("L01", "LIFT", "NO_ROOM_OVERLAP_AREA_M2", "OFFICE")] - 7.5) < 1e-3
        assert abs(ev[("L01", "CORRIDOR", "NO_ROOM_OVERLAP_AREA_M2", "OFFICE")] - 13.5) < 1e-3
        assert abs(ev[("L02", "STAIR", "CONTAINED_IN_FLOOR_OUTSIDE_AREA_M2", None)] - 5.582) < 1e-3
        assert abs(ev[("L02", "STAIR", "NO_ROOM_OVERLAP_AREA_M2", "CORE")] - 6.418) < 1e-3
        assert abs(ev[("L02", "CORRIDOR", "CONTAINED_IN_FLOOR_OUTSIDE_AREA_M2", None)] - 13.5) < 1e-3
        assert all(len(s["walls"]) == 0 for lv in scu["levels"] for s in lv["spaces"])
        assert scu["p10_constraints"] and not scu["vertical_links"]

        # optional independent engine cross-check (shapely in the geometry venv)
        if GEO_PY.exists():
            code = (
                "import json,sys\nfrom shapely.geometry import Polygon,box\n"
                "d=json.load(open(sys.argv[1],encoding='utf-8'))\n"
                "o=[x for x in d['options'] if x['strategy']=='SCULPTURAL'][0]\n"
                "rg=o['program_allocation']['room_geometry']['levels']\n"
                "fl={f['level']:Polygon(f['polygon']) for f in o['floors']}\n"
                "r={}\n"
                "for lv in rg:\n"
                "  L=lv['level']\n"
                "  for n,b in (('STAIR',box(20,10,23,14)),('LIFT',box(20.5,16,23,19)),('CORRIDOR',box(23,10,24.5,19))):\n"
                "    r[L+'|'+n+'|out']=b.difference(fl[L]).area\n"
                "    for rm in lv['rooms']: r[L+'|'+n+'|'+rm['id']]=b.intersection(Polygon(rm['polygon'])).area\n"
                "print(json.dumps(r))\n")
            res = subprocess.run([str(GEO_PY), "-c", code, str(P8_MODEL)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
            assert res.returncode == 0, res.stderr
            sh = json.loads(res.stdout)
            for r in scu["checks"]:
                if r["check"] == "NO_ROOM_OVERLAP_AREA_M2":
                    assert abs(sh[f"{r['level']}|{r['subject']}|{r['room']}"] - r["measured"]) < 1e-4, r
                elif r["check"].startswith("CONTAINED"):
                    assert abs(sh[f"{r['level']}|{r['subject']}|out"] - r["measured"]) < 1e-4, r

        # browser data == CAD model == model json; DXF readback of outlines + opening objects
        on_disk = json.loads((out / "P9_CIRCULATION_VERTICAL_MODEL.json").read_text(encoding="utf-8"))
        embedded = p9.extract_embedded_model((out / "P9_CIRCULATION_VERTICAL_VIEWER.html").read_text(encoding="utf-8"))
        assert on_disk == embedded == json.loads(json.dumps(model)), "viewer/model mismatch"
        html_text = (out / "P9_CIRCULATION_VERTICAL_VIEWER.html").read_text(encoding="utf-8")
        assert "http://" not in html_text.replace("http://www.w3.org/2000/svg", "") and "https://" not in html_text
        assert all(ord(ch) < 0x2190 for ch in html_text), "emoji/symbol outside plain text"
        # HOLD strategy must not draw confirmed .gap polygons / OPENING labels in the browser
        draw_src = html_text[html_text.index("function draw(){"):]
        draw_src = draw_src[:draw_src.index("var dl=")]
        gap_idx = draw_src.index("'class':'gap'")
        guard_idx = draw_src.index("if(!hold){L.openings.forEach")
        assert guard_idx < gap_idx and draw_src.index("OPENING '") > guard_idx, "HOLD draw() may render openings"
        assert draw_src.count("L.openings.forEach") == 1
        rb = p9.readback_dxf(out / "P9_CIRCULATION_VERTICAL_BALANCED.dxf", bal)
        assert rb["ok"] and rb["dxfversion"] == "AC1027" and rb["opening_objects"] == 4 and rb["opening_chords"] == 4
        import ezdxf
        doc = ezdxf.readfile(str(out / "P9_CIRCULATION_VERTICAL_BALANCED.dxf"))
        for layer in ("CIRC_STAIR", "CIRC_LIFT", "CIRC_CORRIDOR", "CIRC_OPENING", "CIRC_VERTICAL_REF", "CIRC_UNPROGRAMMED_REF"):
            assert layer in doc.layers
        assert doc.header["$INSUNITS"] == 6
        assert sum(1 for e in doc.modelspace() if e.dxf.layer == "CIRC_VERTICAL_REF" and e.dxftype() == "LINE") == 2
        # a tampered DXF must fail readback
        bad = copy.deepcopy(bal)
        bad["levels"][0]["openings"][0]["gap_polygon"][0][0] += 0.01
        assert not p9.readback_dxf(out / "P9_CIRCULATION_VERTICAL_BALANCED.dxf", bad)["ok"]

        # determinism: identical receipt hashes on a second run
        _, receipt2 = run_to(tmp, fx, "again")
        assert receipt2["hashes"] == receipt["hashes"]
        b1, b2 = receipt["strategies"]["BALANCED"], receipt2["strategies"]["BALANCED"]
        assert b1["dxf_geometry_digest_sha256"] == b2["dxf_geometry_digest_sha256"]
        assert receipt["cad_readback"] == receipt2["cad_readback"]

        # fail-closed cases (each must raise, and produce no output dir content)
        def forged_poly(f):
            lv = balanced(f)["levels"]["L02"]["spaces"]["LIFT"]["polygon"]
            lv[1][0] += 0.5
            lv[2][0] += 0.5
        raises(lambda: run_to(tmp, make_fixture(tmp, forged_poly, "f1.json"), "f1"), "forged vertical polygon")

        def extra_link(f):
            b = balanced(f)
            b["vertical_links"].append(dict(b["vertical_links"][0], id="STAIR_DUP"))
        raises(lambda: run_to(tmp, make_fixture(tmp, extra_link, "f2.json"), "f2"), "duplicate vertical edge")

        def bad_kind(f):
            balanced(f)["vertical_links"][0]["space"] = "LIFT"
        raises(lambda: run_to(tmp, make_fixture(tmp, bad_kind, "f3.json"), "f3"), "forged link kind")

        def bad_mode(f):
            balanced(f)["vertical_links"][0]["mode"] = "ACTUAL_STAIR_FLIGHT"
        raises(lambda: run_to(tmp, make_fixture(tmp, bad_mode, "f4.json"), "f4"), "unsupported vertical mode")

        def src_sha(f):
            f["source_sha256"] = "0" * 64
        raises(lambda: run_to(tmp, make_fixture(tmp, src_sha, "f5.json"), "f5"), "tampered source sha")

        def mdl_sha(f):
            f["model_sha256"] = "1" * 64
        raises(lambda: run_to(tmp, make_fixture(tmp, mdl_sha, "f6.json"), "f6"), "tampered model sha")

        def dup_open(f):
            ops = balanced(f)["levels"]["L01"]["openings"]
            ops.append(dict(ops[0]))
        raises(lambda: run_to(tmp, make_fixture(tmp, dup_open, "f7.json"), "f7"), "duplicate opening id")

        def dup_pair(f):
            ops = balanced(f)["levels"]["L01"]["openings"]
            ops.append(dict(ops[0], id="OTHER_ID"))
        raises(lambda: run_to(tmp, make_fixture(tmp, dup_pair, "f8.json"), "f8"), "duplicate opening pair")

        def wide(f):
            op = balanced(f)["levels"]["L01"]["openings"][0]
            op["segment"] = [[23, 11.0], [23, 13.0]]
            op["width_m"] = 2.0
        raises(lambda: run_to(tmp, make_fixture(tmp, wide, "f9.json"), "f9"), "opening not 1 m")

        def extra_space(f):
            balanced(f)["levels"]["L01"]["spaces"]["HALL"] = {"function": "CORRIDOR", "polygon": [[1, 1], [2, 1], [2, 2], [1, 2]]}
        raises(lambda: run_to(tmp, make_fixture(tmp, extra_space, "f10.json"), "f10"), "inferred extra space")

        def extra_key(f):
            f["options"][0]["levels"]["L01"]["auto_corridor_from_residual"] = True
        raises(lambda: run_to(tmp, make_fixture(tmp, extra_key, "f11.json"), "f11"), "unknown key")

        def nonrect(f):
            balanced(f)["levels"]["L01"]["spaces"]["STAIR"]["polygon"] = [[20, 10], [23, 10], [23, 14], [21, 15], [20, 14]]
        raises(lambda: run_to(tmp, make_fixture(tmp, nonrect, "f12.json"), "f12"), "non rectangle")

        raises(lambda: p9.run(P8_MODEL, fx, Path(tmp) / "ok", PROJECT), "non-empty out-dir")
        raises(lambda: p9.run(P8_MODEL, fx, Path(tmp) / "wrongproj", "OTHER_PROJECT"), "project mismatch")
        assert not (Path(tmp) / "f1").exists() and not (Path(tmp) / "f5").exists(), "fail-closed left outputs"

        # tampered source model file: fixture model_sha no longer matches
        tampered = Path(tmp) / "tampered_massing.json"
        data = json.loads(P8_MODEL.read_text(encoding="utf-8"))
        data["constraints"]["floor_count"] = 9
        tampered.write_text(json.dumps(data), encoding="utf-8")
        raises(lambda: run_to(tmp, fx, "t1", source=tampered), "tampered source model")

        # geometry-only invalidity is HOLD (not hard error): overlap the corridor onto the stair in BALANCED
        def overlap(f):
            for lv in balanced(f)["levels"].values():
                lv["spaces"]["CORRIDOR"]["polygon"] = [[22, 10], [24.5, 10], [24.5, 19], [22, 19]]
                lv["openings"] = []
            balanced(f)["levels"]["L01"]["spaces"]["CORRIDOR"]  # keep structure valid
        m2, r2 = run_to(tmp, make_fixture(tmp, overlap, "f13.json"), "ov")
        assert {s["strategy"]: s["status"] for s in m2["strategies"]} == {"BALANCED": "HOLD", "SCULPTURAL": "HOLD"}
        assert r2["status"] == "HOLD_ALL_STRATEGIES" and not list((Path(tmp) / "ov").glob("*.dxf"))

        # CLI end to end
        cli = subprocess.run([sys.executable, str(TOOL), str(P8_MODEL), "--fixture", str(fx), "--out-dir",
                              str(Path(tmp) / "cli"), "--expect-project", PROJECT], capture_output=True, text=True,
                             encoding="utf-8", env=ENV)
        assert cli.returncode == 0, cli.stderr
        assert json.loads(cli.stdout)["status"] == "PARTIAL_PASS_WITH_SCULPTURAL_HOLD"
        bad_cli = subprocess.run([sys.executable, str(TOOL), str(P8_MODEL), "--fixture", str(Path(tmp) / "f5.json"),
                                  "--out-dir", str(Path(tmp) / "cli2"), "--expect-project", PROJECT],
                                 capture_output=True, text=True, encoding="utf-8", env=ENV)
        assert bad_cli.returncode == 2 and not (Path(tmp) / "cli2").exists()

    # P8 baseline unchanged by every run above
    assert sha(P8_MODEL) == baseline, "P8 source model was modified"
    print("architecture_circulation_vertical_test: PASS")


if __name__ == "__main__":
    main()
