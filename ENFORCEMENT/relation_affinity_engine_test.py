import importlib.util,unittest
from pathlib import Path
P=Path(__file__).with_name("relation_affinity_engine.py")
s=importlib.util.spec_from_file_location("r",P);r=importlib.util.module_from_spec(s);s.loader.exec_module(r)

POL={"familiar_min_verified_episodes":3,"trusted_min_verified_episodes":8}
class T(unittest.TestCase):
  def member(self,n=0,committed="KNOWN"):
    ev=[{"event_id":"meet","type":"FIRST_MEETING","verified":True,"evidence_ref":"m"}]
    ev += [{"event_id":f"e{i}","type":"SHARED_EPISODE","verified":True,"evidence_ref":f"r{i}"} for i in range(n)]
    return {"character_id":"BELO","committed_state":committed,"events":ev}
  def test_unverified_does_not_count(self):
    m=self.member(2);m["events"].append({"event_id":"fake","type":"SHARED_EPISODE","verified":False,"evidence_ref":"x"})
    x=r.evaluate(m,POL);self.assertEqual(2,x["verified_episode_count"]);self.assertEqual("KNOWN",x["candidate_state"])
  def test_candidate_does_not_auto_commit(self):
    x=r.evaluate(self.member(3),POL);self.assertEqual("FAMILIAR",x["candidate_state"]);self.assertTrue(x["promotion_required"]);self.assertFalse(x["promotion_auto_commit"])
    held=r.commit(x,False);self.assertEqual("KNOWN",held["effective_relationship_state"]);self.assertEqual("HELD",held["status"])
  def test_owner_commit_changes_effective_state(self):
    x=r.evaluate(self.member(3),POL);c=r.commit(x,True);self.assertEqual("FAMILIAR",c["effective_relationship_state"]);self.assertEqual("COMMITTED",c["status"])
  def test_no_reward_or_power(self):
    x=r.evaluate(self.member(8),POL);self.assertEqual((0,0,0),(x["reward_delta"],x["power_delta"],x["ability_delta"]))
if __name__=="__main__":unittest.main()
