import unittest

from TAKY2.enforcement import action_digest, route_fingerprint, stable_hash
from TAKY2.orchestration import guidance_for_failure, role_assignment
from TAKY2.orchestrator import (
    consume_receipt,
    finalize,
    persist_control_incident,
    persist_done_control_incident,
    persist_done_gate_receipt,
    persist_preflight,
    preflight,
    record_outcome,
)
from TAKY2.test_enforcement import startup_receipt, trusted


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
            "startup_readback_receipt": startup_receipt(),
        },
        "route_ledgers": {},
        "preflight_receipts": {},
        "active_attempts": {},
        "execution_outcomes": {},
        "evidence_registry": {},
        "completion_registry": {},
        "independent_review_registry": {},
        "done_gate_receipts": {},
        "control_incidents": {},
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
            "dry_run_plan": {
                "expected_calls": 1,
                "operations": ["single bounded external call"],
                "batch_strategy": "single-batch",
                "fallback": "HOLD",
                "paid_api": False,
            },
        },
    }


class OrchestratorTests(unittest.TestCase):
    def test_role_category_is_stable_but_implementer_actor_is_task_assigned(self):
        claude = role_assignment(
            {
                "kind": "LOCAL_WRITE",
                "assigned_implementer": "CLAUDE_CODE",
                "semantic_owner_ref": "TEST_DOMAIN_OWNER",
                "semantic_owner_scope": "TEST_DOMAIN",
                "worker_roles": ["SCOPE_PLANNER", "TEST_ENGINEER"],
            },
            verification_tier="STANDARD",
        )
        local = role_assignment(
            {
                "kind": "LOCAL_WRITE",
                "assigned_implementer": "LOCAL_CODE_WRITER",
                "semantic_owner_ref": "TEST_DOMAIN_OWNER",
                "semantic_owner_scope": "TEST_DOMAIN",
                "worker_roles": ["SCOPE_PLANNER", "TEST_ENGINEER"],
            },
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
        self.assertEqual(
            claude["execution_model"],
            "ROLE_BASED_COLLABORATIVE_EXECUTION_STRUCTURE",
        )
        self.assertEqual(
            claude["metaphor_model"],
            "SHEPHERDING_COOPERATIVE_EXECUTION_MODEL",
        )
        self.assertEqual(claude["role_registry"]["verifier"], "VERIFIER")
        self.assertEqual(claude["default_actor_bindings"]["verifier"], "CODEX")
        self.assertIsNone(claude["default_actor_bindings"]["implementer"])
        self.assertEqual(claude["actor_bindings"]["implementer"], "CLAUDE_CODE")
        self.assertEqual(claude["implementer"], "CLAUDE_CODE")
        self.assertEqual(local["implementer"], "LOCAL_CODE_WRITER")
        self.assertNotEqual(claude["implementer"], claude["implementer_role"])
        self.assertEqual(claude["orchestrator_role"], "LEAD_ORCHESTRATOR")
        self.assertEqual(claude["orchestrator_actor"], "CHATGPT")
        self.assertEqual(claude["verifier_role"], "VERIFIER")
        self.assertEqual(claude["verifier_actor"], "CODEX")
        self.assertEqual(
            claude["external_ai_calls"],
            "NECESSITY_CHECK_WITHIN_COST",
        )
        self.assertEqual(
            [item["role"] for item in claude["worker_roles"]],
            ["SCOPE_PLANNER", "TEST_ENGINEER"],
        )
        self.assertTrue(
            all(
                item["semantic_owner_ref"] == "TEST_DOMAIN_OWNER"
                for item in claude["worker_roles"]
            )
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

    def test_safe_cost_misroute_is_auto_corrected(self):
        tr = trusted()
        p = plan(action_id="review")
        p["call"]["model"] = "unknown-model"
        out = preflight(p, tr)
        self.assertTrue(out["allowed"])
        self.assertEqual(out["mode"], "CORRECTED_CALL_ALLOWED")
        self.assertEqual(out["correction"]["status"], "CORRECTED")
        self.assertEqual(out["correction"]["gate"], "COST")
        corrected_model = out["correction"]["after"]["call"]["model"]
        self.assertIn(
            corrected_model,
            tr["action_registry"]["review"]["call_policy"]["allowed_models"],
        )

    def test_safe_call_count_overage_is_reduced_and_rechecked(self):
        tr = trusted()
        p = plan(action_id="review")
        p["call"]["model"] = "sonnet"
        p["call"]["effort"] = "medium"
        p["call"]["expected_calls"] = 3
        p["call"]["dry_run_plan"]["expected_calls"] = 3
        out = preflight(p, tr)
        self.assertTrue(out["allowed"])
        self.assertEqual(out["mode"], "CORRECTED_CALL_ALLOWED")
        max_calls = tr["action_registry"]["review"]["call_policy"]["max_calls"]
        self.assertEqual(out["correction"]["after"]["call"]["expected_calls"], max_calls)
        self.assertEqual(
            out["correction"]["after"]["call"]["dry_run_plan"]["expected_calls"],
            max_calls,
        )

    def test_explicit_user_stop_is_terminal(self):
        guidance = guidance_for_failure(
            "DONE",
            "ABANDONED",
            "explicit USER stop",
        )
        self.assertEqual(guidance["mode"], "BLOCKED")
        self.assertTrue(guidance["terminal"])
        self.assertIn("USER stop", guidance["next_action"])

    def test_preflight_safe_tool_blocks_drivefs_reverse_lookup(self):
        p = plan()
        p["tool_action"] = {
            "operation": "google_drive",
            "purpose": "find canonical inbox",
            "target": r"C:\Users\x\AppData\Local\Google\DriveFS",
            "transport": "drivefs_reverse_lookup",
            "connector_available": True,
            "drive_folder_id": "1upSxxdECT5MCC1fvPJFOi24kk7K0LoOB",
            "action_signature": "drivefs-profile-enum",
        }
        out = preflight(p, trusted())
        self.assertFalse(out["allowed"])
        self.assertEqual(out["blocked_by"], "SAFE_TOOL")
        self.assertIn("DRIVE_CONNECTOR_ID_ROUTE_REQUIRED", out["reason"])

    def test_preflight_safe_tool_allows_exact_drive_connector_route(self):
        p = plan()
        p["tool_action"] = {
            "operation": "google_drive",
            "purpose": "read canonical inbox",
            "target": "folder_id:1upSxxdECT5MCC1fvPJFOi24kk7K0LoOB",
            "transport": "connector",
            "connector_available": True,
            "drive_folder_id": "1upSxxdECT5MCC1fvPJFOi24kk7K0LoOB",
            "action_signature": "drive-folder-read-v1",
        }
        out = preflight(p, trusted())
        self.assertTrue(out["allowed"])
        self.assertEqual(out["safe_tool_evaluation"]["gate"], "SAFE_TOOL")
        self.assertEqual(out["safe_tool_evaluation"]["state"], "SAFE_TOOL_OK")
        self.assertEqual(
            [item["gate"] for item in out["results"]],
            ["KEY", "CONTEXT", "ROUTE", "COST"],
        )

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
            "CHATGPT",
        )
        self.assertEqual(a["orchestration"]["verifier"], "CODEX")
        self.assertEqual(a["orchestration"]["independent_reviewer"], "CLAUDE")
        self.assertNotEqual(a["receipt_id"], b["receipt_id"])

    def test_blocked_preflight_persists_structured_control_incident(self):
        p = plan()
        p["action_id"] = "missing"
        t = trusted()
        out = preflight(p, t)
        runtime = persist_control_incident(runtime_state(), out, p, t)
        self.assertEqual(len(runtime["control_incidents"]), 1)
        incident = next(iter(runtime["control_incidents"].values()))
        self.assertEqual(incident["gate"], "KEY")
        self.assertEqual(incident["control_role"], "GUARDIAN")
        self.assertEqual(incident["result"], "CONTROL_INTERVENTION")
        self.assertIn("reason", incident["cause"])
        self.assertIn("route_chosen", incident)
        self.assertEqual(incident["occurrence_count"], 1)

        runtime = persist_control_incident(runtime, out, p, t)
        self.assertEqual(len(runtime["control_incidents"]), 1)
        self.assertEqual(
            next(iter(runtime["control_incidents"].values()))["occurrence_count"],
            2,
        )

    def test_done_failure_persists_guardian_control_incident(self):
        runtime = runtime_state()
        runtime["preflight_receipts"]["pf:test"] = {
            "task_id": "task-q002",
            "action_id": "read",
            "authority_digest": "auth1",
            "semantic_owner_ref": "TEST_DOMAIN_OWNER",
            "semantic_owner_scope": "TEST_DOMAIN",
        }
        report = {"preflight_receipt": "pf:test", "evidence_refs": ["ev1"]}
        out = {
            "allowed": False,
            "state": "REWORK",
            "reason": "trusted critical gaps remain",
            "evidence": ["ev1"],
        }
        runtime = persist_done_control_incident(runtime, report, out)
        self.assertEqual(len(runtime["control_incidents"]), 1)
        incident = next(iter(runtime["control_incidents"].values()))
        self.assertEqual(incident["gate"], "DONE")
        self.assertEqual(incident["control_role"], "GUARDIAN")
        self.assertEqual(incident["decision"], "REWORK")
        self.assertEqual(incident["occurrence_count"], 1)

        runtime = persist_done_control_incident(runtime, report, out)
        self.assertEqual(
            next(iter(runtime["control_incidents"].values()))["occurrence_count"],
            2,
        )

    def test_delivered_unconfirmed_is_not_a_control_incident(self):
        runtime = runtime_state()
        runtime["preflight_receipts"]["pf:test"] = {
            "task_id": "task-q002",
            "action_id": "read",
            "authority_digest": "auth1",
            "semantic_owner_ref": "TEST_DOMAIN_OWNER",
            "semantic_owner_scope": "TEST_DOMAIN",
        }
        report = {"preflight_receipt": "pf:test", "evidence_refs": ["ev1"]}
        out = {
            "allowed": False,
            "state": "DELIVERED_UNCONFIRMED",
            "reason": "verified result awaits explicit USER confirmation",
            "evidence": ["ev1"],
        }
        runtime = persist_done_control_incident(runtime, report, out)
        self.assertEqual(runtime["control_incidents"], {})

    def test_unknown_worker_role_blocks_without_crashing_preflight(self):
        t = trusted()
        t["action_registry"]["read"]["worker_roles"] = ["UNKNOWN_ROLE"]
        out = preflight(plan(), t)
        self.assertFalse(out["allowed"])
        self.assertEqual(out["blocked_by"], "KEY")
        self.assertIn("unknown worker role", out["reason"])
        self.assertEqual(out["orchestration"]["worker_roles"], [])
        self.assertIn("UNKNOWN_ROLE", out["orchestration"]["worker_role_error"])

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
        self.assertTrue(fourth["allowed"])
        route = next(item for item in fourth["results"] if item["gate"] == "ROUTE")
        self.assertEqual(route["state"], "ROUTE_SOFT_BUDGET_EXCEEDED")
        self.assertTrue(
            any(ev.startswith("route-budget-soft-exceeded:") for ev in route["evidence"])
        )

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
                "dry_run_plan": {
                    "expected_calls": 1,
                    "operations": ["single bounded external call"],
                    "batch_strategy": "single-batch",
                    "fallback": "HOLD",
                    "paid_api": False,
                },
            },
        }
        out = preflight(review_plan, t)
        self.assertTrue(out["allowed"])
        self.assertTrue(out["call_allowed"])


    def test_external_call_auto_derives_dry_run_when_omitted(self):
        p = plan()
        p["action_id"] = "review"
        p["attempt"]["method_or_tool"] = "claude"
        p["call"]["model"] = "sonnet"
        p["call"]["effort"] = "medium"
        p["call"].pop("dry_run_plan", None)
        out = preflight(p, trusted())
        self.assertTrue(out["allowed"])
        self.assertTrue(out["call_allowed"])
        dry = out["economy_evaluation"]["dry_run"]
        self.assertEqual(dry["state"], "DRY_RUN_OK")
        self.assertIn("dry-run-source:AUTO_DERIVED", dry["evidence"])

    def test_external_call_dry_run_receipt_evidence_is_bound(self):
        p = plan()
        p["action_id"] = "review"
        p["attempt"]["method_or_tool"] = "claude"
        p["call"]["model"] = "sonnet"
        p["call"]["effort"] = "medium"
        out = preflight(p, trusted())
        self.assertTrue(out["allowed"])
        cost = [x for x in out["results"] if x["gate"] == "COST"][0]
        self.assertTrue(any(x.startswith("dry-run:") for x in cost["evidence"]))
        self.assertIn("DRY_RUN_PLAN", out["economy_evaluation"]["decision_sequence"])


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
            "CHATGPT",
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
        self.assertEqual(receipt["semantic_owner_ref"], "TEST_DOMAIN_OWNER")
        self.assertEqual(receipt["semantic_owner_scope"], "TEST_DOMAIN")
        self.assertEqual(receipt["execution_key"], out["execution_key"])
        self.assertEqual(
            receipt["orchestration"]["orchestrator"],
            "CHATGPT",
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

    def test_unknown_execution_outcome_cannot_be_downgraded_to_failure(self):
        t = trusted()
        out = preflight(plan(), t)
        runtime = persist_preflight(runtime_state(), out)
        runtime["active_attempts"][out["execution_key"]]["status"] = "OUTCOME_UNKNOWN"
        with self.assertRaisesRegex(ValueError, "evidence-bound resolution"):
            record_outcome(runtime, out["receipt_id"], "ENVIRONMENT")

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
            "semantic_owner_ref": receipt["semantic_owner_ref"],
            "semantic_owner_scope": receipt["semantic_owner_scope"],
            "verification_tier": receipt["verification_tier"],
            "key_match": True,
            "critical_gaps": [],
            "required_verifications": ["technical", "intent"],
            "passed_verifications": ["technical", "intent"],
            "evidence_refs": ["ev"],
            "verification_evidence": {
                "technical": "ev",
                "intent": "ev",
            },
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
            "semantic_owner_ref": receipt["semantic_owner_ref"],
            "semantic_owner_scope": receipt["semantic_owner_scope"],
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

    def test_done_gate_decision_is_persisted_with_validator_profile(self):
        runtime = runtime_state()
        out = {
            "allowed": False,
            "state": "NOT_DONE",
            "reason": "missing evidence",
            "evidence": [],
            "validator_profile": {
                "trigger": "BEFORE_PASS_DONE_OR_USER_CONFIRMED",
                "primary": "AUTO",
                "semantic": "AI_SEMANTIC",
                "human_authority_condition": "USER_RESERVED_CONFIRMATION_OR_AUTHORITY_DECISION",
                "receipt_custodian": "GUARDIAN",
            },
        }
        report = {"preflight_receipt": "pf:missing", "evidence_refs": []}
        updated = persist_done_gate_receipt(runtime, report, out)
        self.assertEqual(len(updated["done_gate_receipts"]), 1)
        stored = next(iter(updated["done_gate_receipts"].values()))
        self.assertEqual(stored["state"], "NOT_DONE")
        self.assertEqual(stored["validator_profile"]["primary"], "AUTO")
        self.assertEqual(stored["report_digest"], stable_hash(report))

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
