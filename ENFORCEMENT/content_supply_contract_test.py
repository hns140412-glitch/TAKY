import unittest
from content_supply_contract import audit
class SupplyContractTests(unittest.TestCase):
    def base(self, requirements):
        return {"demand_id":"D1","consumer":"PLAY_CAMP","requirements":requirements}
    def test_incomplete(self):
        self.assertEqual(audit({})["reason"], "CONTRACT_INCOMPLETE")
    def test_no_items(self):
        self.assertEqual(audit(self.base([]))["reason"], "REQUIREMENTS_INVALID")
    def test_duplicate(self):
        self.assertEqual(audit(self.base([{"id":"a"},{"id":"a"}]))["reason"], "DUPLICATE_REQUIREMENT")
    def test_invalid_typed_ids_and_demand(self):
        self.assertEqual(audit(self.base([{'id':[]}]))['reason'],'REQUIREMENTS_INVALID')
        self.assertEqual(audit({'demand_id':True,'consumer':'PLAY_CAMP','requirements':[{'id':'R'}]})['reason'],'CONTRACT_INCOMPLETE')
    def test_existing_source_production_gap(self):
        out=audit(self.base([{"id":"a","gap_cause":"PRODUCT_MISSING"}]))
        self.assertEqual(out["actions"][0]["route"], "PRODUCTION")
        self.assertIsNone(out["coverage"])
        self.assertEqual(out["declared_coverage"], 0)
    def test_asset_binding_not_mining(self):
        out=audit(self.base([{"id":"a","gap_cause":"CONSUMER_NOT_BOUND"}]))
        self.assertEqual(out["actions"][0]["route"], "INTEGRATION")
    def test_raw_gap(self):
        out=audit(self.base([{"id":"a","gap_cause":"RAW_INCOMPLETE"}]))
        self.assertEqual(out["actions"][0]["route"], "GATHERING")
    def test_unproven_claim_is_hold(self):
        out=audit(self.base([{"id":"a","status":"CONSUMED_VERIFIED"}]))
        self.assertEqual(out["status"], "HOLD")
    def test_claimed_consumption_is_not_release(self):
        out=audit(self.base([{"id":"a","status":"CONSUMED_VERIFIED","consumer_evidence":{"artifact_ref":"art","test_ref":"test","revision":"r1"}}]))
        self.assertEqual(out["status"], "CANDIDATE")
        self.assertFalse(out["release_approved"])
        self.assertEqual(out["evidence_scope"],"DECLARATION_ONLY")
    def test_partial_coverage(self):
        out=audit(self.base([{"id":"a","status":"CONSUMED_VERIFIED","consumer_evidence":{"artifact_ref":"a","test_ref":"t","revision":"r"}},{"id":"b","gap_cause":"INDEX_MISSING"}]))
        self.assertIsNone(out["coverage"])
        self.assertEqual(out["declared_coverage"], 0.5)
        self.assertEqual(out["verified"], 0)
        self.assertEqual(out["actions"][0]["route"],"INDEXING")
if __name__=="__main__": unittest.main()
