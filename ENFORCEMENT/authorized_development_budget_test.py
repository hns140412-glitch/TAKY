"""Regression: normal explicitly authorized development is not restricted to one call.

The raised budget requires a trusted USER authorization (signed TAKY2 authority
source_registry entry), not a self-declared record flag.
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

import taky_gate
from taky_gate import validate_record

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TRUSTED_REF = "user:authorization:external-development-test"


class AuthorizedDevelopmentBudgetTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(
            taky_gate,
            "trusted_development_authorization",
            side_effect=lambda ref: ref == TRUSTED_REF,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def gate(self, **extra):
        rec = dict(external_resource_action=True, user_authorized_development=True,
                   user_authorization_ref=TRUSTED_REF,
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

    def test_self_declared_flag_without_trusted_ref_keeps_single_call_budget(self):
        self.assertIn("RULE_NOT_APPLIED", self.gate(user_authorization_ref=None))
        self.assertIn("RULE_NOT_APPLIED", self.gate(user_authorization_ref="user:forged"))

    def test_trusted_ref_without_flag_keeps_single_call_budget(self):
        self.assertIn("RULE_NOT_APPLIED", self.gate(user_authorized_development=False))


class TrustedDevelopmentAuthorizationTests(unittest.TestCase):
    """Exercises the real verifier against a stubbed signed bundle."""

    def verify(self, source_registry, ref=TRUSTED_REF, key_exists=True):
        import TAKY2.state_store as state_store

        bundle = ({"source_registry": source_registry}, {}, "digest")
        with mock.patch.object(state_store, "load_bundle", return_value=bundle), \
             mock.patch.object(Path, "exists", return_value=key_exists), \
             mock.patch.object(Path, "read_bytes", return_value=b"k" * 32):
            return taky_gate.trusted_development_authorization(ref)

    def entry(self, **over):
        src = {"actor": "USER", "kind": "authorization", "scope": "external_development_calls"}
        src.update(over)
        return {TRUSTED_REF: src}

    def test_signed_user_authorization_with_scope_is_trusted(self):
        self.assertTrue(self.verify(self.entry()))

    def test_wrong_scope_kind_actor_or_status_is_rejected(self):
        for over in ({"scope": "doc_write"}, {"scope": None}, {"kind": "statement"},
                     {"actor": "AI"}, {"status": "SUPERSEDED"}, {"status": "REVOKED"}):
            with self.subTest(over=over):
                self.assertFalse(self.verify(self.entry(**over)))

    def test_unknown_or_blank_ref_is_rejected(self):
        self.assertFalse(self.verify(self.entry(), ref="user:other"))
        self.assertFalse(self.verify(self.entry(), ref=""))
        self.assertFalse(self.verify(self.entry(), ref=None))

    def test_missing_runtime_key_fails_closed_without_creating_one(self):
        self.assertFalse(self.verify(self.entry(), key_exists=False))

    def test_bundle_integrity_error_fails_closed(self):
        import TAKY2.state_store as state_store

        with mock.patch.object(state_store, "load_bundle", side_effect=state_store.StateIntegrityError("bad mac")), \
             mock.patch.object(Path, "exists", return_value=True), \
             mock.patch.object(Path, "read_bytes", return_value=b"k" * 32):
            self.assertFalse(taky_gate.trusted_development_authorization(TRUSTED_REF))


if __name__ == "__main__":
    unittest.main()
