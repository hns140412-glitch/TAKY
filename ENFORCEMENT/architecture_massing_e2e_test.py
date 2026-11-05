#!/usr/bin/env python3
"""Geometric regression of massing prototype; no statutory feasibility claims."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("ARCHIGROW_MASSING",ROOT/"TOOLS"/"ARCHIGROW_MASSING.py")
M=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
PSPEC=importlib.util.spec_from_file_location("ARCHIGROW_PIPELINE_RUN",ROOT/"TOOLS"/"ARCHIGROW_PIPELINE_RUN.py")
P=importlib.util.module_from_spec(PSPEC)
PSPEC.loader.exec_module(P)


def source():
    return {
        "schema":"ARCHIGROW_MASSING_INPUT_V1",
        "project_id":"SYNTHETIC_MASSING_TEST",
        "source_role":"SYNTHETIC_TEST",
        "rule_source_status":"UNVERIFIED_DEMO",
        "coordinate_units":"m",
        "site_polygon":[[0,0],[40,0],[40,31],[0,31]],
        "constraints":{"max_coverage_pct":60,"max_far_pct":800,
                       "target_far_counted_area_m2":6486,"floor_count":18,
                       "floor_to_floor_m":3.5,"demo_clearance_m":0.5},
        "strategies":["BALANCED","SCULPTURAL"]
    }


def program():
    return {"entrance_space_id":"LOBBY",
            "spaces":[{"id":"LOBBY","name":"Lobby","area_m2":100,"category":"PUBLIC"},
                      {"id":"SHOP","name":"Shop","area_m2":150,"category":"COMMERCIAL"},
                      {"id":"OFFICE","name":"Office","area_m2":300,"category":"OFFICE"},
                      {"id":"CORE","name":"Core","area_m2":150,"category":"SERVICE"}],
            "links":[{"a":"LOBBY","b":"SHOP","weight":5},
                     {"a":"LOBBY","b":"CORE","weight":3},
                     {"a":"CORE","b":"OFFICE","weight":4,"vertical_preference":"ANY"}]}


class MassingTests(unittest.TestCase):
    def test_concave_program_allocator_fallback(self):
        # Allocator-level regression using the reported concave-case capacities.
        # The supplied source omits the spatial opt-in schema, strategy entry
        # point, and room output schema. End-to-end strategy and Shapely room
        # assertions cannot be authored faithfully from this packet.
        p = program()
        g = M.validate_program(p, "SYNTHETIC_MASSING_TEST", 8, 2000)
        nodes = g["nodes"]
        caps = [693.6] + [217.35] * 7
        original_caps = list(caps)

        level, pref_w = M.allocate_program(g, caps)
        self.assertEqual(set(level), set(nodes))
        self.assertEqual(level["LOBBY"], 0)
        self.assertEqual(level["OFFICE"], 0)
        self.assertEqual(pref_w, 5)
        self.assertEqual(caps, original_caps)
        for floor, capacity in enumerate(caps):
            used = sum(nodes[s]["area_m2"] for s in nodes
                       if level[s] == floor)
            self.assertLessEqual(used, capacity + 1e-9)
        self.assertEqual(M.allocate_program(g, caps), (level, pref_w))

    def test_allocator_true_infeasibility_hold_and_determinism(self):
        p = program()
        g = M.validate_program(p, "SYNTHETIC_MASSING_TEST", 8, 2000)
        nodes = g["nodes"]

        # Aggregate capacity exceeds demand, but no floor can hold OFFICE:
        # entrance fixation leaves only 200 on floor 0.
        caps = [300.0] + [217.35] * 7
        messages = []
        for _ in range(2):
            with self.assertRaises(M.MassingHold) as caught:
                M.allocate_program(g, caps)
            message = str(caught.exception)
            self.assertIn("SPATIAL_PROGRAM_INSUFFICIENT_FLOOR_CAPACITY",
                          message, "Expected a true-infeasibility HOLD")
            self.assertNotIn("SEARCH_BUDGET_EXHAUSTED", message)
            messages.append(message)
        self.assertEqual(messages[0], messages[1])
        self.assertEqual(caps, [300.0] + [217.35] * 7)

        feasible_caps = [693.6] + [217.35] * 7
        expected = M.allocate_program(g, feasible_caps)
        for _ in range(3):
            self.assertEqual(M.allocate_program(g, feasible_caps), expected)

    def test_reel_numerics_and_3d_geometry(self):
        model=M.generate(source())
        self.assertEqual(model["release_status"],"DEMO_GEOMETRY_ONLY__LEGAL_AND_DESIGN_REVIEW_PENDING")
        self.assertFalse(model["legal_feasibility_authorized"])
        self.assertEqual(len(model["options"]),2)
        self.assertNotEqual(
            model["options"][0]["floors"][-1]["polygon"],
            model["options"][1]["floors"][-1]["polygon"])
        for opt in model["options"]:
            k=opt["kpi"]
            self.assertAlmostEqual(k["site_area_m2"],1240,places=3)
            self.assertAlmostEqual(k["gross_floor_area_m2"],6486,places=3)
            self.assertAlmostEqual(k["far_pct"],523.064516129,places=3)
            self.assertAlmostEqual(k["max_height_m"],63.0,places=4)
            self.assertAlmostEqual(k["footprint_area_m2"],744,places=3)
            self.assertAlmostEqual(k["coverage_pct"],60,places=3)
            self.assertEqual(len(opt["floors"]),18)
            self.assertEqual(opt["validation"]["geometry_kpi"],"PASS")
            self.assertEqual(opt["validation"]["source_law"],"NOT_VERIFIED")
            self.assertTrue(all(M.within(f["polygon"],model["site_polygon"]) for f in opt["floors"]))
            self.assertAlmostEqual(sum(f["area_m2"] for f in opt["floors"]),6486,places=3)
            adjacent = [
                M.K.intersection_area(a["polygon"],b["polygon"]) /
                min(a["area_m2"],b["area_m2"])
                for a,b in zip(opt["floors"],opt["floors"][1:])
            ]
            self.assertGreaterEqual(min(adjacent),0.80)
            if opt["strategy"]=="SCULPTURAL":
                self.assertTrue(all(a["area_m2"]>=b["area_m2"]-0.001 for a,b in
                                    zip(opt["floors"],opt["floors"][1:])))

    def test_input_validation_rejects_missing_projected_units(self):
        s=source();s["coordinate_units"]="EPSG:4326"
        with self.assertRaisesRegex(M.MassingHold,"PROJECTED_METER_COORDINATES_REQUIRED"):
            M.generate(s)

    def test_invalid_site_holds(self):
        s=source();s["site_polygon"]=[[0,0],[30,30],[0,30],[30,0]]
        with self.assertRaisesRegex(M.MassingHold,"SITE_POLYGON_INVALID"):
            M.generate(s)

    def test_target_over_far_holds(self):
        s=source();s["constraints"]["max_far_pct"]=300
        with self.assertRaisesRegex(M.MassingHold,"TARGET_EXCEEDS_DECLARED_FAR_CAP"):
            M.generate(s)

    def test_not_enough_buildable_footprint_holds(self):
        s=source();s["constraints"]["demo_clearance_m"]=25
        with self.assertRaisesRegex(M.MassingHold,"NO_INTERIOR_MASS_FOUND"):
            M.generate(s)

    def test_concave_site_not_assumed_rectangular(self):
        s=source()
        s["site_polygon"]=[[0,0],[40,0],[40,12],[28,12],[28,19],[40,19],[40,31],[0,31]]
        s["constraints"]["target_far_counted_area_m2"]=2000
        s["constraints"]["floor_count"]=8
        data=M.generate(s)
        for opt in data["options"]:
            self.assertLessEqual(opt["kpi"]["footprint_area_m2"],M.K.area(s["site_polygon"])*.60+1e-6)
            for f in opt["floors"]:
                self.assertTrue(M.within(f["polygon"],s["site_polygon"]))


    @unittest.skipIf(M.ShapelyPolygon is None, "free Shapely dependency not installed")
    def test_site_shaped_offset_on_concave_parcel(self):
        s=source()
        s["site_polygon"]=[[0,0],[40,0],[40,12],[28,12],[28,19],[40,19],[40,31],[0,31]]
        s["footprint_mode"]="SITE_OFFSET"
        s["constraints"]["target_far_counted_area_m2"]=2000
        s["constraints"]["floor_count"]=8
        data=M.generate(s)
        self.assertIn("SHAPELY",data["geometry_method"])
        for option in data["options"]:
            self.assertAlmostEqual(option["kpi"]["gross_floor_area_m2"],2000,places=2)
            self.assertGreater(len(option["floors"][0]["polygon"]),4)
            self.assertLessEqual(option["kpi"]["footprint_area_m2"],M.K.area(s["site_polygon"])*.6+0.005)
            for floor in option["floors"]:
                self.assertTrue(M.within(floor["polygon"],s["site_polygon"]))

    def test_absent_program_leaves_result_unchanged(self):
        data=M.generate(source())
        self.assertNotIn("spatial_program",data)
        self.assertTrue(all("program_allocation" not in o for o in data["options"]))
        s=source();s["spatial_program"]=program()
        with_program=M.generate(s)
        for a,b in zip(data["options"],with_program["options"]):
            self.assertEqual(a["floors"],b["floors"])
            self.assertEqual(a["kpi"],b["kpi"])

    def test_program_allocation_both_strategies(self):
        s=source();s["spatial_program"]=program()
        data=M.generate(s)
        self.assertEqual(data["spatial_program"]["representation"],"FLOOR_ZONE_ASSIGNMENT_NOT_ROOM_GEOMETRY")
        self.assertFalse(data["spatial_program"]["legal_claim"])
        self.assertEqual(len(data["options"]),2)
        for opt in data["options"]:
            pa=opt["program_allocation"]
            self.assertEqual(pa["representation"],"FLOOR_ZONE_ASSIGNMENT_NOT_ROOM_GEOMETRY")
            self.assertEqual(sorted(x["id"] for x in pa["spaces"]),["CORE","LOBBY","OFFICE","SHOP"])
            self.assertAlmostEqual(sum(x["area_m2"] for x in pa["spaces"]),700,places=6)
            self.assertAlmostEqual(sum(l["assigned_area_m2"] for l in pa["levels"]),700,places=5)
            self.assertAlmostEqual(pa["metrics"]["unassigned_gfa_m2"],6486-700,places=3)
            for l in pa["levels"]:
                self.assertLessEqual(l["assigned_area_m2"],l["capacity_m2"]+1e-6)
            by={x["id"]:x for x in pa["spaces"]}
            self.assertEqual(by["LOBBY"]["level"],"L01")
            self.assertEqual(by["LOBBY"]["access_depth"],0)
            self.assertEqual(by["OFFICE"]["access_depth"],2)
            self.assertEqual(by["LOBBY"]["degree"],2)
            self.assertNotIn("polygon",by["OFFICE"])
            self.assertTrue(0<=pa["score"]<=1)

    def test_same_floor_preference_scores_sensibly(self):
        # Capacity is ample (L01 = 744 m2, 400 m2 cluster), so strongly linked rooms should share a level.
        s=source();s["spatial_program"]=program()
        for opt in M.generate(s)["options"]:
            by={x["id"]:x["level"] for x in opt["program_allocation"]["spaces"]}
            self.assertEqual(by["LOBBY"],by["SHOP"])
            self.assertEqual(by["LOBBY"],by["CORE"])
            self.assertGreaterEqual(opt["program_allocation"]["metrics"]["adjacency_score"],0.9)
        # Forced split lowers adjacency: ANY link is free, preference pulls OFFICE up.
        s["spatial_program"]["spaces"][2]["level_preference"]=10
        for opt in M.generate(s)["options"]:
            pa=opt["program_allocation"]
            by={x["id"]:x for x in pa["spaces"]}
            self.assertTrue(by["OFFICE"]["preference_met"])
            self.assertEqual(by["OFFICE"]["level"],"L10")
            self.assertEqual(pa["metrics"]["level_preference_met_ratio"],1.0)

    def test_program_option_metadata_deterministic_and_ranked(self):
        s=source();s["spatial_program"]=program()
        a,b=M.generate(copy.deepcopy(s)),M.generate(copy.deepcopy(s))
        self.assertEqual(json.dumps(a,sort_keys=True),json.dumps(b,sort_keys=True))
        scores=[o["program_allocation"]["score"] for o in a["options"]]
        tied=abs(scores[0]-scores[1])<=1e-9
        ranks=sorted(o["program_allocation"]["rank"] for o in a["options"])
        self.assertEqual(ranks,[1,1] if tied else [1,2])
        self.assertEqual({o["program_allocation"]["tied"] for o in a["options"]},{tied})
        self.assertEqual(sorted(r["strategy"] for r in a["spatial_program"]["ranking"]),
                         sorted(o["strategy"] for o in a["options"]))

    def _ranked_with_scores(self,scores):
        real=M.program_result
        it=iter(scores)
        def fake(*args,**kw):
            r=real(*args,**kw);r["score"]=next(it);return r
        s=source();s["spatial_program"]=program()
        M.program_result=fake
        try:
            return M.generate(s)
        finally:
            M.program_result=real

    def test_equal_program_scores_share_rank_and_are_marked_tied(self):
        for scores in ([1.0,1.0],[0.8,0.8+5e-10]):
            data=self._ranked_with_scores(scores)
            self.assertEqual([o["program_allocation"]["rank"] for o in data["options"]],[1,1])
            self.assertTrue(all(o["program_allocation"]["tied"] for o in data["options"]))
            self.assertEqual([r["rank"] for r in data["spatial_program"]["ranking"]],[1,1])
            self.assertTrue(all(r["tied"] for r in data["spatial_program"]["ranking"]))
            self.assertIn("does not rank site or geometric",data["spatial_program"]["tie_note"])
            # stable order, no geometric/site tiebreak: options keep generation order
            self.assertEqual([r["strategy"] for r in data["spatial_program"]["ranking"]],
                             [o["strategy"] for o in data["options"]])

    def test_distinct_program_scores_keep_distinct_ranks(self):
        data=self._ranked_with_scores([0.5,0.9])
        self.assertEqual([o["program_allocation"]["rank"] for o in data["options"]],[2,1])
        self.assertFalse(any(o["program_allocation"]["tied"] for o in data["options"]))
        self.assertEqual([r["rank"] for r in data["spatial_program"]["ranking"]],[1,2])

    def test_malformed_program_rejected(self):
        def mutate(fn,pattern):
            s=source();p=program();fn(p);s["spatial_program"]=p
            with self.assertRaisesRegex(M.MassingHold,pattern):
                M.generate(s)
        mutate(lambda p:p["spaces"].append(dict(p["spaces"][0])),"DUPLICATE_SPACE_ID")
        mutate(lambda p:p["spaces"][0].update(area_m2=float("nan")),"INVALID_NUMERIC_PARAMETER")
        mutate(lambda p:p["spaces"][0].update(area_m2=-5),"NUMERIC_PARAMETER_OUT_OF_RANGE")
        mutate(lambda p:p["spaces"][0].update(category="CASTLE"),"CATEGORY_UNSUPPORTED")
        mutate(lambda p:p["spaces"][0].update(level_preference=99),"LEVEL_PREFERENCE_INVALID")
        mutate(lambda p:p["links"].append({"a":"LOBBY","b":"GHOST","weight":1}),"ENDPOINT_MISSING")
        mutate(lambda p:p["links"][0].update(weight=float("inf")),"INVALID_NUMERIC_PARAMETER")
        mutate(lambda p:p["links"][0].update(vertical_preference="DIAGONAL"),"VERTICAL_PREFERENCE_UNSUPPORTED")
        mutate(lambda p:p.update(entrance_space_id="NOPE"),"ENTRANCE_MISSING")
        mutate(lambda p:p.update(project_id="OTHER_PROJECT"),"PROJECT_ID_MISMATCH")
        mutate(lambda p:p.update(rooms=[]),"UNSUPPORTED_FIELD")

    def test_program_disconnected_from_entrance_rejected(self):
        s=source();p=program();p["links"]=[l for l in p["links"] if "OFFICE" not in (l["a"],l["b"])]
        s["spatial_program"]=p
        with self.assertRaisesRegex(M.MassingHold,"DISCONNECTED_FROM_ENTRANCE:OFFICE"):
            M.generate(s)

    def test_program_over_capacity_rejected(self):
        s=source();p=program();p["spaces"][2]["area_m2"]=7000
        s["spatial_program"]=p
        with self.assertRaisesRegex(M.MassingHold,"AREA_EXCEEDS_TARGET_GFA"):
            M.generate(s)
        # Total fits GFA but one space exceeds any single floor.
        s=source();p=program();p["spaces"][2]["area_m2"]=3000
        s["spatial_program"]=p
        with self.assertRaisesRegex(M.MassingHold,"INSUFFICIENT_FLOOR_CAPACITY:OFFICE"):
            M.generate(s)

    def test_site_holes_do_not_silently_disappear(self):
        s=source()
        s["site_holes"]=[[[10,10],[15,10],[15,15],[10,15]]]
        with self.assertRaisesRegex(M.MassingHold,"SITE_HOLES_NOT_SUPPORTED"):
            M.generate(s)


    def test_wgs84_to_projected_local_meters_explicit_and_traceable(self):
        try:
            from pyproj import Transformer
        except ImportError:
            self.skipTest("free pyproj not installed")
        to_projected=Transformer.from_crs("EPSG:4326","EPSG:5179",always_xy=True)
        to_wgs=Transformer.from_crs("EPSG:5179","EPSG:4326",always_xy=True)
        ox,oy=to_projected.transform(127.0,37.5)
        s=source()
        s["site_polygon"]=[list(to_wgs.transform(ox+x,oy+y)) for x,y in s["site_polygon"]]
        s["coordinate_units"]="degrees"
        s["source_crs"]="EPSG:4326"
        s["target_crs"]="EPSG:5179"
        result=M.generate(s)
        self.assertEqual(result["coordinate_frame"]["source_crs"],"EPSG:4326")
        self.assertEqual(result["coordinate_frame"]["projected_crs"],"EPSG:5179")
        self.assertEqual(result["coordinate_units"],"m")
        self.assertAlmostEqual(result["options"][0]["kpi"]["site_area_m2"],1240,places=2)

    def test_wgs84_without_explicit_target_crs_holds(self):
        s=source()
        s["coordinate_units"]="degrees"
        s["source_crs"]="EPSG:4326"
        with self.assertRaisesRegex(M.MassingHold,"EXPLICIT_KOREAN_PROJECTED_CRS_REQUIRED"):
            M.generate(s)

    def test_pipeline_bound_input_and_intact_cached_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            (p/"site.json").write_text(json.dumps(source()),encoding="utf-8")
            manifest={"schema":"ARCHIGROW_PIPELINE_MANIFEST_V1","project_id":source()["project_id"],
                      "stages":["MASSING"],"inputs":{"massing":{"input":"site.json"}}}
            (p/"manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
            a=P.run(p/"manifest.json",p/"run")
            b=P.run(p/"manifest.json",p/"run")
            self.assertEqual(a["status"],"PASS")
            self.assertEqual(b["stages"][0]["status"],"REUSED_LAST_PASS")
            self.assertTrue((p/"run"/"stages"/"MASSING"/"massing_viewer.html").is_file())
            self.assertTrue((p/"run"/"receipts"/"MASSING.json").is_file())
            self.assertFalse(a["legal_feasibility_authorized"])
            html=(p/"run"/"stages"/"MASSING"/"massing_viewer.html").read_text(encoding="utf-8")
            self.assertIn('id="levels"',html)
            self.assertIn('id="strategy"',html)
            self.assertIn('pointermove',html)
            self.assertNotIn('<script src=',html)

    def test_pipeline_rejects_project_identity_crosscontamination(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            (p/"site.json").write_text(json.dumps(source()),encoding="utf-8")
            manifest={"schema":"ARCHIGROW_PIPELINE_MANIFEST_V1","project_id":"OTHER_SITE",
                      "stages":["MASSING"],"inputs":{"massing":{"input":"site.json"}}}
            (p/"manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
            r=P.run(p/"manifest.json",p/"run")
            self.assertEqual(r["stages"][0]["status"],"HOLD")
            self.assertEqual(r["stages"][0]["failure_class"],"PROJECT_ID_MISMATCH")


if __name__=="__main__":
    unittest.main()
