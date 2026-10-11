#!/usr/bin/env python3
import unittest
from execution_checkpoint import validate_approval_evidence
from runtime_orchestrator import (
    validate_delegation_contract,
    _canonical_hash,
    _delegation_parent_snapshot,
)

class AILearningExistingCoverageTest(unittest.TestCase):
    def test_approval_is_bound_to_artifact_action_identity(self):
        binding={"action_kind":"WRITE","action_payload_hash":"sha256:"+"a"*64}
        good={
          "approval_id":"A1","approver_ref":"user","decision":"APPROVE",
          "namespace":"N","task_id":"T","checkpoint_hash":"sha256:"+"b"*64,
          "atomic_unit":"U","action_kind":"WRITE","action_payload_hash":"sha256:"+"a"*64,
        }
        _, failures=validate_approval_evidence(
            good,namespace="N",task_id="T",checkpoint_hash_value="sha256:"+"b"*64,
            atomic_unit="U",approval_binding=binding)
        self.assertEqual(failures,[])
        bad=dict(good); bad["action_payload_hash"]="sha256:"+"c"*64
        _, failures=validate_approval_evidence(
            bad,namespace="N",task_id="T",checkpoint_hash_value="sha256:"+"b"*64,
            atomic_unit="U",approval_binding=binding)
        self.assertIn("APPROVAL_EVIDENCE_ACTION_PAYLOAD_HASH_MISMATCH",failures)

    def test_delegation_cannot_widen_change_scope(self):
        record={
          "task_id":"T","applicable_rule_refs":["R1"],
          "allowed_change_scope":["ENFORCEMENT/*"],"forbidden_actions":["DEPLOY"],
          "approval_scope":[],"connection_scope":[],"cost_ceiling":5,
        }
        parent=_delegation_parent_snapshot(record)
        base={
          "parent_task_id":"T","child_id":"C",
          "parent_contract_hash":_canonical_hash(parent),
          "inherited_rule_refs":["R1"],
          "inherited_change_scope":["ENFORCEMENT/*"],
          "inherited_forbidden_actions":["DEPLOY"],
          "inherited_approval_scope":[],"inherited_connection_scope":[],
          "inherited_cost_ceiling":5,
          "return_contract":["result"],
        }
        result, failures=validate_delegation_contract(record,{**base,"return_fields":["result"],"delegation_contract":base})
        # worker_context carries return_fields only; contract is read from record.
        record["delegation_contract"]=base
        result, failures=validate_delegation_contract(record,{"return_fields":["result"]})
        self.assertEqual(failures,[])
        widened=dict(base); widened["inherited_change_scope"]=["*"]
        record["delegation_contract"]=widened
        _, failures=validate_delegation_contract(record,{"return_fields":["result"]})
        self.assertIn("DELEGATION_CHANGE_SCOPE_WIDENED",failures)

if __name__=="__main__":
    unittest.main()
