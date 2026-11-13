import importlib.util, shutil, subprocess, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
FX = HERE / "fixtures" / "design_gate"
s = importlib.util.spec_from_file_location("h", HERE / "design_gate_harness.py")
h = importlib.util.module_from_spec(s); s.loader.exec_module(h)


def browser_available() -> bool:
    if not shutil.which("node"):
        return False
    r = subprocess.run(["node", "-e", "require('playwright')"], capture_output=True)
    return r.returncode == 0


class SpecLint(unittest.TestCase):
    def test_complete_spec_passes(self):
        r = h.lint_spec((FX / "DESIGN.md").read_text())
        self.assertEqual(r["status"], "PASS", r["findings"])
        self.assertEqual(r["mode"], "EXECUTE")
        self.assertEqual(r["design_system"], "GATE_FIXTURE@1.0.0")

    def test_tokens_only_spec_fails_dgc18(self):
        r = h.lint_spec((FX / "DESIGN_weak.md").read_text())
        self.assertEqual(r["status"], "FAIL")
        joined = " ".join(r["findings"])
        for code in ("NO_TYPOGRAPHY_FONTFAMILY", "NO_LAYOUT_OR_COMPOSITION_SECTION", "NO_PROHIBITION_LIST"):
            self.assertIn(code, joined)
        self.assertEqual(r["mode"], "EXPLORE")  # DGC-01: undeclared mode is EXPLORE

    def test_execute_requires_source_commit(self):
        txt = (FX / "DESIGN.md").read_text().replace("  source_commit: fixture\n", "")
        self.assertIn("EXECUTE_WITHOUT_SOURCE_COMMIT (DGC-02)", h.lint_spec(txt)["findings"])

    def test_duplicate_top_level_key_is_error(self):
        txt = (FX / "DESIGN.md").read_text() + '\n```yaml\ncolors:\n  x: "#000000"\n```\n'
        self.assertEqual(h.lint_spec(txt)["status"], "FAIL")

    def test_harness_failure_is_hold_not_fail(self):
        spec = h.lint_spec((FX / "DESIGN.md").read_text())
        subs = h.judge(spec, {"harness": {"ok": False, "error": "no browser"}})
        self.assertEqual(subs["HARNESS_HEALTH"]["status"], "HOLD")
        self.assertEqual(h.verdict(subs), "HOLD")


@unittest.skipUnless(browser_available(), "node+playwright not available")
class Render(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_good_page_passes_with_hash_bound_receipt(self):
        r = h.run(FX / "DESIGN.md", str(FX / "good.html"), self.tmp / "g")
        self.assertEqual(r["verdict"], "PASS", r["sub_receipts"])
        self.assertEqual(len(r["spec_sha256"]), 64)
        self.assertEqual(len(r["artifact_sha256"]), 64)
        self.assertTrue((self.tmp / "g" / "print.pdf").exists())

    def test_bad_page_fails_on_each_mechanical_axis(self):
        r = h.run(FX / "DESIGN.md", str(FX / "bad.html"), self.tmp / "b")
        sub = r["sub_receipts"]
        self.assertEqual(r["verdict"], "FAIL")
        for k in ("TARGET_RENDER", "TOKEN_FIDELITY", "FONT_PRINT_PDF", "A11Y_BASIC"):
            self.assertEqual(sub[k]["status"], "FAIL", k)
        self.assertEqual(sub["GENERIC_TELLS"]["status"], "ADVISORY")  # never auto-FAIL

    def test_declared_but_missing_font_is_caught(self):
        spec = (FX / "DESIGN.md").read_text().replace("fontFamily: DejaVu Sans", "fontFamily: NoSuchBrandFont")
        (self.tmp / "D.md").write_text(spec)
        page = (FX / "good.html").read_text().replace('"DejaVu Sans"', '"NoSuchBrandFont"')
        (self.tmp / "p.html").write_text(page)
        r = h.run(self.tmp / "D.md", str(self.tmp / "p.html"), self.tmp / "f")
        self.assertEqual(r["sub_receipts"]["FONT_PRINT_PDF"]["status"], "FAIL", r["sub_receipts"]["FONT_PRINT_PDF"])



class ReviewFixes20261111(unittest.TestCase):
    """Codex independent review 2026-11-11 (PR #219): HIGH size mismatch, MEDIUM malformed spec / viewport match."""

    def _png(self, d, name, w, hgt, split=None):
        from PIL import Image
        im = Image.new("RGB", (w, hgt), "white")
        for y in range(0, hgt, 40):  # same stripes in both so overlapping area matches
            for x in range(w):
                for k in range(8):
                    if y + k < hgt:
                        im.putpixel((x, y + k), (0, 0, 0))
        f = Path(d) / name
        im.save(f)
        return f

    def test_half_page_missing_is_fail(self):
        with tempfile.TemporaryDirectory() as d:
            ref = self._png(d, "phone.png", 120, 400)
            shot = self._png(d, "shot.png", 120, 200)
            r = h.visual_compare(ref, {"viewports": [{"id": "phone", "screenshot": str(shot)}]}, 90)
            self.assertEqual(r["status"], "FAIL", r)
            self.assertTrue(any("SIZE_MISMATCH" in f for f in r["findings"]), r["findings"])

    def test_same_size_same_image_passes(self):
        with tempfile.TemporaryDirectory() as d:
            ref = self._png(d, "phone.png", 120, 400)
            shot = self._png(d, "shot.png", 120, 400)
            r = h.visual_compare(ref, {"viewports": [{"id": "phone", "screenshot": str(shot)}]}, 90)
            self.assertEqual(r["status"], "PASS", r)

    def test_unmatched_reference_name_is_hold(self):
        with tempfile.TemporaryDirectory() as d:
            ref = self._png(d, "tablet.png", 120, 400)
            shot = self._png(d, "shot.png", 120, 400)
            vps = [{"id": "phone", "screenshot": str(shot)}, {"id": "desk", "screenshot": str(shot)}]
            r = h.visual_compare(ref, {"viewports": vps}, 90)
            self.assertEqual(r["status"], "HOLD", r)
            # a single viewport with a different name is not a match either (recheck 2026-11-11)
            r = h.visual_compare(ref, {"viewports": vps[:1]}, 90)
            self.assertEqual(r["status"], "HOLD", r)

    def test_malformed_yaml_spec_still_judges(self):
        spec = h.lint_spec("```yaml\ncolors: [unclosed\n```\n")
        self.assertEqual(spec["status"], "FAIL")
        subs = h.judge(spec, {"harness": {"ok": False, "error": "x"}})
        self.assertEqual(subs["HARNESS_HEALTH"]["status"], "HOLD")


class DashboardCriteria20261112(unittest.TestCase):
    """§20.1e DGC-24..30 and the PREMIUM port of SAVEY PG01-PG12 (2026-11-12)."""

    DASH = '\ndashboard:\n  template: T1_DECISION\n  question: "이번 달 계획 안에 있나?"\n  max_filled_cta: 1\n'

    def _spec(self, extra):
        txt = (FX / "DESIGN.md").read_text()
        return txt.replace("\n---\n", extra + "---\n", 1) if txt.startswith("---") else txt

    def test_dashboard_needs_question(self):
        r = h.lint_spec(self._spec("\ndashboard:\n  template: T1_DECISION\n"))
        self.assertIn("DASHBOARD_WITHOUT_QUESTION (DGC-24)", r["findings"])
        self.assertEqual(r["status"], "FAIL")

    def test_dashboard_unknown_template_fails(self):
        r = h.lint_spec(self._spec('\ndashboard:\n  template: BENTO\n  question: "q"\n'))
        self.assertTrue(any("DASHBOARD_TEMPLATE_UNKNOWN" in f for f in r["findings"]), r["findings"])

    def test_complete_dashboard_block_passes(self):
        r = h.lint_spec(self._spec(self.DASH))
        self.assertEqual(r["status"], "PASS", r["findings"])
        self.assertEqual(r["dashboard"]["max_filled_cta"], 1)

    def test_no_dashboard_block_is_unchanged(self):
        self.assertIsNone(h.lint_spec((FX / "DESIGN.md").read_text())["dashboard"])

    def _vp(self, **fv):
        base = {"id": "phone", "horizontal_overflow_px": 0, "text_colors": [], "primary_font_families": [],
                "font_check": {}, "gradient_text_count": 0, "mask_image_count": 0, "min_font_px": 16,
                "small_target_count": 0, "allcaps_label_count": 0, "screenshot_sha256": "x"}
        base["first_viewport"] = {"typeface_count": 1, "font_size_count": 4, "heavy_weight_pct": 0,
                                  "light_weight_count": 0, "big_shadow_count": 0, "text_shadow_count": 0,
                                  "radius_count": 1, "gradient_count": 0, "interactive_count": 3,
                                  "filled_cta_count": 1, "chars": 120, **fv}
        base["fixed_overlap_at_end"] = []
        return base

    def test_premium_is_advisory_and_never_fails_the_verdict(self):
        spec = h.lint_spec(self._spec(self.DASH))
        subs = h.judge(spec, {"harness": {"ok": True}, "print": {"bytes": 1},
                              "viewports": [self._vp(text_shadow_count=3, radius_count=6)]})
        self.assertEqual(subs["PREMIUM"]["status"], "ADVISORY")
        self.assertEqual(subs["PREMIUM"]["score"]["phone"], 9)
        subs["VISUAL_COMPARE"] = {"status": "NOT_APPLICABLE", "findings": []}
        self.assertEqual(h.verdict(subs), "PASS")

    def test_filled_cta_cap_comes_from_dashboard_block(self):
        spec = h.lint_spec(self._spec(self.DASH))
        subs = h.judge(spec, {"harness": {"ok": True}, "print": {"bytes": 1},
                              "viewports": [self._vp(filled_cta_count=3)]})
        self.assertEqual(subs["FIRST_VIEWPORT"]["status"], "ADVISORY")
        self.assertIn("DGC-27", " ".join(subs["FIRST_VIEWPORT"]["findings"]))

    def test_premium_threshold_override(self):
        txt = self._spec(self.DASH).replace("  source_commit: fixture\n",
                                            "  source_commit: fixture\n  thresholds:\n    premium:\n      chars: 600\n")
        self.assertEqual(h.lint_spec(txt)["premium"]["chars"], 600)


@unittest.skipUnless(browser_available(), "node+playwright not available")
class FixedOverlapRender(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_text_under_fixed_bar_at_scroll_end_is_flagged(self):
        r = h.run(FX / "DESIGN.md", str(FX / "fixed_overlap.html"), self.tmp / "o",
                  '[{"id":"phone","width":390,"height":640}]')
        fv = r["sub_receipts"]["FIRST_VIEWPORT"]
        self.assertEqual(fv["status"], "ADVISORY", fv)
        self.assertIn("마지막 기록", " ".join(fv["findings"]))
        self.assertTrue((self.tmp / "o" / "phone.first.png").exists())

    def test_padded_page_with_fixed_bar_passes(self):
        page = (FX / "fixed_overlap.html").read_text().replace("main{max-width:640px;padding:24px 16px}",
                                                                "main{max-width:640px;padding:24px 16px 120px}")
        (self.tmp / "p.html").write_text(page)
        r = h.run(FX / "DESIGN.md", str(self.tmp / "p.html"), self.tmp / "p",
                  '[{"id":"phone","width":390,"height":640}]')
        self.assertEqual(r["sub_receipts"]["FIRST_VIEWPORT"]["status"], "PASS", r["sub_receipts"]["FIRST_VIEWPORT"])

class DashboardSemantics20261113(unittest.TestCase):
    """§20.1g: DGC-25 decision metric size, DGC-26 status vs burn pace, same-shape card row."""
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, html):
        (self.tmp / "d.html").write_text(html)
        return h.run(FX / "DESIGN_dashboard.md", str(self.tmp / "d.html"), self.tmp / "o",
                     '[{"id":"phone","width":390,"height":844}]')

    def test_bad_dashboard_is_flagged_on_all_three(self):
        r = self._run((FX / "dashboard_semantics.html").read_text())
        fv = " ".join(r["sub_receipts"]["FIRST_VIEWPORT"]["findings"])
        self.assertIn("(DGC-25)", fv)
        self.assertIn("62% used at 23%", fv)
        self.assertIn("same-shape card row 4x", " ".join(r["sub_receipts"]["GENERIC_TELLS"]["findings"]))
        self.assertNotEqual(r["verdict"], "FAIL")  # advisory only (DGC-12)

    def test_fixed_dashboard_passes(self):
        html = ((FX / "dashboard_semantics.html").read_text()
                .replace("계획대로 잘 가고 있어요!", "쓰는 속도가 빨라요.")
                .replace(".spent{font-size:34px", ".spent{font-size:16px").replace(".left{font-size:16px", ".left{font-size:34px")
                .replace("grid-template-columns:repeat(4,1fr)", "grid-template-columns:1fr"))
        r = self._run(html)
        self.assertEqual(r["sub_receipts"]["FIRST_VIEWPORT"]["status"], "PASS", r["sub_receipts"]["FIRST_VIEWPORT"])
        self.assertEqual(r["sub_receipts"]["GENERIC_TELLS"]["status"], "PASS", r["sub_receipts"]["GENERIC_TELLS"])

    def test_missing_selector_is_reported_not_silent(self):
        r = self._run((FX / "dashboard_semantics.html").read_text().replace('class="left"', 'class="other"'))
        self.assertIn("decision_metric_selector not found", " ".join(r["sub_receipts"]["FIRST_VIEWPORT"]["findings"]))


if __name__ == "__main__":
    unittest.main()
