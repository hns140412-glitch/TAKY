#!/usr/bin/env python3
import importlib.util, json, shutil, tempfile, unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("m", ROOT / "TOOLS" / "ARCHIGROW_AERIAL_RASTER_QA.py")
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)


def mask(shift=0, labels=(1, 2), size=(40, 30)):
    a = np.zeros((size[1], size[0]), np.uint8)
    if 1 in labels: a[5:15, 5 + shift:15 + shift] = 1
    if 2 in labels: a[18:26, 20:35] = 2
    return a


class T(unittest.TestCase):
    def run_case(self, base=None, cand=None, size=(40, 30), prov=True, drop=None, **extra):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        base = mask() if base is None else base
        cand = mask() if cand is None else cand
        Image.fromarray(base, "L").save(d / "am.png"); Image.fromarray(cand, "L").save(d / "bm.png")
        Image.new("RGB", (40, 30)).save(d / "a.png"); Image.new("RGB", size).save(d / "b.png")
        man = {"base_image": "a.png", "candidate_image": "b.png", "base_mask": "am.png", "candidate_mask": "bm.png",
               "provenance": {"rights_basis": "owner licence", "attestation": "user attested"} if prov
               else {"rights_basis": " ", "attestation": ""}}
        man.update(extra)
        if drop: man[drop] = "nope.png"
        return M.evaluate(man, d), d, man

    def test_match_provisional_never_pass(self):
        r, _, _ = self.run_case(output_mask_extraction_attestation="x")
        self.assertEqual(r["status"], "PROVISIONAL"); self.assertFalse(r["real_output_pass"])
        self.assertIn("NOT_REAL_IMAGE_GEOMETRY_PROOF", r["evidence_class"])
        self.assertEqual(r["objects"]["1"]["iou"], 1.0); self.assertEqual(len(r["hashes"]), 4)

    def test_shift_holds(self):
        r, _, _ = self.run_case(cand=mask(shift=4))
        self.assertEqual(r["status"], "HOLD"); self.assertIn("GEOMETRY_DRIFT:1:CENTROID", r["reasons"])
        self.assertAlmostEqual(r["objects"]["1"]["centroid_px"], 4.0)

    def test_missing_label_holds(self):
        r, _, _ = self.run_case(cand=mask(labels=(1,)))
        self.assertEqual(r["status"], "HOLD")
        self.assertTrue(any(x.startswith("LABEL_SET_MISMATCH") for x in r["reasons"]))

    def test_swapped_labels_hold(self):
        sw = mask().copy(); sw[sw == 1] = 9; sw[sw == 2] = 1; sw[sw == 9] = 2
        r, _, _ = self.run_case(cand=sw)
        self.assertEqual(r["status"], "HOLD"); self.assertIn("GEOMETRY_DRIFT:1:IOU", r["reasons"])

    def test_shape_mismatch_holds(self):
        r, _, _ = self.run_case(size=(41, 30))
        self.assertTrue(any(x.startswith("SIZE_MISMATCH") for x in r["reasons"]))

    def test_empty_holds(self):
        z = np.zeros((30, 40), np.uint8)
        r, _, _ = self.run_case(base=z, cand=z)
        self.assertEqual(r["status"], "HOLD"); self.assertIn("NO_OBJECTS", r["reasons"])

    def test_provenance_unverified_holds(self):
        r, _, _ = self.run_case(prov=False)
        self.assertEqual(r["status"], "HOLD"); self.assertIn("PROVENANCE_UNVERIFIED", r["reasons"])

    def test_missing_file_holds(self):
        r, _, _ = self.run_case(drop="candidate_mask")
        self.assertEqual(r["status"], "HOLD")
        self.assertTrue(any(x.startswith("INPUT_UNREADABLE:candidate_mask") for x in r["reasons"]))

    def test_rgb_mask_rejected(self):
        r, d, man = self.run_case()
        Image.new("RGB", (40, 30)).save(d / "bm.png")
        self.assertEqual(M.evaluate(man, d)["status"], "HOLD")

    def test_loosened_thresholds_hold_shifted_object(self):
        loose = [{"max_centroid_px": 100.0}, {"max_bbox_px": 999}, {"min_iou": 0.0},
                 {"max_pixel_delta_ratio": 1.0}, {"min_iou": float("nan")}, {"max_centroid_px": float("inf")},
                 {"max_bbox_px": True}, {"max_bbox_px": "2"}, {"max_bbox_px": -1}, {"min_iou": 1.5},
                 {"unknown_key": 1}, {"max_centroid_px": None}]
        for th in loose:
            with self.subTest(thresholds=th):
                r, _, _ = self.run_case(cand=mask(shift=4), thresholds=th)
                self.assertEqual(r["status"], "HOLD")
                self.assertTrue(any(x.startswith("THRESHOLD_INVALID") for x in r["reasons"]), r["reasons"])
                self.assertFalse(r["objects"])

    def test_non_object_thresholds_hold(self):
        for raw in (["min_iou"], "strict", 0.9):
            with self.subTest(thresholds=raw):
                r, _, _ = self.run_case(thresholds=raw)
                self.assertEqual(r["status"], "HOLD")
                self.assertIn("THRESHOLD_INVALID:not_object", r["reasons"])

    def test_tightened_thresholds_allowed(self):
        r, _, _ = self.run_case(thresholds={"max_centroid_px": 0.5, "min_iou": 1.0, "max_bbox_px": 0})
        self.assertEqual(r["status"], "PROVISIONAL")
        self.assertEqual(r["thresholds"]["max_centroid_px"], 0.5)

    def test_cli_receipt_exit_codes(self):
        _, d, man = self.run_case()
        (d / "m.json").write_text(json.dumps(man)); out = d / "r.json"
        self.assertEqual(M.main([str(d / "m.json"), "--output", str(out)]), 0)
        self.assertEqual(json.loads(out.read_text())["status"], "PROVISIONAL")
        self.assertEqual(M.main([str(d / "missing.json")]), 1)


if __name__ == "__main__":
    unittest.main()
