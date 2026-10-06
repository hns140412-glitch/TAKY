import unittest

from TAKY2.enforcement import action_digest, route_fingerprint
from TAKY2.orchestration import guidance_for_failure, role_assignment
from TAKY2.orchestrator import (
    consume_receipt,
    finalize,
    persist_preflight,
    preflight,
    record_outcome,
)
from TAKY2.test_enforcement import trusted


def runtime_state():
    return {
        "runtime_version": 1,
        "authority_digest": "auth1",
        "runtime": {
            "account_attestation": {
                "account": "HNS",
                "verified": True,
                "binding_mode": "FIRST_AUTH_RUNTIME",
                "identity_provider": "GOOGLE_OIDC_VERIFIED",
                "principal_id": "google:sub-hns",
                "family_id": "family-hns",
                "self_member_id": "member-hns",
                "source": "central-family-session",
                "evidence_ref": "auth:test",
                "session_id": "session-test",
                "first_bound_evidence_ref": "auth:test",
                "first_bound_session_id": "session-test",
                "verified_by": "auth-bridge",
            }
        },
        "context": {
            "premise_loaded": True,
            "snapshot_verified": True,
            "full_reread_authorized": False,
        },
        "route_ledgers": {},
        "preflight_receipts": {},
        "active_attempts": {},
        "execution_outcomes": {},
        "evidence_registry": {},
        "completion_registry": {},
        "consumed_approvals": {},
        "user_events": {},
    }


def plan(method="python", task_id="task-q002", action_id="read"):
    return {
        "task_id": task_id,
        "action_id": action_id,
        "context": {"mode": "delta"},
        "attempt": {
            "target": "Q002",
            "method_or_tool": method,
        },
        "call": {
            "model": "local",
            "effort": "low",
            "context": "delta",
            "expected_calls": 1,
        },
    }


class OrchestratorTests(unittest.TestCase):
    def test_role_category_is_stable_but_implementer_actor_is_task_assigned(self):
        claude = role_assignment(
            {"kind": "LOCAL_WRITE", "assigned_implementer": "CLAUDE_CODE"},
            verification_tier="STANDARD",
        )
        local = role_assignment(
            {"kind": "LOCAL_WRITE", "assigned_implementer": "LOCAL_CODE_WRITER"},
            verification_tier="STANDARD",
        )
        self.assertEqual(claude["implementer_role"], "CODE_WRITER")
        self.assertEqual(local["implementer_role"], "CODE_WRITER")
        self.assertEqual(claude["implementer_actor"], "CLAUDE_CODE")
        self.assertEqual(local["implementer_actor"], "LOCAL_CODE_WRITER")
        self.assertNotEqual(claude["implementer_actor"], local["implementer_actor"])
        self.assertEqual(
            claude["implementer_assignment_policy"],
            "TASK_FIT_NECESSITY",
        )
        self.assertEqual(
            claude["available_control_roles"],
            ["NAVIGATOR", "GUARDIAN", "DRIVER", "SCOUT"],
        )
        self.assertEqual(claude["economy_policy"], "SAVEY_AI_ECONOMY")
        self.assertEqual(
            claude["canonical_systemwide_ref"],
            "TAKY_SYSTEMWIDE_LOGIC_RECONCILIATION_V2_CANONICAL@2026-10-06",
        )

    def test_recoverable_gate_state_redirects_instead_of_terminal_block(self):
        guidance = guidance_for_failure(
            "KEY",
            "KEY_NOT_LOCKED",
            "user-grounded intent missing",
        )
        self.assertEqual(guidance["mode"], "REDIRECT")
        self.assertFalse(guidance["terminal"])
        self.assertIn("trusted USER intent", guidance["next_action"])

    def test_explicit_user_stop_is_terminal(self):
        guidance = guidance_for_failure(
            "DONE",
            "ABANDONED",
            "explicit USER stop",
        )
        self.assertEqual(guidance["mode"], "BLOCKED")
        self.assertTrue(guidance["terminal"])
        self.assertIn("USER stop", guidance["next_action"])

    def test_preflight_key_not_locked_returns_redirect_guidance(self):
        t = trusted()
        t["key"].pop("USER_INTENT")
        out = preflight(plan(), t)
        self.assertFalse(out["allowed"])
        self.assertEqual(out["blocked_by"], "KEY")
        self.assertEqual(out["mode"], "REDIRECT")
        self.assertFalse(out["guidance"]["terminal"])

    def test_preflight_has_unique_receipt_and_local_only_mode(self):
        t = trusted()
        a = preflight(plan(), t)
        b = preflight(plan(), t)
        self.assertTrue(a["allowed"])
        self.assertFalse(a["call_allowed"])
        self.assertEqual(a["mode"], "LOCAL_ONLY")
        self.assertEqual(
            a["orchestration"]["orchestrator"],
            "CHATGPT_LEAD_ORCHESTRATOR",
        )
        self.assertEqual(a["orchestration"]["verifier"], "CODEX")
        self.assertEqual(a["orchestration"]["independent_reviewer"], "CLAUDE")
        self.assertNotEqual(a["receipt_id"], b["receipt_id"])

    def test_task_id_change_cannot_bypass_same_route_lock(self):
        t = trusted()
        first = preflight(plan(task_id="task-a"), t)
        runtime = persist_preflight(runtime_state(), first)

        t["active_attempts"] = runtime["active_attempts"]
        t["route_ledgers"] = runtime["route_ledgers"]

        second = preflight(plan(task_id="task-b"), t)
        self.assertFalse(second["allowed"])
        self.assertEqual(second["blocked_by"], "ROUTE")

    def test_different_routes_are_counted_within_trusted_scope(self):
        t = trusted()
        runtime = runtime_state()
        for method in ["a", "b", "c"]:
            t["route_ledgers"] = runtime["route_ledgers"]
            out = preflight(plan(method=method, task_id="t-" + method), t)
            self.assertTrue(out["allowed"])
            runtime = persist_preflight(runtime, out)
            runtime["active_attempts"].pop(out["execution_key"], None)

        t["route_ledgers"] = runtime["route_ledgers"]
        t["active_attempts"] = runtime["active_attempts"]
        fourth = preflight(plan(method="d", task_id="t-d"), t)
        self.assertFalse(fourth["allowed"])
        self.assertEqual(fourth["blocked_by"], "ROUTE")
        packet = fourth["escalation_packet"]
        self.assertIn("cause", packet)
        self.assertIn("attempts", packet)
        self.assertIn("remaining_options", packet)
        self.assertIn("recommendation", packet)
        self.assertIn("user_decision_or_info", packet)

    def test_route_budget_is_scoped_by_action_execution_scope(self):
        t = trusted()
        runtime = runtime_state()
        for method in ["a", "b", "c"]:
            t["route_ledgers"] = runtime["route_ledgers"]
            out = preflight(plan(method=method, task_id="t-" + method), t)
            runtime = persist_preflight(runtime, out)
            runtime["active_attempts"].pop(out["execution_key"], None)

        t["route_ledgers"] = runtime["route_ledgers"]
        review_plan = {
            "task_id": "review-1",
            "action_id": "review",
            "context": {"mode": "delta"},
            "attempt": {"target": "Q002", "method_or_tool": "claude"},
            "call": {
                "model": "sonnet",
                "effort": "medium",
                "context": "delta",
                "expected_calls": 1,
            },
        }
        out = preflight(review_plan, t)
        self.assertTrue(out["allowed"])
        self.assertTrue(out["call_allowed"])

    def test_plan_cannot_supply_fake_action(self):
        p = plan()
        p["action_id"] = "missing"
        p["action"] = {"kind": "EXTERNAL_WRITE"}
        out = preflight(p, trusted())
        self.assertFalse(out["allowed"])
        self.assertEqual(out["blocked_by"], "KEY")
        self.assertEqual(out["mode"], "REDIRECT")
        self.assertEqual(
            out["guidance"]["owner"],
            "CHATGPT_LEAD_ORCHESTRATOR",
        )
        self.assertIn("registered action", out["guidance"]["next_action"])

    def test_receipt_binds_action_call_and_execution_identity(self):
        out = preflight(plan(), trusted())
        runtime = persist_preflight(runtime_state(), out)
        receipt = runtime["preflight_receipts"][out["receipt_id"]]
        self.assertEqual(receipt["authority_digest"], "auth1")
        self.assertEqual(receipt["plan_digest"], out["plan_digest"])
        self.assertEqual(receipt["call_digest"], out["call_digest"])
        self.assertEqual(receipt["action_id"], "read")
        self.assertEqual(receipt["execution_key"], out["execution_key"])
        self.assertEqual(
            receipt["orchestration"]["orchestrator"],
            "CHATGPT_LEAD_ORCHESTRATOR",
        )
        self.assertEqual(receipt["orchestration"]["verifier"], "CODEX")
        self.assertEqual(
            receipt["orchestration"]["independent_reviewer"],
            "CLAUDE",
        )
        self.assertFalse(receipt["call_allowed"])
        self.assertEqual(
            [item["gate"] for item in receipt["gate_receipts"]],
            ["KEY", "CONTEXT", "ROUTE", "COST"],
        )
        for item in receipt["gate_receipts"]:
            profile = item["validator_profile"]
            self.assertIn(profile["primary"], {"AUTO", "AI_SEMANTIC", "HUMAN_AUTHORITY"})
            self.assertIn("trigger", profile)
            self.assertIn("human_authority_condition", profile)
            self.assertIn(profile["receipt_custodian"], {"GUARDIAN", "DRIVER"})

    def test_bound_approval_consumes_specific_ref_only(self):
        t = trusted()
        action = t["action_registry"]["delete"]
        approval_key = "action:" + action_digest(action)
        t["approvals"][approval_key] = "u:approve"

        first = preflight(plan(task_id="delete-1", action_id="delete"), t)
        self.assertTrue(first["allowed"])
        runtime = persist_preflight(runtime_state(), first)
        self.assertEqual(
            runtime["consumed_approvals"][approval_key],
            "u:approve",
        )

        t["consumed_approvals"] = runtime["consumed_approvals"]
        blocked = preflight(
            plan(task_id="delete-2", action_id="delete"),
            t,
        )
        self.assertFalse(blocked["allowed"])

        t["approvals"][approval_key] = "u:approve2"
        reapproved = preflight(
            plan(task_id="delete-3", action_id="delete"),
            t,
        )
        self.assertTrue(reapproved["allowed"])

    def test_failure_outcome_updates_only_its_execution_scope(self):
        t = trusted()
        out = preflight(plan(), t)
        runtime = persist_preflight(runtime_state(), out)
        updated = record_outcome(runtime, out["receipt_id"], "VALIDATION")

        self.assertEqual(
            updated["execution_outcomes"][out["receipt_id"]],
            "VALIDATION",
        )
        self.assertNotIn(out["execution_key"], updated["active_attempts"])
        scope = out["execution_scope"]
        self.assertTrue(
            updated["route_ledgers"][scope]["failed_signatures"]
        )

    def test_success_outcome_is_required_for_done(self):
        t = trusted()
        out = preflight(plan(), t)
        rid = out["receipt_id"]
        runtime = persist_preflight(runtime_state(), out)
        runtime = record_outcome(runtime, rid, "SUCCESS")

        t["preflight_receipts"] = runtime["preflight_receipts"]
        t["execution_outcomes"] = runtime["execution_outcomes"]
        receipt = runtime["preflight_receipts"][rid]
        t["completion_registry"][rid] = {
            "plan_digest": receipt["plan_digest"],
            "action_digest": receipt["action_digest"],
            "call_digest": receipt["call_digest"],
            "authority_digest": receipt["authority_digest"],
            "verification_tier": receipt["verification_tier"],
            "key_match": True,
            "critical_gaps": [],
            "required_verifications": ["technical", "intent"],
            "passed_verifications": ["technical", "intent"],
            "user_confirmation_ref": None,
        }
        t["evidence_registry"]["ev"] = {
            "type": "runtime_test",
            "evidence_type": "runtime_test",
            "verified": True,
            "acceptance_state": "ACCEPTED",
            "claim_supported": "execution_verification",
            "scope": receipt["execution_scope"],
            "producer": "executor-1",
            "validator": "verifier-1",
            "source_or_artifact_ref": "ev",
            "authority_digest_or_key_version": receipt["authority_digest"],
            "verification_tier": receipt["verification_tier"],
            "source_status": "CURRENT",
            "receipt_id": rid,
            "plan_digest": receipt["plan_digest"],
            "action_digest": receipt["action_digest"],
            "call_digest": receipt["call_digest"],
        }

        result = finalize(
            {"preflight_receipt": rid, "evidence_refs": ["ev"]},
            t,
        )
        self.assertEqual(result["state"], "DELIVERED_UNCONFIRMED")

    def test_consumed_receipt_removes_execution_lock(self):
        runtime = runtime_state()
        runtime["preflight_receipts"]["pf:x"] = {
            "consumed": False,
            "execution_key": "ek",
        }
        runtime["active_attempts"]["ek"] = {
            "receipt_id": "pf:x",
            "status": "SUCCESS",
        }
        updated = consume_receipt(runtime, "pf:x")
        self.assertTrue(updated["preflight_receipts"]["pf:x"]["consumed"])
        self.assertNotIn("ek", updated["active_attempts"])

    def test_route_fingerprint_normalization_prevents_alias_budget_bypass(self):
        self.assertEqual(
            route_fingerprint({"target": "Q002", "method_or_tool": "Python"}),
            route_fingerprint({"target": " q002 ", "method_or_tool": "python "}),
        )


if __name__ == "__main__":
    unittest.main()
