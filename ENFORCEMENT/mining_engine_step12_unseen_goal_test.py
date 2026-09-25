#!/usr/bin/env python3
import unittest
from mining_engine_step12_unseen_goal import run_benchmark

FOREIGN={"strategies":[{"strategy_id":"LEARN-1","task_family":"LEARNING_ENGINE","goal_pattern":"adaptive learning mastery","status":"PROMOTED"}],"failures":[]}

class UnseenGoalTest(unittest.TestCase):
    def test_multi_family_unseen_goals(self):
        payload={"minimum_distinct_families":4,"cases":[
          {"case_id":"UG-ARCH","task":{"task_family":"ARCHITECTURE_REGULATION","goal":"establish evidence for a newly encountered facade setback rule","unknown":["official rule text","effective date"],"conflict":["secondary summaries disagree"],"freshness_required":True,"max_research_depth":"D3"},"memory":FOREIGN,"gold":{"expected_frontier_ids":["official rule text","effective date","secondary summaries disagree"],"expected_depth":"D3","expect_no_memory_strategy":True}},
          {"case_id":"UG-DEVICE","task":{"task_family":"DEVICE_PROCUREMENT","goal":"compare an unfamiliar field scanner workflow","unknown":["supported formats"],"foundation_requirements":["integration requirements"],"max_research_depth":"D2"},"memory":FOREIGN,"gold":{"expected_frontier_ids":["supported formats","integration requirements"],"expected_depth":"D1","expect_no_memory_strategy":True}},
          {"case_id":"UG-PUBLIC","task":{"task_family":"PUBLIC_DATA","goal":"locate an unfamiliar municipal dataset","unknown":["canonical dataset"],"freshness_required":True,"max_research_depth":"D2"},"memory":FOREIGN,"gold":{"expected_frontier_ids":["canonical dataset"],"expected_depth":"D1","expect_no_memory_strategy":True}},
          {"case_id":"UG-UI","task":{"task_family":"MOTION_REFERENCE","goal":"find implementation evidence for an unfamiliar interaction","unknown":["reference implementation","runtime constraints"],"advanced_requirements":["fallback behavior"],"max_research_depth":"D2"},"memory":FOREIGN,"gold":{"expected_frontier_ids":["reference implementation","runtime constraints","fallback behavior"],"expected_depth":"D2","expect_no_memory_strategy":True}}
        ]}
        r=run_benchmark(payload)
        self.assertTrue(r["pass"],r)
        self.assertEqual(r["passed"],4)

    def test_empty_suite_fails(self):
        self.assertFalse(run_benchmark({"cases":[]})["pass"])

if __name__=="__main__": unittest.main()
