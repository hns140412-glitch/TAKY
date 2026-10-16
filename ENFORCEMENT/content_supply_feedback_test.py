import unittest
from content_supply_feedback import feedback
class FeedbackTest(unittest.TestCase):
    def test_forming_gap(self):
        out=feedback({'status':'BLOCKED','stage':'FORMING','reason':'RAW_CHANGED'},demand_id='D')
        self.assertEqual(out['next_stage'],'FORMING')
    def test_consumer_gap(self):
        out=feedback({'status':'BLOCKED','stage':'INTEGRATION','reason':'CONSUMER_RECEIPT_INVALID'},demand_id='D')
        self.assertEqual(out['next_stage'],'INTEGRATION')
    def test_local_success_is_not_app_success(self):
        out=feedback({'status':'LOCAL_E2E_PASS','stage':'VALIDATION'},demand_id='D')
        self.assertEqual(out['next_stage'],'APPLICATION_INTEGRATION')
        self.assertFalse(out['release_approved'])
    def test_invalid(self):
        self.assertEqual(feedback({},demand_id='')['status'],'INVALID_FEEDBACK')
        self.assertEqual(feedback({'stage':[]},demand_id='D')['status'],'INVALID_FEEDBACK')
    def test_missing_index_results_are_targeted_not_auto_mined(self):
        outcome={'status':'BLOCKED','stage':'COVERAGE_DIAGNOSIS',
                 'reason':'INDEX_NO_MATCH_NOT_SOURCE_ABSENCE',
                 'detail':{'inventory':[{'id':'R1','state':'COVERAGE_RECHECK'},
                                        {'id':'R2','state':'REUSE_CANDIDATES'}]}}
        result=feedback(outcome,demand_id='D')
        self.assertEqual(result['next_stage'],'COVERAGE_DIAGNOSIS')
        self.assertEqual(result['targeted_gap_ids'],['R1'])
        self.assertFalse(result['automatic_mining_authorized'])
if __name__=='__main__':unittest.main()
