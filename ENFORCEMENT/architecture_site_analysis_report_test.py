#!/usr/bin/env python3
"""Offline site report evidence and output regression."""
import hashlib
import importlib.util
import json
import contextlib
import shutil
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


@contextlib.contextmanager
def fixture_dir():
    root = ROOT / ("site_analysis_test_" + uuid.uuid4().hex)
    root.mkdir()
    try:
        yield root
    finally:
        shutil.rmtree(root)

spec = importlib.util.spec_from_file_location("site_report", ROOT / "TOOLS" / "ARCHIGROW_SITE_ANALYSIS_REPORT.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)
PID = "SYNTHETIC_FIXTURE"
PNU = "1154510300108280004"


def source():
    return {"project_id": PID, "pnu": PNU, "status": "HOLD", "failure_class": "DESIGN_PARAMETERS_MISSING",
            "eum": {"pnu": PNU, "area_m2": 1200, "address": "SYNTHETIC FIXTURE PARCEL",
                    "evidence_sha256": "a"*64, "document_status": "ONLINE_VIEW_NOT_LEGAL_CERTIFICATE",
                    "parcel_identity_status": "VISIBLE_ADDRESS_MATCHES_PNU_BOUND_CADASTRAL"},
            "parcel": {"pnu": PNU, "projected_crs": "EPSG:5186", "projected_origin_m": [200000, 500000],
                       "polygon_local_m": [[0, 0], [40, 0], [40, 30], [0, 30]],
                       "polygon_area_m2": 1200, "source": "VWORLD_LP_PA_CBND_BUBUN",
                       "evidence_sha256": "b"*64},
            "comparison": {"result": "MATCH_WITHIN_SCREENING_TOLERANCE"}}


def write(path, doc):
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


class SiteReportTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("pptx"), "python-pptx unavailable in this interpreter")
    def test_editable_pptx_has_seven_slides_and_source_values(self):
        from pptx import Presentation
        from pptx.enum.shapes import MSO_SHAPE_TYPE
        from pptx.util import Inches
        with fixture_dir() as root:
            inp = write(root / "site.json", source())
            result = R.build(PID, inp, root / "out")
            self.assertEqual(result["capabilities"]["pptx"], "AVAILABLE")
            path = root / "out" / "site_analysis.pptx"
            self.assertGreater(path.stat().st_size, 10000)
            deck = Presentation(path)
            self.assertEqual(len(deck.slides), 7)
            self.assertAlmostEqual(deck.slide_width, Inches(13.333), delta=1000)
            self.assertEqual(deck.slide_height, Inches(7.5))
            all_text = "\n".join(shape.text for slide in deck.slides for shape in slide.shapes if shape.has_text_frame)
            for value in (PID, PNU, "1200 m²", "NOT_REQUIRED_NOT_PROVIDED",
                          "No solar study supplied", "no legal certification"):
                self.assertIn(value, all_text)
            parcel = [shape for shape in deck.slides[1].shapes if shape.name == "Editable parcel boundary"]
            self.assertEqual(len(parcel), 1)
            self.assertEqual(parcel[0].shape_type, MSO_SHAPE_TYPE.FREEFORM)
            for slide in deck.slides:
                self.assertTrue(any(shape.has_text_frame for shape in slide.shapes))
                for shape in slide.shapes:
                    self.assertGreaterEqual(shape.left, 0)
                    self.assertGreaterEqual(shape.top, 0)
                    self.assertLessEqual(shape.left + shape.width, deck.slide_width + 1000)
                    self.assertLessEqual(shape.top + shape.height, deck.slide_height + 1000)

    def test_pptx_failure_is_explicit_hold(self):
        with fixture_dir() as root:
            inp = write(root / "site.json", source())
            with patch.object(R, "_pptx", side_effect=RuntimeError("save failed")):
                result = R.build(PID, inp, root / "out")
            self.assertEqual(result["report_status"], "HOLD")
            self.assertIn("FAILED:RuntimeError:save failed", result["capabilities"]["pptx"])
            self.assertFalse((root / "out" / "site_analysis.pptx").exists())
            saved = json.loads((root / "out" / "analysis_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["capabilities"]["pptx"], result["capabilities"]["pptx"])

    def test_source_pass_independent_of_design_and_output_is_source_bound(self):
        with fixture_dir() as root:
            inp = write(root / "site.json", source())
            result = R.build(PID, inp, root / "out")
            self.assertEqual(result["source_status"], "PASS")
            self.assertEqual(result["design_status"], "NOT_REQUIRED_NOT_PROVIDED")
            self.assertEqual(result["area"]["eum_area_m2"], 1200)
            self.assertEqual(result["area"]["polygon_area_m2"], 1200)
            self.assertEqual(result["area"]["delta_m2"], 0)
            self.assertEqual(result["sections"]["site_source"]["source"]["sha256"], hashlib.sha256(inp.read_bytes()).hexdigest())
            self.assertEqual(result["page_count"], 7)
            self.assertEqual(result["available_section_count"], 3)
            svg = (root / "out" / "site_map.svg").read_text(encoding="utf-8")
            html = (root / "out" / "site_analysis.html").read_text(encoding="utf-8")
            self.assertIn('id="parcel"', svg)
            self.assertIn('M100.000,625.000', svg)
            self.assertIn('data-layer="parcel"', html)
            self.assertIn("No solar study report", html)
            self.assertNotIn("bus stop", html.lower())
            self.assertEqual(html.count('class="page"'), 7)

    def test_exact_project_binding_all_inputs(self):
        with fixture_dir() as root:
            inp = write(root / "site.json", source())
            with self.assertRaisesRegex(R.ReportHold, "PROJECT_ID_MISMATCH:site_source"):
                R.build("OTHER", inp, root / "out")
            ctx = write(root / "context.json", {"schema": "ARCHIGROW_CONTEXT_OBSTACLES_V1", "project_id": "OTHER"})
            with self.assertRaisesRegex(R.ReportHold, "PROJECT_ID_MISMATCH:context"):
                R.build(PID, inp, root / "out", context=ctx)
            self.assertFalse((root / "out" / "site_analysis.html").exists())

    def test_area_mismatch_and_tampered_geometry_hold(self):
        with fixture_dir() as root:
            doc = source()
            doc["eum"]["area_m2"] = 1300
            doc["comparison"]["result"] = "HOLD_AREA_MISMATCH"
            r = R.build(PID, write(root / "site.json", doc), root / "out")
            self.assertEqual(r["source_status"], "HOLD")
            self.assertEqual(r["area"]["delta_m2"], -100)
            doc["parcel"]["polygon_area_m2"] = 1500
            with self.assertRaisesRegex(R.ReportHold, "AREA_EVIDENCE_INVALID"):
                R.build(PID, write(root / "site.json", doc), root / "other")

    def test_missing_evidence_hold(self):
        with fixture_dir() as root:
            doc = {"project_id": PID, "status": "HOLD", "failure_class": "VWORLD_FREE_API_KEY_NOT_CONFIGURED"}
            r = R.build(PID, write(root / "site.json", doc), root / "out")
            self.assertEqual(r["source_status"], "HOLD")
            self.assertIsNone(r["area"])
            self.assertIn("Parcel geometry is unavailable", (root / "out" / "site_analysis.html").read_text(encoding="utf-8"))

    def test_optional_provenance_unknown_height_and_no_invented_solar(self):
        with fixture_dir() as root:
            inp = write(root / "site.json", source())
            ctx = {"schema": "ARCHIGROW_CONTEXT_OBSTACLES_V1", "project_id": PID,
                   "source_class": "SYNTHETIC_FIXTURE", "completeness": {"height_unknown_count": 1},
                   "obstacles": [{"id": "B1", "footprint_m": [[45, 0], [50, 0], [50, 10], [45, 10]],
                                  "footprint_area_m2": 50, "height_m": None, "height_source": "UNKNOWN"}]}
            ctx_path = write(root / "context.json", ctx)
            solar = {"schema": "ARCHIGROW_SOLAR_STUDY_REPORT_V1", "project_id": PID,
                     "result_status": "LIMITED", "dates": [{"id": "D1", "date": "2026-06-21"}],
                     "claims": {"metric_kind": "GEOMETRIC_DIRECT_SUN_EXPOSURE_LINE_OF_SIGHT",
                                "legal_sunlight_compliance": "NOT_EVALUATED"}}
            solar_path = write(root / "solar.json", solar)
            massing = {"schema": "ARCHIGROW_MASSING_RESULT_V1", "project_id": PID,
                       "rule_source_status": "UNVERIFIED_DEMO", "options": []}
            mass_path = write(root / "massing.json", massing)
            r = R.build(PID, inp, root / "out", ctx_path, solar_path, mass_path)
            self.assertEqual(r["available_section_count"], 6)
            for key, path in (("context", ctx_path), ("solar", solar_path), ("massing", mass_path)):
                self.assertEqual(r["sections"][key]["source"]["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            html = (root / "out" / "site_analysis.html").read_text(encoding="utf-8")
            self.assertIn("Unknown", html)
            self.assertIn("SYNTHETIC_FIXTURE", html)
            self.assertIn("NOT_EVALUATED", html)
            self.assertIn('id="buildings"', (root / "out" / "site_map.svg").read_text(encoding="utf-8"))

    def test_conflicting_collector_status_and_evidence_hash_hold(self):
        with fixture_dir() as root:
            doc = source()
            doc["failure_class"] = "EUM_VISIBLE_ADDRESS_CADASTRAL_MISMATCH"
            r = R.build(PID, write(root / "site.json", doc), root / "out")
            self.assertEqual(r["source_status"], "HOLD")
            doc["eum"]["evidence_sha256"] = "missing"
            with self.assertRaisesRegex(R.ReportHold, "SOURCE_EVIDENCE_HASH_MISSING"):
                R.build(PID, write(root / "site.json", doc), root / "other")

    def test_optional_hash_and_geometry_binding(self):
        with fixture_dir() as root:
            inp = write(root / "site.json", source())
            mass = write(root / "massing.json", {"schema": "ARCHIGROW_MASSING_RESULT_V1", "project_id": PID,
                                                 "site_polygon": [[0,0],[1,0],[0,1]], "options": []})
            with self.assertRaisesRegex(R.ReportHold, "MASSING_SITE_POLYGON_MISMATCH"):
                R.build(PID, inp, root / "out", massing=mass)
            doc = json.loads(mass.read_text(encoding="utf-8"))
            doc["site_polygon"] = source()["parcel"]["polygon_local_m"]
            write(mass, doc)
            solar = write(root / "solar.json", {"schema": "ARCHIGROW_SOLAR_STUDY_REPORT_V1",
                                                 "project_id": PID, "input_hashes": {"massing_result": "0"*64}})
            with self.assertRaisesRegex(R.ReportHold, "SOLAR_INPUT_HASH_MISMATCH:massing"):
                R.build(PID, inp, root / "out", solar=solar, massing=mass)

    def test_selected_option_is_bound_in_standalone_svg(self):
        import xml.etree.ElementTree as ET
        with fixture_dir() as root:
            site_path = write(root / "site.json", source())
            massing_path = write(root / "massing.json", {
                "schema": "ARCHIGROW_MASSING_RESULT_V1", "project_id": PID,
                "rule_source_status": "SYNTHETIC_UNVERIFIED",
                "options": [
                    {"strategy": "A test", "kpi": {"gross_floor_area_m2": 2100, "max_height_m": 12}},
                    {"strategy": "C test", "kpi": {"gross_floor_area_m2": 3100, "max_height_m": 20}},
                ]})
            a = R.build(PID, site_path, root / "out_a", massing=massing_path, option="A")
            c = R.build(PID, site_path, root / "out_c", massing=massing_path, option="C")
            self.assertEqual(a["selected_option"]["id"], "O1")
            self.assertEqual(c["selected_option"]["id"], "O2")
            def selected(folder):
                tree = ET.parse(root / folder / "site_map.svg")
                ns = {"svg": "http://www.w3.org/2000/svg"}
                meta = tree.find(".//svg:metadata[@id='site-source-selection']", ns)
                self.assertIsNotNone(meta)
                return json.loads(meta.text)
            first, last = selected("out_a"), selected("out_c")
            self.assertEqual(first["selected_option"]["id"], "O1")
            self.assertEqual(last["selected_option"]["id"], "O2")
            self.assertEqual(last["selected_option"]["gfa_m2"], 3100)
            self.assertEqual(last["project_id"], PID)
            self.assertEqual(last["pnu"], PNU)
            self.assertFalse(last["legal_certification"])
            self.assertEqual(last["input_sha256"]["massing"], hashlib.sha256(massing_path.read_bytes()).hexdigest())

    def test_self_crossing_parcel_rejected(self):
        with fixture_dir() as root:
            doc = source()
            doc["parcel"]["polygon_local_m"] = [[0,0],[40,30],[40,0],[0,30]]
            with self.assertRaisesRegex(R.ReportHold, "PARCEL_RING_SELF_INTERSECTION"):
                R.build(PID, write(root / "site.json", doc), root / "out")


if __name__ == "__main__":
    unittest.main()
