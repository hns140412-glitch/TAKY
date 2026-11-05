#!/usr/bin/env python3
"""ArchiGrow SITE_CONTEXT + SOLAR_STUDY regression. Synthetic/fixture data only; no network, no legal claims.

Run with the free-geo venv (pvlib, shapely, pyproj, numpy, pandas):
  D:/Git PWA/TAKY_AI_WORKBENCH/.venv_archigrow_geo/Scripts/python.exe -I ENFORCEMENT/architecture_solar_context_test.py
"""
import copy, importlib.util, json, math, os, shutil, tempfile, unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "ENFORCEMENT" / "fixtures" / "archigrow_solar"


def mod(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "TOOLS" / (name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


try:
    import pvlib, shapely, pyproj  # noqa: F401
    HAVE = True
except ImportError:
    HAVE = False

SC = mod("ARCHIGROW_SOLAR_CONTEXT")
BC = mod("ARCHIGROW_BUILDING_CONTEXT")
M = mod("ARCHIGROW_MASSING")
P = mod("ARCHIGROW_PIPELINE_RUN")
PS = mod("ARCHIGROW_PARCEL_SOURCE")


def jl(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def small_cfg(**over):
    """One winter-solstice date, 20-min steps: keeps the suite fast."""
    cfg = jl("solar_study_input.json")
    cfg["time"]["dates"] = [{"id": "WINTER_SOLSTICE", "date": "2026-12-22"}]
    cfg["time"]["step_minutes"] = 20
    cfg["ground_grid"] = {"spacing_m": 6, "margin_m": 6, "window_id": "W0900_1500"}
    cfg.update(over)
    return cfg


def wall_scene(wall_h=20.0, dists=(20.0, 60.0), z=0.0):
    """Wide E-W wall south of two ground receivers lying due north of it (hand-checkable)."""
    ctx = {"schema": "ARCHIGROW_CONTEXT_OBSTACLES_V1", "project_id": "WALL_TEST", "source_class": "SYNTHETIC_FIXTURE",
           "scene": {"kind": "LOCAL_M"}, "obstacles": [{
               "id": "WALL", "footprint_m": [[-300, 0], [300, 0], [300, 2], [-300, 2]], "height_m": wall_h,
               "height_min_m": wall_h, "height_max_m": wall_h, "height_source": "SYNTHETIC_FIXTURE_DECLARED_HEIGHT", "confidence": "SYNTHETIC"}]}
    mass_in = jl("massing_site_input.json")
    mass_in["project_id"] = "WALL_TEST"
    mass_in["site_polygon"] = [[-20, 400], [20, 400], [20, 431], [-20, 431]]  # far away, harmless
    cfg = small_cfg(project_id="WALL_TEST")
    cfg["receivers"] = {"points": [{"id": "D%d" % int(d), "x": 0, "y": 2 + d, "z_above_ground_m": z} for d in dists]}
    cfg["ground_grid"] = None
    cfg["time"]["step_minutes"] = 10
    return cfg, M.generate(mass_in), ctx


def study(cfg, massing, ctx):
    return SC.run_study(cfg, massing, ctx)


@unittest.skipUnless(HAVE, "free pvlib/shapely/pyproj not installed in this interpreter")
class SolarPhysics(unittest.TestCase):
    frame = {"lat": 37.5665, "lon": 126.978, "east": [1.0, 0.0], "north": [0.0, 1.0]}

    def test_seoul_winter_solstice_noon_sun_is_south_and_correct_height(self):
        steps, info = SC.sun_steps(self.frame, "2026-12-22", "Asia/Seoul", "CIVIL_KST", 11 * 60, 14 * 60, 1, 0.0)
        top = max(steps, key=lambda s: s["elevation_deg"])
        self.assertAlmostEqual(top["azimuth_deg"], 180.0, delta=1.0)
        # 90 - latitude + declination(-23.44) ; solar elevation at culmination
        self.assertAlmostEqual(top["elevation_deg"], 90 - 37.5665 - 23.44, delta=0.6)
        # civil KST solar noon is ~12:30 for 126.98E (not 12:00): proves tz/longitude handling
        self.assertTrue(12 * 60 + 25 <= top["minute"] <= 12 * 60 + 36, top["label"])
        self.assertTrue(top["civil_time"].endswith("+09:00"))
        self.assertAlmostEqual(info["longitude_correction_min"], -32.088, places=2)

    def test_summer_solstice_is_higher_and_winter_sunrise_is_after_0730_kst(self):
        w, _ = SC.sun_steps(self.frame, "2026-12-22", "Asia/Seoul", "CIVIL_KST", 6 * 60, 18 * 60, 5, 0.0)
        s, _ = SC.sun_steps(self.frame, "2026-06-21", "Asia/Seoul", "CIVIL_KST", 6 * 60, 18 * 60, 5, 0.0)
        self.assertGreater(max(x["elevation_deg"] for x in s) - max(x["elevation_deg"] for x in w), 40)
        rise = next(x for x in w if x["up"])
        self.assertTrue(7 * 60 + 30 <= rise["minute"] <= 7 * 60 + 55, rise["label"])

    def test_morning_south_east_afternoon_south_west(self):
        st, _ = SC.sun_steps(self.frame, "2026-12-22", "Asia/Seoul", "CIVIL_KST", 9 * 60, 17 * 60, 60, 3.0)
        by = {s["label"]: s for s in st}
        self.assertTrue(90 < by["09:00"]["azimuth_deg"] < 150)
        self.assertTrue(210 < by["16:00"]["azimuth_deg"] < 270)

    def test_local_apparent_solar_basis_puts_solar_noon_at_south(self):
        st, info = SC.sun_steps(self.frame, "2026-12-22", "Asia/Seoul", "LOCAL_APPARENT_SOLAR", 12 * 60, 12 * 60 + 1, 1, 0.0)
        self.assertAlmostEqual(st[0]["azimuth_deg"], 180.0, delta=1.0)
        self.assertAlmostEqual(info["solar_minus_civil_offset_min"], -32.088 + info["equation_of_time_min"], places=2)

    def test_shadow_points_opposite_the_sun_and_has_trigonometric_length(self):
        shadow = SC.Shadow(2000)
        poly = shadow.Polygon([(0, 0), (0.2, 0), (0.2, 0.2), (0, 0.2)])
        steps, _ = SC.sun_steps(self.frame, "2026-12-22", "Asia/Seoul", "CIVIL_KST", 9 * 60, 16 * 60, 60, 3.0)
        for st in steps:
            u = shadow.union_of([(poly, 0.0, 30.0)], st, 0.0)
            cx, cy = u.centroid.x - 0.1, u.centroid.y - 0.1
            az = math.degrees(math.atan2(cx, cy)) % 360
            want = (st["azimuth_deg"] + 180) % 360
            self.assertAlmostEqual((az - want + 180) % 360 - 180, 0, delta=1.0, msg=st["label"])
            far = max(math.hypot(x - 0.1, y - 0.1) for x, y in u.exterior.coords)
            self.assertAlmostEqual(far, 30.0 / math.tan(math.radians(st["elevation_deg"])), delta=0.6 + 0.01 * far)
        morning, afternoon = steps[0], steps[-1]
        um = shadow.union_of([(poly, 0, 30)], morning, 0)
        ua = shadow.union_of([(poly, 0, 30)], afternoon, 0)
        self.assertLess(um.centroid.x, 0)      # morning shadow falls to the west
        self.assertGreater(ua.centroid.x, 0)   # afternoon shadow falls to the east
        self.assertGreater(um.centroid.y, 0)   # winter shadows fall north

    def test_taller_building_casts_larger_shadow_monotonically(self):
        shadow = SC.Shadow(2000)
        poly = shadow.Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        st = SC.sun_steps(self.frame, "2026-12-22", "Asia/Seoul", "CIVIL_KST", 11 * 60, 12 * 60, 60, 3.0)[0][0]
        areas = [shadow.union_of([(poly, 0, h)], st, 0).area for h in (10, 20, 40)]
        self.assertTrue(areas[0] < areas[1] < areas[2], areas)

    def test_slab_shadow_respects_receiver_height(self):
        shadow = SC.Shadow(2000)
        poly = shadow.Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        st = SC.sun_steps(self.frame, "2026-12-22", "Asia/Seoul", "CIVIL_KST", 12 * 60, 13 * 60, 60, 3.0)[0][0]
        a0 = shadow.union_of([(poly, 0, 20)], st, 0).area
        a10 = shadow.union_of([(poly, 0, 20)], st, 10).area
        self.assertGreater(a0, a10)
        self.assertTrue(shadow.union_of([(poly, 0, 20)], st, 20).is_empty)

    def test_projected_frame_north_matches_true_north_within_convergence(self):
        site = {"site_polygon": [[0, 0], [40, 0], [40, 31], [0, 31]], "coordinate_frame": {"projected_crs": "EPSG:5186", "projected_origin_m": [198056.367, 551885.031]},
                "site_area_basis": None}
        fr = SC.build_frame({}, site, None)
        self.assertAlmostEqual(fr["lat"], 37.5665, delta=0.001)
        self.assertLess(abs(fr["north"][0]), 0.01)
        self.assertEqual(fr["location_verification"], "PROJECTED_FRAME_DECLARED_NOT_SOURCE_BOUND")


@unittest.skipUnless(HAVE, "free geo dependencies not installed")
class SolarEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.massing = M.generate(jl("massing_site_input.json"))
        cls.ctx = jl("context_obstacles_synthetic.json")
        cls.cfg = small_cfg()
        cls.report, cls.viewer = study(cls.cfg, cls.massing, cls.ctx)
        cls.rep2, _ = study(cls.cfg, cls.massing, cls.ctx)

    def day(self):
        return self.report["dates"]["WINTER_SOLSTICE"]

    def test_wall_hand_calculation_ground_receivers(self):
        cfg, mass, ctx = wall_scene(20.0, (20.0, 60.0, 120.0))
        cfg["time"]["windows"] = [{"id": "W1130_1300", "start": "11:30", "end": "13:00"}]
        rep, _ = study(cfg, mass, ctx)
        sc = rep["dates"]["WINTER_SOLSTICE"]["scenarios"]["BALANCED"]
        near, mid, far = (sc["RCV-D%d" % d]["nominal"]["W1130_1300"]["total_min"] for d in (20, 60, 120))
        # elevation ~28.5-29 deg at 11:30-13:00 -> shadow length ~ 20/tan(29) = 36 m
        self.assertEqual(near, 0)       # 20 m behind a 20 m wall: shaded
        self.assertGreater(mid, 0)      # 60 m away: lit around noon
        self.assertEqual(far, 90)       # 120 m away: lit for the full 90 min window
        # elevated receiver (z=15) at 20 m is above the shadow of a 20 m wall (shadow reach (20-15)/tan = 9 m)
        cfg2, mass2, ctx2 = wall_scene(20.0, (20.0,), z=15.0)
        cfg2["time"]["windows"] = cfg["time"]["windows"]
        rep2, _ = study(cfg2, mass2, ctx2)
        self.assertEqual(rep2["dates"]["WINTER_SOLSTICE"]["scenarios"]["BALANCED"]["RCV-D20"]["nominal"]["W1130_1300"]["total_min"], 90)

    def test_nearby_obstacle_and_proposal_reduce_sun(self):
        d = self.day()["scenarios"]
        base_total = sum(r["nominal"]["W0900_1500"]["total_min"] for r in d["BASE"].values() if r["nominal_valid"])
        alt_total = sum(r["nominal"]["W0900_1500"]["total_min"] for r in d["BALANCED"].values() if r["nominal_valid"])
        self.assertLess(alt_total, base_total)
        no_ctx = copy.deepcopy(self.ctx)
        no_ctx["obstacles"] = [o for o in no_ctx["obstacles"] if o["id"] != "CTX-S"]
        r2, _ = study(self.cfg, self.massing, no_ctx)
        pt = "RCV-YARD_PT"
        with_s = self.day()["scenarios"]["BASE"][pt]["nominal"]["W0900_1700"]["total_min"]
        without_s = r2["dates"]["WINTER_SOLSTICE"]["scenarios"]["BASE"][pt]["nominal"]["W0900_1700"]["total_min"]
        self.assertGreaterEqual(without_s, with_s)

    def test_proposal_height_increases_loss(self):
        short = copy.deepcopy(self.massing)
        short["options"] = [copy.deepcopy(o) for o in short["options"] if o["strategy"] == "BALANCED"]
        short["options"][0]["floors"] = short["options"][0]["floors"][:5]  # same footprint, lower building
        rs, _ = study(self.cfg, short, self.ctx)
        def lost(rep):
            a = rep["dates"]["WINTER_SOLSTICE"]["scenarios"]
            return sum(a["BASE"][k]["nominal"]["W0900_1700"]["total_min"] - a["BALANCED"][k]["nominal"]["W0900_1700"]["total_min"]
                       for k in a["BASE"] if a["BASE"][k].get("nominal_valid"))
        self.assertGreater(lost(self.report), lost(rs))
        self.assertGreater(lost(rs), 0)

    def test_alternatives_produce_different_results(self):
        d = self.day()["scenarios"]
        diff = [k for k in d["BALANCED"] if d["BALANCED"][k].get("lit_bits") != d["SCULPTURAL"][k].get("lit_bits")]
        self.assertTrue(diff)
        self.assertNotEqual(self.viewer["dates"][0]["prop_shadow"]["BALANCED"], self.viewer["dates"][0]["prop_shadow"]["SCULPTURAL"])

    def test_deterministic_ids_and_results(self):
        self.assertEqual([r["id"] for r in self.report["receivers"]], [r["id"] for r in self.rep2["receivers"]])
        self.assertEqual(self.report["dates"], self.rep2["dates"])
        self.assertTrue(all(r["id"].startswith("RCV-") for r in self.report["receivers"]))
        self.assertEqual(len({r["id"] for r in self.report["receivers"]}), len(self.report["receivers"]))

    def test_cumulative_and_longest_continuous_are_consistent_with_bits(self):
        step = self.report["time"]["step_minutes"]
        d = self.day()
        steps = d["steps"]
        for sc in d["scenarios"].values():
            for rec in sc.values():
                if not rec.get("nominal_valid"):
                    continue
                bits = rec["lit_bits"]
                for w in self.report["time"]["windows"]:
                    sel = [bits[i] for i, s in enumerate(steps) if SC.hhmm(w["start"]) <= s["minute"] < SC.hhmm(w["end"])]
                    run = best = 0
                    for ch in sel:
                        run = run + 1 if ch == "1" else 0
                        best = max(best, run)
                    self.assertEqual(rec["nominal"][w["id"]]["total_min"], sel.count("1") * step)
                    self.assertEqual(rec["nominal"][w["id"]]["longest_min"], best * step)
                    self.assertLessEqual(rec["nominal"][w["id"]]["longest_min"], rec["nominal"][w["id"]]["total_min"])

    def test_facing_away_facade_receivers_get_no_direct_sun(self):
        cfg = small_cfg()
        cfg["receivers"] = {"facade_sets": [{"id": "N1_NORTH", "building_id": "CTX-N1", "spacing_m": 10, "heights_above_ground_m": [4.5],
                                              "facing_filter": {"azimuth_deg": 0, "tolerance_deg": 30}}], "points": [], "grids": []}
        rep, _ = study(cfg, self.massing, self.ctx)
        for rec in rep["dates"]["WINTER_SOLSTICE"]["scenarios"]["BASE"].values():
            self.assertEqual(rec["nominal"]["W0900_1700"]["total_min"], 0)
            self.assertEqual(rec["potential"]["W0900_1700"], 0)

    def test_height_uncertainty_gives_bounds_around_nominal(self):
        d = self.day()["scenarios"]["BALANCED"]
        for rec in d.values():
            if rec.get("nominal_valid"):
                for w in rec["nominal"]:
                    self.assertLessEqual(rec["bound_min"][w]["total_min"], rec["nominal"][w]["total_min"])
                    self.assertLessEqual(rec["nominal"][w]["total_min"], rec["bound_max"][w]["total_min"])
        spread = [r for r in d.values() if r.get("nominal_valid") and r["bound_max"]["W0900_1700"]["total_min"] > r["bound_min"]["W0900_1700"]["total_min"]]
        self.assertTrue(spread, "floors-derived heights (LOW confidence) must widen at least one receiver interval")

    def test_geometry_indicators_and_claim_boundary(self):
        ig = self.report["indicators_geometry"]["BALANCED"]
        self.assertTrue(ig["kpi_recomputed_matches_reported"])
        self.assertAlmostEqual(ig["far_pct"], 4200 / 1240 * 100, places=3)
        self.assertAlmostEqual(ig["bcr_pct"], 60.0, places=3)
        self.assertEqual(ig["story_count"], 12)
        self.assertAlmostEqual(ig["max_height_m"], 39.6, places=4)
        self.assertEqual(ig["official_vs_polygon_status"], "GEOMETRY_ONLY_NO_OFFICIAL_AREA")
        self.assertIsNone(ig["statutory_setback_m"])
        self.assertEqual(ig["statutory_setback_status"], "NOT_SOURCED")
        self.assertEqual(self.report["claims"]["legal_sunlight_compliance"], "NOT_EVALUATED")
        self.assertIn("NOT_CONNECTED", self.report["claims"]["meteorological_sunshine"])
        self.assertTrue(all(a["status"] in ("NOT_CONNECTED", "NOT_EVALUATED") for a in self.report["future_adapters"]))
        self.assertEqual(self.report["data_class"], "SYNTHETIC_OR_FIXTURE_NOT_PUBLIC_DATA")
        self.assertEqual(self.report["location"]["verification"], "SYNTHETIC_DECLARED")
        self.assertEqual(self.report["terrain"]["mode"], "FLAT_TERRAIN_ASSUMED")

    def test_directional_shadow_duration_winter_is_northern(self):
        dd = self.day()["directional_shadow"]["BALANCED"]["minutes"]
        self.assertEqual(dd["S"], 0)
        self.assertGreater(dd["N"] + dd["NE"] + dd["NW"], 0)

    def test_unknown_and_zero_heights_hold_limited_never_zero(self):
        ctx = jl("context_obstacles_unknown_height.json")
        rep, _ = study(self.cfg, self.massing, ctx)
        self.assertEqual(rep["result_status"], "LIMITED")
        self.assertEqual(rep["hold_reason"], "CONTEXT_HEIGHT_UNKNOWN_LIMITED_RESULT")
        self.assertEqual(rep["context"]["height_unknown_ids"], ["CTX-S"])
        affected = rep["context"]["unknown_height_affected_receivers"]
        self.assertTrue(affected)
        sc = rep["dates"]["WINTER_SOLSTICE"]["scenarios"]["BALANCED"]
        rid = affected[0]
        self.assertFalse(sc[rid]["nominal_valid"])
        self.assertIsNone(sc[rid]["nominal"])
        self.assertTrue(any(sc[r]["bound_max"]["W0900_1700"]["total_min"] > sc[r]["bound_min"]["W0900_1700"]["total_min"] for r in affected))
        # an obstacle treated as zero height would match the "CTX-S removed" result; the bounds must straddle it
        no_s = copy.deepcopy(self.ctx)
        no_s["obstacles"] = [o for o in no_s["obstacles"] if o["id"] != "CTX-S"]
        r0, _ = study(self.cfg, self.massing, no_s)
        zero_like = r0["dates"]["WINTER_SOLSTICE"]["scenarios"]["BALANCED"][rid]["nominal"]["W0900_1700"]["total_min"]
        self.assertGreaterEqual(sc[rid]["bound_max"]["W0900_1700"]["total_min"], zero_like)
        self.assertLess(sc[rid]["bound_min"]["W0900_1700"]["total_min"], zero_like + 1)

    def test_context_overlapping_proposal_holds_unless_demolition_declared(self):
        ctx = copy.deepcopy(self.ctx)
        ctx["obstacles"].append({"id": "EXISTING-ON-SITE", "footprint_m": [[10, 5], [30, 5], [30, 20], [10, 20]], "height_m": 8,
                                 "height_min_m": 8, "height_max_m": 8, "height_source": "SYNTHETIC_FIXTURE_DECLARED_HEIGHT", "confidence": "SYNTHETIC"})
        with self.assertRaisesRegex(SC.SolarHold, "CONTEXT_OVERLAPS_PROPOSAL"):
            study(self.cfg, self.massing, ctx)
        cfg = small_cfg(demolition_assumed_ids=["EXISTING-ON-SITE"])
        rep, _ = study(cfg, self.massing, ctx)
        self.assertEqual(rep["context"]["demolition_assumed_ids"], ["EXISTING-ON-SITE"])

    def test_identity_and_frame_guards(self):
        with self.assertRaisesRegex(SC.SolarHold, "PROJECT_ID_MISMATCH"):
            study(small_cfg(project_id="OTHER"), self.massing, self.ctx)
        geo = copy.deepcopy(self.ctx)
        geo["scene"] = {"projected_crs": "EPSG:5186", "origin_m": [1, 2]}
        with self.assertRaisesRegex(SC.SolarHold, "SCENE_FRAME_MISMATCH"):
            study(self.cfg, self.massing, geo)
        cfg = small_cfg()
        cfg.pop("location")
        with self.assertRaisesRegex(SC.SolarHold, "LOCATION_REQUIRED"):
            study(cfg, self.massing, self.ctx)
        cfg = small_cfg()
        cfg["scene"] = {}
        with self.assertRaisesRegex(SC.SolarHold, "SCENE_NORTH_REQUIRED"):
            study(cfg, self.massing, self.ctx)
        cfg = small_cfg()
        cfg["receivers"] = {}
        with self.assertRaisesRegex(SC.SolarHold, "NO_RECEIVERS_DEFINED"):
            study(cfg, self.massing, self.ctx)

    def test_scene_axis_declaration_rotates_true_north(self):
        """Scene +Y pointing true east: true north is scene -X; the scene wall becomes N-S, so a receiver 20 m east of it is lit at noon."""
        cfg, mass, ctx = wall_scene(20.0, (20.0,))
        cfg["scene"] = {"y_axis_true_azimuth_deg": 90}
        cfg["time"]["windows"] = [{"id": "W1130_1300", "start": "11:30", "end": "13:00"}]
        fr = SC.build_frame(cfg, mass, ctx)
        self.assertAlmostEqual(fr["north"][0], -1.0, places=6)
        self.assertAlmostEqual(fr["east"][1], 1.0, places=6)
        rep, _ = study(cfg, mass, ctx)
        self.assertEqual(rep["location"]["scene_y_axis_true_azimuth_deg"], 90.0)
        self.assertEqual(rep["dates"]["WINTER_SOLSTICE"]["scenarios"]["BALANCED"]["RCV-D20"]["nominal"]["W1130_1300"]["total_min"], 90)

    def test_viewer_is_standalone_and_carries_selectors(self):
        html = SC.viewer_html(self.viewer)
        for token in ('id="alt"', 'id="date"', 'id="time"', 'id="gridMode"', "__solar"):
            self.assertIn(token, html)
        self.assertNotIn("<script src=", html)
        self.assertNotIn("http://", html.replace("http://www.w3.org", ""))
        self.assertNotIn("__DATA__", html)


@unittest.skipUnless(HAVE, "free geo dependencies not installed")
class BuildingContext(unittest.TestCase):
    def page_paths(self):
        return [str(FIX / "vworld_bldginfo_page1.json"), str(FIX / "vworld_bldginfo_page2.json")]

    def scene(self):
        return {"projected_crs": "EPSG:5186", "origin_m": [198056.367, 551885.031]}

    def run_fixture(self, pages=None):
        cfg = jl("site_context_input_fixture.json")
        cfg["fixture_pages"] = pages or self.page_paths()
        return BC.build(cfg, self.scene(), [[0, 0], [40, 0], [40, 31], [0, 31]], FIX)

    def test_vworld_shaped_pages_pagination_ids_and_height_policy(self):
        doc, receipt = self.run_fixture()
        comp = doc["completeness"]
        self.assertTrue(comp["pagination"]["complete"])
        self.assertEqual(comp["pagination"]["records_collected"], 9)
        self.assertEqual(len(comp["pagination"]["page_sha256"]), 2)
        ids = [o["id"] for o in doc["obstacles"]]
        self.assertEqual(ids, sorted(ids))
        self.assertIn("BLD-lt_c_bldginfo.8#p0", ids)
        self.assertIn("BLD-lt_c_bldginfo.8#p1", ids)
        self.assertNotIn("BLD-lt_c_bldginfo.7", ids)  # outside the 150 m radius
        by = {o["id"]: o for o in doc["obstacles"]}
        self.assertEqual(by["BLD-lt_c_bldginfo.1"]["height_source"], "REPORTED_HEIGHT")
        self.assertAlmostEqual(by["BLD-lt_c_bldginfo.1"]["height_m"], 30.0)
        two = by["BLD-lt_c_bldginfo.2"]
        self.assertEqual(two["height_source"], "FLOORS_X_ASSUMED_FLOOR_TO_FLOOR")
        self.assertEqual(two["confidence"], "LOW")
        self.assertLess(two["height_min_m"], two["height_m"] < two["height_max_m"] and two["height_m"] or 0)
        zero = by["BLD-lt_c_bldginfo.9"]
        self.assertIsNone(zero["height_m"])
        self.assertEqual(zero["height_source"], "UNKNOWN")
        self.assertIn("ZERO_OR_INVALID_REPORTED_HEIGHT", zero["issues"])
        self.assertEqual(comp["status"], "LIMITED_UNKNOWN_HEIGHTS")
        self.assertEqual(doc["source_status"], "FIXTURE_NOT_PUBLIC_DATA")
        self.assertEqual(comp["field_mapping_status"], "ALIAS_BASED_UNVERIFIED_AGAINST_LIVE_RESPONSE")
        self.assertEqual(receipt["request"]["bbox_wgs84"], comp["pagination"]["bbox_wgs84"])
        # EPSG:4326 -> EPSG:5186 local: footprint of feature 1 must land at its authored local coordinates
        xs = [p[0] for p in by["BLD-lt_c_bldginfo.1"]["footprint_m"]]
        self.assertAlmostEqual(min(xs), 5, delta=0.05)
        self.assertAlmostEqual(max(xs), 35, delta=0.05)

    def test_incomplete_pagination_holds(self):
        with self.assertRaisesRegex(BC.ContextHold, "PAGINATION_INCOMPLETE"):
            self.run_fixture(pages=self.page_paths()[:1])

    def test_live_mode_without_key_is_honestly_unavailable(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            cfg = jl("site_context_input_live.json")
            with tempfile.TemporaryDirectory() as tmp:
                inp = Path(tmp) / "in.json"
                inp.write_text(json.dumps(cfg), encoding="utf-8")
                r = BC.run(inp, Path(tmp) / "out", scene=self.scene(), site_polygon=[[0, 0], [40, 0], [40, 31], [0, 31]],
                           fetch=lambda u: self.fail("network must not be touched without a key"))
        self.assertEqual(r["status"], "HOLD")
        self.assertEqual(r["failure_class"], "VWORLD_FREE_API_KEY_NOT_CONFIGURED")
        self.assertEqual(r["building_context_status"], "UNAVAILABLE")

    def test_live_mode_paginates_hashes_raw_and_never_stores_the_key(self):
        pages = {1: (FIX / "vworld_bldginfo_page1.json").read_bytes(), 2: (FIX / "vworld_bldginfo_page2.json").read_bytes()}
        seen = []
        def fetch(url):
            seen.append(url)
            n = int(url.split("page=")[1].split("&")[0])
            return pages[n], "application/json", 200
        secret = "SECRET_TEST_KEY_123"
        cfg = jl("site_context_input_live.json")
        with tempfile.TemporaryDirectory() as tmp:
            inp = Path(tmp) / "in.json"
            inp.write_text(json.dumps(cfg), encoding="utf-8")
            r = BC.run(inp, Path(tmp) / "out", scene=self.scene(), site_polygon=[[0, 0], [40, 0], [40, 31], [0, 31]],
                       fetch=fetch, key=secret)
            blob = "".join(p.read_text(encoding="utf-8", errors="ignore") for p in Path(tmp).rglob("*") if p.is_file())
            self.assertEqual(r["status"], "PASS")
            self.assertEqual(len(r["raw_refs"]), 2)
            for ref in r["raw_refs"]:
                self.assertIn(PS.digest(Path(ref).read_bytes()), Path(ref).name)
            self.assertNotIn(secret, blob)
        self.assertEqual(len(seen), 2)
        self.assertIn("geomFilter=BOX%28", seen[0])
        self.assertIn("data=LT_C_BLDGINFO", seen[0])
        self.assertEqual(r["source_status"], "OFFICIAL_API_OBSERVED_NOT_LEGAL_RECORD")

    def test_live_http_error_does_not_leak_key(self):
        with self.assertRaises(BC.ContextHold) as cm:
            BC.fetch_layer("LT_C_BLDGINFO", [1, 2, 3, 4], "SECRET_TEST_KEY_123", fetch=lambda u: (_ for _ in ()).throw(RuntimeError(u)))
        self.assertNotIn("SECRET_TEST_KEY_123", cm.exception.detail + cm.exception.code)

    def test_offline_geojson_unpinned_is_labelled_not_verified_and_pin_mismatch_holds(self):
        feat = {"type": "FeatureCollection", "features": [{"type": "Feature", "id": "a1", "properties": {"heit": "21.5"},
                "geometry": {"type": "Polygon", "coordinates": [[[50, 0], [60, 0], [60, 10], [50, 10], [50, 0]]]}}]}
        with tempfile.TemporaryDirectory() as tmp:
            gj = Path(tmp) / "b.geojson"
            gj.write_text(json.dumps(feat), encoding="utf-8")
            cfg = {"schema": BC.SCHEMA_INPUT, "project_id": "X", "mode": "OFFLINE_GEOJSON", "radius_m": 150,
                   "offline_geojson": {"path": "b.geojson", "source_crs": "LOCAL_M", "provenance": {"publisher": "test"}}}
            doc, rec = BC.build(cfg, {"kind": "LOCAL_M"}, [[0, 0], [40, 0], [40, 31], [0, 31]], tmp)
            self.assertEqual(doc["source_status"], "OFFLINE_FILE_UNPINNED_NOT_VERIFIED")
            self.assertEqual(doc["obstacles"][0]["height_source"], "REPORTED_HEIGHT")
            cfg["offline_geojson"]["trusted_sha256"] = PS.digest(gj.read_bytes())
            self.assertEqual(BC.build(cfg, {"kind": "LOCAL_M"}, [[0, 0], [40, 0], [40, 31], [0, 31]], tmp)[0]["source_status"], "SHA_PINNED_OFFLINE_FILE")
            cfg["offline_geojson"]["trusted_sha256"] = "0" * 64
            with self.assertRaisesRegex(BC.ContextHold, "SHA_PIN_MISMATCH"):
                BC.build(cfg, {"kind": "LOCAL_M"}, [[0, 0], [40, 0], [40, 31], [0, 31]], tmp)
            cfg["offline_geojson"].pop("provenance")
            cfg["offline_geojson"].pop("trusted_sha256")
            with self.assertRaisesRegex(BC.ContextHold, "CRS_AND_PROVENANCE_REQUIRED"):
                BC.build(cfg, {"kind": "LOCAL_M"}, [[0, 0], [40, 0], [40, 31], [0, 31]], tmp)

    def test_height_derivation_rules(self):
        self.assertEqual(BC.derive_height({"heit": "0"})["height_source"], "UNKNOWN")
        self.assertEqual(BC.derive_height({"heit": "abc"})["height_source"], "UNKNOWN")
        self.assertEqual(BC.derive_height({"heit": "-3", "grnd_flr": "4"})["height_source"], "FLOORS_X_ASSUMED_FLOOR_TO_FLOOR")
        self.assertEqual(BC.derive_height({})["height_m"], None)
        self.assertEqual(BC.derive_height({"heit": 12.5})["height_source"], "REPORTED_HEIGHT")
        self.assertEqual(BC.derive_height({"grnd_flr": 0})["height_source"], "UNKNOWN")


@unittest.skipUnless(HAVE, "free geo dependencies not installed")
class PipelineIntegration(unittest.TestCase):
    def copy_fixture(self, tmp, manifest):
        dst = Path(tmp) / "fx"
        shutil.copytree(FIX, dst)
        return dst, dst / manifest

    def test_synthetic_manifest_runs_massing_then_solar_with_receipts_and_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst, man = self.copy_fixture(tmp, "manifest_solar_synthetic.json")
            sc = json.loads((dst / "solar_study_input.json").read_text(encoding="utf-8"))
            sc["time"]["dates"] = sc["time"]["dates"][:1]
            sc["time"]["step_minutes"] = 30
            (dst / "solar_study_input.json").write_text(json.dumps(sc), encoding="utf-8")
            a = P.run(man, Path(tmp) / "run")
            self.assertEqual(a["status"], "PASS", a["stages"])
            self.assertEqual([s["stage"] for s in a["stages"]], ["MASSING", "SOLAR_STUDY"])
            self.assertTrue(a["evidence_ladder"]["SOLAR_DIRECT_SUN_STUDY_COMPUTED"])
            self.assertFalse(a["evidence_ladder"]["LEGAL_SUNLIGHT_VERIFIED"])
            self.assertFalse(a["evidence_ladder"]["SOURCE_VERIFIED"])
            out = Path(tmp) / "run" / "stages" / "SOLAR_STUDY"
            self.assertTrue((out / "solar_study_report.json").is_file())
            self.assertTrue((out / "solar_viewer.html").is_file())
            rcp = json.loads((Path(tmp) / "run" / "receipts" / "SOLAR_STUDY.json").read_text(encoding="utf-8"))
            self.assertEqual(rcp["status"], "PASS")
            self.assertEqual({o["ref"].rsplit("\\", 1)[-1].rsplit("/", 1)[-1] for o in rcp["outputs"]}, {"solar_study_report.json", "solar_viewer.html"})
            b = P.run(man, Path(tmp) / "run")
            self.assertEqual({s["stage"]: s["status"] for s in b["stages"]}, {"MASSING": "REUSED_LAST_PASS", "SOLAR_STUDY": "REUSED_LAST_PASS"})
            # source-hash invalidation: change one declared context height -> solar stage recomputes, massing stays cached
            ctx = json.loads((dst / "context_obstacles_synthetic.json").read_text(encoding="utf-8"))
            ctx["obstacles"][0]["height_m"] = ctx["obstacles"][0]["height_min_m"] = ctx["obstacles"][0]["height_max_m"] = 45.0
            (dst / "context_obstacles_synthetic.json").write_text(json.dumps(ctx), encoding="utf-8")
            c = P.run(man, Path(tmp) / "run")
            self.assertEqual({s["stage"]: s["status"] for s in c["stages"]}, {"MASSING": "REUSED_LAST_PASS", "SOLAR_STUDY": "PASS"})
            self.assertNotEqual(rcp["fingerprint"], json.loads((Path(tmp) / "run" / "receipts" / "SOLAR_STUDY.json").read_text(encoding="utf-8"))["fingerprint"])

    def test_vworld_shaped_pipeline_and_page_change_invalidates_downstream(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst, man = self.copy_fixture(tmp, "manifest_solar_vworld_fixture.json")
            sc = json.loads((dst / "solar_study_input_vworld_frame.json").read_text(encoding="utf-8"))
            sc["time"]["step_minutes"] = 30
            (dst / "solar_study_input_vworld_frame.json").write_text(json.dumps(sc), encoding="utf-8")
            a = P.run(man, Path(tmp) / "run")
            self.assertEqual({s["stage"]: s["status"] for s in a["stages"]}, {"MASSING": "PASS", "SITE_CONTEXT": "PASS", "SOLAR_STUDY": "PASS"})
            rep = json.loads((Path(tmp) / "run" / "stages" / "SOLAR_STUDY" / "solar_study_report.json").read_text(encoding="utf-8"))
            self.assertEqual(rep["context"]["source_class"] if "source_class" in rep["context"] else rep["context"]["source_classes"][0], "VWORLD_SHAPED_FIXTURE")
            self.assertEqual(rep["data_class"], "SYNTHETIC_OR_FIXTURE_NOT_PUBLIC_DATA")
            self.assertEqual(rep["location"]["verification"], "PROJECTED_FRAME_DECLARED_NOT_SOURCE_BOUND")
            p2 = dst / "vworld_bldginfo_page1.json"
            d = json.loads(p2.read_text(encoding="utf-8"))
            d["response"]["result"]["featureCollection"]["features"][0]["properties"]["heit"] = "44"
            p2.write_text(json.dumps(d), encoding="utf-8")
            b = P.run(man, Path(tmp) / "run")
            self.assertEqual({s["stage"]: s["status"] for s in b["stages"]}, {"MASSING": "REUSED_LAST_PASS", "SITE_CONTEXT": "PASS", "SOLAR_STUDY": "PASS"})

    def test_unknown_height_stage_holds_with_failure_class(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst, man = self.copy_fixture(tmp, "manifest_solar_synthetic.json")
            m = json.loads(man.read_text(encoding="utf-8"))
            m["inputs"]["solar_study"]["context_file"] = "context_obstacles_unknown_height.json"
            man.write_text(json.dumps(m), encoding="utf-8")
            sc = json.loads((dst / "solar_study_input.json").read_text(encoding="utf-8"))
            sc["time"]["dates"] = sc["time"]["dates"][:1]
            sc["time"]["step_minutes"] = 30
            (dst / "solar_study_input.json").write_text(json.dumps(sc), encoding="utf-8")
            r = P.run(man, Path(tmp) / "run")
            st = {s["stage"]: s for s in r["stages"]}
            self.assertEqual(st["SOLAR_STUDY"]["status"], "HOLD")
            self.assertEqual(st["SOLAR_STUDY"]["failure_class"], "CONTEXT_HEIGHT_UNKNOWN_LIMITED_RESULT")
            self.assertEqual(r["status"], "HOLD")
            self.assertFalse(r["evidence_ladder"]["SOLAR_DIRECT_SUN_STUDY_COMPUTED"])

    def test_live_site_context_without_key_blocks_solar(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst, man = self.copy_fixture(tmp, "manifest_solar_vworld_fixture.json")
            m = json.loads(man.read_text(encoding="utf-8"))
            m["inputs"]["site_context"] = {"input": "site_context_input_live.json"}
            man.write_text(json.dumps(m), encoding="utf-8")
            with mock.patch.dict(os.environ, {}, clear=True):
                r = P.run(man, Path(tmp) / "run")
            st = {s["stage"]: s for s in r["stages"]}
            self.assertEqual(st["SITE_CONTEXT"]["status"], "HOLD")
            self.assertEqual(st["SITE_CONTEXT"]["failure_class"], "VWORLD_FREE_API_KEY_NOT_CONFIGURED")
            self.assertEqual(st["SOLAR_STUDY"]["status"], "BLOCKED")

    def test_eum_area_without_cadastral_key_blocks_site_context_and_solar(self):
        """Red team: prior EUM PNU 1154510300108280004 / 149.1 m2 stays unverified without VWorld; nothing downstream runs."""
        pnu = "1154510300108280004"
        eum = {"pnu": pnu, "area_m2": 149.1, "address": "서울특별시 금천구 시흥동 828-4번지", "evidence_sha256": "c" * 64,
               "source": "EUM_OFFICIAL_WEB_VIEW", "observed_at": "2026-10-18T00:00:00+00:00",
               "document_status": "ONLINE_VIEW_NOT_LEGAL_CERTIFICATE"}
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            (t / "site_src.json").write_text(json.dumps({"schema": "ARCHIGROW_SITE_SOURCE_INPUT_V1", "project_id": "RED_TEAM", "pnu": pnu,
                "constraints": {"max_coverage_pct": 60, "max_far_pct": 800, "target_far_counted_area_m2": 300, "floor_count": 4,
                                "floor_to_floor_m": 3.3, "demo_clearance_m": 0.5}}), encoding="utf-8")
            (t / "ctx.json").write_text(json.dumps({"schema": "ARCHIGROW_SITE_CONTEXT_INPUT_V1", "project_id": "RED_TEAM", "mode": "VWORLD_LIVE"}), encoding="utf-8")
            sc = small_cfg(project_id="RED_TEAM")
            (t / "solar.json").write_text(json.dumps(sc), encoding="utf-8")
            (t / "m.json").write_text(json.dumps({"schema": "ARCHIGROW_PIPELINE_MANIFEST_V1", "project_id": "RED_TEAM",
                "stages": ["SITE_SOURCE", "MASSING", "SITE_CONTEXT", "SOLAR_STUDY"],
                "inputs": {"site_source": {"input": "site_src.json"}, "massing": {"source_stage": "SITE_SOURCE"},
                           "site_context": {"input": "ctx.json"}, "solar_study": {"input": "solar.json", "context_stage": "SITE_CONTEXT"}}}), encoding="utf-8")
            with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(P.mod("ARCHIGROW_PARCEL_SOURCE.py"), "fetch_eum", lambda p, raw_dir=None: eum):
                r = P.run(t / "m.json", t / "run")
        st = {s["stage"]: s for s in r["stages"]}
        self.assertEqual(st["SITE_SOURCE"]["status"], "HOLD")
        self.assertEqual(st["SITE_SOURCE"]["failure_class"], "VWORLD_FREE_API_KEY_NOT_CONFIGURED")
        for s in ("MASSING", "SITE_CONTEXT", "SOLAR_STUDY"):
            self.assertEqual(st[s]["status"], "BLOCKED", s)
        self.assertFalse(r["evidence_ladder"]["SITE_SOURCE_AREA_AND_IDENTITY_CROSSCHECKED"])
        self.assertFalse(r["evidence_ladder"]["SOLAR_DIRECT_SUN_STUDY_COMPUTED"])


if __name__ == "__main__":
    unittest.main()
