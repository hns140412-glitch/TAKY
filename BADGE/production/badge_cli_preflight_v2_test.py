#!/usr/bin/env python3
import unittest
from badge_cli_preflight_v2 import inspect
class PreflightTests(unittest.TestCase):
    def test_structural_pass_but_execution_blocked_without_adapter(self):
        r=inspect();self.assertTrue(r["structural_preflight_pass"]);self.assertFalse(r["cli_ready"])
        self.assertIn("EXECUTOR_ADAPTER_NOT_BOUND",r["blockers"])
        self.assertIn("GENERATION_NOT_EXPLICITLY_ENABLED",r["blockers"])
    def test_generation_cannot_be_enabled_without_adapter(self):
        r=inspect(enable_generation=True);self.assertFalse(r["structural_preflight_pass"])
        self.assertIn("GENERATION_WITHOUT_EXECUTOR_FORBIDDEN",r["errors"])
    def test_bound_adapter_plus_explicit_enable_is_ready_not_executed(self):
        r=inspect(executor_adapter="LOCAL_CLI_TEST_ADAPTER",enable_generation=True)
        self.assertTrue(r["structural_preflight_pass"]);self.assertTrue(r["cli_ready"])
        self.assertFalse(r["generation_executed"])
    def test_batch_plan_is_five_and_complete(self):
        r=inspect();self.assertEqual(5,r["batch_size"]);self.assertEqual(7,r["rework_batch_count"])
        self.assertEqual(31,sum(len(x) for x in r["rework_batches"]))
        self.assertTrue(all(len(x)<=5 for x in r["rework_batches"]))
    def test_initial_award_rule(self):
        r=inspect();self.assertEqual(29,r["counts"]["KEEP_CANDIDATE"]);self.assertEqual(31,r["counts"]["REWORK_REQUIRED"])
if __name__=="__main__":unittest.main()
