#!/usr/bin/env python3
"""Real-Chrome regression for the site studio: interaction, option binding and exports.

Needs headless Chrome (skipped otherwise) and python-pptx for the PPTX parts. Interactions
are dispatched as real DOM events by the page's own ?selftest=1 routine and read back from
the dumped DOM; the PPTX/HTML exports come from the loopback bridge over HTTP.
"""
import html as htmllib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chrome_profile_lifecycle import ChromeProfile  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "site_analysis_visual_fixture" / "urban_demo"
CHROME = next((Path(p) for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                                 r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                                 shutil.which("google-chrome") or "", shutil.which("chromium") or "") if p and Path(p).is_file()), None)
HAVE_PPTX = importlib.util.find_spec("pptx") is not None


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "TOOLS" / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STUDIO = load("site_studio", "ARCHIGROW_SITE_STUDIO.py")
REPORT = STUDIO.load_report()
INPUTS = dict(project_id="SYNTHETIC_URBAN_BLOCK_01", receipt=FIXTURE / "site_source_receipt.json",
              context=FIXTURE / "context_obstacles.json", solar=FIXTURE / "solar_study_report.json",
              massing=FIXTURE / "massing_result.json")


def chrome(*args, url, width=1440, height=1000):
    # Use CDP's actual device viewport for DOM tests; --window-size can be
    # clamped to 500px and Chrome CLI --dump-dom intermittently hangs on Windows.
    # The transient profile lives under the OS tmp and is always removed (leaks raise).
    flags_win = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    if "--dump-dom" in args:
        script = ROOT / "ENFORCEMENT" / "architecture_site_studio_cdp.js"
        with ChromeProfile("taky_chrome_cdp_") as profile:
            proc = profile.adopt(subprocess.Popen(
                ["node", str(script), url, str(width), str(height)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env={**os.environ, "TAKY_CDP_PROFILE": str(profile.path)}, creationflags=flags_win))
            try:
                out, err = proc.communicate(timeout=35)
            except subprocess.TimeoutExpired:
                profile.terminate()
                raise RuntimeError("CHROME_CDP_FAILED:timeout")
            if proc.returncode:
                raise RuntimeError("CHROME_CDP_FAILED:" + err.decode("utf-8", errors="replace")[-400:])
            return out
    with ChromeProfile("taky_chrome_pdf_") as profile:
        flags = ["--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={profile.path}",
                 f"--window-size={width},{height}", "--virtual-time-budget=8000", *args, url]
        # Chrome helper processes can keep inherited pipes open after the main process exits,
        # so capture through a file and wait on the main process only.
        sink = profile.path / "stdout.bin"
        with open(sink, "wb") as handle:
            proc = profile.adopt(subprocess.Popen([str(CHROME), *flags], stdout=handle, stderr=subprocess.DEVNULL,
                                                  creationflags=flags_win))
            proc.wait(timeout=90)
        return sink.read_bytes()


class FixtureLeakError(RuntimeError):
    pass


def make_fixture_dir(prefix):
    """Isolated fixture directory in the OS temp (never the repository root)."""
    return Path(tempfile.mkdtemp(prefix=prefix))


def remove_fixture_dir(path, attempts=8, delay=0.25):
    """Remove exactly this directory with bounded retry; residue raises FixtureLeakError (HOLD)."""
    path, last = Path(path), ""
    for _ in range(attempts):
        if not path.exists():
            return
        try:
            shutil.rmtree(path)
        except OSError as exc:
            last = type(exc).__name__
        if path.exists():
            time.sleep(delay)
    if path.exists():
        raise FixtureLeakError(f"FIXTURE_LEAK HOLD: {path.name} still present after {attempts} attempts ({last or 'unknown'})")


def own_fixture_dir(testcase_cls, prefix):
    """Create the dir and register its removal as a class cleanup, which also runs when setUpClass fails."""
    path = make_fixture_dir(prefix)
    testcase_cls.addClassCleanup(remove_fixture_dir, path)
    return path


def selftest_result(dom):
    found = re.search(r'<pre id="selftest-result">(.*?)</pre>', dom, re.S)
    assert found, "selftest did not complete"
    return json.loads(htmllib.unescape(found.group(1)))


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = own_fixture_dir(cls, "site_studio_test_")
        cls.studio = STUDIO.Studio(INPUTS["project_id"], INPUTS["receipt"], cls.tmp / "out",
                                   INPUTS["context"], INPUTS["solar"], INPUTS["massing"])
        cls.studio.publish()
        cls.page = (cls.tmp / "out" / "site_analysis.html").resolve()


@unittest.skipUnless(CHROME, "headless Chrome unavailable")
class BrowserInteraction(Base):
    def run_selftest(self, width, height):
        dom = chrome("--dump-dom", url=self.page.as_uri() + "?selftest=1", width=width, height=height).decode("utf-8")
        return selftest_result(dom), dom

    def test_desktop_and_mobile_interactions_all_pass(self):
        for width, height in ((1440, 1000), (1920, 1080), (390, 844)):
            result, _ = self.run_selftest(width, height)
            failed = [c for c in result["checks"] if not c["pass"]]
            self.assertEqual(failed, [], f"viewport {width}: {failed}")
            names = {c["check"] for c in result["checks"]}
            for needed in ("wheel_zoom_in", "drag_pan", "reset", "keyboard_zoom", "layer_off",
                           "unknown_height_not_zero", "option_O1_kpi", "option_O2_recalc_matches_python",
                           "option_O3_svg_export_bound", "option_O3_comparison_selected",
                           "comparison_card_click_selects_option", "recalc_repeatable", "solar_not_rendered_as_result",
                           "baseline_O1_selected_independent", "baseline_O3_delta_matches_python", "option_change_keeps_baseline",
                           "receipt_carries_baseline", "matrix_row_click_selects_option", "delta_arithmetic",
                           "unknown_kpi_stays_unknown", "no_horizontal_overflow"):
                self.assertIn(needed, names)

    def test_unknown_building_selected_for_real_and_never_zero(self):
        result, _ = self.run_selftest(1440, 1000)
        check = next(c for c in result["checks"] if c["check"] == "unknown_height_not_zero")
        self.assertTrue(check["pass"])
        self.assertIn("SYN-", check["detail"])
        self.assertIn("UNKNOWN", check["detail"])

    def test_query_option_survives_load_and_updates_report_pages(self):
        dom = chrome("--dump-dom", url=self.page.as_uri() + "?opt=O3").decode("utf-8")
        self.assertIn('data-selected-option="O3"', dom)
        self.assertIn("30,200.0 m²", dom)
        self.assertRegex(dom, r'<tr data-opt-id="O3" class="sel"')
        self.assertNotRegex(dom, r'<tr data-opt-id="O1" class="sel"')
        self.assertIn("C 타워형", dom.split('class="seltag"')[1][:200])

    def test_url_baseline_and_option_are_independent_and_match_independent_arithmetic(self):
        massing = json.loads(INPUTS["massing"].read_text(encoding="utf-8"))
        ring = json.loads(INPUTS["receipt"].read_text(encoding="utf-8"))["parcel"]["polygon_local_m"]
        area = REPORT._area(REPORT._ring(ring))
        kpi = {f"O{i+1}": o["kpi"] for i, o in enumerate(massing["options"])}
        gfa = {k: v["gross_floor_area_m2"] for k, v in kpi.items()}
        hgt = {k: v["max_height_m"] for k, v in kpi.items()}
        for width in (1440, 1920):
            dom = chrome("--dump-dom", url=self.page.as_uri() + "?base=O2&opt=O3", width=width, height=1000).decode("utf-8")
            self.assertIn('data-selected-option="O3"', dom)
            self.assertRegex(dom, r'<tr data-mx-opt="O2" class="base"')
            self.assertRegex(dom, r'<tr data-mx-opt="O3" class="sel"')
            self.assertEqual(len(re.findall(r'<tr data-mx-opt="[^"]+" class="[^"]*\bbase\b', dom)), 1)
            d_gfa = gfa["O3"] - gfa["O2"]
            d_h = hgt["O3"] - hgt["O2"]
            d_r = gfa["O3"] / area - gfa["O2"] / area
            expect = {"gfa_m2": f"{d_gfa:+,.1f} m² ({d_gfa / gfa['O2'] * 100:+.1f}%)",
                      "max_height_m": f"{d_h:+,.1f} m ({d_h / hgt['O2'] * 100:+.1f}%)",
                      "gfa_ratio": f"{d_r:+,.3f} ({d_r / (gfa['O2'] / area) * 100:+.1f}%)"}
            for key, text in expect.items():
                self.assertRegex(dom, rf'data-mx-cell="O3:{key}">{re.escape(htmllib.escape(text))}<')
                self.assertRegex(dom, rf'data-d="O3:{key}">{re.escape(htmllib.escape(text))}<')
            self.assertRegex(dom, r'data-mx-cell="O2:gfa_m2">기준<')
            self.assertIn("선택안 C 타워형 vs 기준안 B 중정형", dom)
            self.assertIn("우열·허가 판단 아님", dom)

    def test_unknown_option_kpi_is_unknown_never_zero_in_matrix(self):
        massing = json.loads(INPUTS["massing"].read_text(encoding="utf-8"))
        del massing["options"][1]["kpi"]["gross_floor_area_m2"]
        path = self.tmp / "massing_unknown_gfa.json"
        path.write_text(json.dumps(massing), encoding="utf-8")
        out = self.tmp / "unknown_out"
        REPORT.build(INPUTS["project_id"], INPUTS["receipt"], out, INPUTS["context"], None, path)
        dom = chrome("--dump-dom", url=(out / "site_analysis.html").resolve().as_uri() + "?base=O1&opt=O1").decode("utf-8")
        self.assertRegex(dom, r'data-mx-val="O2:gfa_m2">Unknown m²<')
        self.assertRegex(dom, r'data-mx-cell="O2:gfa_m2">Unknown<')
        self.assertRegex(dom, r'data-mx-cell="O2:gfa_ratio">Unknown<')
        self.assertRegex(dom, r'data-d="O2:gfa_m2">Unknown<')
        self.assertRegex(dom, r'data-mx-cell="O2:max_height_m">\+11\.4 m')
        dom = chrome("--dump-dom", url=(out / "site_analysis.html").resolve().as_uri() + "?base=O2&opt=O1").decode("utf-8")
        self.assertRegex(dom, r'data-mx-cell="O1:gfa_m2">Unknown<')
        self.assertRegex(dom, r'data-mx-cell="O3:gfa_m2">Unknown<')
        self.assertNotRegex(dom, r'data-mx-cell="O[13]:gfa_m2">\+?0\.0')

    def test_evidence_panel_shows_provenance_without_freshness_claim(self):
        dom = chrome("--dump-dom", url=self.page.as_uri(), width=1440, height=1000).decode("utf-8")
        panel = re.search(r'<div class="box evidence" id="evidence-impact">(.*?)</div></section>', dom, re.S).group(1)
        hashes = json.loads(re.search(r'id="studio-data">(.*?)</script>', self.page.read_text(encoding="utf-8"), re.S).group(1))["input_sha256"]
        self.assertEqual(len(re.findall(r'<article class="ev ', panel)), 4)
        for key, digest in hashes.items():
            self.assertIn(digest[:16], panel, key)
        self.assertEqual(panel.count('data-ev-class="SYNTHETIC"'), 4)
        self.assertNotIn('data-ev-class="VERIFIED_SCREENING"', panel)
        for category in ("site", "context", "massing", "solar"):
            self.assertIn(f'data-category="{category}"', panel)
        self.assertIn("보고서 06쪽", panel)
        self.assertIn("PPTX 슬라이드 6", panel)
        self.assertIn("최신 공식 데이터셋이라는 뜻이 아닙니다", panel)
        self.assertNotRegex(re.sub(r"<[^>]+>", " ", panel), r"\b(19|20)\d\d[-./]\d{1,2}[-./]\d{1,2}\b")

    def test_print_pdf_has_seven_report_pages_without_studio(self):
        out = self.tmp / "print.pdf"
        chrome(f"--print-to-pdf={out}", "--no-pdf-header-footer", url=self.page.as_uri())
        data = out.read_bytes()
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertEqual(len(re.findall(rb"/Type\s*/Page[^s]", data)), 7)

    def test_source_mismatch_holds_and_is_not_shown_as_pass(self):
        receipt = json.loads(INPUTS["receipt"].read_text(encoding="utf-8"))
        receipt["eum"]["area_m2"] = 14500.0
        receipt["comparison"]["result"] = "HOLD_AREA_MISMATCH"
        bad = self.tmp / "bad_receipt.json"
        bad.write_text(json.dumps(receipt), encoding="utf-8")
        manifest = REPORT.build(INPUTS["project_id"], bad, self.tmp / "bad_out", INPUTS["context"],
                                INPUTS["solar"], INPUTS["massing"], option="O2")
        self.assertEqual(manifest["source_status"], "HOLD")
        self.assertEqual(manifest["recalc"]["outcome"], "HOLD")
        dom = chrome("--dump-dom", url=(self.tmp / "bad_out" / "site_analysis.html").resolve().as_uri()).decode("utf-8")
        self.assertIn("SOURCE HOLD", dom)
        self.assertNotIn("SOURCE PASS", dom)
        self.assertRegex(dom, r'data-ev="site_source"[^>]*data-integrity="HOLD"')
        self.assertIn("데이터 무결성 HOLD", dom)


class StaticSemantics(Base):
    def test_no_invented_layers_and_provenance_present(self):
        text = self.page.read_text(encoding="utf-8")
        for forbidden in ('id="roads"', 'id="trees"', 'id="shadow', 'id="sun'):
            self.assertNotIn(forbidden, text)
        data = json.loads(re.search(r'id="studio-data">(.*?)</script>', text, re.S).group(1))
        self.assertTrue(data["synthetic"])
        unknown = [b for b in data["buildings"] if b["height_m"] is None]
        self.assertEqual(len(unknown), 3)
        self.assertFalse(data["solar"]["calculated"])
        self.assertEqual(set(data["input_sha256"]), {"context", "solar", "massing", "site_source"})
        self.assertEqual([o["id"] for o in data["options"]], ["O1", "O2", "O3"])
        manifest = json.loads((self.tmp / "out" / "analysis_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["selected_option"]["selection"], "DEFAULT_FIRST")
        self.assertEqual(manifest["page_count"], 7)
        self.assertEqual(text.count('class="page-preview"'), 7)
        self.assertIn("설계 대안 비교", text)
        self.assertEqual(text.count('class="compare-card"'), 3)
        self.assertIn('data-compare-opt="O3"', text)

    def test_delta_matrix_arithmetic_unknown_and_baseline_contract(self):
        options = [{"id": "A", "label": "A", "gfa_m2": 1000, "max_height_m": 10.0},
                   {"id": "B", "label": "B", "gfa_m2": 1500, "max_height_m": 8.0},
                   {"id": "C", "label": "C", "gfa_m2": None, "max_height_m": None},
                   {"id": "D", "label": "D", "gfa_m2": 0, "max_height_m": 12.0}]
        rows = {r["id"]: r for r in REPORT.delta_matrix(options, 500.0, "A")}
        self.assertTrue(rows["A"]["is_baseline"])
        self.assertEqual(rows["B"]["delta"]["gfa_m2"], {"abs": 500, "pct": 50.0})
        self.assertEqual(rows["B"]["delta"]["max_height_m"], {"abs": -2, "pct": -20.0})
        self.assertEqual(rows["B"]["values"]["gfa_ratio"], 3.0)
        self.assertEqual(rows["B"]["delta"]["gfa_ratio"], {"abs": 1.0, "pct": 50.0})
        self.assertEqual(rows["C"]["delta"]["gfa_m2"], {"abs": None, "pct": None})
        self.assertIsNone(rows["C"]["values"]["gfa_ratio"])
        self.assertEqual(REPORT.delta_text(rows["C"], "gfa_m2"), "Unknown")
        self.assertEqual(REPORT.delta_text(rows["B"], "gfa_m2"), "+500.0 m² (+50.0%)")
        self.assertEqual(REPORT.delta_text(rows["B"], "max_height_m"), "-2.0 m (-20.0%)")
        self.assertEqual(REPORT.delta_text(rows["A"], "gfa_m2"), "기준")
        self.assertEqual(REPORT.delta_text(rows["A"], "gfa_m2", base_word="(base)"), "(base)")
        self.assertEqual(rows["D"]["delta"]["gfa_m2"], {"abs": -1000, "pct": -100.0})
        zero_base = {r["id"]: r for r in REPORT.delta_matrix(options, 500.0, "D")}
        self.assertEqual(zero_base["B"]["delta"]["gfa_m2"], {"abs": 1500, "pct": None})
        self.assertEqual(REPORT.delta_text(zero_base["B"], "gfa_m2"), "+1,500.0 m²")
        unknown_base = {r["id"]: r for r in REPORT.delta_matrix(options, 500.0, "C")}
        self.assertEqual(unknown_base["A"]["delta"]["gfa_m2"], {"abs": None, "pct": None})
        with self.assertRaisesRegex(REPORT.ReportHold, "BASELINE_NOT_FOUND"):
            REPORT.delta_matrix(options, 500.0, "Z")
        self.assertEqual(REPORT.delta_matrix([], 500.0, None), [])

    def test_payload_delta_matches_shared_function_for_every_baseline_and_default_is_first(self):
        manifest = REPORT.build(out_dir=self.tmp / "d0", **{**self.studio.args})
        self.assertEqual(manifest["comparison"]["baseline_option"]["id"], "O1")
        self.assertEqual(manifest["comparison"]["baseline_option"]["selection"], "DEFAULT_FIRST")
        data = json.loads(re.search(r'id="studio-data">(.*?)</script>', (self.tmp / "d0" / "site_analysis.html").read_text(encoding="utf-8"), re.S).group(1))
        self.assertEqual((data["baseline"], data["built_baseline"]), ("O1", "O1"))
        area = data["recalc_python"]["parcel_area_m2"]
        for base in ("O1", "O2", "O3"):
            shared = REPORT.delta_matrix(data["options"], REPORT._area(data["parcel_ring"]), base)
            self.assertEqual(data["delta_python"][base], shared)
            row = next(r for r in shared if r["id"] == "O3")
            self.assertAlmostEqual(row["values"]["gfa_ratio"], data["recalc_python"]["ratio_by_option"]["O3"], places=3)
        self.assertEqual(data["delta_python"]["O1"][2]["delta"]["gfa_m2"]["abs"], 7100)
        self.assertAlmostEqual(data["delta_python"]["O1"][2]["delta"]["max_height_m"]["abs"], 33.0, places=3)
        self.assertEqual(data["delta_python"]["O3"][0]["delta"]["gfa_m2"]["abs"], -7100)
        self.assertGreater(area, 0)

    def test_explicit_baseline_is_bound_in_static_report_and_unknown_baseline_holds(self):
        manifest = REPORT.build(out_dir=self.tmp / "b2", option="C", baseline="B", **{**self.studio.args})
        self.assertEqual(manifest["comparison"]["baseline_option"]["id"], "O2")
        self.assertEqual(manifest["comparison"]["baseline_option"]["selection"], "EXPLICIT")
        self.assertEqual(manifest["selected_option"]["id"], "O3")
        self.assertEqual(next(r for r in manifest["comparison"]["rows"] if r["id"] == "O3")["delta"]["gfa_m2"]["abs"], 2300)
        page = (self.tmp / "b2" / "site_analysis.html").read_text(encoding="utf-8")
        self.assertIn('data-d="O3:gfa_m2">+2,300.0 m² (+8.2%)<', page)
        self.assertIn('data-d="O2:gfa_m2">기준<', page)
        self.assertIn('data-mx-cell="O1:gfa_m2">-4,800.0 m² (-17.2%)<', page)
        self.assertIn('data-bind="base-label">B 중정형<', page)
        svg_meta = (self.tmp / "b2" / "site_map.svg").read_text(encoding="utf-8")
        self.assertIn('"baseline_option":{', svg_meta)
        self.assertIn('"id":"O2"', svg_meta.split('"baseline_option"')[1][:200])
        for bad in ("Z9",):
            with self.assertRaisesRegex(REPORT.ReportHold, "OPTION_NOT_FOUND"):
                REPORT.build(out_dir=self.tmp / "b3", baseline=bad, **{**self.studio.args})
        with self.assertRaisesRegex(REPORT.ReportHold, "BASELINE_REQUIRES_MASSING_RESULT"):
            REPORT.build(INPUTS["project_id"], INPUTS["receipt"], self.tmp / "b4", INPUTS["context"], None, None, baseline="O1")

    def test_evidence_impact_separates_missing_optional_from_integrity_hold(self):
        manifest = REPORT.build(INPUTS["project_id"], INPUTS["receipt"], self.tmp / "e1", INPUTS["context"], None, None)
        by_key = {e["key"]: e for e in manifest["evidence_impact"]}
        self.assertEqual(by_key["massing"]["evidence_class"], "MISSING")
        self.assertEqual(by_key["massing"]["integrity"], "NOT_PROVIDED")
        self.assertIsNone(by_key["massing"]["sha256"])
        self.assertEqual(by_key["solar"]["integrity"], "NOT_PROVIDED")
        self.assertEqual(by_key["context"]["evidence_class"], "SYNTHETIC")
        self.assertEqual({e["category"] for e in manifest["evidence_impact"]}, {"site", "context", "massing", "solar"})
        self.assertIsNone(manifest["comparison"]["baseline_option"])
        self.assertIn("비교할 대안이 없습니다", (self.tmp / "e1" / "site_analysis.html").read_text(encoding="utf-8"))
        receipt = json.loads(INPUTS["receipt"].read_text(encoding="utf-8"))
        receipt["eum"]["area_m2"] = 14500.0
        receipt["comparison"]["result"] = "HOLD_AREA_MISMATCH"
        bad = self.tmp / "e_bad.json"
        bad.write_text(json.dumps(receipt), encoding="utf-8")
        held = REPORT.build(INPUTS["project_id"], bad, self.tmp / "e2", INPUTS["context"], INPUTS["solar"], INPUTS["massing"])
        held_by = {e["key"]: e for e in held["evidence_impact"]}
        self.assertEqual((held_by["site_source"]["integrity"], held_by["site_source"]["state"]), ("HOLD", "HOLD"))
        self.assertEqual(held_by["massing"]["integrity"], "OK")
        full = {e["key"]: e for e in REPORT.build(out_dir=self.tmp / "e3", **{**self.studio.args})["evidence_impact"]}
        for key, entry in full.items():
            self.assertEqual(entry["evidence_class"], "SYNTHETIC", key)
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")

    def test_repeated_builds_are_deterministic_and_bad_option_holds(self):
        a = REPORT.build(out_dir=self.tmp / "r1", option="O2", **{**self.studio.args})
        b = REPORT.build(out_dir=self.tmp / "r2", option="O2", **{**self.studio.args})
        self.assertEqual(a["recalc"], b["recalc"])
        self.assertEqual((self.tmp / "r1" / "site_analysis.html").read_bytes(), (self.tmp / "r2" / "site_analysis.html").read_bytes())
        with self.assertRaisesRegex(REPORT.ReportHold, "OPTION_NOT_FOUND"):
            REPORT.build(out_dir=self.tmp / "r3", option="Z9", **{**self.studio.args})

    def test_letter_and_index_select_same_massing_option(self):
        by_letter = REPORT.build(out_dir=self.tmp / "l", option="C", **{**self.studio.args})
        by_index = REPORT.build(out_dir=self.tmp / "i", option="3", **{**self.studio.args})
        self.assertEqual(by_letter["selected_option"]["id"], "O3")
        self.assertEqual(by_letter["selected_option"]["label"], "C 타워형")
        self.assertEqual(by_index["selected_option"]["gfa_m2"], 30200)


@unittest.skipUnless(HAVE_PPTX, "python-pptx unavailable in this interpreter")
class BridgeExports(Base):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.server = STUDIO.serve(cls.studio, 0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        # LIFO: the server stops before the fixture directory is removed.
        cls.addClassCleanup(lambda: (cls.server.shutdown(), cls.server.server_close()))
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    def get(self, path):
        try:
            with urllib.request.urlopen(self.base + path, timeout=60) as r:
                return r.status, dict(r.headers), r.read()
        except urllib.error.HTTPError as exc:
            try:
                return exc.code, dict(exc.headers), exc.read()
            finally:
                exc.close()

    def deck_text(self, data):
        import io
        from pptx import Presentation
        deck = Presentation(io.BytesIO(data))
        self.assertEqual(len(deck.slides), 7)
        slides = []
        for slide in deck.slides:
            parts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
            for s in slide.shapes:
                if s.has_table:
                    parts += [c.text for row in s.table.rows for c in row.cells]
            slides.append("\n".join(parts))
        return deck, slides

    def test_loopback_only_and_health(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        code, _, body = self.get("/api/health")
        self.assertEqual((code, json.loads(body)["studio"]), (200, "ARCHIGROW_SITE_STUDIO"))

    def test_pptx_follows_selected_option_exactly(self):
        expected = {"O1": ("A 저층 개방형", "23100", "1.708"),
                    "O2": ("B 중정형", "27900", "2.063"),
                    "O3": ("C 타워형", "30200", "2.233")}
        seen = set()
        for opt, (label, gfa, ratio) in expected.items():
            code, headers, data = self.get(f"/api/export?format=pptx&option={opt}")
            self.assertEqual(code, 200)
            self.assertEqual(headers["X-Selected-Option"], opt)
            _, slides = self.deck_text(data)
            self.assertIn(f"OPTION {label} ({opt})", slides[0])
            self.assertIn(f"OPTION {label}", slides[5])
            marked = [l for l in slides[5].split("\n") if l == "SELECTED"]
            self.assertEqual(len(marked), 1)
            self.assertIn(f"GFA / geometry area = {ratio}", slides[5])
            self.assertIn(f"{gfa} m²", slides[5])
            for other in expected:
                if other != opt:
                    self.assertNotIn(f"OPTION {expected[other][0]} ({other})", slides[0])
            seen.add(data)
        self.assertEqual(len(seen), 3)

    def test_pptx_contains_native_context_buildings_with_unknown_height(self):
        code, _, data = self.get("/api/export?format=pptx&option=O2")
        deck, slides = self.deck_text(data)
        names = [s.name for s in deck.slides[1].shapes]
        self.assertEqual(sum(n.startswith("Context building") for n in names), 18)
        self.assertEqual(names.count("Editable parcel boundary"), 1)
        self.assertIn("?", slides[1])
        self.assertNotIn("0 m", [t for t in slides[1].split("\n") if t.strip() == "0 m"])

    def test_html_svg_exports_and_errors(self):
        code, _, html = self.get("/api/export?format=html&option=C")
        self.assertEqual(code, 200)
        self.assertRegex(html.decode("utf-8"), r'<tr data-opt-id="O3" class="sel"')
        code, headers, svg = self.get("/api/export?format=svg&option=O1")
        self.assertEqual((code, headers["X-Selected-Option"]), (200, "O1"))
        self.assertIn(b'id="parcel"', svg)
        code, _, body = self.get("/api/export?format=pptx&option=NOPE")
        self.assertEqual(code, 409)
        self.assertIn("OPTION_NOT_FOUND", json.loads(body)["failure_class"])
        self.assertEqual(self.get("/api/export?format=exe")[0], 400)
        self.assertEqual(self.get("/../secret")[0], 404)

    def test_changed_source_blocks_old_page_recalc_and_export(self):
        # ArchiSofts-style freshness contract: never pair a previous UI snapshot
        # with a newly changed source. The test uses its own copied receipt.
        mutable = self.tmp / "mutable_receipt.json"
        mutable.write_bytes(INPUTS["receipt"].read_bytes())
        local = STUDIO.Studio(INPUTS["project_id"], mutable, self.tmp / "mutable_out",
                             INPUTS["context"], INPUTS["solar"], INPUTS["massing"])
        local.publish("O1")
        server = STUDIO.serve(local, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"

        def check(path):
            try:
                with urllib.request.urlopen(base + path, timeout=35) as response:
                    return response.status, json.loads(response.read()) if path == "/api/health" else None
            except urllib.error.HTTPError as exc:
                body = json.loads(exc.read())
                exc.close()
                return exc.code, body
        try:
            self.assertEqual(check("/api/health")[1]["snapshot"], "CURRENT")
            self.assertEqual(check("/api/recalc?option=O2")[0], 200)
            doc = json.loads(mutable.read_text(encoding="utf-8"))
            doc["eum"]["address"] = "SYNTHETIC CHANGED LOCATION (not legal)"
            mutable.write_text(json.dumps(doc), encoding="utf-8")
            self.assertEqual(check("/api/health")[1]["snapshot"], "STALE")
            for uri in ("/", "/api/recalc?option=O2", "/api/export?format=pptx&option=O2"):
                status, payload = check(uri)
                self.assertEqual(status, 409, uri)
                self.assertEqual(payload["failure_class"], "STALE_SOURCE_REFRESH_REQUIRED")
            local.publish("O2")
            self.assertEqual(check("/api/health")[1]["snapshot"], "CURRENT")
            self.assertEqual(check("/api/recalc?option=O2")[0], 200)
        finally:
            server.shutdown()
            server.server_close()

    def test_pptx_baseline_comparison_matches_explicit_baseline_not_browser_only(self):
        code, _, data = self.get("/api/export?format=pptx&option=O3&baseline=O2")
        self.assertEqual(code, 200)
        _, slides = self.deck_text(data)
        lines = slides[5].split("\n")
        self.assertEqual(lines.count("BASELINE"), 1)
        self.assertEqual(lines.count("SELECTED"), 1)
        self.assertIn("+2,300.0 m² (+8.2%)", slides[5])
        self.assertIn("-4,800.0 m² (-17.2%)", slides[5])
        self.assertIn("Baseline B 중정형 (O2)", slides[5])
        code, _, default = self.get("/api/export?format=pptx&option=O3")
        _, default_slides = self.deck_text(default)
        self.assertIn("+7,100.0 m²", default_slides[5])
        self.assertIn("Baseline A 저층 개방형 (O1)", default_slides[5])
        self.assertNotEqual(slides[5], default_slides[5])
        code, _, body = self.get("/api/export?format=pptx&option=O3&baseline=NOPE")
        self.assertEqual(code, 409)
        self.assertIn("OPTION_NOT_FOUND", json.loads(body)["failure_class"])

    def test_recalc_endpoint_returns_comparison_for_requested_baseline(self):
        code, headers, body = self.get("/api/export?format=manifest&option=O3&baseline=O2")
        doc = json.loads(body)
        self.assertEqual(doc["comparison"]["baseline_option"]["id"], "O2")
        page = json.loads(re.search(r'id="studio-data">(.*?)</script>', self.page.read_text(encoding="utf-8"), re.S).group(1))
        self.assertEqual(doc["comparison"]["rows"], page["delta_python"]["O2"])
        code, _, body = self.get("/api/recalc?option=O3&baseline=O2")
        self.assertEqual(json.loads(body)["comparison"]["baseline_option"]["id"], "O2")

    def test_recalc_endpoint_matches_page_payload(self):
        code, _, body = self.get("/api/recalc?option=O3")
        doc = json.loads(body)
        page = re.search(r'id="studio-data">(.*?)</script>', self.page.read_text(encoding="utf-8"), re.S).group(1)
        base = json.loads(page)["recalc_python"]
        self.assertEqual(doc["selected_option"]["id"], "O3")
        self.assertEqual(doc["recalc"]["parcel_area_m2"], base["parcel_area_m2"])
        self.assertEqual(doc["recalc"]["gfa_to_parcel_area_ratio"], base["ratio_by_option"]["O3"])


GB7_LIKE = {
    "schema": "ARCHIGROW_PIPELINE_MANIFEST_V1", "project_id": "GB7", "route": "PRODUCTION", "stages": ["WORKBOOK_AUDIT"],
    "inputs": {"workbook": {"xlsx": "요청자료/강북7구역_A3.xlsx", "source_role": "PROVISIONAL_DERIVED"}},
    "source_lock_notes": {"original_input": "ORIGINAL_BYTES_PENDING (not found on local D:, Drive F:)",
                          "leak": r"see F:\내 드라이브\TAKY\secret\x.xlsx and C:\Users\someone\a.dwg"},
}


class SourceReadiness(unittest.TestCase):
    """Unready manifest (GB7-like): read-only readiness page, HOLD for exports, ready baseline untouched."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = own_fixture_dir(cls, "site_studio_ready_")
        cls.gb7 = cls.write("gb7", GB7_LIKE)
        evil = json.loads(json.dumps(GB7_LIKE))
        evil["project_id"] = "<script>alert(1)</script>\"'&"
        evil["inputs"]["workbook"]["source_role"] = "<img src=x onerror=alert(2)>"
        evil["source_lock_notes"] = {"<b>k</b>": "<svg onload=alert(3)>"}
        cls.evil = cls.write("evil", evil)

    @classmethod
    def write(cls, name, doc):
        folder = cls.tmp / name
        folder.mkdir()
        (folder / "manifest.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        return STUDIO.Studio.from_pipeline_manifest(folder / "manifest.json", folder / "out")

    def serve(self, studio):
        server = STUDIO.serve(studio, 0)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close()))
        base = f"http://127.0.0.1:{server.server_address[1]}"

        def get(path):
            try:
                with urllib.request.urlopen(base + path, timeout=30) as r:
                    return r.status, r.read()
            except urllib.error.HTTPError as exc:
                try:
                    return exc.code, exc.read()
                finally:
                    exc.close()
        return get

    def test_manifest_role_and_stage_names_do_not_certify_completion(self):
        # A manifest can name a registered stage and describe an ORIGINAL file,
        # but neither alone proves execution or independent certification.
        studio = STUDIO.Studio("GB7", None, self.tmp / "role_out",
                               manifest={"project_id": "GB7", "stages": ["WORKBOOK_AUDIT"],
                                         "inputs": {"workbook": {"source_role": "ORIGINAL"}}})
        readiness = studio.readiness()
        self.assertFalse(readiness["workbook"]["certified"])
        self.assertIn("완료 증거 아님", studio.readiness_html())
        self.assertIn("공식 확인 별도", studio.readiness_html())

    def test_unready_manifest_loads_without_crash_and_is_not_bound(self):
        self.assertFalse(self.gb7.bound)
        with self.assertRaises(self.gb7.report.ReportHold):
            self.gb7.publish()
        self.assertTrue(self.gb7.snapshot_stale())

    def test_readiness_json_and_html_over_http(self):
        get = self.serve(self.gb7)
        code, body = get("/api/readiness")
        doc = json.loads(body)
        self.assertEqual((code, doc["status"], doc["failure_class"]), (200, "HOLD", "SITE_SOURCE_NOT_BOUND"))
        self.assertEqual(doc["project_id"], "GB7")
        self.assertEqual(doc["workbook"], {"source_role": "PROVISIONAL_DERIVED", "certified": False, "file": "강북7구역_A3.xlsx"})
        states = {l["id"]: l["state"] for l in doc["layers"]}
        self.assertEqual(states, {"SITE_ANALYSIS": "MISSING", "context": "ABSENT", "solar": "ABSENT", "massing": "ABSENT"})
        self.assertEqual(doc["pnu_status"], "NOT_PROVIDED_NOT_INFERRED")
        code, page = get("/")
        text = page.decode("utf-8")
        self.assertEqual(code, 200)
        for needle in ("GB7", "PROVISIONAL_DERIVED", "SITE_SOURCE_NOT_BOUND", "19자리 PNU", "공식 인증 아님", 'href="/api/readiness"'):
            self.assertIn(needle, text)
        self.assertEqual(re.findall(r"<button[^>]*>", text), ['<button class="btn" aria-disabled="true" disabled>'] * 2)
        health = json.loads(get("/api/health")[1])
        self.assertEqual(health["snapshot"], "NOT_BOUND")

    def test_no_absolute_path_or_certification_claim(self):
        get = self.serve(self.gb7)
        everything = get("/")[1].decode("utf-8") + get("/api/readiness")[1].decode("utf-8")
        for leaked in ("F:\\", "C:\\", "D:\\", "someone", "secret", str(ROOT), "VWORLD_KEY=", "api_key"):
            self.assertNotIn(leaked, everything)
        self.assertIn("[경로 생략]", everything)
        self.assertNotRegex(everything, r"\d{19}")
        for claim in ("PASS", "CERTIFIED", "공식 확인", "검증 완료"):
            self.assertNotIn(claim, everything)

    def test_user_controlled_fields_are_escaped(self):
        get = self.serve(self.evil)
        text = get("/")[1].decode("utf-8")
        for raw in ("<script>alert", "<img src=x", "<svg onload", "<b>k</b>"):
            self.assertNotIn(raw, text)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", text)
        self.assertEqual(len(re.findall(r"<script", text)), 0)

    def test_export_and_recalc_return_409_hold_not_500(self):
        get = self.serve(self.gb7)
        for path in ("/api/export?format=pptx", "/api/export?format=html", "/api/export?format=svg", "/api/recalc", "/api/recalc?option=O1"):
            code, body = get(path)
            self.assertEqual(code, 409, path)
            self.assertEqual(json.loads(body), {"status": "HOLD", "failure_class": "SITE_SOURCE_NOT_BOUND"})

    def test_declared_but_missing_receipt_stays_hold(self):
        doc = json.loads(json.dumps(GB7_LIKE))
        doc["inputs"]["site_analysis"] = {"site_source_receipt": "missing.json", "context": "c.json"}
        studio = self.write("declared", doc)
        states = {l["id"]: l["state"] for l in studio.readiness()["layers"]}
        self.assertEqual((states["SITE_ANALYSIS"], states["context"]), ("DECLARED_FILE_MISSING", "DECLARED_FILE_MISSING"))
        self.assertEqual(self.serve(studio)("/api/export")[0], 409)

    def test_ready_synthetic_fixture_unaffected(self):
        studio = STUDIO.Studio(INPUTS["project_id"], INPUTS["receipt"], self.tmp / "ready_out",
                               INPUTS["context"], INPUTS["solar"], INPUTS["massing"])
        self.assertTrue(studio.bound)
        studio.publish()
        get = self.serve(studio)
        self.assertEqual(json.loads(get("/api/health")[1])["snapshot"], "CURRENT")
        page = get("/")[1].decode("utf-8")
        self.assertIn("studio-data", page)
        self.assertNotIn("SITE_SOURCE_NOT_BOUND", page)
        self.assertEqual(get("/api/recalc")[0], 200)


if __name__ == "__main__":
    unittest.main()
