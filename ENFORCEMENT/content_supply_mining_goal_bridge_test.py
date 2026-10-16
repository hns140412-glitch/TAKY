import unittest
from content_supply_mining_goal_bridge import evaluate_raw_goal

class MiningGoalBridgeTests(unittest.TestCase):
    def test_verified_raw_covers_only_its_requirement(self):
        out=evaluate_raw_goal(['R1','R2'],['R1'])
        self.assertEqual(out['status'],'RAW_HASH_CANDIDATE_ONLY')
        self.assertEqual(out['raw_coverage'],0.5)
        self.assertIn('R2',out['unresolved_ids'])
        self.assertFalse(out['content_goal_sufficient'])
    def test_full_raw_coverage_never_means_content_release(self):
        out=evaluate_raw_goal(['R1'],['R1'])
        self.assertTrue(out['raw_goal_sufficient'])
        self.assertFalse(out['content_goal_sufficient'])
        self.assertFalse(out['release_approved'])
    def test_missing_raw_is_open(self):
        out=evaluate_raw_goal(['R1'],[])
        self.assertEqual(out['unresolved_ids'],['R1'])
if __name__=='__main__':unittest.main()
