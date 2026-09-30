"""Regression for legacy-untyped Index rows and domain-use gates.
All rows are synthetic. Does not attest an actual independent owner receipt."""
import unittest
from learning_index_bridge import retrieve_learning_evidence
from learning_runtime import run_learning_cycle
from learning_orchestrator import orchestrate_learning
from owner_test_fixture import make_row,verifier_for
from index_owner_use_gate import reviewed_learning_row

def row(**kwargs):
    return {"source_id":"SYNTHETIC:TEST:1","canonical_title":"fraction reasoning",
            **kwargs}
def cycle(item):
    return run_learning_cycle({"context":{"skill_id":"SYNTHETIC_TEST"},
             "evidence_candidates":[item],"observations":[]},
             owner_verified_source_ids={item["source_id"]})

class IndexOwnerUseGuardTest(unittest.TestCase):
 def test_untyped_legacy_is_discovery_only(self):
    item=row(utilization_class="REFERENCE_ONLY")
    result=retrieve_learning_evidence({"query":"fraction reasoning","minimum_results":1},[item])
    self.assertFalse(result["evidence_sufficient_for_review"])
    self.assertEqual(result["evidence_gap"]["staged_candidate_count"],1)
    self.assertEqual(cycle(item)["next_learning_action"]["planner_allocation_allowed"],False)

 def test_claimed_ready_class_cannot_overcome_candidate_or_missing_state(self):
    for state in (None,"CANDIDATE","STAGED","PENDING","HELD","REJECTED"):
        with self.subTest(state=state):
            item=row(authorization_class="READY_WITH_GUARDS",index_state=state)
            self.assertFalse(cycle(item)["next_learning_action"]["planner_allocation_allowed"])
 def test_explicit_indexed_reference_only_not_executable(self):
    item=row(index_state="INDEXED",authorization_class="REFERENCE_ONLY")
    find=retrieve_learning_evidence({"query":"fraction reasoning"},[item])
    self.assertFalse(find["evidence_sufficient_for_review"])
    run=cycle(item)
    self.assertEqual(run["strategy_selection"]["strategy"],"HOLD_FOR_EVIDENCE")
    self.assertFalse(run["next_learning_action"]["planner_allocation_allowed"])

 def test_missing_domain_class_not_silent_reference_only(self):
    item=row(index_state="INDEXED")
    self.assertFalse(cycle(item)["next_learning_action"]["planner_allocation_allowed"])

 def test_explicit_indexed_authorized_classes_still_work(self):
    for cls in ("READY_WITH_GUARDS","CONDITIONAL","DIRECT_USE_READY"):
        with self.subTest(cls=cls):
            item=row(index_state="INDEXED",authorization_class=cls)
            self.assertTrue(cycle(item)["next_learning_action"]["planner_allocation_allowed"])

 def test_orchestrator_propagates_missing_owner_gap_to_mining(self):
    output=orchestrate_learning({"evidence_request":{"query":"fraction reasoning","minimum_results":1},
         "index_rows":[row(utilization_class="REFERENCE_ONLY")],
         "context":{"skill_id":"SYNTHETIC_TEST"},"observations":[]})
    self.assertFalse(output["retrieval"]["evidence_sufficient_for_review"])
    self.assertFalse(output["runtime"]["next_learning_action"]["planner_allocation_allowed"])
    self.assertIsNotNone(output["mining_request_candidate"])

if __name__=="__main__":unittest.main()
