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

    def test_malformed_yaml_spec_still_judges(self):
        spec = h.lint_spec("```yaml\ncolors: [unclosed\n```\n")
        self.assertEqual(spec["status"], "FAIL")
        subs = h.judge(spec, {"harness": {"ok": False, "error": "x"}})
        self.assertEqual(subs["HARNESS_HEALTH"]["status"], "HOLD")

if __name__ == "__main__":
    unittest.main()
