#!/usr/bin/env python3
"""Source-to-exercise-to-observation/Planner negative & positive deterministic test.

These are test responses, not observations of the user's child.
"""
import unittest
from mining_grade5_fraction_slice import ACTIVITY, MATH_PDF_SHA256, check_response
from learning_runtime import run_learning_cycle
from learning_consumer_adapters import to_ready_planner_request


def example():
    return {
        "steps":[
            {"operation":"DIVIDE","factor":3,
             "fraction":{"numerator":2,"denominator":3},
             "reason":"분자와 분모를 모두 3으로 나누면 값이 유지돼요."},
            {"operation":"MULTIPLY","factor":2,
             "fraction":{"numerator":12,"denominator":18},
             "reason":"분자와 분모를 각각 2배 하면 값이 유지돼요."},
        ],"hint_used":False,
    }


class SourceToConsumerTest(unittest.TestCase):
    def test_source_anchored_and_rewritten_not_original_bank_copy(self):
        self.assertEqual(ACTIVITY["source"]["sha256"],MATH_PDF_SHA256)
        self.assertEqual(ACTIVITY["source"]["physical_pdf_pages"],[113,117,118])
        self.assertIn("3383177",ACTIVITY["source"]["publisher_post"])
        self.assertEqual(ACTIVITY["state"],"REFERENCE_ONLY_NOT_INDEXED")
        self.assertFalse(ACTIVITY["planner_allocation_allowed"])
        self.assertIn("6/9",ACTIVITY["original_prompt"])

    def test_valid_two_methods_do_not_auto_validate_explanation_or_mastery(self):
        result=check_response(example())
        self.assertTrue(result["arithmetic_consistent"])
        self.assertEqual(result["state"],"REASONING_REVIEW_PENDING")
        self.assertFalse(result["reasoning_verified"])
        self.assertIsNone(result["learning_observation"]["correct"])
        self.assertFalse(result["planner_allocation_allowed"])
        self.assertTrue(all(x["operation_consistent"] for x in result["step_assessments"]))

    def test_equivalent_result_wrong_declared_factor_is_not_accepted(self):
        bad=example();bad["steps"][0]["factor"]=2
        out=check_response(bad)
        self.assertFalse(out["arithmetic_consistent"])
        self.assertTrue(out["step_assessments"][0]["fraction_equivalent"])
        self.assertFalse(out["step_assessments"][0]["operation_consistent"])
        self.assertEqual(out["state"],"GUIDED_RETRY_CANDIDATE")

    def test_num_or_den_only_change_is_detected(self):
        bad=example();bad["steps"][0]["fraction"]={"numerator":2,"denominator":9}
        result=check_response(bad)
        self.assertFalse(result["step_assessments"][0]["fraction_equivalent"])
        self.assertFalse(result["step_assessments"][0]["operation_consistent"])

    def test_empty_explanation_or_hints_do_not_disappear(self):
        bad=example();bad["steps"][0]["reason"]=" "
        bad["hint_used"]=True
        out=check_response(bad)
        self.assertEqual(out["state"],"GUIDED_RETRY_CANDIDATE")
        self.assertEqual(out["step_assessments"][0]["reason_review_state"],"MISSING")
        self.assertTrue(out["hint_used"])
        self.assertTrue(out["learning_observation"]["assisted"])
        self.assertIsNone(out["learning_observation"]["correct"])

    def test_invalid_factor_zero_bool_or_oversize_is_not_accepted(self):
        for factor in [0,True,1000,-3]:
            with self.subTest(factor=factor):
                bad=example();bad["steps"][0]["factor"]=factor
                self.assertFalse(check_response(bad)["arithmetic_consistent"])

    def test_missing_step_never_mints_learning_observation(self):
        bad=example();bad["steps"]=bad["steps"][:1]
        out=check_response(bad)
        self.assertEqual(out["state"],"HOLD_INPUT")
        self.assertIsNone(out["learning_observation"])

    def test_unindexed_reference_cannot_trigger_learning_action_or_planner(self):
        observed=check_response(example())
        runtime=run_learning_cycle({
            "context":{"skill_id":observed["learning_observation"]["skill_id"]},
            "evidence_candidates":[{
                "source_id":"PROVISIONAL:ICE3383177:MATH",
                "index_state":"STAGED",
                "authorization_class":"REFERENCE_ONLY",
                "canonical_title":"Source-anchored grade-5 fraction exercise",
            }],
            "observations":[observed["learning_observation"]],
        })
        self.assertEqual(runtime["strategy_selection"]["strategy"],"HOLD_FOR_EVIDENCE")
        self.assertEqual(runtime["next_learning_action"]["action"],"NO_LEARNING_ACTION")
        ready=to_ready_planner_request({"runtime":runtime})
        self.assertFalse(ready["accepted_for_planner"])
        self.assertIsNone(ready["planner_date"])


if __name__=="__main__":unittest.main()
