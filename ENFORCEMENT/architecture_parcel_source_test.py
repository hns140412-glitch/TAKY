#!/usr/bin/env python3
"""Source-grounded parcel acquisition regression: no fabricated cadastral area."""
import copy,importlib.util,json,os,tempfile,unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
def mod(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/"TOOLS"/(name+".py"))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
S=mod("ARCHIGROW_PARCEL_SOURCE")
M=mod("ARCHIGROW_MASSING")
P=mod("ARCHIGROW_PIPELINE_RUN")
ROUTER=mod("ARCHIGROW_WORKFLOW_ROUTER")
PNU="1154510300108280004"

def sample_eum(pnu=PNU,area=1240):
    return {"pnu":pnu,"area_m2":area,"address":"서울특별시 금천구 시흥동 828-4번지",
            "view_url":S.EUM+"?mode=search&pnu="+pnu,
            "evidence_sha256":"b"*64,"source":"EUM_OFFICIAL_WEB_VIEW",
            "observed_at":"2026-10-18T00:00:00+00:00",
            "document_status":"ONLINE_VIEW_NOT_LEGAL_CERTIFICATE"}
def feature(pnu=PNU,holes=False):
    ring=[[200000,500000],[200040,500000],[200040,500031],[200000,500031],[200000,500000]]
    coords=[ring]
    if holes:coords.append([[200010,500010],[200015,500010],[200015,500015],[200010,500015],[200010,500010]])
    return {"response":{"status":"OK","result":{"featureCollection":{
        "type":"FeatureCollection","features":[{"type":"Feature",
            "properties":{"pnu":pnu,"addr":"서울특별시 금천구 시흥동 828-4"},
            "geometry":{"type":"Polygon","coordinates":coords}}]}}}}
def design_input():
    return {"schema":"ARCHIGROW_SITE_SOURCE_INPUT_V1","project_id":"PARCEL_OFFLINE_FIXTURE",
            "pnu":PNU,"constraints":{"max_coverage_pct":60,"max_far_pct":800,
                   "target_far_counted_area_m2":6486,"floor_count":18,
                   "floor_to_floor_m":3.5,"demo_clearance_m":0.5},
            "strategies":["BALANCED","SCULPTURAL"]}

class ParcelSourceTests(unittest.TestCase):
    def test_address_to_pnu_vworld_contract_and_eum_match(self):
        address="서울특별시 금천구 시흥동 828-4"
        geocode={"response":{"status":"OK","refined":{
            "structure":{"level4LC":PNU},
            "text":"서울특별시 금천구 시흥동 828-4"}}}
        resolved=S.parse_vworld_address(geocode,address)
        self.assertEqual(resolved["pnu"],PNU)
        src=design_input()
        src.pop("pnu")
        src["parcel_address"]=address
        with mock.patch.dict(os.environ,{"VWORLD_KEY":"MOCK_KEY"},clear=True):
            actual=S.build(src,eum_fetch=lambda p:sample_eum(p),
                           vworld_fetch=lambda p,k,d:S.parse_vworld(feature(),p),
                           address_fetch=lambda a,k,d:resolved)
        self.assertEqual(actual["status"],"PASS")
        self.assertEqual(actual["pnu"],PNU)
        self.assertEqual(actual["address_resolution"]["method"],"VWORLD_PARCEL_GETCOORD_REFINED_PNU")

    def test_address_ambiguous_or_wrong_pnu_does_not_fabricate(self):
        with self.assertRaisesRegex(S.SiteHold,"PNU_NOT_FOUND"):
            S.parse_vworld_address({"response":{"status":"OK","refined":{
                "structure":{"level4LC":"11545"},"text":"no PNU"}}},"any address")
        src=design_input()
        src.pop("pnu")
        src["parcel_address"]="서울특별시 금천구 시흥동 828-4"
        with mock.patch.dict(os.environ,{"VWORLD_KEY":"MOCK_KEY"},clear=True):
            actual=S.build(src,eum_fetch=lambda p:sample_eum(p),
                           vworld_fetch=lambda p,k,d:S.parse_vworld(feature(),p),
                           address_fetch=lambda a,k,d:{
                               "pnu":PNU,"refined_address":"서울특별시 마포구 공덕동 1-82번지"})
        self.assertEqual(actual["status"],"HOLD")
        self.assertEqual(actual["failure_class"],"VWORLD_GEOCODE_EUM_ADDRESS_MISMATCH")
        self.assertNotIn("massing_input",actual)

    def test_address_requires_key_without_guess(self):
        src=design_input()
        src.pop("pnu")
        src["parcel_address"]="서울특별시 금천구 시흥동 828-4"
        with mock.patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(S.SiteHold,"VWORLD_FREE_API_KEY_NOT_CONFIGURED"):
                S.build(src,eum_fetch=lambda p:sample_eum(p))

    def test_raw_official_payload_preserved_by_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw=(f'<html>{PNU}<table>'
                 '<tr><th>소재지</th><td>서울특별시 금천구 시흥동 828-4번지</td></tr>'
                 '<tr><td id="present_area">1,240.25 ㎡</td></tr>'
                 '</table></html>').encode("euc-kr")
            record=S.fetch_eum(PNU,fetch=lambda url:(raw,"text/html; charset=euc-kr",200),
                               raw_dir=tmp)
            self.assertTrue(Path(record["raw_ref"]).is_file())
            self.assertEqual(Path(record["raw_ref"]).read_bytes(),raw)
            self.assertEqual(len(list(Path(tmp).glob("*"))),1)
            same=S.fetch_eum(PNU,fetch=lambda url:(raw,"text/html; charset=euc-kr",200),
                             raw_dir=tmp)
            self.assertEqual(same["raw_ref"],record["raw_ref"])

    def test_eum_html_area_parsed_from_real_id(self):
        raw=(f'<html><input value="{PNU}"><table>'
             '<tr><th>소재지</th><td>서울특별시 금천구 시흥동 828-4번지</td></tr>'
             '<tr><th>면적</th><td id="present_area">1,240.25 ㎡</td></tr>'
             '</table></html>').encode("euc-kr")
        a=S.parse_eum(raw,PNU)
        self.assertEqual(a["area_m2"],1240.25)
        self.assertEqual(a["source"],"EUM_OFFICIAL_WEB_VIEW")
        self.assertEqual(len(a["evidence_sha256"]),64)
    def test_eum_missing_and_wrong_identity_hold(self):
        for raw in [b'<td id="present_area">1240</td>',f'{PNU}<td id="present_area">-</td>'.encode()]:
            with self.assertRaises(S.SiteHold):S.parse_eum(raw,PNU)
    def test_cadastral_polygon_parser_correct_geometry(self):
        r=S.parse_vworld(feature(),PNU)
        self.assertAlmostEqual(r["polygon_area_m2"],1240,places=5)
        self.assertEqual(r["projected_crs"],"EPSG:5186")
        self.assertEqual(r["polygon_local_m"][0],[0,0])
    def test_wrong_pnu_and_hole_holds(self):
        for data in [feature("1154510300108280005"),feature(holes=True)]:
            with self.assertRaises(S.SiteHold):S.parse_vworld(data,PNU)
    def test_area_missing_key_keeps_eum_evidence_and_does_not_make_site(self):
        with mock.patch.dict(os.environ,{},clear=True):
            r=S.build(design_input(),eum_fetch=lambda p:sample_eum(p))
        self.assertEqual(r["status"],"HOLD")
        self.assertEqual(r["failure_class"],"VWORLD_FREE_API_KEY_NOT_CONFIGURED")
        self.assertEqual(r["eum"]["area_m2"],1240)
        self.assertNotIn("massing_input",r)
    def test_full_offline_contract_to_existing_massing(self):
        vworld=lambda p,k,d:S.parse_vworld(feature(),p)
        with mock.patch.dict(os.environ,{"VWORLD_KEY":"OFFLINE_MOCK_KEY"},clear=True):
            r=S.build(design_input(),eum_fetch=lambda p:sample_eum(p),vworld_fetch=vworld)
        self.assertEqual(r["status"],"PASS")
        self.assertEqual(r["massing_input"]["site_area_basis"]["source"],"LAND_USE_EUM")
        self.assertEqual(r["comparison"]["result"],"MATCH_WITHIN_SCREENING_TOLERANCE")
        mass=M.generate(r["massing_input"])
        self.assertEqual(len(mass["options"]),2)
        for o in mass["options"]:
            self.assertAlmostEqual(o["kpi"]["site_area_m2"],1240,places=3)
            self.assertEqual(o["kpi"]["site_area_source"],"LAND_USE_EUM")
            self.assertAlmostEqual(o["kpi"]["far_pct"],6486/1240*100,places=2)
        html=M.viewer_html(mass)
        self.assertIn("site_area_basis",html)
        self.assertIn("토지이음",html)
        self.assertFalse(mass["legal_feasibility_authorized"])
    def test_eum_area_is_denominator_not_polygon_area(self):
        with mock.patch.dict(os.environ,{"VWORLD_KEY":"MOCK_KEY"},clear=True):
            result=S.build(design_input(),eum_fetch=lambda p:sample_eum(p,area=1241),
                           vworld_fetch=lambda p,k,d:S.parse_vworld(feature(),p))
        self.assertEqual(result["status"],"PASS")
        mass=M.generate(result["massing_input"])
        kpi=mass["options"][0]["kpi"]
        self.assertAlmostEqual(kpi["site_area_m2"],1241)
        self.assertAlmostEqual(kpi["geometry_area_m2"],1240)
        self.assertAlmostEqual(kpi["far_pct"],6486/1241*100,places=3)

    def test_eum_visible_address_must_match_cadastral_even_with_same_pnu(self):
        mistaken=sample_eum()
        mistaken["address"]="서울특별시 마포구 공덕동 1-82번지"
        with mock.patch.dict(os.environ,{"VWORLD_KEY":"MOCK_KEY"},clear=True):
            result=S.build(design_input(),eum_fetch=lambda p:mistaken,
                          vworld_fetch=lambda p,k,d:S.parse_vworld(feature(),p))
        self.assertEqual(result["status"],"HOLD")
        self.assertEqual(result["failure_class"],"EUM_VISIBLE_ADDRESS_CADASTRAL_MISMATCH")
        self.assertNotIn("massing_input",result)

    def test_differing_official_area_holds(self):
        with mock.patch.dict(os.environ,{"VWORLD_KEY":"MOCK_KEY"},clear=True):
            r=S.build(design_input(),eum_fetch=lambda p:sample_eum(p,area=1270),
                      vworld_fetch=lambda p,k,d:S.parse_vworld(feature(),p))
        self.assertEqual(r["status"],"HOLD")
        self.assertEqual(r["failure_class"],"OFFICIAL_AREA_VS_GEOMETRY_MISMATCH")
        self.assertNotIn("massing_input",r)
    def test_pnu_required(self):
        s=design_input();s["pnu"]="1"
        with self.assertRaisesRegex(S.SiteHold,"PNU_19_DIGITS_REQUIRED"):
            S.build(s,eum_fetch=lambda p:sample_eum(p))
    def test_unbound_official_area_cannot_bypass_site_source(self):
        with mock.patch.dict(os.environ,{"VWORLD_KEY":"MOCK_KEY"},clear=True):
            result=S.build(design_input(),eum_fetch=lambda p:sample_eum(p),
                           vworld_fetch=lambda p,k,d:S.parse_vworld(feature(),p))
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            (p/"site.json").write_text(json.dumps(result["massing_input"]),encoding="utf-8")
            manifest={"schema":"ARCHIGROW_PIPELINE_MANIFEST_V1",
                      "project_id":design_input()["project_id"],"stages":["MASSING"],
                      "inputs":{"massing":{"input":"site.json"}}}
            (p/"manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
            run=P.run(p/"manifest.json",p/"run")
            receipt=json.loads((p/"run"/"receipts"/"MASSING.json").read_text(encoding="utf-8"))
            self.assertEqual(run["status"],"HOLD")
            self.assertEqual(receipt["failure_class"],"EUM_AREA_REQUIRES_VERIFIED_SITE_SOURCE_STAGE")

    def test_full_pipeline_rebuilds_when_official_area_changes(self):
        """Same PNU/manifest, changed EUM RAW must force massing rerun."""
        src=design_input()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            (p/"site.json").write_text(json.dumps(src),encoding="utf-8")
            manifest=ROUTER.manifest_template(src["project_id"],"SITE_MASSING")
            manifest["inputs"]["site_source"]["input"]="site.json"
            (p/"manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
            source_module=P.mod("ARCHIGROW_PARCEL_SOURCE.py")
            observed_area=[1240]
            def fake_run(infile,out):
                with mock.patch.dict(os.environ,{"VWORLD_KEY":"MOCK_KEY"},clear=True):
                    response=S.build(src,eum_fetch=lambda pn:sample_eum(pn,observed_area[0]),
                                     vworld_fetch=lambda pn,k,d:S.parse_vworld(feature(),pn))
                out=Path(out);out.mkdir(parents=True,exist_ok=True)
                receipt=dict(response,raw_refs=[])
                (out/"site_source_receipt.json").write_text(json.dumps(receipt),encoding="utf-8")
                (out/"massing_site_input.json").write_text(json.dumps(response["massing_input"]),encoding="utf-8")
                return receipt
            with mock.patch.object(source_module,"run",side_effect=fake_run):
                first=P.run(p/"manifest.json",p/"run")
                self.assertEqual(first["status"],"PASS")
                self.assertEqual(first["stages"][0]["status"],"PASS")
                self.assertEqual(first["stages"][1]["status"],"PASS")
                self.assertTrue(first["evidence_ladder"]["SITE_SOURCE_AREA_AND_IDENTITY_CROSSCHECKED"])
                self.assertTrue(first["evidence_ladder"]["EUM_AREA_OBSERVED"])
                self.assertTrue(first["evidence_ladder"]["CADASTRAL_API_BOUNDARY_OBSERVED"])
                self.assertFalse(first["evidence_ladder"]["APPLICABLE_RULE_VERIFIED"])
                second=P.run(p/"manifest.json",p/"run")
                self.assertEqual(second["stages"][0]["status"],"PASS")
                self.assertEqual(second["stages"][1]["status"],"REUSED_LAST_PASS")
                observed_area[0]=1241
                third=P.run(p/"manifest.json",p/"run")
                self.assertEqual(third["status"],"PASS")
                self.assertEqual(third["stages"][1]["status"],"PASS")
                res=json.loads((p/"run"/"stages"/"MASSING"/"massing_result.json").read_text(encoding="utf-8"))
                self.assertAlmostEqual(res["options"][0]["kpi"]["site_area_m2"],1241)
                self.assertAlmostEqual(res["options"][0]["kpi"]["far_pct"],6486/1241*100,places=3)

    def test_site_massing_route_and_dependency(self):
        m=ROUTER.manifest_template("PARCEL_OFFLINE_FIXTURE","SITE_MASSING")
        self.assertEqual(m["stages"],["SITE_SOURCE","MASSING"])
        self.assertEqual(m["inputs"]["massing"],{"source_stage":"SITE_SOURCE"})
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            (p/"site.json").write_text(json.dumps(design_input()),encoding="utf-8")
            m["inputs"]["site_source"]["input"]="site.json"
            (p/"manifest.json").write_text(json.dumps(m),encoding="utf-8")
            # Key unavailable; EUM mocked via the module already imported by pipeline.
            source_module=P.mod("ARCHIGROW_PARCEL_SOURCE.py")
            with mock.patch.object(source_module,"run",return_value={
                "status":"HOLD","failure_class":"VWORLD_FREE_API_KEY_NOT_CONFIGURED",
                "pnu":PNU,"eum":sample_eum()}):
                # P.run requires on-disk evidence: stub writes the receipt as the real run would.
                def fake_run(infile,out):
                    out=Path(out);out.mkdir(parents=True,exist_ok=True)
                    payload={"status":"HOLD","failure_class":"VWORLD_FREE_API_KEY_NOT_CONFIGURED",
                             "pnu":PNU,"eum":sample_eum()}
                    (out/"site_source_receipt.json").write_text(json.dumps(payload),encoding="utf-8")
                    return payload
                with mock.patch.object(source_module,"run",side_effect=fake_run):
                    result=P.run(p/"manifest.json",p/"run")
            self.assertEqual(result["status"],"HOLD")
            self.assertEqual(result["stages"][0]["failure_class"],"VWORLD_FREE_API_KEY_NOT_CONFIGURED")
            self.assertTrue(result["evidence_ladder"]["EUM_AREA_OBSERVED"])
            self.assertFalse(result["evidence_ladder"]["CADASTRAL_API_BOUNDARY_OBSERVED"])
            self.assertFalse(result["evidence_ladder"]["SITE_SOURCE_AREA_AND_IDENTITY_CROSSCHECKED"])
            receipts=json.loads((p/"run"/"receipts"/"MASSING.json").read_text(encoding="utf-8"))
            self.assertEqual(receipts["status"],"BLOCKED")
            self.assertIn("SITE_SOURCE",receipts.get("blocked_by",[]))

if __name__=="__main__":unittest.main()
