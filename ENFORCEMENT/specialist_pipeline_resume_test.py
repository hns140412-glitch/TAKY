import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("specialist_pipeline_resume.py")
s=importlib.util.spec_from_file_location("r",P);r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
def state():
 return {"schema":"TAKY_SPECIALIST_PIPELINE_RESUME_V1","stages":[
  {"name":"AUTHORITY_RESTORE","status":"PASS","evidence_ref":"e0"},
  {"name":"GROUP_SOURCE_SHA_LOCK","status":"PASS","evidence_ref":"e1"},
  {"name":"MEMBER_ID_REFERENCE_BINDING","status":"PASS","evidence_ref":"e2"},
  {"name":"INDIVIDUAL_TRANSPARENT_CUTOUT","status":"OPEN","resume_reason":"IMAGE_GENERATION_UNAVAILABLE"},
  {"name":"INDIVIDUAL_MASK_SPEC","status":"BLOCKED","resume_reason":"WAIT_CUTOUT"},
  {"name":"BODY_PROP_GEAR_FINAL_ART","status":"BLOCKED","resume_reason":"WAIT_SOURCE_LOCK"},
  {"name":"SIX_REACTION_FINAL_ART","status":"BLOCKED","resume_reason":"WAIT_FINAL_ART"},
  {"name":"PER_ID_PACKAGE_AUDIT","status":"BLOCKED","resume_reason":"WAIT_FILES"},
  {"name":"UI_BINDING_AND_RENDER","status":"BLOCKED","resume_reason":"WAIT_APPROVED_ASSETS"},
  {"name":"VIEWPORT_DEVICE_VISUAL_QA","status":"BLOCKED","resume_reason":"WAIT_RENDER"},
  {"name":"RELEASE","status":"HOLD","resume_reason":"EXPLICIT_APPROVAL_REQUIRED"}
 ]}
class T(unittest.TestCase):
 def test_next_resume(self):
  x=r.next_resume(state());self.assertTrue(x["pass"]);self.assertEqual("INDIVIDUAL_TRANSPARENT_CUTOUT",x["resume_stage"])
 def test_pass_regression_block(self):
  a=state();b=state();b["stages"][1]={"name":"GROUP_SOURCE_SHA_LOCK","status":"OPEN","resume_reason":"x"}
  x=r.recover(a,b);self.assertEqual("PASS_REGRESSION_FORBIDDEN",x["error"])
if __name__=="__main__":unittest.main()
