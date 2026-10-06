import unittest

from TAKY2.enforcement import (
    action_digest,
    context_gate,
    cost_gate,
    done_gate,
    key_gate,
    record_failure,
    route_fingerprint,
    route_gate,
    stable_hash,
)


def ledger():
    return {
        "route_budget": 3,
        "seen_routes": [],
        "failed_signatures": [],
        "transient_failures": {},
        "last_failure_by_route": {},
    }


def trusted():
    return {
        "_authority_digest": "auth1",
        "system_identity": {
            "name": "TAKY",
            "identity_name": "TAKY_SYSTEM_IDENTITY",
            "version": 1,
            "source_ref": "u:taky-identity",
            "canonical_systemwide_ref": "TAKY_SYSTEMWIDE_LOGIC_RECONCILIATION_V2_CANONICAL@2026-10-06",
            "slogans": [
                "Think Again, Keep Your Key.",
                "Think Again, You're The Key.",
            ],
            "key_owner": "USER",
            "final_authority": "USER",
            "user_not_debugger": True,
            "execution_duty": "AI_COLLABORATION_GROUP",
        },
        "orchestration_contract": {
            "name": "TAKY_SHEPHERDING_COOPERATIVE_EXECUTION",
            "version": 3,
            "source_ref": "u:shepherding-model",
            "parent_system_ref": "TAKY_SYSTEM_IDENTITY@1",
            "execution_model": "SHEPHERDING_COOPERATIVE_EXECUTION_MODEL",
            "canonical_systemwide_ref": "TAKY_SYSTEMWIDE_LOGIC_RECONCILIATION_V2_CANONICAL@2026-10-06",
            "canonical_source_ref": "u:systemwide-canonical",
            "control_roles": ["NAVIGATOR", "GUARDIAN", "DRIVER", "SCOUT"],
            "economy_policy": "SAVEY_AI_ECONOMY",
            "purpose": "GUIDE_TO_RESULT",
            "roles": {
                "orchestrator": "CHATGPT_LEAD_ORCHESTRATOR",
                "implementer": "CODE_WRITER",
                "verifier": "CODEX",
                "independent_reviewer": "CLAUDE",
                "final_authority": "USER"
            },
            "role_policy": {
                "implementer_assignment": "TASK_FIT_NECESSITY",
                "role_labels_do_not_authorize_calls": True,
                "implementer_is_role_category_not_fixed_model": True,
                "role_not_agent": True,
                "routing_does_not_transfer_semantic_ownership": True,
                "semantic_owner_remains_domain_owner": True,
            },
            "implementation_status": {
                "control_role_schema": "OPEN",
                "semantic_owner_binding": "OPEN",
                "worker_role_contracts": "OPEN",
                "shared_savey_economy_policy": "OPEN",
            },
            "guidance_loop": [
                "OBSERVE", "CLASSIFY", "ASSIGN", "EXECUTE",
                "CROSS_CHECK", "REDIRECT", "VERIFY", "DELIVER"
            ],
            "gate_policy": {
                "default": "REDIRECT_BEFORE_ESCALATE",
                "user_not_debugger": True,
                "block_is_not_goal": True
            }
        },
        "key": {
            "USER_INTENT": {
                "value": "deliver result",
                "provenance": "USER_STATED",
                "source_ref": "u:intent",
                "scope": "task",
                "version": 1,
            },
            "AUTHORIZED_TARGET": {
                "value": "HNS",
                "provenance": "USER_STATED",
                "source_ref": "u:target",
                "scope": "branch",
                "version": 1,
            },
            "AUTHORIZED_ACTION_CLASSES": {
                "value": ["doc_write"],
                "provenance": "USER_STATED",
                "source_ref": "u:class",
                "scope": "branch",
                "version": 1,
            },
        },
        "source_registry": {
            "u:intent": {"actor": "USER", "kind": "statement"},
            "u:target": {"actor": "USER", "kind": "statement"},
            "u:class": {"actor": "USER", "kind": "authorization"},
            "u:approve": {"actor": "USER", "kind": "approval"},
            "u:approve2": {"actor": "USER", "kind": "approval"},
            "u:taky-identity": {"actor": "USER", "kind": "statement"},
            "u:shepherding-model": {"actor": "USER", "kind": "statement"},
            "u:systemwide-canonical": {
                "actor": "USER",
                "kind": "statement",
                "status": "CANONICAL",
            },
            "u:legacy-border-collie": {
                "actor": "USER",
                "kind": "statement",
                "status": "SUPERSEDED",
                "superseded_by": "u:shepherding-model",
            },
        },
        "approvals": {},
        "action_registry": {
            "read": {
                "kind": "READ",
                "execution_scope": "read-scope",
                "call_policy": {"mode": "LOCAL_ONLY"},
            },
            "write": {
                "kind": "EXTERNAL_WRITE",
                "target_account": "HNS",
                "action_class": "doc_write",
                "execution_scope": "write-scope",
                "call_policy": {"mode": "LOCAL_ONLY"},
            },
            "delete": {
                "kind": "DELETE",
                "target_account": "HNS",
                "action_class": "doc_write",
                "object": "x",
                "execution_scope": "delete-scope",
                "call_policy": {"mode": "LOCAL_ONLY"},
            },
            "review": {
                "kind": "READ",
                "execution_scope": "review-scope",
                "call_policy": {
                    "mode": "EXTERNAL_REQUIRED",
                    "allowed_models": ["sonnet"],
                    "max_calls": 1,
                    "max_effort": "medium",
                    "allow_parallel": False,
                    "allow_subagents": False,
                },
            },
            "optional-review": {
                "kind": "READ",
                "execution_scope": "optional-review-scope",
                "call_policy": {
                    "mode": "EXTERNAL_OPTIONAL",
                    "allowed_models": ["sonnet"],
                    "max_calls": 1,
                    "max_effort": "medium",
                },
            },
        },
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
        "route_ledger": ledger(),
        "route_ledgers": {},
        "capabilities": ["shell", "local_python"],
        "preflight_receipts": {},
        "active_attempts": {},
        "execution_outcomes": {},
        "evidence_registry": {},
        "completion_registry": {},
        "consumed_approvals": {},
        "user_events": {},
    }


class KeyGateTests(unittest.TestCase):
    def test_shepherding_cooperative_contract_is_required(self):
        t = trusted()
        t.pop("orchestration_contract")
        result = key_gate(t, {"action_id": "read"})
        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "BLOCKED")
        self.assertIn("shepherding cooperative", result.reason)

    def test_taky_system_identity_is_top_level_required(self):
        t = trusted()
        t.pop("system_identity")
        result = key_gate(t, {"action_id": "read"})
        self.assertFalse(result.allowed)
        self.assertIn("top-level system identity", result.reason)

    def test_parent_slogans_belong_to_taky_not_subordinate_contract(self):
        t = trusted()
        t["orchestration_contract"]["slogan_parent"] = [
            "Think Again, Keep Your Key.",
            "Think Again, You're The Key.",
        ]
        result = key_gate(t, {"action_id": "read"})
        self.assertFalse(result.allowed)
        self.assertIn("belong to TAKY system identity", result.reason)

    def test_execution_model_must_reference_taky_system_identity(self):
        t = trusted()
        t["orchestration_contract"]["parent_system_ref"] = "OTHER_SYSTEM@1"
        result = key_gate(t, {"action_id": "read"})
        self.assertFalse(result.allowed)
        self.assertIn("subordinate to TAKY", result.reason)

    def test_systemwide_canonical_promotion_is_required(self):
        t = trusted()
        t["orchestration_contract"]["canonical_source_ref"] = "u:legacy-border-collie"
        result = key_gate(t, {"action_id": "read"})
        self.assertFalse(result.allowed)
        self.assertIn("canonical reconciliation", result.reason)

    def test_canonical_control_roles_are_not_agent_bindings(self):
        t = trusted()
        t["orchestration_contract"]["control_roles"] = [
            "CHATGPT",
            "CODEX",
            "CLAUDE",
            "SCOUT",
        ]
        result = key_gate(t, {"action_id": "read"})
        self.assertFalse(result.allowed)
        self.assertIn("control roles mismatch", result.reason)

    def test_semantic_owner_must_remain_with_domain_owner(self):
        t = trusted()
        t["orchestration_contract"]["role_policy"][
            "semantic_owner_remains_domain_owner"
        ] = False
        result = key_gate(t, {"action_id": "read"})
        self.assertFalse(result.allowed)
        self.assertIn("semantic owner boundary", result.reason)

    def test_superseded_border_collie_source_cannot_be_live_contract_authority(self):
        t = trusted()
        t["orchestration_contract"]["source_ref"] = "u:legacy-border-collie"
        result = key_gate(t, {"action_id": "read"})
        self.assertFalse(result.allowed)
        self.assertIn("trusted USER provenance", result.reason)

    def test_plan_cannot_self_describe_unregistered_action(self):
        self.assertEqual(
            key_gate(trusted(), {"action_id": "missing"}).state,
            "BLOCKED",
        )

    def test_fake_user_source_is_blocked(self):
        t = trusted()
        t["key"]["USER_INTENT"]["source_ref"] = "fake"
        self.assertFalse(key_gate(t, {"action_id": "read"}).allowed)

    def test_actual_account_is_trusted_runtime(self):
        t = trusted()
        t["runtime"]["account_attestation"]["account"] = "OTHER"
        self.assertEqual(
            key_gate(t, {"action_id": "write"}).state,
            "BLOCKED",
        )

    def test_external_write_requires_first_auth_runtime_binding_mode(self):
        t = trusted()
        t["runtime"]["account_attestation"]["binding_mode"] = "LEGACY"
        result = key_gate(t, {"action_id": "write"})
        self.assertEqual(result.state, "BLOCKED")
        self.assertIn("first-auth", result.reason)

    def test_external_write_requires_each_stable_binding_field(self):
        for field in (
            "identity_provider",
            "principal_id",
            "family_id",
            "self_member_id",
            "first_bound_evidence_ref",
            "first_bound_session_id",
        ):
            with self.subTest(field=field):
                t = trusted()
                t["runtime"]["account_attestation"].pop(field)
                result = key_gate(t, {"action_id": "write"})
                self.assertEqual(result.state, "BLOCKED")
                self.assertIn("runtime identity binding", result.reason)

    def test_external_write_rejects_self_verified_binding(self):
        for verifier_id in (
            "HNS",
            "hns",
            "google:sub-hns",
            "GOOGLE:SUB-HNS",
            "member-hns",
            "MEMBER-HNS",
        ):
            with self.subTest(verifier_id=verifier_id):
                t = trusted()
                t["runtime"]["account_attestation"]["verified_by"] = verifier_id
                result = key_gate(t, {"action_id": "write"})
                self.assertEqual(result.state, "BLOCKED")
                self.assertIn("self-verify", result.reason)

    def test_external_write_requires_trusted_auth_source_and_provider(self):
        for field, value, expected in (
            ("source", "other-session", "source is not trusted"),
            ("identity_provider", "OTHER_PROVIDER", "identity provider is not trusted"),
        ):
            with self.subTest(field=field):
                t = trusted()
                t["runtime"]["account_attestation"][field] = value
                result = key_gate(t, {"action_id": "write"})
                self.assertEqual(result.state, "BLOCKED")
                self.assertIn(expected, result.reason)

    def test_external_write_requires_canonical_session_evidence(self):
        for field in ("evidence_ref", "session_id", "verified_by"):
            with self.subTest(field=field):
                t = trusted()
                t["runtime"]["account_attestation"][field] = (
                    " " + t["runtime"]["account_attestation"][field] + " "
                )
                result = key_gate(t, {"action_id": "write"})
                self.assertEqual(result.state, "BLOCKED")
                self.assertIn("not canonical", result.reason)

    def test_authorized_write_does_not_burn_irrelevant_approval(self):
        t = trusted()
        action = t["action_registry"]["write"]
        key = "action:" + action_digest(action)
        t["approvals"][key] = "u:approve"
        r = key_gate(t, {"action_id": "write"})
        self.assertTrue(r.allowed)
        self.assertNotIn("approval-key:" + key, r.evidence)

    def test_irreversible_action_needs_bound_approval(self):
        t = trusted()
        action = t["action_registry"]["delete"]
        key = "action:" + action_digest(action)
        self.assertEqual(
            key_gate(t, {"action_id": "delete"}).state,
            "USER_DECISION_REQUIRED",
        )
        t["approvals"][key] = "u:approve"
        self.assertTrue(key_gate(t, {"action_id": "delete"}).allowed)

    def test_reapproval_with_new_ref_is_valid(self):
        t = trusted()
        action = t["action_registry"]["delete"]
        key = "action:" + action_digest(action)
        t["approvals"][key] = "u:approve"
        t["consumed_approvals"][key] = "u:approve"
        self.assertFalse(key_gate(t, {"action_id": "delete"}).allowed)
        t["approvals"][key] = "u:approve2"
        self.assertTrue(key_gate(t, {"action_id": "delete"}).allowed)

    def test_forbidden_malformed_fails_closed(self):
        t = trusted()
        t["key"]["FORBIDDEN"] = {
            "value": "DELETE",
            "provenance": "USER_STATED",
            "source_ref": "u:intent",
        }
        self.assertEqual(
            key_gate(t, {"action_id": "read"}).state,
            "BLOCKED",
        )


class ContextGateTests(unittest.TestCase):
    def test_delta_passes_after_premise(self):
        self.assertTrue(context_gate(trusted(), {"mode": "delta"}).allowed)

    def test_repeated_full_read_is_blocked(self):
        self.assertEqual(
            context_gate(trusted(), {"mode": "full"}).state,
            "SKIP_FULL_REREAD",
        )

    def test_missing_authority_digest_is_read_only(self):
        t = trusted()
        t["_authority_digest"] = None
        self.assertEqual(
            context_gate(t, {"mode": "delta"}).state,
            "READ_ONLY",
        )


class RouteGateTests(unittest.TestCase):
    def attempt(self, method="python"):
        return {"target": "Q002", "method_or_tool": method}

    def test_route_fingerprint_is_normalized(self):
        a = {"target": " Q002 ", "method_or_tool": "Python "}
        b = {"target": "q002", "method_or_tool": "python"}
        self.assertEqual(route_fingerprint(a), route_fingerprint(b))

    def test_same_failure_route_is_blocked(self):
        t = trusted()
        a = self.attempt()
        t["route_ledger"] = record_failure(t["route_ledger"], a, "VALIDATION")
        self.assertEqual(route_gate(t, a).state, "BLOCKED")

    def test_transient_is_bounded_across_classes(self):
        t = trusted()
        a = self.attempt()
        t["route_ledger"] = record_failure(t["route_ledger"], a, "TIMEOUT")
        self.assertTrue(route_gate(t, a).allowed)
        t["route_ledger"] = record_failure(t["route_ledger"], a, "RATE_LIMIT")
        self.assertEqual(route_gate(t, a).state, "USER_DECISION_REQUIRED")

    def test_budget_counts_distinct_seen_routes(self):
        t = trusted()
        t["route_ledger"]["seen_routes"] = [
            route_fingerprint(self.attempt(method))
            for method in ["a", "b", "c"]
        ]
        self.assertEqual(
            route_gate(t, self.attempt("d")).state,
            "USER_DECISION_REQUIRED",
        )

    def test_user_not_debugger(self):
        t = trusted()
        a = self.attempt() | {
            "ask_user": True,
            "needed_capability": "shell",
        }
        self.assertEqual(
            route_gate(t, a).state,
            "USER_DEBUGGER_VIOLATION",
        )


class CostGateTests(unittest.TestCase):
    def test_local_only_is_trusted_policy_not_plan_claim(self):
        t = trusted()
        action = t["action_registry"]["read"]
        r = cost_gate(t, action, {
            "model": "opus",
            "effort": "max",
            "expected_calls": 99,
            "necessary": True,
        })
        self.assertEqual(r.state, "SKIP_CALL")

    def test_untrusted_model_is_blocked(self):
        t = trusted()
        action = t["action_registry"]["review"]
        r = cost_gate(t, action, {
            "model": "claude-opus-5-5",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
        })
        self.assertEqual(r.state, "REROUTE_CHEAPER")

    def test_plan_cannot_raise_effort_without_approval(self):
        t = trusted()
        action = t["action_registry"]["review"]
        call = {
            "model": "sonnet",
            "effort": "high",
            "expected_calls": 1,
            "context": "delta",
        }
        self.assertEqual(
            cost_gate(t, action, call).state,
            "REROUTE_CHEAPER",
        )

    def test_multiple_calls_need_trusted_approval(self):
        t = trusted()
        action = t["action_registry"]["review"]
        call = {
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 2,
            "context": "delta",
        }
        self.assertEqual(
            cost_gate(t, action, call).state,
            "REROUTE_CHEAPER",
        )

    def test_optional_external_call_requires_trusted_approval(self):
        t = trusted()
        action = t["action_registry"]["optional-review"]
        call = {
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
        }
        self.assertEqual(
            cost_gate(t, action, call).state,
            "REROUTE_CHEAPER",
        )
        key = "cost:" + stable_hash(call)
        t["approvals"][key] = "u:approve"
        r = cost_gate(t, action, call)
        self.assertTrue(r.allowed)
        self.assertIn("approval-key:" + key, r.evidence)


class DoneGateTests(unittest.TestCase):
    def ready(self):
        t = trusted()
        rid = "pf:t1:abc"
        t["preflight_receipts"][rid] = {
            "allowed": True,
            "task_id": "t1",
            "plan_digest": "p1",
            "call_digest": "c1",
            "action_digest": "a1",
            "authority_digest": "auth1",
            "consumed": False,
        }
        t["execution_outcomes"][rid] = "SUCCESS"
        t["completion_registry"][rid] = {
            "plan_digest": "p1",
            "action_digest": "a1",
            "call_digest": "c1",
            "key_match": True,
            "critical_gaps": [],
            "required_verifications": ["technical", "intent"],
            "passed_verifications": ["technical", "intent"],
            "user_confirmation_ref": None,
        }
        t["evidence_registry"]["ev1"] = {
            "type": "runtime_test",
            "verified": True,
            "receipt_id": rid,
            "plan_digest": "p1",
            "action_digest": "a1",
            "call_digest": "c1",
        }
        return t, rid

    def test_evidence_from_other_receipt_is_rejected(self):
        t, rid = self.ready()
        t["evidence_registry"]["ev1"]["receipt_id"] = "other"
        self.assertEqual(
            done_gate(t, {"preflight_receipt": rid, "evidence_refs": ["ev1"]}).state,
            "NOT_DONE",
        )

    def test_verified_result_stays_unconfirmed(self):
        t, rid = self.ready()
        self.assertEqual(
            done_gate(t, {"preflight_receipt": rid, "evidence_refs": ["ev1"]}).state,
            "DELIVERED_UNCONFIRMED",
        )

    def test_confirmation_must_be_bound_to_same_receipt(self):
        t, rid = self.ready()
        t["user_events"]["u:confirm"] = {
            "actor": "USER",
            "kind": "confirmation",
            "receipt_id": rid,
            "verified_by": "ui-bridge",
        }
        t["completion_registry"][rid]["user_confirmation_ref"] = "u:confirm"
        self.assertTrue(
            done_gate(t, {"preflight_receipt": rid, "evidence_refs": ["ev1"]}).allowed
        )

    def test_consumed_receipt_cannot_be_reused(self):
        t, rid = self.ready()
        t["preflight_receipts"][rid]["consumed"] = True
        self.assertEqual(
            done_gate(t, {"preflight_receipt": rid, "evidence_refs": ["ev1"]}).state,
            "NOT_DONE",
        )


if __name__ == "__main__":
    unittest.main()
