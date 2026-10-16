"""Adversarial fixture for the existing TAKY UI completion guard. No live app/Drive changes."""
import copy
import hashlib
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

import ai_execution_guard as guard
from taky_gate import validate_record

FAIL = "AI_UI_COMPLETION_EVIDENCE_MISSING"


def png(width=390, height=844):
    def chunk(tag, data):
        return struct.pack(">I",len(data))+tag+data+struct.pack(">I",zlib.crc32(tag+data)&0xffffffff)
    signature=bytes.fromhex("89504e470d0a1a0a")
    ihdr=struct.pack(">IIBBBBB",width,height,8,6,0,0,0)
    pixels=(bytes([0])+bytes(width*4))*height
    return signature+chunk(b"IHDR",ihdr)+chunk(b"IDAT",zlib.compress(pixels))+chunk(b"IEND",b"")


def save(folder, name, data):
    p=folder/name
    p.write_bytes(data if isinstance(data,bytes) else json.dumps(data).encode("utf-8"))
    return {"path":str(p),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}


def make_fixture(folder):
    reference=save(folder,"approved.png",png())
    rendered=save(folder,"rendered.png",png())
    vid="VISUAL-TEST-A"
    keys={"work_id":"WI-TEST","screen_id":"screen-home","run_id":"run-123"}
    approval={
        "schema":"TAKY_APPROVAL_RECORD_V1","approval_state":"APPROVED",
        "visual_id":vid,"screen_id":keys["screen_id"],
        "source_sha256":reference["sha256"],
    }
    idx={"provenance_only":[{
        "visual_id":vid,"source_sha256":reference["sha256"],
        "allowed_to_promote_current":True,"current_hns_master_binding":"VERIFIED",
        "actual_app_runtime_binding":"VERIFIED",
    }]}
    index_path=folder/"trusted_index.json"
    index_path.write_text(json.dumps(idx),encoding="utf-8")
    def report(filename, schema, check_names, **extra):
        info={"schema":schema,**keys,"status":"PASS",
              "checks":[{"name":name,"expected":"requirement satisfied",
                         "observed":"requirement satisfied","status":"PASS"} for name in check_names],
              **extra}
        return save(folder,filename+".json",info)
    visual=report("visual","TAKY_UI_VISUAL_COMPARE_V1",
                  ["layout","color","approved_assets"],
                  tool="PLAYWRIGHT",reference_sha256=reference["sha256"],
                  rendered_sha256=rendered["sha256"])
    evidence={
        **keys,"viewport":{"width":390,"height":844},
        "reference":{"approved_id":vid,"reference_file":reference,
                     "approval_record":save(folder,"approval.json",approval)},
        "visual":{"rendered_screenshot":rendered,"comparison_report":visual,
                  "passed":True,"layout_compared":True,"color_compared":True,
                  "approved_assets_compared":True},
        "interaction_report":report("interact","TAKY_UI_INTERACTION_TEST_V1",["user_interaction"]),
        "data_binding_report":report("binding","TAKY_UI_DATA_BINDING_TEST_V1",["data_consumption"]),
        "regression_report":report("regression","TAKY_UI_REGRESSION_TEST_V1",["existing_behavior"]),
        "intent_acceptance_report":report("intent","TAKY_UI_INTENT_ACCEPTANCE_V1",["user_intent"]),
        "interaction_passed":True,"data_binding_passed":True,
        "regression_passed":True,"intent_acceptance_passed":True,
    }
    config = {
        **keys,"url":"http://127.0.0.1:4321/",
        "viewport":{"width":390,"height":844},
        "steps":[{"action":"click","selector":"#sample"}],
    }
    config_ref = save(folder,"runner-config.json",config)
    accessibility=save(folder,"accessibility_snapshot.txt",b"- button \"sample\"\n")
    accessibility["truncated"]=False
    receipt={
        "accessibility_snapshot":accessibility,
        "config_path":config_ref["path"],"config_sha256":config_ref["sha256"],
        "schema":"TAKY_UI_BROWSER_RUNTIME_RECEIPT_V1",
        "status":"SCREENSHOT_CAPTURED_NOT_VISUAL_PASS",
        **keys, "target_kind":"LOOPBACK_APP",
        "viewport":{"width":390,"height":844},
        "observed":{"width":390,"height":844,"scrollWidth":390},
        "browser_channel":"chrome",
        "steps":[{"action":"click","selector":"#sample","status":"PASS"}],
        "page_errors":[],"rendered_screenshot":rendered,
        "release_approved":False,"is_approved_design":False,
    }
    evidence["browser_runtime_receipt"]=save(folder,"browser-receipt.json",receipt)
    return {"deliverable_type":"UI_SCREEN","status":"DONE","ui_completion_evidence":evidence},index_path


class UIProvenanceAdversarialTest(unittest.TestCase):
    def test_provenance_valid_and_adversarial_mutations(self):
        with tempfile.TemporaryDirectory(prefix="taky-ui-proof-") as tmp:
            folder=Path(tmp)
            base,index_path=make_fixture(folder)
            with patch.object(guard,"_APPROVAL_INDEX",index_path):
                self.assertNotIn(FAIL,validate_record(base))
                self.assertNotIn(FAIL,guard.validate_ai_execution(base))
                # V2 checks the observed text at the actual step, rather than
                # requiring an earlier screen's text to survive navigation.
                v2_config={
                    "work_id":"WI-TEST","screen_id":"screen-home","run_id":"run-123",
                    "url":"http://127.0.0.1:4321/",
                    "viewport":{"width":390,"height":844},
                    "steps":[{"action":"expectText","selector":"#old-page","value":"old-screen"},
                             {"action":"click","selector":"#sample"}],
                }
                v2_cfg_ref=save(folder,"runner-v2-config.json",v2_config)
                v2_receipt=json.loads((folder/"browser-receipt.json").read_text(encoding="utf-8"))
                v2_receipt["schema"]="TAKY_UI_BROWSER_RUNTIME_RECEIPT_V2"
                v2_receipt["config_path"]=v2_cfg_ref["path"]
                v2_receipt["config_sha256"]=v2_cfg_ref["sha256"]
                v2_receipt["steps"]=[
                    {"action":"expectText","selector":"#old-page","status":"PASS",
                     "expected_text":"old-screen","observed_text":"old-screen"},
                    {"action":"click","selector":"#sample","status":"PASS"},
                ]
                current=copy.deepcopy(base)
                current["ui_completion_evidence"]["browser_runtime_receipt"]=save(
                    folder,"browser-v2-good.json",v2_receipt)
                self.assertNotIn(FAIL,validate_record(current))
                v2_receipt["steps"][0]["observed_text"]="forged"
                current["ui_completion_evidence"]["browser_runtime_receipt"]=save(
                    folder,"browser-v2-forged.json",v2_receipt)
                self.assertIn(FAIL,validate_record(current))
                current=copy.deepcopy(base)
                a11y_path=folder/"accessibility_snapshot.txt"
                a11y_original=a11y_path.read_bytes()
                a11y_path.write_bytes(b"tampered accessibility")
                self.assertIn(FAIL,validate_record(current))
                a11y_path.write_bytes(a11y_original)
                current=copy.deepcopy(base)
                original_receipt=json.loads((folder/"browser-receipt.json").read_text(encoding="utf-8"))
                original_receipt["accessibility_snapshot"]["truncated"]=True
                current["ui_completion_evidence"]["browser_runtime_receipt"]=save(
                    folder,"truncated-receipt.json",original_receipt)
                self.assertIn(FAIL,validate_record(current))
                current=copy.deepcopy(base)
                current["ui_completion_evidence"].pop("browser_runtime_receipt")
                self.assertIn(FAIL,validate_record(current))
                current=copy.deepcopy(base)
                config_file=folder/"runner-config.json"
                config_bytes=config_file.read_bytes()
                config_file.write_text('{"url":"https://external.example"}',encoding="utf-8")
                self.assertIn(FAIL,validate_record(current))
                config_file.write_bytes(config_bytes)
                current=copy.deepcopy(base)
                receipt_path=folder/"browser-receipt.json"
                receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
                receipt["target_kind"]="ISOLATED_DATA_FIXTURE"
                current["ui_completion_evidence"]["browser_runtime_receipt"]=save(folder,"fixture-receipt.json",receipt)
                self.assertIn(FAIL,validate_record(current))
                current=copy.deepcopy(base)
                receipt["target_kind"]="LOOPBACK_APP"
                receipt["run_id"]="different-run"
                current["ui_completion_evidence"]["browser_runtime_receipt"]=save(folder,"wrong-run-receipt.json",receipt)
                self.assertIn(FAIL,validate_record(current))
                current=copy.deepcopy(base)
                current["ui_completion_evidence"]["reference"]["approved_id"]="FORGED"
                self.assertIn(FAIL,validate_record(current))
                current=copy.deepcopy(base)
                current["ui_completion_evidence"]["run_id"]="different-run"
                self.assertIn(FAIL,validate_record(current))
                current=copy.deepcopy(base)
                current["ui_completion_evidence"]["visual"]["color_compared"]=False
                self.assertIn(FAIL,validate_record(current))
                current=copy.deepcopy(base)
                current["status"]="OPEN"
                current["result_state"]="DONE"
                self.assertIn(FAIL,validate_record(current))
                current=copy.deepcopy(base)
                raw_image=png()
                corrupt=save(folder,"rendered_corrupt.png",raw_image[:40]+raw_image[-12:])
                current["ui_completion_evidence"]["visual"]["rendered_screenshot"]=corrupt
                visual_report=json.loads((folder/"visual.json").read_text(encoding="utf-8"))
                visual_report["rendered_sha256"]=corrupt["sha256"]
                current["ui_completion_evidence"]["visual"]["comparison_report"]=save(
                    folder,"visual_corrupt.json",visual_report)
                self.assertIn(FAIL,validate_record(current))
                # A forged PASS report with truthful SHA values must not hide
                # gross differences between the approved and rendered pixels.
                from PIL import Image
                viewport={"width":390,"height":844}
                reference=base["ui_completion_evidence"]["reference"]["reference_file"]
                original=Image.open(folder/"approved.png").convert("RGBA")
                original.putpixel((12,12),(0,0,0,255))
                subtle=folder/"rendered_subtle.png"
                original.save(subtle)
                subtle_artifact=save(folder,"rendered_subtle.png",subtle.read_bytes())
                self.assertTrue(guard._pixel_fidelity_verified(reference,subtle_artifact,viewport))
                alternate=folder/"rendered_other.png"
                Image.new("RGBA",(390,844),(0,0,0,255)).save(alternate)
                new_img=save(folder,"rendered_other.png",alternate.read_bytes())
                current=copy.deepcopy(base)
                current["ui_completion_evidence"]["visual"]["rendered_screenshot"]=new_img
                report=json.loads((folder/"visual.json").read_text(encoding="utf-8"))
                report["rendered_sha256"]=new_img["sha256"]
                report["claimed_pixel_difference_fraction"]=0.0
                current["ui_completion_evidence"]["visual"]["comparison_report"]=save(
                    folder,"visual_forged_pass.json",report)
                self.assertIn(FAIL,validate_record(current))
                current=copy.deepcopy(base)
                current["ui_completion_evidence"]["viewport"]["width"]=391
                self.assertIn(FAIL,validate_record(current))
                approval_path=folder/"approval.json"
                record=json.loads(approval_path.read_text(encoding="utf-8"))
                record["approval_state"]="REJECTED"
                current=copy.deepcopy(base)
                current["ui_completion_evidence"]["reference"]["approval_record"]=save(folder,"approval.json",record)
                self.assertIn(FAIL,validate_record(current))
                save(folder,"approval.json",{**record,"approval_state":"APPROVED"})
                index=json.loads(index_path.read_text(encoding="utf-8"))
                index["provenance_only"][0]["allowed_to_promote_current"]=False
                index_path.write_text(json.dumps(index),encoding="utf-8")
                self.assertIn(FAIL,validate_record(base))
            print("UI_PROVENANCE_ATTACKS_PASS: trusted baseline, forgery, cross-run, color, state, rejected approval, unpromoted")

if __name__=="__main__":
    unittest.main()
