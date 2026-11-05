#!/usr/bin/env python3
import importlib.util, json, re, shutil, tempfile, unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sp", ROOT / "TOOLS" / "ARCHIGROW_AERIAL_STYLE_PREVIEW.py")
S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
SVG = ROOT / "site_analysis_visual_fixture" / "urban_demo" / "out" / "site_map.svg"


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = Path(tempfile.mkdtemp()); cls.addClassCleanup(shutil.rmtree, cls.d, True)
        cls.P, cls.n = S.render(SVG, cls.d / "a")
        cls.rec = S.verify(cls.P, SVG, cls.n)

    def test_count_and_receipt(self):
        g = re.search(r'<g id="buildings"[^>]*>(.*?)</g>', SVG.read_text(encoding="utf-8"), re.S).group(1)
        self.assertEqual(self.n, g.count("<path")); self.assertEqual(self.n, 18)
        r = self.rec
        self.assertEqual(r["extraction_holds"], [])
        self.assertIn(r["status"], ("PROVISIONAL", "HOLD")); self.assertNotEqual(r["status"], "PASS")
        self.assertEqual(r["status"], "PROVISIONAL")
        self.assertEqual(len(r["qa"]["objects"]), 18); self.assertFalse(r["qa"]["real_output_pass"])
        self.assertEqual(r["source_sha256"], S.sha(SVG)); self.assertEqual(r["banner"], S.BANNER)
        self.assertEqual(r["real_aerial_status"], "NOT_VERIFIED")
        self.assertEqual(r["files"]["candidate_image"]["sha256"], S.sha(self.P["candidate_image"]))

    def test_visual_changed_and_reproducible(self):
        b, c = (np.array(Image.open(self.P[k]).convert("RGB")) for k in ("base_image", "candidate_image"))
        self.assertGreater(np.count_nonzero((b != c).any(axis=2)), 100000)
        P2, _ = S.render(SVG, self.d / "b")
        for k in ("base_image", "candidate_image", "base_mask", "comparison"):
            self.assertEqual(S.sha(self.P[k]), S.sha(P2[k]))

    def test_candidate_mask_is_rgb_derived(self):
        bm = np.array(Image.open(self.P["base_mask"])); cm = np.array(Image.open(self.P["candidate_mask"]))
        self.assertEqual(set(np.unique(cm)) - {0}, set(range(1, 19)))
        d = np.count_nonzero((bm > 0) != (cm > 0))
        self.assertTrue(0 < d < 100)  # only the joint seam differs: measured from RGB, not copied

    def test_pixel_injected_drift_holds_after_extraction(self):
        P, n = S.render(SVG, self.d / "c")
        a = np.array(Image.open(P["candidate_image"]))
        ys, xs = np.nonzero(np.array(Image.open(P["base_mask"])) == 1)
        a[ys.min():ys.max() + 1, xs.max() + 1:xs.max() + 9] = (100, 100, 112)  # grow footprint 1 by 8px
        Image.fromarray(a).save(P["candidate_image"])
        r = S.verify(P, SVG, n)
        self.assertEqual(r["extraction_holds"], []); self.assertEqual(r["status"], "HOLD")
        self.assertTrue(any(x.startswith("GEOMETRY_DRIFT:1") for x in r["qa"]["reasons"]))
        a[300:310, 5:15] = (100, 100, 112)  # extra isolated region
        Image.fromarray(a).save(P["candidate_image"])
        r = S.verify(P, SVG, n)
        self.assertEqual(r["status"], "HOLD"); self.assertTrue(r["extraction_holds"])

    def test_bad_inputs_fail_closed(self):
        with self.assertRaises(OSError): S.render(self.d / "missing.svg", self.d / "x")
        bad = self.d / "bad.svg"
        for body in ('<path d="M0 0 C 1 1 2 2 3 3 Z"/>', '<circle r="3"/>', '<path d="M1 1 L5 1 L5 5"/>'):
            bad.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800"><g id="buildings">%s</g></svg>' % body)
            with self.assertRaises(ValueError): S.parse_svg(bad)


class PhotoMode(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.d, True)
        rng = np.random.default_rng(7)
        self.arr = rng.integers(0, 256, (40, 56, 3), dtype=np.uint8)
        self.src = self.d / "src.png"; Image.fromarray(self.arr).save(self.src)
        self.rc = self.d / "rc.json"; self._receipt(S.sha(self.src))
        self.out = self.d / "out"

    def _receipt(self, digest):
        self.rc.write_text(json.dumps({"source": "t", "service": "t", "bytes": self.src.stat().st_size, "sha256": digest,
                                       "image_size": [56, 40], "rights_basis": "public domain test"}), encoding="utf-8")

    def test_photo_tone_only_verified_reproducible(self):
        before = S.sha(self.src)
        r = S.run_photo(self.src, self.out, self.rc)
        self.assertEqual((r["status"], r["proof_label"], r["max_pixel_residual"]), ("PROVISIONAL", "PIXELWISE_TRANSFORM_VERIFIED", 0))
        self.assertEqual(r["mode"], "PHOTO_PIXELWISE_TONE_ONLY"); self.assertIn("NOT_REAL_IMAGE_GEOMETRY_PROOF", r["disclaimers"])
        self.assertEqual(r["attribution"], "public domain test"); self.assertEqual(r["source_sha256"], before)
        self.assertEqual(r["result_sha256"], S.sha(self.out / "photo_enhanced.png"))
        out = np.array(Image.open(self.out / "photo_enhanced.png"))
        self.assertEqual(out.shape, self.arr.shape); self.assertGreater(r["changed_pixel_fraction"], 0.5)
        self.assertEqual(S.sha(self.src), before)
        S.run_photo(self.src, self.d / "out2", self.rc)
        self.assertEqual(S.sha(self.out / "photo_enhanced.png"), S.sha(self.d / "out2" / "photo_enhanced.png"))
        self.assertEqual(sorted(p.name for p in self.out.iterdir()), ["photo_comparison.png", "photo_enhanced.png", "photo_receipt.json"])

    def test_photo_one_pixel_tamper_and_warp_hold(self):
        S.run_photo(self.src, self.out, self.rc)
        png = self.out / "photo_enhanced.png"; good = np.array(Image.open(png))
        t = good.copy(); t[5, 7, 1] ^= 1; Image.fromarray(t).save(png)
        r = S.verify_photo(self.src, png, self.rc)
        self.assertEqual(r["status"], "HOLD"); self.assertEqual(r["residual_pixel_count"], 1)
        Image.fromarray(np.roll(good, 4, axis=1)).save(png)  # 4px warp
        self.assertEqual(S.verify_photo(self.src, png, self.rc)["status"], "HOLD")
        Image.fromarray(good[:, :-1]).save(png)  # size change
        r = S.verify_photo(self.src, png, self.rc)
        self.assertEqual(r["status"], "HOLD"); self.assertTrue(any(h.startswith("SIZE_CHANGED") for h in r["holds"]))

    def test_photo_bad_receipt_and_format_hold(self):
        self._receipt("0" * 64)
        r = S.run_photo(self.src, self.out, self.rc)
        self.assertEqual(r["status"], "HOLD"); self.assertIn("SOURCE_SHA256_MISMATCH", r["holds"])
        self.assertFalse((self.out / "photo_enhanced.png").exists())
        self.assertEqual(S.run_photo(self.src, self.d / "o3", self.d / "none.json")["status"], "HOLD")
        self.rc.write_text("{bad", encoding="utf-8")
        self.assertEqual(S.run_photo(self.src, self.d / "o4", self.rc)["status"], "HOLD")
        gif = self.d / "x.gif"; Image.fromarray(self.arr).convert("P").save(gif)
        self.rc.write_text(json.dumps({"source": "t", "service": "t", "bytes": gif.stat().st_size, "sha256": S.sha(gif),
                                       "image_size": [56, 40], "rights_basis": "x"}), encoding="utf-8")
        with self.assertRaises(ValueError): S.run_photo(gif, self.d / "o5", self.rc)
        self.assertEqual(S.main(["--photo", str(gif), str(self.d / "o6"), "--source-receipt", str(self.rc)]), 2)

    def test_photo_cli_and_svg_command_coexist(self):
        self.assertEqual(S.main(["--photo", str(self.src), str(self.out), "--source-receipt", str(self.rc)]), 0)
        self.assertEqual(S.main(["--photo", str(self.src), str(self.out)]), 2)


if __name__ == "__main__":
    unittest.main()
