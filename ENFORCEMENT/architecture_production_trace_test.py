#!/usr/bin/env python3
import importlib.util, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("m",ROOT/"TOOLS"/"ARCHIGROW_PRODUCTION_TRACE.py")
M=importlib.util.module_from_spec(spec); spec.loader.exec_module(M)

def st(stage,inp,out,objs,status="PASS",**kw):
    x={"stage":stage,"status":status,"tool":"TEST_TOOL","tool_version":"1",
       "recorded_at":"2026-10-04T12:30:00+09:00","input_refs":inp,"output_refs":out,
       "checks":[{"check_id":stage+"_CHECK","pass":True}],"object_ids":objs}
    x.update(kw); return x

def full():
    return {"project_id":"P1","selected_option_id":"OPT1","stages":[
      st("BIM_CAD",["OPT:OPT1"],["CAD:R1"],["U1","C1"]),
      st("AREA_LAW_QA",["CAD:R1"],["QA:R1"],["U1","C1"]),
      st("DETAIL",["QA:R1"],["DETAIL:R1"],["U1","C1"]),
      st("QTO_COST",["DETAIL:R1"],["COST:R1"],["U1","C1"],quantity_refs=["QTO:R1"],cost_source_refs=["COSTSRC:2026-10"],cost_as_of="2026-10-04"),
      st("REVIEW_PERMIT",["COST:R1"],["PERMIT:R1"],["U1","C1"],authority_evidence_refs=["AUTH:PERMIT:R1"]),
      st("FIELD_RFI",["PERMIT:R1"],["FIELD:R1"],["U1","C1"],rfi_refs=["RFI:001"]),
      st("AS_BUILT_LESSON",["FIELD:R1"],["ASBUILT:R1"],["U1","C1"],result_evidence_refs=["RESULT:ASBUILT:R1"],lesson="RFI response preserved core geometry and reduced rework.")
    ]}

class T(unittest.TestCase):
    def test_full_chain_passes_and_learning_is_case_only(self):
        r=M.validate_trace(full()); self.assertTrue(r["ok"]); self.assertTrue(r["production_complete"])
        self.assertFalse(r["legal_feasibility_authorized"]); self.assertFalse(r["cost_truth_authorized"])
        c=M.learning_candidate(r); self.assertTrue(c["ok"]); self.assertEqual(c["state"],"CASE"); self.assertFalse(c["promotion_authorized"])
    def test_previous_output_must_feed_next_stage(self):
        x=full(); x["stages"][1]["input_refs"]=["OTHER"]
        r=M.validate_trace(x); self.assertFalse(r["ok"]); self.assertTrue(any("PREVIOUS_OUTPUT_NOT_CONSUMED" in z for z in r["issues"]))
    def test_new_object_requires_change_evidence(self):
        x=full(); x["stages"][2]["object_ids"].append("D1")
        r=M.validate_trace(x); self.assertFalse(r["ok"]); self.assertTrue(any("NEW_OBJECT_WITHOUT_CHANGE_EVIDENCE" in z for z in r["issues"]))
    def test_new_object_with_change_ref_allowed(self):
        x=full(); x["stages"][2]["object_ids"].append("D1"); x["stages"][2]["object_change_refs"]=["CHANGE:DETAIL:001"]
        for s in x["stages"][3:]:
            s["object_ids"].append("D1")
        r=M.validate_trace(x); self.assertTrue(r["ok"])
    def test_cost_requires_quantity_and_cost_source(self):
        x=full(); x["stages"][3].pop("cost_source_refs")
        r=M.validate_trace(x); self.assertFalse(r["ok"]); self.assertTrue(any("COST_SOURCE_REF_REQUIRED" in z for z in r["issues"]))
    def test_permit_pass_requires_authority_evidence(self):
        x=full(); x["stages"][4].pop("authority_evidence_refs")
        r=M.validate_trace(x); self.assertFalse(r["ok"]); self.assertTrue(any("PERMIT_AUTHORITY_EVIDENCE_REQUIRED" in z for z in r["issues"]))
    def test_field_stage_requires_rfi_or_change_ref(self):
        x=full(); x["stages"][5].pop("rfi_refs")
        r=M.validate_trace(x); self.assertFalse(r["ok"]); self.assertTrue(any("RFI_OR_FIELD_CHANGE_REF_REQUIRED" in z for z in r["issues"]))
    def test_downstream_after_fail_forbidden(self):
        x=full(); x["stages"][1]["status"]="FAIL"; x["stages"][1]["checks"]=[{"check_id":"FAIL","pass":False}]
        r=M.validate_trace(x); self.assertFalse(r["ok"]); self.assertTrue(any("DOWNSTREAM_AFTER_FAIL_FORBIDDEN" in z for z in r["issues"]))
    def test_incomplete_chain_is_not_learning_candidate(self):
        x=full(); x["stages"]=x["stages"][:4]
        r=M.validate_trace(x); self.assertTrue(r["ok"]); self.assertFalse(r["production_complete"])
        self.assertFalse(M.learning_candidate(r)["ok"])

if __name__=="__main__": unittest.main()
