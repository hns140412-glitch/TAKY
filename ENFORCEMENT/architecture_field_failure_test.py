#!/usr/bin/env python3
"""Regression for field/community failure modes (GitHub issues, Autodesk/CAD forums, Pillow, Chromium):
cp949 DXF layers, \\U+ escapes, OCS-mirrored polylines, visually-closed polylines, overlaid spikes,
silently missing layers, and >179 MP renders tripping the decompression-bomb guard."""
import importlib.util, json, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/"TOOLS"/f"{name}.py"); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
A=load("ARCHIGROW_AREA_DXF_SVG"); BUILD=load("ARCHIGROW_COMPETITION_BUILD")

def sq(x,y,w,h): return [(x,y),(x+w,y),(x+w,y+h),(x,y+h)]
def lw(handle,layer,pts,closed=True,extrusion=None):
    s=["0","LWPOLYLINE","5",handle,"8",layer,"90",str(len(pts)),"70","1" if closed else "0"]
    for x,y in pts: s+=["10",str(x),"20",str(y)]
    if extrusion: s+=["210",str(extrusion[0]),"220",str(extrusion[1]),"230",str(extrusion[2])]
    return s
def dxf_bytes(entities,acadver="AC1015",codepage="ANSI_949",encoding="cp949",insunits=4):
    s=["0","SECTION","2","HEADER","9","$ACADVER","1",acadver]+(["9","$DWGCODEPAGE","3",codepage] if codepage else [])+["9","$INSUNITS","70",str(insunits),"0","ENDSEC",
       "0","SECTION","2","ENTITIES"]
    for e in entities: s+=e
    s+=["0","ENDSEC","0","EOF"]
    return ("\n".join(s)+"\n").encode(encoding)

class FieldFailures(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.d=Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def run_case(self,raw,layers):
        (self.d/"in.dxf").write_bytes(raw)
        (self.d/"map.json").write_text(json.dumps({"project_id":"P1","layers":layers,"source_revision":"R1"},ensure_ascii=False),encoding="utf-8")
        return A.export(self.d/"in.dxf",self.d/"map.json",self.d/"out",reader="builtin")
    def kinds(self,ov): return {i["issue"] for i in ov["issues"]}
    def notes(self,ov): return {n["notice"] for n in ov["notices"]}

    def test_cp949_korean_layer_names_map(self):
        layers={"면적-연면적":{"level":"1F","scope":"GROSS_FLOOR","operation":"ADD"}}
        ov=self.run_case(dxf_bytes([lw("A1","면적-연면적",sq(0,0,10000,10000))]),layers)
        self.assertEqual((ov["issues"],ov["totals"][0]["area_m2"],ov["source_encoding"]),([],100.0,"cp949"))
    def test_r2007_utf8_and_unicode_escape_layers_map(self):
        layers={"면적":{"level":"1F","scope":"GROSS_FLOOR","operation":"ADD"}}
        ov=self.run_case(dxf_bytes([lw("A1","면적",sq(0,0,1000,1000))],acadver="AC1021",codepage="ANSI_949",encoding="utf-8"),layers)
        self.assertEqual(ov["totals"][0]["area_m2"],1.0)
        ov=self.run_case(dxf_bytes([lw("A1","\\U+BA74\\U+C801",sq(0,0,1000,1000))],codepage="ANSI_1252",encoding="ascii"),layers)
        self.assertEqual(ov["totals"][0]["area_m2"],1.0)
    def test_missing_mapped_layer_holds_instead_of_silent_loss(self):
        layers={"면적-연면적":{"level":"1F","scope":"GROSS_FLOOR","operation":"ADD"},"면적-발코니":{"level":"1F","scope":"BALCONY","operation":"ADD"},
                "면적-보이드":{"level":"1F","scope":"GROSS_FLOOR","operation":"SUBTRACT","optional":True}}
        ov=self.run_case(dxf_bytes([lw("A1","면적-연면적",sq(0,0,1000,1000))]),layers)
        self.assertIn("MAPPED_LAYER_NOT_FOUND",self.kinds(ov)); self.assertIn("OPTIONAL_LAYER_ABSENT",self.notes(ov))
        self.assertEqual(ov["geometry_status"],"HOLD")
    def test_mirrored_ocs_polyline_normalized_for_containment(self):
        layers={"ADD":{"level":"1F","scope":"GF","operation":"ADD"},"VOID":{"level":"1F","scope":"GF","operation":"SUBTRACT"}}
        void=[(-3000,2000),(-2000,2000),(-2000,3000),(-3000,3000)]   # OCS x of a mirrored entity; WCS x = 2000..3000
        ov=self.run_case(dxf_bytes([lw("A1","ADD",sq(0,0,10000,10000)),lw("V1","VOID",void,extrusion=(0,0,-1))]),layers)
        self.assertEqual(ov["issues"],[]); self.assertIn("MIRRORED_OCS_NORMALIZED",self.notes(ov)); self.assertEqual(ov["totals"][0]["area_m2"],99.0)
        tilted=self.run_case(dxf_bytes([lw("A1","ADD",sq(0,0,1000,1000)),lw("T1","ADD",sq(0,0,10,10),extrusion=(0,0.7071,0.7071))]),layers)
        self.assertIn("NON_PLAN_EXTRUSION",self.kinds(tilted))
    def test_visually_closed_polyline_without_flag_accepted_with_notice(self):
        layers={"ADD":{"level":"1F","scope":"GF","operation":"ADD"}}
        ov=self.run_case(dxf_bytes([lw("A1","ADD",sq(0,0,1000,1000)+[(0,0)],closed=False)]),layers)
        self.assertEqual((ov["issues"],ov["totals"][0]["area_m2"]),([],1.0)); self.assertIn("CLOSED_BY_COINCIDENT_ENDPOINTS",self.notes(ov))
        still_open=self.run_case(dxf_bytes([lw("A1","ADD",sq(0,0,1000,1000),closed=False),lw("A2","ADD",sq(2000,0,10,10))]),layers)
        self.assertIn("OPEN_BOUNDARY",self.kinds(still_open))
    def test_overlaid_segment_spike_rejected(self):
        layers={"ADD":{"level":"1F","scope":"GF","operation":"ADD"}}
        spike=[(0,0),(1000,0),(1500,0),(1000,0),(1000,1000),(0,1000)]
        ov=self.run_case(dxf_bytes([lw("S1","ADD",spike),lw("A2","ADD",sq(3000,0,10,10))]),layers)
        self.assertIn("OVERLAID_SEGMENT_SPIKE",self.kinds(ov))
    def test_large_render_inspected_not_rejected_as_bomb(self):
        from PIL import Image
        p=self.d/"hero.png"; Image.new("1",(14000,13000)).save(p)   # 182 MP > Pillow 2x MAX_IMAGE_PIXELS
        meta=BUILD.inspect_source(str(p))
        self.assertEqual((meta["kind"],meta["width_px"]),("RASTER",14000)); self.assertEqual(Image.MAX_IMAGE_PIXELS,89478485)

if __name__=="__main__": unittest.main()
