"""Regression: normal explicitly authorized development is not restricted to one call."""
import unittest
from taky_gate import validate_record

class AuthorizedDevelopmentBudgetTests(unittest.TestCase):
    def gate(self, **extra):
        rec = dict(external_resource_action=True, user_authorized_development=True,
                   external_call_count_for_same_goal=5)
        rec.update(extra)
        return validate_record(rec)

    def test_normal_repeated_implementation_has_reasonable_budget(self):
        self.assertNotIn("RULE_NOT_APPLIED", self.gate())

    def test_bulk_use_needs_explicit_override(self):
        self.assertIn("RULE_NOT_APPLIED", self.gate(external_call_count_for_same_goal=9))

    def test_replay_without_new_evidence_still_blocked(self):
        self.assertIn("RULE_NOT_APPLIED", self.gate(same_external_call_repeated_without_new_evidence=True))

    def test_paid_and_deploy_are_not_automatically_whitelisted(self):
        for risky in ("paid_api_call", "deployment_attempted", "destructive_action"):
            with self.subTest(risky=risky):
                self.assertIn("RULE_NOT_APPLIED", self.gate(**{risky: True}))

    def test_existing_explicit_budget_remains_authoritative(self):
        self.assertIn("RULE_NOT_APPLIED", self.gate(external_call_budget=2))
        self.assertNotIn("RULE_NOT_APPLIED", self.gate(external_call_budget=2, explicit_override_approved=True))

if __name__ == "__main__":
    unittest.main()
