import importlib.util, unittest
from pathlib import Path

def load(name,file):
  p=Path(__file__).with_name(file)
  s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

cbe=load("cbe","character_behavior_engine.py")
ace=load("ace","asset_composition_contract.py")

class T(unittest.TestCase):
  def approved_registry(self):
    return {"characters":[{
      "character_id":"BELO","visual_id":"VID-08","runtime_source_eligible":True,
      "approved_parts":[
        {"role":"BODY","asset_pointer":"TAKY-ASSETS:BELO:BODY:sha","approval_state":"APPROVED","actions":[]},
        {"role":"FACE","asset_pointer":"TAKY-ASSETS:BELO:FACE:sha","approval_state":"APPROVED","actions":["READ_BOOK"]},
        {"role":"HAND","asset_pointer":"TAKY-ASSETS:BELO:HAND:sha","approval_state":"APPROVED","actions":["READ_BOOK"]},
        {"role":"PROP","asset_pointer":"TAKY-ASSETS:BELO:BOOK:sha","approval_state":"APPROVED","actions":["READ_BOOK"]}
      ],
      "fallback":{"character_id":"BELO","asset_pointer":"TAKY-ASSETS:BELO:BODY:sha"}
    }]}
  def state(self):
    return {"main_character_id":"BELO","mode":"TRACE","characters":[
      {"character_id":"BELO","visual_id":"VID-08","relationship_state":"FAMILIAR","available":True}
    ]}
  def test_behavior_to_composition_e2e(self):
    cmd=cbe.run(self.state())
    self.assertEqual([],cbe.validate_command(cmd))
    out=ace.resolve(cmd,self.approved_registry())
    self.assertTrue(out["pass"])
    self.assertEqual("READ_BOOK",out["action"])
    self.assertEqual(4,len(out["asset_pointers"]))
    self.assertFalse(out["generation_allowed"])
  def test_unapproved_source_blocks_runtime(self):
    reg=self.approved_registry();reg["characters"][0]["runtime_source_eligible"]=False
    cmd=cbe.run(self.state())
    out=ace.resolve(cmd,reg)
    self.assertFalse(out["pass"]);self.assertEqual("SOURCE_NOT_RUNTIME_ELIGIBLE",out["error"])
  def test_visual_id_mismatch_blocks(self):
    reg=self.approved_registry();reg["characters"][0]["visual_id"]="VID-99"
    cmd=cbe.run(self.state())
    out=ace.resolve(cmd,reg)
    self.assertFalse(out["pass"]);self.assertEqual("VISUAL_ID_MISMATCH",out["error"])
if __name__=="__main__":unittest.main()
