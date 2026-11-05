#!/usr/bin/env python3
"""Regression of ARCHIGROW_MASSING_DWG: P3 massing DXF receipt -> native AC1032 DWG via AutoCAD 2024 Core Console + native reopen.
One real two-strategy conversion (CLI) is shared by the provenance tests; every HOLD path fails before/without CAD or against a stand-in.
Synthetic geometry only; no statutory, project-data or legal claims. Local, no network. Skips (not passes) if AutoCAD Core Console is absent."""
import importlib.util
import os
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(name,rel):
    spec=importlib.util.spec_from_file_location(name,ROOT/rel)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod
W=load("ARCHIGROW_MASSING_DWG","TOOLS/ARCHIGROW_MASSING_DWG.py")
DXFT=load("architecture_massing_dxf_test","ENFORCEMENT/architecture_massing_dxf_test.py")
DXF=DXFT.D
TOOL=ROOT/"TOOLS"/"ARCHIGROW_MASSING_DWG.py"
PID=DXFT.PID
HAVE_CAD=Path(W.DEFAULT_EXE).is_file()

def make_p3(base):
    """Real P3 DXF stage into base (BALANCED rectangle + SCULPTURAL concave L); returns receipt path."""
    base=Path(base);base.mkdir(parents=True,exist_ok=True)
    src=base/"massing_result.json";src.write_text(json.dumps(DXFT.result()),encoding="utf-8")
    out=base/"p3"
    r=DXF.build(src,out,PID)
    assert r["status"]=="PASS",r
    return out/"massing_dxf_receipt.json"
def tree(p):
    return {str(f.relative_to(p)):W.sha(f) for f in Path(p).rglob("*") if f.is_file()}

@unittest.skipUnless(HAVE_CAD,"AutoCAD 2024 Core Console not installed")
class RealConversion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.dir=Path(cls.tmp.name)
        cls.p3=make_p3(cls.dir/"in");cls.p3_before=tree(cls.dir/"in")
        cls.out=cls.dir/"out dir"   # space on purpose (real repo paths have spaces)
        cls.proc=subprocess.run([sys.executable,str(TOOL),str(cls.p3),"--out-dir",str(cls.out),"--expect-project",PID],capture_output=True,text=True,timeout=120)
        cls.receipt=json.loads((cls.out/"massing_dwg_receipt.json").read_text(encoding="utf-8"))
    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_cli_pass_two_strategies_native_reopen(self):
        self.assertEqual(self.proc.returncode,0,self.proc.stdout+self.proc.stderr)
        r=self.receipt
        self.assertEqual(r["status"],"PASS",r["failure_class"]);self.assertEqual(r["project_id"],PID)
        self.assertEqual([o["strategy"] for o in r["options"]],["BALANCED","SCULPTURAL"])
        self.assertEqual(r["legal_status"],"NOT_VERIFIED");self.assertEqual(r["schema"],"ARCHIGROW_MASSING_DWG_RECEIPT_V1")
        self.assertEqual(r["stage_id"],"MASSING_DWG_HANDOFF")
        for o in r["options"]:
            n=o["expected_entity_count"]
            self.assertEqual(n,7)
            nr=o["native_reopen"]
            self.assertEqual((nr["polylines"],nr["closed_polylines"],nr["insunits"]),(n,n,6))
            self.assertEqual(nr["dwgname"],"massing_%s.dwg"%o["strategy"])
            self.assertEqual(o["status"],"PASS")

    def test_dwg_is_native_ac1032_and_hashes_bind(self):
        for o in self.receipt["options"]:
            dwg=Path(o["dwg"]["ref"])
            self.assertTrue(os.path.samefile(dwg.parent,self.out/o["strategy"]))
            self.assertEqual(dwg.read_bytes()[:6],b"AC1032")
            self.assertEqual(W.sha(dwg),o["dwg"]["sha256"])
            self.assertEqual(dwg.stat().st_size,o["dwg"]["bytes"])
            self.assertEqual(W.sha(o["dxf"]["ref"]),o["dxf"]["sha256"])   # DXF identity bound next to the DWG identity
            for k,v in o["logs"].items():
                self.assertEqual(W.sha(v["ref"]),v["sha256"],k)
            self.assertEqual(Path(o["logs"]["cerr"]["ref"]).read_bytes().strip(),b"")
            self.assertIn("TAKY_NATIVE_DWG_POLYLINES=",W.decode(Path(o["logs"]["vout"]["ref"]).read_bytes()))

    def test_provenance_and_limits(self):
        r=self.receipt
        self.assertEqual(r["p3_receipt"]["sha256"],W.sha(self.p3));self.assertEqual(r["p3_receipt"]["ref"],str(self.p3))
        p3=json.loads(self.p3.read_text(encoding="utf-8"))
        self.assertEqual(r["source_sha256"],p3["source_sha256"]);self.assertEqual(r["p3_inputs"],p3["inputs"])
        self.assertEqual(r["cad_engine"]["exe_sha256"],W.sha(W.DEFAULT_EXE))
        lim=" ".join(r["limitations"])
        self.assertIn("Synthetic sample boundary and room area polygon only; not finished wall/door/window/corridor",lim)
        self.assertIn("Not statutory",lim);self.assertIn("not a real site",lim)

    def test_inputs_untouched_and_only_owned_files_in_out_dir(self):
        self.assertEqual(tree(self.dir/"in"),self.p3_before)
        names={str(f.relative_to(self.out)).replace("\\","/") for f in self.out.rglob("*") if f.is_file()}
        expect={"massing_dwg_receipt.json"}
        for s in ("BALANCED","SCULPTURAL"):
            for e in (".dwg","_convert.scr","_verify.scr","_convert.stdout.txt","_convert.stderr.txt","_verify.stdout.txt","_verify.stderr.txt"):
                expect.add("%s/massing_%s%s"%(s,s,e))
        self.assertEqual(names,expect)   # no stray .dwl/.bak/.log

    def test_scripts_contain_only_validated_content(self):
        for o in self.receipt["options"]:
            c=Path(o["logs"]["cscr"]["ref"]).read_text(encoding="utf-8")
            self.assertIn('(command "_.SAVE" "%s")'%str(o["dwg"]["ref"]).replace("\\","/"),c)
            self.assertNotIn("SAVEAS",c.upper())
            self.assertNotIn("\\",c)

    def test_rerun_into_same_out_dir_is_conflict_hold_and_overwrites_nothing(self):
        before=tree(self.out)
        r=W.build(self.p3,self.out,PID)
        self.assertEqual(r["status"],"HOLD");self.assertTrue(r["failure_class"].startswith("TARGET_EXISTS"),r["failure_class"])
        self.assertIsNone(r["receipt_ref"])   # receipt is create-only as well
        self.assertEqual(tree(self.out),before)

class HoldPaths(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.dir=Path(self.tmp.name)
        self.p3=make_p3(self.dir/"in")
    def tearDown(self):
        self.tmp.cleanup()
    def hold(self,code,out="out",p3=None,expect=PID,**kw):
        o=self.dir/out
        r=W.build(p3 or self.p3,o,expect,**kw)
        self.assertEqual(r["status"],"HOLD",r)
        self.assertTrue(str(r["failure_class"]).startswith(code),r["failure_class"])
        self.assertEqual(r["options"],[])
        self.assertEqual([p for p in o.rglob("*.dwg") if p.read_bytes()[:6]==b"AC1032"],[],"partial DWG left behind")
        return r,o
    def edit_p3(self,fn):
        d=json.loads(self.p3.read_text(encoding="utf-8"));fn(d)
        self.p3.write_text(json.dumps(d),encoding="utf-8")

    def test_wrong_project_hold(self):
        r,o=self.hold("PROJECT_MISMATCH",expect="OTHER_PROJECT")
        self.assertEqual(r["project_id"],None)   # nothing from a mismatching receipt is trusted
        self.assertEqual([p.name for p in o.iterdir()],["massing_dwg_receipt.json"])

    def test_modified_source_dxf_sha_hold(self):
        dxf=Path(json.loads(self.p3.read_text(encoding="utf-8"))["options"][1]["dxf"]["ref"])
        dxf.write_bytes(dxf.read_bytes()+b"\n0\nEOF\n")
        self.hold("P3_DXF_SHA_MISMATCH:SCULPTURAL")

    def test_input_receipt_not_pass_hold(self):
        self.edit_p3(lambda d:d.update(status="HOLD"))
        self.hold("P3_RECEIPT_NOT_PASS")
    def test_option_not_pass_hold(self):
        self.edit_p3(lambda d:d["options"][0].update(status="HOLD"))
        self.hold("P3_OPTION_NOT_PASS")

    def test_missing_core_executable_hold(self):
        r,o=self.hold("ACCORECONSOLE_MISSING",exe=self.dir/"nope"/"accoreconsole.exe")
        self.assertEqual([p.name for p in o.iterdir()],["massing_dwg_receipt.json"])
    def test_wrong_executable_name_hold(self):
        self.hold("ACCORECONSOLE_MISSING",exe=Path(sys.executable))

    def test_existing_target_conflict_hold_and_preserved(self):
        d=self.dir/"out"/"BALANCED";d.mkdir(parents=True)
        t=d/"massing_BALANCED.dwg";t.write_bytes(b"USER OWNED SENTINEL")
        r,o=self.hold("TARGET_EXISTS:massing_BALANCED.dwg")
        self.assertEqual(t.read_bytes(),b"USER OWNED SENTINEL")
        self.assertFalse((o/"SCULPTURAL").exists(),"no strategy may be converted when any target conflicts")

    def test_existing_receipt_not_overwritten(self):
        o=self.dir/"out";o.mkdir();(o/"massing_dwg_receipt.json").write_text("KEEP",encoding="utf-8")
        r=W.build(self.p3,o,PID,exe=self.dir/"nope"/"accoreconsole.exe")
        self.assertEqual(r["status"],"HOLD");self.assertIsNone(r["receipt_ref"])
        self.assertEqual((o/"massing_dwg_receipt.json").read_text(encoding="utf-8"),"KEEP")

    def test_unsupported_strategy_name_hold(self):
        for bad in ("balanced","BAL-ANCED","BAL ANCED","BAL1","..\\EVIL",'A"B',""):
            self.edit_p3(lambda d:d["options"][0].update(strategy=bad))
            self.hold("STRATEGY_NAME_UNSUPPORTED",out="out_%d"%abs(hash(bad)))
    def test_unsafe_out_dir_hold(self):
        for bad in ("o(x)","o;x","o'x"):
            self.hold("UNSUPPORTED_PATH",out=bad)
    def test_non_ascii_out_dir_hold(self):
        self.hold("UNSUPPORTED_PATH",out="출력")
    def test_out_dir_inside_p3_input_hold(self):
        d=self.p3.parent
        before=tree(self.dir/"in")
        r=W.build(self.p3,d/"BALANCED"/"dwg",PID,exe=self.dir/"nope"/"accoreconsole.exe")
        self.assertEqual(r["failure_class"],"OUT_DIR_OVERLAPS_P3_INPUT")
        fake=self.dir/"bin"/"accoreconsole.exe";fake.parent.mkdir();shutil.copy(sys.executable,fake)
        r=W.build(self.p3,d/"BALANCED"/"dwg",PID,exe=fake)
        self.assertEqual(r["failure_class"],"OUT_DIR_OVERLAPS_P3_INPUT")
        self.assertFalse((d/"BALANCED"/"dwg").exists());self.assertEqual(tree(self.dir/"in"),before)
        self.assertEqual(W.build(self.p3,self.p3.parent,PID,exe=fake)["failure_class"],"OUT_DIR_OVERLAPS_P3_INPUT")
        self.assertEqual(tree(self.dir/"in"),before)
    def test_dxf_outside_receipt_dir_hold(self):
        other=self.dir/"elsewhere";other.mkdir()
        dxf=Path(json.loads(self.p3.read_text(encoding="utf-8"))["options"][0]["dxf"]["ref"])
        moved=other/dxf.name;shutil.copy(dxf,moved)
        self.edit_p3(lambda d:d["options"][0]["dxf"].update(ref=str(moved)))
        self.hold("P3_DXF_PATH_NOT_OWNED_BY_RECEIPT")
    def test_entity_count_inconsistent_hold(self):
        self.edit_p3(lambda d:d["options"][0].update(entity_count=99))
        self.hold("P3_ENTITY_COUNT_INCONSISTENT")
    def test_unreadable_and_wrong_schema_hold(self):
        (self.dir/"b").mkdir();bad=self.dir/"b"/"bad.json";bad.write_text("{not json",encoding="utf-8")
        self.hold("P3_RECEIPT_UNREADABLE",p3=bad)
        self.edit_p3(lambda d:d.update(schema="X"))
        self.hold("P3_RECEIPT_SCHEMA_UNSUPPORTED")
        self.hold("P3_RECEIPT_UNREADABLE",p3=self.dir/"b"/"missing.json")

    def test_cad_failure_is_hold_and_cleans_only_created_dwg(self):
        # stand-in "core console": python.exe copied as accoreconsole.exe fails on /i /s args -> non-zero exit -> HOLD, no PASS
        fake=self.dir/"bin"/"accoreconsole.exe";fake.parent.mkdir();shutil.copy(sys.executable,fake)
        r,o=self.hold("CAD_NONZERO_EXIT:convert:BALANCED",exe=fake)
        self.assertFalse((o/"SCULPTURAL").exists())
        self.assertIn("massing_BALANCED_convert.scr",[Path(x).name for x in r["diagnostic_files"]])  # evidence kept
        self.assertTrue(json.loads((o/"massing_dwg_receipt.json").read_text(encoding="utf-8"))["status"]=="HOLD")

    def test_license_and_policy_text_is_hold(self):
        for text in ("Your license has expired","Subscription required","blocked by policy"):
            with self.assertRaises(W.Hold) as c:
                W.judge_call("t",0,text.encode("utf-16le"),b"")
            self.assertTrue(str(c.exception).startswith("NATIVE_CAD_LICENSE_OR_POLICY"))
        with self.assertRaises(W.Hold):W.judge_call("t",1,b"ok",b"")
        with self.assertRaises(W.Hold):W.judge_call("t",0,b"ok",b"boom")
        self.assertEqual(W.judge_call("t",0,"한글 ok".encode("utf-8"),b""),"한글 ok")

    def test_decode_utf16_and_marker_must_be_unique(self):
        m="TAKY_NATIVE_DWG_POLYLINES=8 CLOSED=8 INSUNITS=6 DWGNAME=massing_X.dwg"
        for raw in (("\ufeff"+m).encode("utf-16le"),m.encode("utf-16le"),m.encode("utf-8")):
            self.assertEqual(len(W.MARKER.findall(W.decode(raw))),1)
        self.assertEqual(len(W.MARKER.findall(W.decode((m+"\n"+m).encode("utf-8")))),2)   # duplicate => caller HOLDs
        self.assertEqual(W.MARKER.findall(W.decode(b'(strcat "TAKY_NATIVE_DWG_POLYLINES=" (itoa n)')),[])  # echoed source is not a result

    def test_timeout_is_capped_at_40s(self):
        self.assertLessEqual(W.CALL_TIMEOUT_S,40)
        seen={}
        orig=W.subprocess.run
        def spy(*a,**k):
            seen["t"]=k.get("timeout");raise W.subprocess.TimeoutExpired(a[0],k.get("timeout"))
        W.subprocess.run=spy
        try:
            with self.assertRaises(W.Hold) as c:W.run_cad("x.exe",[],self.dir,"convert:T",999)
        finally:
            W.subprocess.run=orig
        self.assertEqual(seen["t"],40);self.assertTrue(str(c.exception).startswith("CAD_TIMEOUT"))

if __name__=="__main__":
    unittest.main(verbosity=1)
