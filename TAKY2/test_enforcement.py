import unittest

from copy import deepcopy

from TAKY2.enforcement import (
    STARTUP_READBACK_SOURCE_REFS,
    action_digest,
    context_gate,
    cost_gate,
    done_gate,
    dry_run_gate,
    key_gate,
    record_failure,
    route_fingerprint,
    route_gate,
    safe_tool_gate,
    stable_hash,
    startup_readback_receipt_id,
)
from TAKY2.orchestration import ECONOMY_CONTRACT


def ledger():
    return {
        "route_budget": 3,
        "seen_routes": [],
        "failed_signatures": [],
        "transient_failures": {},
        "last_failure_by_route": {},
    }


def startup_receipt(authority_digest="auth1"):
    revisions = {
        "START_HERE": "r1",
        "CANONICAL": "r2",
        "SYSTEMWIDE_V2": "r3",
        "CURRENT": "r4",
    }
    sources = [
        {
            "kind": kind,
            "ref": STARTUP_READBACK_SOURCE_REFS[kind],
            "revision": revisions[kind],
        }
        for kind in ("START_HERE", "CANONICAL", "SYSTEMWIDE_V2", "CURRENT")
    ]
    return {
        "receipt_id": startup_readback_receipt_id(authority_digest, sources),
        "authority_digest": authority_digest,
        "verified": True,
        "verified_by": "startup-test-verifier",
        "sources": sources,
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
            "name": "TAKY_ROLE_BASED_COLLABORATIVE_EXECUTION",
            "version": 5,
            "source_ref": "u:role-based-collaboration",
            "parent_system_ref": "TAKY_SYSTEM_IDENTITY@1",
            "execution_model": "ROLE_BASED_COLLABORATIVE_EXECUTION_STRUCTURE",
            "metaphor_model": "SHEPHERDING_COOPERATIVE_EXECUTION_MODEL",
            "canonical_systemwide_ref": "TAKY_SYSTEMWIDE_LOGIC_RECONCILIATION_V2_CANONICAL@2026-10-06",
            "canonical_source_ref": "u:systemwide-canonical",
            "control_roles": ["NAVIGATOR", "GUARDIAN", "DRIVER", "SCOUT"],
            "economy_policy": "SAVEY_AI_ECONOMY",
            "economy_contract": deepcopy(ECONOMY_CONTRACT),
            "purpose": "GUIDE_TO_RESULT",
            "role_registry": {
                "orchestrator": "LEAD_ORCHESTRATOR",
                "implementer": "CODE_WRITER",
                "verifier": "VERIFIER",
                "independent_reviewer": "INDEPENDENT_REVIEWER",
                "final_authority": "FINAL_AUTHORITY",
            },
            "default_actor_bindings": {
                "orchestrator": "CHATGPT",
                "implementer": None,
                "verifier": "CODEX",
                "independent_reviewer": "CLAUDE",
                "final_authority": "USER",
            },
            "role_policy": {
                "implementer_assignment": "TASK_FIT_NECESSITY",
                "role_labels_do_not_authorize_calls": True,
                "implementer_is_role_category_not_fixed_model": True,
                "role_not_agent": True,
                "routing_does_not_transfer_semantic_ownership": True,
                "semantic_owner_remains_domain_owner": True,
            },
            "call_policy": {
                "claude_codex_remote": "NECESSITY_CHECK_WITHIN_COST",
            },
            "implementation_status": {
                "role_actor_binding": "IMPLEMENTED",
                "control_role_schema": "IMPLEMENTED",
                "semantic_owner_binding": "IMPLEMENTED",
                "worker_role_contracts": "IMPLEMENTED",
                "shared_savey_economy_policy": "IMPLEMENTED",
                "owner_map_registry": "IMPLEMENTED",
                "startup_readback_receipt": "IMPLEMENTED",
                "delivery_confirmation_split": "IMPLEMENTED",
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
            "u:shepherding-model": {
                "actor": "USER", "kind": "statement", "status": "REFERENCE_METAPHOR"
            },
            "u:role-based-collaboration": {"actor": "USER", "kind": "statement"},
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
        "semantic_owner_registry": {
            "TEST_DOMAIN_OWNER": {
                "status": "RESOLVED",
                "scopes": ["TEST_DOMAIN"],
                "can_own_semantics": True,
                "owner_type": "TEST",
            },
            "TEST_OWNER_GAP": {
                "status": "OWNER_GAP",
                "scopes": ["TEST_GAP"],
                "can_own_semantics": False,
                "owner_type": "UNRESOLVED",
            },
            "TAKY_MOBILE": {
                "status": "RESOLVED",
                "scopes": ["TAKY_MOBILE"],
                "can_own_semantics": False,
                "owner_type": "PROJECTION",
            },
        },
        "approvals": {},
        "action_registry": {
            "read": {
                "kind": "READ",
                "semantic_owner_ref": "TEST_DOMAIN_OWNER",
                "semantic_owner_scope": "TEST_DOMAIN",
                "worker_roles": ["SCOPE_PLANNER", "TEST_ENGINEER"],
                "execution_scope": "read-scope",
                "call_policy": {"mode": "LOCAL_ONLY"},
            },
            "write": {
                "kind": "EXTERNAL_WRITE",
                "semantic_owner_ref": "TEST_DOMAIN_OWNER",
                "semantic_owner_scope": "TEST_DOMAIN",
                "worker_roles": ["BUILDER", "TEST_ENGINEER"],
                "target_account": "HNS",
                "action_class": "doc_write",
                "execution_scope": "write-scope",
                "call_policy": {"mode": "LOCAL_ONLY"},
            },
            "delete": {
                "kind": "DELETE",
                "semantic_owner_ref": "TEST_DOMAIN_OWNER",
                "semantic_owner_scope": "TEST_DOMAIN",
                "worker_roles": ["BUG_FIXER", "TEST_ENGINEER"],
                "target_account": "HNS",
                "action_class": "doc_write",
                "object": "x",
                "execution_scope": "delete-scope",
                "call_policy": {"mode": "LOCAL_ONLY"},
            },
            "review": {
                "kind": "READ",
                "semantic_owner_ref": "TEST_DOMAIN_OWNER",
                "semantic_owner_scope": "TEST_DOMAIN",
                "worker_roles": ["SCOPE_PLANNER", "TEST_ENGINEER"],
                "execution_scope": "review-scope",
                "call_policy": {
                    "mode": "EXTERNAL_REQUIRED",
                    "requirement_class": "QUALITY_REQUIRED",
                    "billing_class": "SUBSCRIPTION_QUOTA",
                    "allowed_models": ["sonnet"],
                    "model_quality": {"sonnet": 2},
                    "minimum_quality": 2,
                    "max_calls": 1,
                    "max_effort": "medium",
                    "allow_parallel": False,
                    "allow_subagents": False,
                },
            },
            "optional-review": {
                "kind": "READ",
                "semantic_owner_ref": "TEST_DOMAIN_OWNER",
                "semantic_owner_scope": "TEST_DOMAIN",
                "worker_roles": ["SCOPE_PLANNER"],
                "execution_scope": "optional-review-scope",
                "call_policy": {
                    "mode": "EXTERNAL_OPTIONAL",
                    "billing_class": "SUBSCRIPTION_QUOTA",
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
            "startup_readback_receipt": startup_receipt(),
        },
        "route_ledger": ledger(),
        "route_ledgers": {},
        "capabilities": ["shell", "local_python"],
        "preflight_receipts": {},
        "active_attempts": {},
        "execution_outcomes": {},
        "evidence_registry": {},
        "economy_evidence_registry": {},
        "completion_registry": {},
        "consumed_approvals": {},
        "user_events": {},
    }


class SafeToolGateTests(unittest.TestCase):
    def test_drive_connector_id_route_passes(self):
        result = safe_tool_gate({
            "operation": "google_drive",
            "purpose": "read canonical inbox",
            "target": "folder_id:1upSxxdECT5MCC1fvPJFOi24kk7K0LoOB",
            "transport": "connector",
            "connector_available": True,
            "drive_folder_id": "1upSxxdECT5MCC1fvPJFOi24kk7K0LoOB",
            "action_signature": "drive-folder-read-v1",
        })
        self.assertTrue(result.allowed)
        self.assertEqual(result.state, "SAFE_TOOL_OK")

    def test_drivefs_reverse_lookup_is_blocked_when_connector_exists(self):
        result = safe_tool_gate({
            "operation": "google_drive",
            "purpose": "find canonical inbox",
            "target": r"C:\Users\x\AppData\Local\Google\DriveFS",
            "transport": "drivefs_reverse_lookup",
            "connector_available": True,
            "drive_folder_id": "1upSxxdECT5MCC1fvPJFOi24kk7K0LoOB",
            "action_signature": "drivefs-profile-enum",
        })
        self.assertFalse(result.allowed)
        self.assertIn("DRIVE_CONNECTOR_ID_ROUTE_REQUIRED", result.reason)

    def test_broad_environment_dump_is_blocked(self):
        result = safe_tool_gate({
            "operation": "shell",
            "purpose": "find setting",
            "target": "known repo",
            "transport": "shell",
            "command": "Get-ChildItem Env:",
            "action_signature": "env-dump",
        })
        self.assertFalse(result.allowed)
        self.assertIn("BROAD_ENV_ENUMERATION_FORBIDDEN", result.reason)

    def test_blocked_signature_cannot_repeat(self):
        result = safe_tool_gate({
            "operation": "shell",
            "purpose": "retry",
            "target": "known target",
            "transport": "shell",
            "previous_block_signature": "same",
            "action_signature": "same",
        })
        self.assertFalse(result.allowed)
        self.assertIn("BLOCKED_ACTION_SIGNATURE_RETRY_FORBIDDEN", result.reason)


class KeyGateTests(unittest.TestCase):
    def test_role_based_collaborative_contract_is_required(self):
        t = trusted()
        t.pop("orchestration_contract")
        result = key_gate(t, {"action_id": "read"})
        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "BLOCKED")
        self.assertIn("role-based collaborative", result.reason)

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

    def test_savey_must_remain_corrective_router_optimizer(self):
        t = trusted()
        t["orchestration_contract"]["economy_contract"]["operating_mode"] = "BLOCK_FIRST"
        result = key_gate(t, {"action_id": "read"})
        self.assertFalse(result.allowed)
        self.assertIn("corrective-router economy contract mismatch", result.reason)

    def test_role_registry_cannot_be_replaced_by_actor_names(self):
        t = trusted()
        t["orchestration_contract"]["role_registry"]["verifier"] = "CODEX"
        result = key_gate(t, {"action_id": "read"})
        self.assertFalse(result.allowed)
        self.assertIn("role_registry mismatch", result.reason)

    def test_default_implementer_cannot_be_fixed_to_model(self):
        t = trusted()
        t["orchestration_contract"]["default_actor_bindings"]["implementer"] = "CLAUDE_CODE"
        result = key_gate(t, {"action_id": "read"})
        self.assertFalse(result.allowed)
        self.assertIn("default_actor_bindings mismatch", result.reason)

    def test_necessity_is_not_a_sixth_gate_call_policy(self):
        t = trusted()
        t["orchestration_contract"]["call_policy"]["claude_codex_remote"] = "NECESSITY_GATE_ONLY"
        result = key_gate(t, {"action_id": "read"})
        self.assertFalse(result.allowed)
        self.assertIn("inside COST/Driver", result.reason)

    def test_unknown_worker_role_is_blocked(self):
        t = trusted()
        t["action_registry"]["read"]["worker_roles"] = ["UNKNOWN_ROLE"]
        result = key_gate(t, {"action_id": "read"})
        self.assertFalse(result.allowed)
        self.assertIn("unknown worker role", result.reason)

    def test_worker_roles_are_task_fit_not_mandatory_full_pipeline(self):
        t = trusted()
        t["action_registry"]["read"]["worker_roles"] = ["TEST_ENGINEER"]
        result = key_gate(t, {"action_id": "read"})
        self.assertTrue(result.allowed)

    def test_unregistered_semantic_owner_is_owner_gap(self):
        t = trusted()
        t["action_registry"]["read"]["semantic_owner_ref"] = "UNKNOWN_OWNER"
        result = key_gate(t, {"action_id": "read"})
        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "OWNER_GAP")

    def test_explicit_owner_gap_is_not_guessed(self):
        t = trusted()
        t["action_registry"]["read"]["semantic_owner_ref"] = "TEST_OWNER_GAP"
        t["action_registry"]["read"]["semantic_owner_scope"] = "TEST_GAP"
        result = key_gate(t, {"action_id": "read"})
        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "OWNER_GAP")
        self.assertIn("unresolved", result.reason)

    def test_projection_cannot_be_semantic_owner(self):
        t = trusted()
        t["action_registry"]["read"]["semantic_owner_ref"] = "TAKY_MOBILE"
        t["action_registry"]["read"]["semantic_owner_scope"] = "TAKY_MOBILE"
        result = key_gate(t, {"action_id": "read"})
        self.assertFalse(result.allowed)
        self.assertIn("cannot own semantics", result.reason)

    def test_semantic_owner_scope_must_match_registry(self):
        t = trusted()
        t["action_registry"]["read"]["semantic_owner_scope"] = "OTHER_SCOPE"
        result = key_gate(t, {"action_id": "read"})
        self.assertFalse(result.allowed)
        self.assertIn("scope mismatch", result.reason)

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


    def test_startup_readback_receipt_is_required(self):
        t = trusted()
        t["context"]["startup_readback_receipt"] = None
        result = context_gate(t, {"mode": "delta"})
        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "READ_ONLY")

    def test_startup_readback_receipt_authority_must_match(self):
        t = trusted()
        t["context"]["startup_readback_receipt"]["authority_digest"] = "stale"
        result = context_gate(t, {"mode": "delta"})
        self.assertFalse(result.allowed)
        self.assertIn("stale", result.reason)

    def test_startup_readback_source_ref_must_match_authority_document(self):
        t = trusted()
        t["context"]["startup_readback_receipt"]["sources"][0]["ref"] = "drive:wrong"
        result = context_gate(t, {"mode": "delta"})
        self.assertFalse(result.allowed)
        self.assertIn("source ref mismatch", result.reason)

    def test_startup_readback_receipt_id_must_bind_digest_and_revisions(self):
        t = trusted()
        t["context"]["startup_readback_receipt"]["sources"][0]["revision"] = "r9"
        result = context_gate(t, {"mode": "delta"})
        self.assertFalse(result.allowed)
        self.assertIn("receipt_id mismatch", result.reason)

    def test_startup_readback_duplicate_source_kind_is_rejected(self):
        t = trusted()
        t["context"]["startup_readback_receipt"]["sources"][1]["kind"] = "START_HERE"
        result = context_gate(t, {"mode": "delta"})
        self.assertFalse(result.allowed)
        self.assertIn("duplicated", result.reason)


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
        result = route_gate(t, a)
        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "REROUTE_REQUIRED")
        self.assertIn("different route internally", result.reason)

    def test_route_budget_is_soft_optimizer_not_user_authority_wall(self):
        t = trusted()
        t["route_ledger"]["seen_routes"] = [
            route_fingerprint(self.attempt(method))
            for method in ["a", "b", "c"]
        ]
        result = route_gate(t, self.attempt("d"))
        self.assertTrue(result.allowed)
        self.assertEqual(result.state, "ROUTE_SOFT_BUDGET_EXCEEDED")
        self.assertTrue(
            any(ev.startswith("route-budget-soft-exceeded:") for ev in result.evidence)
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
    def add_economy_decision(self, t, action, ref, decision_kind):
        t["economy_evidence_registry"][ref] = {
            "decision_kind": decision_kind,
            "verified": True,
            "acceptance_state": "ACCEPTED",
            "source_status": "CURRENT",
            "authority_digest": t["_authority_digest"],
            "action_digest": action_digest(action),
            "semantic_owner_ref": action["semantic_owner_ref"],
            "semantic_owner_scope": action["semantic_owner_scope"],
            "requirement_class": action["call_policy"].get(
                "requirement_class",
                "QUALITY_REQUIRED",
            ),
            "acceptance_ref": "acceptance:test-quality",
        }

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
        self.assertEqual(r.state, "REROUTE_LOWEST_SUFFICIENT")

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
            "REROUTE_LOWEST_SUFFICIENT",
        )

    def test_allowed_efforts_is_exact_policy_not_only_maximum(self):
        t = trusted()
        action = t["action_registry"]["review"]
        action["call_policy"]["allowed_efforts"] = ["medium"]
        self.assertEqual(action["call_policy"]["allowed_efforts"], ["medium"])
        low = cost_gate(t, action, {
            "model": "sonnet",
            "effort": "low",
            "expected_calls": 1,
            "context": "delta",
        })
        self.assertFalse(low.allowed)
        self.assertEqual(low.state, "REROUTE_LOWEST_SUFFICIENT")
        self.assertIn("not allowed", low.reason)

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
            "REROUTE_LOWEST_SUFFICIENT",
        )

    def test_ui_generation_capability_is_guided_not_blocked(self):
        t = trusted()
        action = t["action_registry"]["optional-review"]
        action["call_policy"]["requirement_class"] = "CAPABILITY_REQUIRED"
        action["call_policy"]["required_capability"] = "UI_IMAGE_GENERATION"
        action["call_policy"]["model_capabilities"] = {
            "sonnet": ["UI_IMAGE_GENERATION"],
        }
        call = {
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
        }
        r = cost_gate(t, action, call)
        self.assertTrue(r.allowed)
        self.assertEqual(r.state, "COST_OK")
        self.assertIn("requirement-class:CAPABILITY_REQUIRED", r.evidence)
        self.assertIn("required-capability:UI_IMAGE_GENERATION", r.evidence)
        self.assertIn("billing-class:SUBSCRIPTION_QUOTA", r.evidence)

    def test_voice_generation_capability_is_guided_not_blocked(self):
        t = trusted()
        action = t["action_registry"]["optional-review"]
        action["call_policy"]["requirement_class"] = "CAPABILITY_REQUIRED"
        action["call_policy"]["required_capability"] = "TTS_AUDIO_GENERATION"
        action["call_policy"]["model_capabilities"] = {
            "sonnet": ["TTS_AUDIO_GENERATION"],
        }
        call = {
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
        }
        r = cost_gate(t, action, call)
        self.assertTrue(r.allowed)
        self.assertEqual(r.state, "COST_OK")
        self.assertIn("required-capability:TTS_AUDIO_GENERATION", r.evidence)

    def test_capability_required_without_resolved_capability_reroutes_internally(self):
        t = trusted()
        action = t["action_registry"]["optional-review"]
        action["call_policy"]["requirement_class"] = "CAPABILITY_REQUIRED"
        call = {
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
        }
        r = cost_gate(t, action, call)
        self.assertFalse(r.allowed)
        self.assertEqual(r.state, "REROUTE_REQUIRED")
        self.assertIn("resolve required_capability", r.reason)

    def test_external_action_requires_explicit_billing_class(self):
        t = trusted()
        action = t["action_registry"]["optional-review"]
        action["call_policy"].pop("billing_class", None)
        action["call_policy"].pop("model_billing", None)
        call = {
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
        }
        r = cost_gate(t, action, call)
        self.assertFalse(r.allowed)
        self.assertEqual(r.state, "BLOCKED")
        self.assertIn("billing_class required", r.reason)

    def test_capability_required_rejects_model_without_capability(self):
        t = trusted()
        action = t["action_registry"]["optional-review"]
        action["call_policy"]["requirement_class"] = "CAPABILITY_REQUIRED"
        action["call_policy"]["required_capability"] = "TTS_AUDIO_GENERATION"
        action["call_policy"]["model_capabilities"] = {
            "sonnet": ["TEXT_REVIEW"],
        }
        r = cost_gate(t, action, {
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
        })
        self.assertFalse(r.allowed)
        self.assertEqual(r.state, "REROUTE_LOWEST_SUFFICIENT")
        self.assertIn("required capability", r.reason)

    def test_paid_api_requires_trusted_approval(self):
        t = trusted()
        action = t["action_registry"]["optional-review"]
        action["call_policy"]["billing_class"] = "PAID_API"
        call = {
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
        }
        r = cost_gate(t, action, call)
        self.assertFalse(r.allowed)
        self.assertEqual(r.state, "USER_DECISION_REQUIRED")
        self.assertIn("paid API", r.reason)
        key = "cost:" + stable_hash(call)
        t["approvals"][key] = "u:approve"
        approved = cost_gate(t, action, call)
        self.assertTrue(approved.allowed)
        self.assertIn("approval-key:" + key, approved.evidence)

    def test_authority_can_still_require_optional_approval(self):
        t = trusted()
        action = t["action_registry"]["optional-review"]
        action["call_policy"]["require_optional_approval"] = True
        call = {
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
        }
        r = cost_gate(t, action, call)
        self.assertFalse(r.allowed)
        self.assertEqual(r.state, "USER_DECISION_REQUIRED")

    def test_unnecessary_external_call_is_skipped_only_with_trusted_decision(self):
        t = trusted()
        action = t["action_registry"]["review"]
        self.add_economy_decision(
            t, action, "econ:necessity", "EXTERNAL_NOT_NECESSARY"
        )
        r = cost_gate(t, action, {
            "necessity_decision_ref": "econ:necessity",
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
        })
        self.assertTrue(r.allowed)
        self.assertEqual(r.state, "SKIP_CALL")
        self.assertIn("economy-decision:econ:necessity", r.evidence)

    def test_reusable_context_is_reused_only_with_trusted_decision(self):
        t = trusted()
        action = t["action_registry"]["review"]
        self.add_economy_decision(t, action, "econ:reuse", "REUSE_SUFFICIENT")
        r = cost_gate(t, action, {
            "reuse_decision_ref": "econ:reuse",
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
        })
        self.assertTrue(r.allowed)
        self.assertEqual(r.state, "SKIP_CALL")

    def test_local_route_is_used_only_with_trusted_sufficiency_decision(self):
        t = trusted()
        action = t["action_registry"]["review"]
        self.add_economy_decision(t, action, "econ:local", "LOCAL_SUFFICIENT")
        r = cost_gate(t, action, {
            "local_decision_ref": "econ:local",
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
        })
        self.assertTrue(r.allowed)
        self.assertEqual(r.state, "SKIP_CALL")

    def test_self_asserted_skip_claims_are_blocked(self):
        t = trusted()
        action = t["action_registry"]["review"]
        cases = [
            {"necessary": False},
            {"reuse_available": True, "reuse_satisfies_acceptance": True},
            {"local_sufficient": True, "local_meets_acceptance": True},
        ]
        for extra in cases:
            with self.subTest(extra=extra):
                call = {
                    "model": "sonnet",
                    "effort": "medium",
                    "expected_calls": 1,
                    "context": "delta",
                } | extra
                r = cost_gate(t, action, call)
                self.assertFalse(r.allowed)
                self.assertEqual(r.state, "BLOCKED")
                self.assertIn("untrusted economy", r.reason)

    def test_stale_or_mismatched_economy_decision_cannot_skip(self):
        t = trusted()
        action = t["action_registry"]["review"]
        self.add_economy_decision(t, action, "econ:reuse", "REUSE_SUFFICIENT")
        t["economy_evidence_registry"]["econ:reuse"]["authority_digest"] = "stale"
        r = cost_gate(t, action, {
            "reuse_decision_ref": "econ:reuse",
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
        })
        self.assertFalse(r.allowed)
        self.assertIn("authority is stale", r.reason)

    def test_lowest_cost_route_cannot_drop_below_acceptance_quality(self):
        t = trusted()
        action = t["action_registry"]["review"]
        action["call_policy"]["allowed_models"] = ["haiku", "sonnet"]
        action["call_policy"]["model_quality"] = {"haiku": 1, "sonnet": 2}
        action["call_policy"]["minimum_quality"] = 2
        r = cost_gate(t, action, {
            "model": "haiku",
            "effort": "low",
            "expected_calls": 1,
            "context": "delta",
        })
        self.assertFalse(r.allowed)
        self.assertEqual(r.state, "REROUTE_QUALITY_FLOOR")

    def test_quality_required_external_call_requires_quality_floor(self):
        t = trusted()
        action = t["action_registry"]["review"]
        action["call_policy"].pop("model_quality", None)
        action["call_policy"].pop("minimum_quality", None)
        r = cost_gate(t, action, {
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
        })
        self.assertFalse(r.allowed)
        self.assertEqual(r.state, "BLOCKED")
        self.assertIn("quality floor", r.reason)

    def test_quality_required_skip_requires_acceptance_ref(self):
        t = trusted()
        action = t["action_registry"]["review"]
        self.add_economy_decision(t, action, "econ:quality-skip", "REUSE_SUFFICIENT")
        t["economy_evidence_registry"]["econ:quality-skip"].pop("acceptance_ref")
        r = cost_gate(t, action, {
            "reuse_decision_ref": "econ:quality-skip",
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
        })
        self.assertFalse(r.allowed)
        self.assertEqual(r.state, "BLOCKED")
        self.assertIn("acceptance_ref", r.reason)

    def test_parallel_requires_trusted_safety_and_independence(self):
        t = trusted()
        action = t["action_registry"]["review"]
        action["call_policy"]["allow_parallel"] = True
        r = cost_gate(t, action, {
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
            "parallel": True,
        })
        self.assertFalse(r.allowed)
        self.assertIn("safety/independence", r.reason)
        action["call_policy"]["parallel_safe"] = True
        action["call_policy"]["independent_items"] = True
        self.assertTrue(cost_gate(t, action, {
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
            "parallel": True,
        }).allowed)

    def test_batch_requires_trusted_safe_policy(self):
        t = trusted()
        action = t["action_registry"]["review"]
        r = cost_gate(t, action, {
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
            "batch_size": 2,
        })
        self.assertFalse(r.allowed)
        action["call_policy"]["allow_batch"] = True
        action["call_policy"]["batch_safe"] = True
        self.assertTrue(cost_gate(t, action, {
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
            "batch_size": 2,
        }).allowed)

    def test_retry_count_is_throttled_from_trusted_route_ledger(self):
        t = trusted()
        action = t["action_registry"]["review"]
        action["call_policy"]["max_retries"] = 1
        attempt = {"target": "Q002", "method_or_tool": "python"}
        fp = route_fingerprint(attempt)
        t["route_ledger"]["transient_failures"][fp] = 2
        r = cost_gate(
            t,
            action,
            {
                "model": "sonnet",
                "effort": "medium",
                "expected_calls": 1,
                "context": "delta",
            },
            route_fp=fp,
        )
        self.assertFalse(r.allowed)
        self.assertEqual(r.state, "THROTTLE_HOLD")

    def test_plan_cannot_self_assert_retry_count(self):
        t = trusted()
        action = t["action_registry"]["review"]
        r = cost_gate(t, action, {
            "model": "sonnet",
            "effort": "medium",
            "expected_calls": 1,
            "context": "delta",
            "retry_count": 0,
        })
        self.assertFalse(r.allowed)
        self.assertEqual(r.state, "BLOCKED")
        self.assertIn("trusted route ledger", r.reason)


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
            "semantic_owner_ref": "TEST_DOMAIN_OWNER",
            "semantic_owner_scope": "TEST_DOMAIN",
            "consumed": False,
        }
        t["execution_outcomes"][rid] = "SUCCESS"
        t["completion_registry"][rid] = {
            "plan_digest": "p1",
            "action_digest": "a1",
            "call_digest": "c1",
            "authority_digest": "auth1",
            "semantic_owner_ref": "TEST_DOMAIN_OWNER",
            "semantic_owner_scope": "TEST_DOMAIN",
            "verification_tier": "STANDARD",
            "key_match": True,
            "critical_gaps": [],
            "required_verifications": ["technical", "intent"],
            "passed_verifications": ["technical", "intent"],
            "evidence_refs": ["ev1"],
            "verification_evidence": {
                "technical": "ev1",
                "intent": "ev1",
            },
            "user_confirmation_ref": None,
        }
        t["evidence_registry"]["ev1"] = {
            "type": "runtime_test",
            "evidence_type": "runtime_test",
            "verified": True,
            "acceptance_state": "ACCEPTED",
            "claim_supported": "execution_verification",
            "producer": "executor-1",
            "validator": "verifier-1",
            "source_or_artifact_ref": "ev1",
            "authority_digest_or_key_version": "auth1",
            "semantic_owner_ref": "TEST_DOMAIN_OWNER",
            "semantic_owner_scope": "TEST_DOMAIN",
            "verification_tier": "STANDARD",
            "source_status": "CURRENT",
            "receipt_id": rid,
            "plan_digest": "p1",
            "action_digest": "a1",
            "call_digest": "c1",
        }
        return t, rid

    def test_installation_only_cannot_prove_user_intent(self):
        t, rid = self.ready()
        t["evidence_registry"]["ev1"]["claim_supported"] = "extension_installed"
        result = done_gate(t, {"preflight_receipt": rid, "evidence_refs": ["ev1"]})
        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "NOT_DONE")
        self.assertIn("installation/build-only", result.reason)

    def test_receipt_without_semantic_owner_is_rejected(self):
        t, rid = self.ready()
        t["preflight_receipts"][rid].pop("semantic_owner_ref")
        result = done_gate(t, {"preflight_receipt": rid, "evidence_refs": ["ev1"]})
        self.assertEqual(result.state, "NOT_DONE")
        self.assertIn("semantic_owner_ref missing", result.reason)

    def test_completion_semantic_owner_must_match_receipt(self):
        t, rid = self.ready()
        t["completion_registry"][rid]["semantic_owner_ref"] = "OTHER_OWNER"
        result = done_gate(t, {"preflight_receipt": rid, "evidence_refs": ["ev1"]})
        self.assertEqual(result.state, "NOT_DONE")
        self.assertIn("completion semantic_owner_ref mismatch", result.reason)

    def test_evidence_semantic_owner_must_match_receipt(self):
        t, rid = self.ready()
        t["evidence_registry"]["ev1"]["semantic_owner_ref"] = "OTHER_OWNER"
        result = done_gate(t, {"preflight_receipt": rid, "evidence_refs": ["ev1"]})
        self.assertEqual(result.state, "NOT_DONE")
        self.assertIn("evidence semantic_owner_ref mismatch", result.reason)

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
            "explicit": True,
            "verified_by": "ui-bridge",
        }
        t["completion_registry"][rid]["user_confirmation_ref"] = "u:confirm"
        self.assertTrue(
            done_gate(t, {"preflight_receipt": rid, "evidence_refs": ["ev1"]}).allowed
        )

    def test_non_explicit_confirmation_event_cannot_confirm(self):
        t, rid = self.ready()
        t["user_events"]["u:implicit"] = {
            "actor": "USER",
            "kind": "confirmation",
            "receipt_id": rid,
            "explicit": False,
            "verified_by": "ui-bridge",
        }
        t["completion_registry"][rid]["user_confirmation_ref"] = "u:implicit"
        result = done_gate(
            t,
            {"preflight_receipt": rid, "evidence_refs": ["ev1"]},
        )
        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "DELIVERED_UNCONFIRMED")

    def test_done_requires_predicate_to_evidence_binding(self):
        t, rid = self.ready()
        t["completion_registry"][rid]["verification_evidence"].pop("intent")
        result = done_gate(
            t,
            {"preflight_receipt": rid, "evidence_refs": ["ev1"]},
        )
        self.assertEqual(result.state, "BLOCKED")
        self.assertIn("predicates lack evidence bindings", result.reason)

    def test_consumed_receipt_cannot_be_reused(self):
        t, rid = self.ready()
        t["preflight_receipts"][rid]["consumed"] = True
        self.assertEqual(
            done_gate(t, {"preflight_receipt": rid, "evidence_refs": ["ev1"]}).state,
            "NOT_DONE",
        )

    def test_stale_evidence_cannot_satisfy_done(self):
        t, rid = self.ready()
        t["evidence_registry"]["ev1"]["acceptance_state"] = "STALE"
        self.assertEqual(
            done_gate(t, {"preflight_receipt": rid, "evidence_refs": ["ev1"]}).state,
            "NOT_DONE",
        )

    def test_superseded_evidence_cannot_prove_current_claim(self):
        t, rid = self.ready()
        t["evidence_registry"]["ev1"]["source_status"] = "SUPERSEDED"
        result = done_gate(t, {"preflight_receipt": rid, "evidence_refs": ["ev1"]})
        self.assertEqual(result.state, "NOT_DONE")
        self.assertIn("superseded", result.reason)

    def test_evidence_authority_must_match_receipt(self):
        t, rid = self.ready()
        t["evidence_registry"]["ev1"]["authority_digest_or_key_version"] = "old-auth"
        result = done_gate(t, {"preflight_receipt": rid, "evidence_refs": ["ev1"]})
        self.assertEqual(result.state, "NOT_DONE")
        self.assertIn("authority mismatch", result.reason)

    def test_strong_evidence_rejects_self_validation(self):
        t, rid = self.ready()
        t["preflight_receipts"][rid]["verification_tier"] = "STRONG"
        t["preflight_receipts"][rid]["orchestration"] = {
            "independent_reviewer_role": "INDEPENDENT_REVIEWER",
            "independent_reviewer_actor": "CLAUDE",
        }
        t["completion_registry"][rid]["verification_tier"] = "STRONG"
        t["completion_registry"][rid]["required_verifications"] = [
            "structural", "technical", "intent", "independent"
        ]
        t["completion_registry"][rid]["passed_verifications"] = [
            "structural", "technical", "intent", "independent"
        ]
        t["completion_registry"][rid]["verification_evidence"] = {
            "structural": "ev1",
            "technical": "ev1",
            "intent": "ev1",
            "independent": "ev1",
        }
        t["evidence_registry"]["ev1"]["verification_tier"] = "STRONG"
        t["evidence_registry"]["ev1"]["producer"] = "same-actor"
        t["evidence_registry"]["ev1"]["validator"] = "same-actor"
        t["evidence_registry"]["ev1"]["independent_reviewer_role"] = "INDEPENDENT_REVIEWER"
        t["evidence_registry"]["ev1"]["independent_reviewer_actor"] = "CLAUDE"
        t["evidence_registry"]["ev1"]["independent_reviewer"] = "CLAUDE"
        result = done_gate(t, {"preflight_receipt": rid, "evidence_refs": ["ev1"]})
        self.assertEqual(result.state, "PARTIAL")
        self.assertIn("independent validator", result.reason)


    def test_dry_run_gate_auto_derives_safe_defaults(self):
        t = trusted()
        action = {
            "kind": "READ",
            "semantic_owner_ref": "TEST_DOMAIN_OWNER",
            "semantic_owner_scope": "TEST_DOMAIN",
            "execution_scope": "review-scope",
            "call_policy": {
                "mode": "EXTERNAL_REQUIRED",
                "max_calls": 1,
                "billing_class": "SUBSCRIPTION_QUOTA",
            },
        }
        result = dry_run_gate(t, action, {"expected_calls": 1})
        self.assertTrue(result.allowed)
        self.assertEqual(result.state, "DRY_RUN_OK")
        self.assertIn("dry-run-source:AUTO_DERIVED", result.evidence)
        self.assertTrue(any(ev.startswith("dry-run-derived:") for ev in result.evidence))

    def test_dry_run_gate_accepts_bounded_batch(self):
        t = trusted()
        action = {
            "kind": "READ",
            "semantic_owner_ref": "TEST_DOMAIN_OWNER",
            "semantic_owner_scope": "TEST_DOMAIN",
            "call_policy": {
                "mode": "EXTERNAL_REQUIRED",
                "billing_class": "SUBSCRIPTION_QUOTA",
            },
        }
        result = dry_run_gate(t, action, {
            "expected_calls": 1,
            "dry_run_plan": {
                "expected_calls": 1,
                "operations": ["read related files", "apply one patch", "run relevant regression"],
                "batch_strategy": "one bounded batch",
                "fallback": "HOLD",
                "paid_api": False,
            },
        })
        self.assertTrue(result.allowed)
        self.assertEqual(result.state, "DRY_RUN_OK")
        self.assertTrue(result.evidence[0].startswith("dry-run:"))

    def test_packet_only_external_review_requires_bound_packet_digest(self):
        t = trusted()
        action = {
            "kind": "READ",
            "semantic_owner_ref": "TEST_DOMAIN_OWNER",
            "semantic_owner_scope": "TEST_DOMAIN",
            "call_policy": {
                "mode": "EXTERNAL_REQUIRED",
                "billing_class": "SUBSCRIPTION_QUOTA",
                "execution_mode": "PACKET_ONLY",
            },
        }
        packet = "compact review packet"
        call = {
            "expected_calls": 1,
            "execution_mode": "PACKET_ONLY",
            "packet_digest": stable_hash(packet),
            "dry_run_plan": {
                "expected_calls": 1,
                "operations": ["judge supplied review packet only"],
                "batch_strategy": "single-packet",
                "fallback": "HOLD",
                "paid_api": False,
            },
        }
        result = dry_run_gate(t, action, call)
        self.assertTrue(result.allowed)
        missing = dict(call)
        missing.pop("packet_digest")
        blocked = dry_run_gate(t, action, missing)
        self.assertFalse(blocked.allowed)
        self.assertEqual(blocked.state, "DRY_RUN_INVALID")

    def test_codex_verify_only_requires_bound_packet(self):
        t = trusted()
        action = {
            "kind": "READ",
            "semantic_owner_ref": "TEST_DOMAIN_OWNER",
            "semantic_owner_scope": "TEST_DOMAIN",
            "call_policy": {
                "mode": "EXTERNAL_REQUIRED",
                "billing_class": "SUBSCRIPTION_QUOTA",
                "execution_mode": "CODEX_VERIFY_ONLY",
            },
        }
        packet = "compact codex verifier packet"
        call = {
            "model": "codex",
            "expected_calls": 1,
            "execution_mode": "CODEX_VERIFY_ONLY",
            "packet_digest": stable_hash(packet),
        }
        result = dry_run_gate(t, action, call)
        self.assertTrue(result.allowed)
        self.assertEqual(result.state, "DRY_RUN_OK")

        wrong = dict(call)
        wrong["execution_mode"] = "BOUNDED"
        blocked = dry_run_gate(t, action, wrong)
        self.assertFalse(blocked.allowed)
        self.assertEqual(blocked.state, "DRY_RUN_MISMATCH")


if __name__ == "__main__":
    unittest.main()
