import importlib.util,unittest
from pathlib import Path

def load(name,file):
  p=Path(__file__).with_name(file)
  s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

rel=load("rel","relation_affinity_engine.py")
cbe=load("cbe","character_behavior_engine.py")
ace=load("ace","asset_composition_contract.py")
rr=load("rr","runtime_renderer_contract.py")

class FullLoop(unittest.TestCase):
  def registry(self):
    return {"characters":[{
      "character_id":"BELO","visual_id":"VID-08","runtime_source_eligible":True,
      "approved_parts":[
        {"role":"BODY","asset_pointer":"TAKY-ASSETS:BELO:BODY:sha","approval_state":"APPROVED","actions":[]},
        {"role":"FACE","asset_pointer":"TAKY-ASSETS:BELO:FACE:sha","approval_state":"APPROVED","actions":["POINT"]},
        {"role":"ARM","asset_pointer":"TAKY-ASSETS:BELO:ARM:sha","approval_state":"APPROVED","actions":["POINT"]},
        {"role":"HAND","asset_pointer":"TAKY-ASSETS:BELO:HAND:sha","approval_state":"APPROVED","actions":["POINT"]}
      ],
      "fallback":{"character_id":"BELO","asset_pointer":"TAKY-ASSETS:BELO:BODY:sha"}
    }]}
  def relation_member(self):
    ev=[{"event_id":"meet","type":"FIRST_MEETING","verified":True,"evidence_ref":"m"}]
    ev += [{"event_id":f"e{i}","type":"SHARED_EPISODE","verified":True,"evidence_ref":f"r{i}"} for i in range(8)]
    return {"character_id":"BELO","committed_state":"KNOWN","events":ev}
  def test_relation_behavior_composition_renderer(self):
    result=rel.evaluate(self.relation_member(),{"familiar_min_verified_episodes":3,"trusted_min_verified_episodes":8})
    committed=rel.commit(result,True)
    self.assertEqual("TRUSTED",committed["effective_relationship_state"])
    state={
      "main_character_id":"BELO","needs_hint":True,
      "characters":[{"character_id":"BELO","visual_id":"VID-08","relationship_state":committed["effective_relationship_state"],"available":True}]
    }
    cmd=cbe.run(state)
    self.assertEqual("COACH",cmd["dialogue_level"])
    self.assertEqual("POINT",cmd["action"])
    comp=ace.resolve(cmd,self.registry())
    self.assertTrue(comp["pass"])
    plan=rr.render_plan(cmd,comp)
    self.assertTrue(plan["pass"])
    self.assertTrue(plan["design_gate_required"])
    self.assertFalse(plan["asset_generation_allowed"])
  def test_uncommitted_candidate_does_not_affect_behavior(self):
    result=rel.evaluate(self.relation_member(),{"familiar_min_verified_episodes":3,"trusted_min_verified_episodes":8})
    held=rel.commit(result,False)
    state={"main_character_id":"BELO","needs_hint":True,
      "characters":[{"character_id":"BELO","visual_id":"VID-08","relationship_state":held["effective_relationship_state"],"available":True}]}
    cmd=cbe.run(state)
    self.assertEqual("HINT",cmd["dialogue_level"])
    self.assertEqual("KNOWN",cmd["relationship_state"])
if __name__=="__main__":unittest.main()
