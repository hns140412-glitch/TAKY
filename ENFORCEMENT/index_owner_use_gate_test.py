"""Adversarial trusted-host boundary tests; all receipts and rows synthetic."""
import unittest
from owner_test_fixture import make_row,verifier_for
from index_owner_use_gate import reviewed_learning_row
from learning_orchestrator import orchestrate_learning
from learning_index_bridge import retrieve_learning_evidence
from learning_runtime import run_learning_cycle

ROW=make_row("TEST_OWNER_ID","fraction reasoning",short_summary="fraction reasoning")
VERIFIER=verifier_for(ROW)
REQUEST={"query":"fraction reasoning","minimum_results":1}

class IndexOwnerIndependentTrust(unittest.TestCase):
 def test_no_host_verifier_blocks_claimed_indexed_and_forged_payload_receipt(self):
    fake=dict(ROW,owner_verified=True,index_review_receipt={
        "issuer":"INDEXING_OWNER","decision":"INDEXED","reviewed":True})
    out=retrieve_learning_evidence(REQUEST,[fake])
    self.assertFalse(out["evidence_sufficient_for_review"])
    self.assertEqual(out["evidence_gap"]["staged_candidate_count"],1)
    self.assertIsNone(reviewed_learning_row(fake,None))

 def test_matching_independent_owner_registry_permits_only_reviewed_row(self):
    out=retrieve_learning_evidence(REQUEST,[ROW],owner_verifier=VERIFIER)
    self.assertTrue(out["evidence_sufficient_for_review"])
    self.assertEqual(out["evidence_candidates"][0]["row"]["source_ref"],ROW["source_ref"])
 def test_request_flags_cannot_override_independent_registry(self):
    edits=(
       {"source_id":"OTHER"},
       {"content_hash":"0"*64},
       {"index_version":"FAKE_VERSION"},
       {"source_ref":"FAKE_REF"},
       {"authorization_class":"DIRECT_USE_READY"},
       {"locator":"https://attacker.example/test"},
    )
    for changed in edits:
        with self.subTest(changed=changed):
            candidate={**ROW,**changed}
            self.assertIsNone(reviewed_learning_row(candidate,VERIFIER))
    def exploded(*_): raise RuntimeError("test-only verifier failure")
    self.assertIsNone(reviewed_learning_row(ROW,exploded))

 def test_orchestrator_and_runtime_fail_closed_without_verifier(self):
    payload={"evidence_request":REQUEST,"index_rows":[ROW],
             "context":{"skill_id":"SYNTHETIC_TEST"},"observations":[]}
    blocked=orchestrate_learning(payload)
    self.assertEqual(blocked["runtime"]["strategy_selection"]["strategy"],"HOLD_FOR_EVIDENCE")
    self.assertFalse(blocked["runtime"]["next_learning_action"]["planner_allocation_allowed"])
    direct=run_learning_cycle({"context":{},"evidence_candidates":[ROW],"observations":[]})
    self.assertFalse(direct["next_learning_action"]["planner_allocation_allowed"])
    authorized=orchestrate_learning(payload,owner_verifier=VERIFIER)
    self.assertTrue(authorized["retrieval"]["evidence_sufficient_for_review"])
    self.assertEqual(authorized["runtime"]["strategy_selection"]["reason"],"NO_LEARNER_OBSERVATION")
    self.assertFalse(authorized["runtime"]["next_learning_action"]["planner_allocation_allowed"])
    observed=orchestrate_learning({**payload,"observations":[{"correct":False,"assisted":False}]},
                                  owner_verifier=VERIFIER)
    self.assertTrue(observed["runtime"]["next_learning_action"]["planner_allocation_allowed"])
    self.assertIsNone(observed["runtime"]["next_learning_action"]["planner_date"])

 def test_independent_conditional_receipt_is_reviewable_not_action_ready(self):
    conditional=make_row("TEST_CONDITIONAL","fraction reasoning",
                         short_summary="fraction reasoning",
                         authorization_class="CONDITIONAL")
    output=orchestrate_learning(
       {"evidence_request":REQUEST,"index_rows":[conditional],
        "context":{"skill_id":"SYNTHETIC_TEST"},"observations":[]},
       owner_verifier=verifier_for(conditional))
    self.assertTrue(output["retrieval"]["evidence_sufficient_for_review"])
    self.assertEqual(output["runtime"]["strategy_selection"]["strategy"],"HOLD_FOR_REVIEW")
    self.assertFalse(output["runtime"]["next_learning_action"]["planner_allocation_allowed"])
    self.assertIsNone(output["mining_request_candidate"])

if __name__=="__main__":unittest.main()
