import json
from pathlib import Path
import tempfile
import unittest

from TAKY2.bridges import (
    BridgeViolation,
    bind_account_attestation,
    claim_execution_receipt,
    _minimal_packet_env,
    execute_with_receipt,
    reconcile_execution_claim,
    record_independent_review,
    record_startup_readback,
    record_user_confirmation,
    record_user_stop,
    verify_execution,
)
from TAKY2.orchestrator import finalize, persist_preflight, preflight
from TAKY2.state_store import (
    StateIntegrityError,
    authority_digest,
    initialize_runtime,
    load_bundle,
    rebind_authority,
    save_runtime,
    stage_authority_rebind,
)
from TAKY2.enforcement import stable_hash
from TAKY2.test_enforcement import startup_receipt, trusted
from TAKY2.test_orchestrator import runtime_state


KEY = b"r" * 32


def overlay_runtime(base, runtime):
    out = dict(base)
    for key in (
        "runtime",
        "context",
        "route_ledgers",
        "preflight_receipts",
        "active_attempts",
        "execution_outcomes",
        "execution_calls",
        "evidence_registry",
        "completion_registry",
        "independent_review_registry",
        "done_gate_receipts",
        "control_incidents",
        "consumed_approvals",
        "user_events",
    ):
        out[key] = runtime.get(key, {})
    out["_authority_digest"] = runtime.get("authority_digest")
    return out


def write_plan():
    return {
        "task_id": "integration-write",
        "action_id": "write",
        "context": {"mode": "delta"},
        "attempt": {
            "target": "Q002",
            "method_or_tool": "python",
        },
        "call": {
            "model": "local",
            "effort": "low",
            "context": "delta",
            "expected_calls": 1,
        },
    }


class AccountAttestationBridgeTests(unittest.TestCase):
    def evidence(self, account="HNS"):
        return {
            "account": account,
            "authenticated": True,
            "source": "central-family-session",
            "evidence_ref": "auth:e1",
            "session_id": "session-1",
            "identity_provider": "GOOGLE_OIDC_VERIFIED",
            "principal_id": "google:sub-hns",
            "family_id": "family-hns",
            "self_member_id": "member-hns",
        }

    def test_attestation_requires_real_verifier_callback(self):
        with self.assertRaises(BridgeViolation):
            bind_account_attestation(
                runtime_state(),
                trusted(),
                self.evidence(),
                verifier=lambda evidence: False,
                verifier_id="auth-bridge",
            )

    def test_attestation_must_match_authorized_account(self):
        with self.assertRaises(BridgeViolation):
            bind_account_attestation(
                runtime_state(),
                trusted(),
                self.evidence("OTHER"),
                verifier=lambda evidence: True,
                verifier_id="auth-bridge",
            )

    def test_attestation_binds_verified_account(self):
        initial = runtime_state()
        initial["runtime"]["account_attestation"] = None
        runtime = bind_account_attestation(
            initial,
            trusted(),
            self.evidence(),
            verifier=lambda evidence: evidence["authenticated"] is True,
            verifier_id="auth-bridge",
        )
        attestation = runtime["runtime"]["account_attestation"]
        self.assertTrue(attestation["verified"])
        self.assertEqual(attestation["account"], "HNS")
        self.assertEqual(attestation["binding_mode"], "FIRST_AUTH_RUNTIME")
        self.assertEqual(attestation["principal_id"], "google:sub-hns")
        self.assertEqual(attestation["family_id"], "family-hns")
        self.assertEqual(attestation["self_member_id"], "member-hns")
        self.assertEqual(attestation["first_bound_session_id"], "session-1")
        self.assertEqual(attestation["verified_by"], "auth-bridge")

    def test_attestation_requires_stable_runtime_identity_fields(self):
        evidence = self.evidence()
        evidence.pop("family_id")
        with self.assertRaises(BridgeViolation):
            bind_account_attestation(
                runtime_state(),
                trusted(),
                evidence,
                verifier=lambda evidence: True,
                verifier_id="auth-bridge",
            )

    def test_first_binding_requires_trusted_source_and_identity_provider(self):
        for field, value, pattern in (
            ("source", "other-session", "trusted central family session"),
            ("identity_provider", "OTHER_PROVIDER", "identity provider is not trusted"),
        ):
            with self.subTest(field=field):
                initial = runtime_state()
                initial["runtime"]["account_attestation"] = None
                evidence = self.evidence()
                evidence[field] = value
                with self.assertRaisesRegex(BridgeViolation, pattern):
                    bind_account_attestation(
                        initial,
                        trusted(),
                        evidence,
                        verifier=lambda evidence: True,
                        verifier_id="auth-bridge",
                    )

    def test_same_identity_can_refresh_session_without_rebinding(self):
        first = runtime_state()
        first["runtime"]["account_attestation"] = None
        first = bind_account_attestation(
            first,
            trusted(),
            self.evidence(),
            verifier=lambda evidence: True,
            verifier_id="auth-bridge",
        )
        refreshed = self.evidence()
        refreshed["evidence_ref"] = "auth:e2"
        refreshed["session_id"] = "session-2"
        second = bind_account_attestation(
            first,
            trusted(),
            refreshed,
            verifier=lambda evidence: True,
            verifier_id="auth-bridge",
        )
        attestation = second["runtime"]["account_attestation"]
        self.assertEqual(attestation["session_id"], "session-2")
        self.assertEqual(attestation["evidence_ref"], "auth:e2")
        self.assertEqual(attestation["first_bound_session_id"], "session-1")
        self.assertEqual(attestation["first_bound_evidence_ref"], "auth:e1")

    def test_bound_identity_cannot_silently_change(self):
        first = runtime_state()
        first["runtime"]["account_attestation"] = None
        first = bind_account_attestation(
            first,
            trusted(),
            self.evidence(),
            verifier=lambda evidence: True,
            verifier_id="auth-bridge",
        )
        mutations = {
            "identity_provider": "OTHER_PROVIDER",
            "principal_id": "google:other",
            "family_id": "family-other",
            "self_member_id": "member-other",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                changed = self.evidence()
                changed[field] = value
                with self.assertRaises(BridgeViolation):
                    bind_account_attestation(
                        first,
                        trusted(),
                        changed,
                        verifier=lambda evidence: True,
                        verifier_id="auth-bridge",
                    )

    def test_legacy_verified_attestation_requires_explicit_migration(self):
        runtime = runtime_state()
        runtime["runtime"]["account_attestation"] = {
            "account": "HNS",
            "verified": True,
            "source": "legacy-oauth-session",
            "evidence_ref": "legacy:e1",
            "session_id": "legacy-session",
            "verified_by": "legacy-auth-bridge",
        }
        with self.assertRaisesRegex(BridgeViolation, "explicit migration"):
            bind_account_attestation(
                runtime,
                trusted(),
                self.evidence(),
                verifier=lambda evidence: True,
                verifier_id="auth-bridge",
            )

    def test_incomplete_existing_binding_cannot_be_repaired_silently(self):
        runtime = runtime_state()
        runtime["runtime"]["account_attestation"].pop("family_id")
        with self.assertRaisesRegex(BridgeViolation, "identity binding is incomplete"):
            bind_account_attestation(
                runtime,
                trusted(),
                self.evidence(),
                verifier=lambda evidence: True,
                verifier_id="auth-bridge",
            )

    def test_unverified_existing_attestation_cannot_be_promoted_silently(self):
        runtime = runtime_state()
        runtime["runtime"]["account_attestation"]["verified"] = False
        with self.assertRaisesRegex(BridgeViolation, "not verified"):
            bind_account_attestation(
                runtime,
                trusted(),
                self.evidence(),
                verifier=lambda evidence: True,
                verifier_id="auth-bridge",
            )

    def test_non_mapping_existing_attestation_fails_closed(self):
        runtime = runtime_state()
        runtime["runtime"]["account_attestation"] = "corrupt"
        with self.assertRaisesRegex(BridgeViolation, "malformed"):
            bind_account_attestation(
                runtime,
                trusted(),
                self.evidence(),
                verifier=lambda evidence: True,
                verifier_id="auth-bridge",
            )

    def test_existing_binding_missing_anchor_fails_closed(self):
        for field in ("first_bound_evidence_ref", "first_bound_session_id"):
            with self.subTest(field=field):
                runtime = runtime_state()
                runtime["runtime"]["account_attestation"].pop(field)
                with self.assertRaisesRegex(BridgeViolation, "identity binding is incomplete"):
                    bind_account_attestation(
                        runtime,
                        trusted(),
                        self.evidence(),
                        verifier=lambda evidence: True,
                        verifier_id="auth-bridge",
                    )

    def test_account_principal_or_member_cannot_self_verify(self):
        evidence = self.evidence()
        for verifier_id in (
            "HNS",
            " HNS ",
            "hns",
            evidence["principal_id"],
            " " + evidence["principal_id"] + " ",
            evidence["self_member_id"],
            " " + evidence["self_member_id"] + " ",
        ):
            with self.subTest(verifier_id=verifier_id):
                initial = runtime_state()
                initial["runtime"]["account_attestation"] = None
                with self.assertRaises(BridgeViolation):
                    bind_account_attestation(
                        initial,
                        trusted(),
                        evidence,
                        verifier=lambda evidence: True,
                        verifier_id=verifier_id,
                    )

    def test_refresh_cannot_change_source_or_verifier(self):
        first = runtime_state()
        first["runtime"]["account_attestation"] = None
        first = bind_account_attestation(
            first,
            trusted(),
            self.evidence(),
            verifier=lambda evidence: True,
            verifier_id="auth-bridge",
        )
        changed_source = self.evidence()
        changed_source["source"] = "weaker-source"
        with self.assertRaises(BridgeViolation):
            bind_account_attestation(
                first,
                trusted(),
                changed_source,
                verifier=lambda evidence: True,
                verifier_id="auth-bridge",
            )
        with self.assertRaises(BridgeViolation):
            bind_account_attestation(
                first,
                trusted(),
                self.evidence(),
                verifier=lambda evidence: True,
                verifier_id="different-auth-bridge",
            )

    def test_first_auth_runtime_binding_unlocks_targeted_write_preflight(self):
        base = trusted()
        runtime = runtime_state()
        runtime["runtime"]["account_attestation"] = None
        bound = bind_account_attestation(
            runtime,
            base,
            self.evidence(),
            verifier=lambda evidence: True,
            verifier_id="central-family-session-verifier",
        )
        out = preflight(write_plan(), overlay_runtime(base, bound))
        self.assertTrue(out["allowed"])
        self.assertEqual(
            bound["runtime"]["account_attestation"]["binding_mode"],
            "FIRST_AUTH_RUNTIME",
        )


class StartupReadbackBridgeTests(unittest.TestCase):
    def test_verified_startup_readback_is_recorded(self):
        runtime = runtime_state()
        receipt = {
            "authority_digest": "auth1",
            "sources": startup_receipt()["sources"],
        }
        updated = record_startup_readback(
            runtime,
            receipt,
            verifier=lambda value: True,
            verifier_id="startup-verifier",
        )
        stored = updated["context"]["startup_readback_receipt"]
        self.assertTrue(stored["verified"])
        self.assertEqual(stored["authority_digest"], "auth1")
        self.assertEqual(
            {item["kind"] for item in stored["sources"]},
            {"START_HERE", "CANONICAL", "SYSTEMWIDE_V2", "CURRENT"},
        )

    def test_startup_readback_missing_current_is_rejected(self):
        runtime = runtime_state()
        receipt = {
            "authority_digest": "auth1",
            "sources": startup_receipt()["sources"][:-1],
        }
        with self.assertRaisesRegex(BridgeViolation, "CURRENT"):
            record_startup_readback(
                runtime,
                receipt,
                verifier=lambda value: True,
                verifier_id="startup-verifier",
            )


class ExecutorVerifierUserBridgeTests(unittest.TestCase):
    def prepared(self):
        base = trusted()
        runtime = runtime_state()
        runtime["runtime"]["account_attestation"] = None
        runtime = bind_account_attestation(
            runtime,
            base,
            {
                "account": "HNS",
                "authenticated": True,
                "source": "central-family-session",
                "evidence_ref": "auth:e1",
                "session_id": "session-1",
                "identity_provider": "GOOGLE_OIDC_VERIFIED",
                "principal_id": "google:sub-hns",
                "family_id": "family-hns",
                "self_member_id": "member-hns",
            },
            verifier=lambda evidence: True,
            verifier_id="auth-bridge",
        )
        scoped = overlay_runtime(base, runtime)
        out = preflight(write_plan(), scoped)
        self.assertTrue(out["allowed"])
        runtime = persist_preflight(runtime, out)
        return base, runtime, out

    def invocation(self, provider="local"):
        return {
            "provider": provider,
            "method_or_tool": "python",
            "call": write_plan()["call"],
            "argv": ["python", "-c", "print('ok')"],
        }

    def test_local_only_receipt_blocks_external_provider(self):
        base, runtime, out = self.prepared()
        with self.assertRaises(BridgeViolation):
            execute_with_receipt(
                runtime,
                out["receipt_id"],
                self.invocation("claude"),
                runner=lambda invocation: {"returncode": 0},
                executor_id="executor-1",
            )

    def test_local_only_blocks_argv_route_spoof(self):
        base, runtime, out = self.prepared()
        bad = self.invocation()
        bad["argv"] = ["claude", "-p", "should-not-run"]
        with self.assertRaises(BridgeViolation):
            execute_with_receipt(
                runtime,
                out["receipt_id"],
                bad,
                runner=lambda invocation: {"returncode": 0},
                executor_id="executor-1",
            )

    def test_executor_cannot_change_receipt_bound_call(self):
        base, runtime, out = self.prepared()
        bad = self.invocation()
        bad["call"] = dict(bad["call"], model="sonnet")
        with self.assertRaises(BridgeViolation):
            execute_with_receipt(
                runtime,
                out["receipt_id"],
                bad,
                runner=lambda invocation: {"returncode": 0},
                executor_id="executor-1",
            )

    def test_executor_cannot_self_certify(self):
        base, runtime, out = self.prepared()
        runtime, result = execute_with_receipt(
            runtime,
            out["receipt_id"],
            self.invocation(),
            runner=lambda invocation: {"returncode": 0, "stdout": "written"},
            executor_id="executor-1",
        )
        with self.assertRaises(BridgeViolation):
            verify_execution(
                runtime,
                out["receipt_id"],
                verifier=lambda call, receipt: {
                    "passed": True,
                    "evidence_ref": "ev:1",
                    "evidence_type": "runtime_test",
                    "verifier_role": "VERIFIER",
                    "verifier_actor": "CODEX",
                    "key_match": True,
                    "required_verifications": ["technical"],
                    "passed_verifications": ["technical"],
                    "critical_gaps": [],
                },
                verifier_id="executor-1",
            )

    def test_verifier_failure_updates_route_anti_repeat_ledger(self):
        base, runtime, out = self.prepared()
        runtime, result = execute_with_receipt(
            runtime,
            out["receipt_id"],
            self.invocation(),
            runner=lambda invocation: {"returncode": 1, "stderr": "failed"},
            executor_id="executor-1",
        )
        runtime = verify_execution(
            runtime,
            out["receipt_id"],
            verifier=lambda call, receipt: {
                "passed": False,
                "evidence_ref": "ev:failed",
                "evidence_type": "runtime_test",
                "verifier_role": "VERIFIER",
                    "verifier_actor": "CODEX",
            },
            verifier_id="verifier-1",
        )
        scope = out["execution_scope"]
        self.assertTrue(runtime["route_ledgers"][scope]["failed_signatures"])

        scoped = overlay_runtime(base, runtime)
        blocked = preflight(write_plan(), scoped)
        self.assertFalse(blocked["allowed"])
        self.assertEqual(blocked["blocked_by"], "ROUTE")

    def test_silence_never_confirms(self):
        base, runtime, out = self.prepared()
        with self.assertRaises(BridgeViolation):
            record_user_confirmation(
                runtime,
                out["receipt_id"],
                {
                    "actor": "USER",
                    "kind": "confirmation",
                    "receipt_id": out["receipt_id"],
                    "event_ref": "user:confirm:1",
                    "explicit": False,
                },
                verifier=lambda event: True,
                verifier_id="ui-bridge",
            )

    def test_strong_verification_rejects_string_only_independent_reviewer(self):
        base, runtime, out = self.prepared()
        rid = out["receipt_id"]
        runtime, _ = execute_with_receipt(
            runtime,
            rid,
            self.invocation(),
            runner=lambda invocation: {"returncode": 0},
            executor_id="executor-1",
        )
        with self.assertRaisesRegex(
            BridgeViolation,
            "independent review receipt",
        ):
            verify_execution(
                runtime,
                rid,
                verifier=lambda call, receipt: {
                    "passed": True,
                    "evidence_ref": "ev:string-only",
                    "evidence_type": "runtime_test",
                    "verifier_role": "VERIFIER",
                    "verifier_actor": "CODEX",
                    "independent_reviewer_role": "INDEPENDENT_REVIEWER",
                    "independent_reviewer_actor": "CLAUDE",
                    "key_match": True,
                    "required_verifications": [
                        "structural", "technical", "intent", "independent"
                    ],
                    "passed_verifications": [
                        "structural", "technical", "intent", "independent"
                    ],
                    "critical_gaps": [],
                },
                verifier_id="verifier-1",
            )

    def test_independent_review_requires_verified_attestation(self):
        base, runtime, out = self.prepared()
        rid = out["receipt_id"]
        runtime, _ = execute_with_receipt(
            runtime,
            rid,
            self.invocation(),
            runner=lambda invocation: {"returncode": 0},
            executor_id="executor-1",
        )
        review = {
            "reviewer_role": "INDEPENDENT_REVIEWER",
                "reviewer_actor": "CLAUDE",
            "receipt_id": rid,
            "evidence_ref": "review:unverified",
            "source_or_artifact_ref": "claude:review:unverified",
            "target_result_digest": runtime["execution_calls"][rid]["result_digest"],
            "authority_digest": runtime["preflight_receipts"][rid]["authority_digest"],
            "passed": True,
            "critical_gaps": [],
        }
        with self.assertRaisesRegex(
            BridgeViolation,
            "attestation verification failed",
        ):
            record_independent_review(
                runtime,
                rid,
                review,
                reviewer_id="claude-session-1",
                review_verifier=lambda review, receipt, call: False,
                review_verifier_id="claude-review-bridge",
            )

    def test_independent_review_rejects_wrong_target_digest(self):
        base, runtime, out = self.prepared()
        rid = out["receipt_id"]
        runtime, _ = execute_with_receipt(
            runtime,
            rid,
            self.invocation(),
            runner=lambda invocation: {"returncode": 0},
            executor_id="executor-1",
        )
        with self.assertRaisesRegex(BridgeViolation, "target result mismatch"):
            record_independent_review(
                runtime,
                rid,
                {
                    "reviewer_role": "INDEPENDENT_REVIEWER",
                "reviewer_actor": "CLAUDE",
                    "receipt_id": rid,
                    "evidence_ref": "review:wrong-digest",
                    "source_or_artifact_ref": "claude:review:wrong-digest",
                    "target_result_digest": "wrong",
                    "authority_digest": runtime["preflight_receipts"][rid]["authority_digest"],
                    "passed": True,
                    "critical_gaps": [],
                },
                reviewer_id="claude-session-1",
                review_verifier=lambda review, receipt, call: True,
                review_verifier_id="claude-review-bridge",
            )

    def test_primary_verifier_cannot_also_be_independent_reviewer(self):
        base, runtime, out = self.prepared()
        rid = out["receipt_id"]
        runtime, _ = execute_with_receipt(
            runtime,
            rid,
            self.invocation(),
            runner=lambda invocation: {"returncode": 0},
            executor_id="executor-1",
        )
        runtime = record_independent_review(
            runtime,
            rid,
            {
                "reviewer_role": "INDEPENDENT_REVIEWER",
                "reviewer_actor": "CLAUDE",
                "receipt_id": rid,
                "evidence_ref": "review:same-verifier",
                "source_or_artifact_ref": "claude:review:same-verifier",
                "target_result_digest": runtime["execution_calls"][rid]["result_digest"],
                "authority_digest": runtime["preflight_receipts"][rid]["authority_digest"],
                "passed": True,
                "critical_gaps": [],
            },
            reviewer_id="same-verifier",
            review_verifier=lambda review, receipt, call: True,
            review_verifier_id="claude-review-bridge",
        )
        with self.assertRaisesRegex(
            BridgeViolation,
            "primary verifier cannot also be independent reviewer",
        ):
            verify_execution(
                runtime,
                rid,
                verifier=lambda call, receipt: {
                    "passed": True,
                    "evidence_ref": "ev:same-verifier",
                    "evidence_type": "runtime_test",
                    "verifier_role": "VERIFIER",
                    "verifier_actor": "CODEX",
                    "independent_reviewer_role": "INDEPENDENT_REVIEWER",
                    "independent_reviewer_actor": "CLAUDE",
                    "independent_review_ref": "review:same-verifier",
                    "key_match": True,
                    "required_verifications": [
                        "structural", "technical", "intent", "independent"
                    ],
                    "passed_verifications": [
                        "structural", "technical", "intent", "independent"
                    ],
                    "critical_gaps": [],
                },
                verifier_id="same-verifier",
            )

    def test_execution_verifier_cannot_launder_independent_review_type(self):
        base, runtime, out = self.prepared()
        rid = out["receipt_id"]
        runtime, _ = execute_with_receipt(
            runtime,
            rid,
            self.invocation(),
            runner=lambda invocation: {"returncode": 0},
            executor_id="executor-1",
        )
        with self.assertRaisesRegex(BridgeViolation, "cannot launder"):
            verify_execution(
                runtime,
                rid,
                verifier=lambda call, receipt: {
                    "passed": True,
                    "evidence_ref": "ev:laundered",
                    "evidence_type": "independent_review",
                    "verifier_role": "VERIFIER",
                    "verifier_actor": "CODEX",
                    "key_match": True,
                    "required_verifications": ["technical", "intent"],
                    "passed_verifications": ["technical", "intent"],
                    "critical_gaps": [],
                },
                verifier_id="verifier-1",
            )

    def test_full_integration_e2e_reaches_user_confirmed(self):
        base, runtime, out = self.prepared()
        rid = out["receipt_id"]

        runtime, result = execute_with_receipt(
            runtime,
            rid,
            self.invocation(),
            runner=lambda invocation: {
                "returncode": 0,
                "stdout": "document updated",
                "stderr": "",
            },
            executor_id="executor-1",
        )
        self.assertNotIn(rid, runtime["execution_outcomes"])

        runtime = record_independent_review(
            runtime,
            rid,
            {
                "reviewer_role": "INDEPENDENT_REVIEWER",
                "reviewer_actor": "CLAUDE",
                "receipt_id": rid,
                "evidence_ref": "review:e2e",
                "source_or_artifact_ref": "claude:review:e2e",
                "target_result_digest": runtime["execution_calls"][rid]["result_digest"],
                "authority_digest": runtime["preflight_receipts"][rid]["authority_digest"],
                "passed": True,
                "critical_gaps": [],
            },
            reviewer_id="claude-session-1",
            review_verifier=lambda review, receipt, call: True,
            review_verifier_id="claude-review-bridge",
        )

        runtime = verify_execution(
            runtime,
            rid,
            verifier=lambda call, receipt: {
                "passed": call["result"]["returncode"] == 0,
                "evidence_ref": "ev:e2e",
                "evidence_type": "runtime_test",
                "verifier_role": "VERIFIER",
                    "verifier_actor": "CODEX",
                "independent_reviewer_role": "INDEPENDENT_REVIEWER",
                    "independent_reviewer_actor": "CLAUDE",
                "independent_review_ref": "review:e2e",
                "key_match": True,
                "required_verifications": [
                    "structural", "technical", "intent", "independent"
                ],
                "passed_verifications": [
                    "structural", "technical", "intent", "independent"
                ],
                "critical_gaps": [],
            },
            verifier_id="verifier-1",
        )

        delivered = finalize(
            {"preflight_receipt": rid, "evidence_refs": ["ev:e2e", "review:e2e"]},
            overlay_runtime(base, runtime),
        )
        self.assertEqual(delivered["state"], "DELIVERED_UNCONFIRMED")

        runtime = record_user_confirmation(
            runtime,
            rid,
            {
                "actor": "USER",
                "kind": "confirmation",
                "receipt_id": rid,
                "event_ref": "user:confirm:e2e",
                "explicit": True,
            },
            verifier=lambda event: event.get("explicit") is True,
            verifier_id="ui-bridge",
        )
        confirmed = finalize(
            {"preflight_receipt": rid, "evidence_refs": ["ev:e2e", "review:e2e"]},
            overlay_runtime(base, runtime),
        )
        self.assertTrue(confirmed["allowed"])
        self.assertEqual(confirmed["state"], "USER_CONFIRMED")


    def test_verification_requires_codex_role(self):
        base, runtime, out = self.prepared()
        runtime, result = execute_with_receipt(
            runtime,
            out["receipt_id"],
            self.invocation(),
            runner=lambda invocation: {"returncode": 0},
            executor_id="executor-1",
        )
        with self.assertRaises(BridgeViolation):
            verify_execution(
                runtime,
                out["receipt_id"],
                verifier=lambda call, receipt: {
                    "passed": True,
                    "evidence_ref": "ev:wrong-role",
                    "evidence_type": "runtime_test",
                    "verifier_role": "INDEPENDENT_REVIEWER",
                    "verifier_actor": "CLAUDE",
                    "key_match": True,
                    "required_verifications": [
                        "structural", "technical", "intent", "independent"
                    ],
                    "passed_verifications": [
                        "structural", "technical", "intent", "independent"
                    ],
                    "independent_reviewer_role": "INDEPENDENT_REVIEWER",
                    "independent_reviewer_actor": "CLAUDE",
                    "critical_gaps": [],
                },
                verifier_id="verifier-1",
            )

    def test_strong_independent_review_requires_claude_role(self):
        base, runtime, out = self.prepared()
        runtime, result = execute_with_receipt(
            runtime,
            out["receipt_id"],
            self.invocation(),
            runner=lambda invocation: {"returncode": 0},
            executor_id="executor-1",
        )
        with self.assertRaises(BridgeViolation):
            verify_execution(
                runtime,
                out["receipt_id"],
                verifier=lambda call, receipt: {
                    "passed": True,
                    "evidence_ref": "ev:wrong-reviewer",
                    "evidence_type": "runtime_test",
                    "verifier_role": "VERIFIER",
                    "verifier_actor": "CODEX",
                    "independent_reviewer_role": "INDEPENDENT_REVIEWER",
                    "independent_reviewer_actor": "OTHER",
                    "key_match": True,
                    "required_verifications": [
                        "structural", "technical", "intent", "independent"
                    ],
                    "passed_verifications": [
                        "structural", "technical", "intent", "independent"
                    ],
                    "critical_gaps": [],
                },
                verifier_id="verifier-1",
            )

    def test_strong_tier_rejects_under_specified_verification(self):
        base, runtime, out = self.prepared()
        self.assertEqual(out["verification_tier"], "STRONG")
        runtime, result = execute_with_receipt(
            runtime,
            out["receipt_id"],
            self.invocation(),
            runner=lambda invocation: {"returncode": 0},
            executor_id="executor-1",
        )
        with self.assertRaises(BridgeViolation):
            verify_execution(
                runtime,
                out["receipt_id"],
                verifier=lambda call, receipt: {
                    "passed": True,
                    "evidence_ref": "ev:weak",
                    "evidence_type": "runtime_test",
                    "verifier_role": "VERIFIER",
                    "verifier_actor": "CODEX",
                    "key_match": True,
                    "required_verifications": ["technical", "intent"],
                    "passed_verifications": ["technical", "intent"],
                    "critical_gaps": [],
                },
                verifier_id="verifier-1",
            )

    def test_explicit_user_stop_marks_receipt_abandoned(self):
        base, runtime, out = self.prepared()
        rid = out["receipt_id"]
        runtime = record_user_stop(
            runtime,
            rid,
            {
                "actor": "USER",
                "kind": "stop",
                "receipt_id": rid,
                "event_ref": "user:stop:1",
                "explicit": True,
            },
            verifier=lambda event: event.get("explicit") is True,
            verifier_id="ui-bridge",
        )
        self.assertEqual(runtime["execution_outcomes"][rid], "ABANDONED")
        self.assertTrue(runtime["preflight_receipts"][rid]["consumed"])
        result = finalize(
            {"preflight_receipt": rid, "evidence_refs": ["none"]},
            overlay_runtime(base, runtime),
        )
        self.assertEqual(result["state"], "ABANDONED")


class AuthorityRebindTests(unittest.TestCase):
    def make_state(self, old_authority=None):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        old_authority = old_authority or {"key": {"generation": 1}}
        example = {
            "runtime_version": 1,
            "authority_digest": "",
            "runtime": {"account_attestation": None},
            "context": {},
            "route_ledgers": {},
            "preflight_receipts": {},
            "active_attempts": {},
            "execution_outcomes": {},
            "execution_calls": {},
            "evidence_registry": {},
            "completion_registry": {},
            "control_incidents": {},
            "consumed_approvals": {},
            "user_events": {},
            "authority_rebind_history": [],
        }
        ap = root / "authority.json"
        ep = root / "runtime.example.json"
        rp = root / "runtime.json"
        anchor = root / "runtime.anchor.json"
        lock = root / "runtime.lock"
        ap.write_text(json.dumps(old_authority), encoding="utf-8")
        ep.write_text(json.dumps(example), encoding="utf-8")
        runtime = initialize_runtime(
            ap, ep, rp, runtime_key=KEY, anchor_path=anchor
        )
        return tmp, ap, ep, rp, anchor, lock, old_authority, runtime

    def test_authority_change_without_staged_user_rebind_fails_closed(self):
        tmp, ap, ep, rp, anchor, lock, old, runtime = self.make_state()
        try:
            ap.write_text(json.dumps({"key": {"generation": 2}}), encoding="utf-8")
            with self.assertRaises(StateIntegrityError):
                rebind_authority(
                    ap,
                    rp,
                    lock_path=lock,
                    runtime_key=KEY,
                    anchor_path=anchor,
                )
        finally:
            tmp.cleanup()

    def test_explicit_staged_user_rebind_migrates_digest(self):
        tmp, ap, ep, rp, anchor, lock, old, runtime = self.make_state()
        try:
            new_authority = {"key": {"generation": 2}}
            new_digest = authority_digest(new_authority)
            staged = stage_authority_rebind(
                runtime,
                current_authority=old,
                new_authority=new_authority,
                user_event={
                    "actor": "USER",
                    "kind": "authority_rebind",
                    "explicit": True,
                    "event_ref": "user:rebind:1",
                    "authorized_new_digest": new_digest,
                },
                event_verifier=lambda event: event.get("explicit") is True,
                verifier_id="ui-bridge",
            )
            staged = save_runtime(
                staged,
                expected_version=runtime["runtime_version"],
                authority_digest_value=runtime["authority_digest"],
                runtime_path=rp,
                lock_path=lock,
                runtime_key=KEY,
                anchor_path=anchor,
            )
            ap.write_text(json.dumps(new_authority), encoding="utf-8")

            with self.assertRaises(StateIntegrityError):
                load_bundle(ap, rp, runtime_key=KEY, anchor_path=anchor)

            rebound = rebind_authority(
                ap,
                rp,
                lock_path=lock,
                runtime_key=KEY,
                anchor_path=anchor,
            )
            self.assertEqual(rebound["authority_digest"], new_digest)
            self.assertEqual(
                rebound["authority_rebind_history"][-1]["event_ref"],
                "user:rebind:1",
            )
            trusted_bundle, loaded, digest = load_bundle(
                ap, rp, runtime_key=KEY, anchor_path=anchor
            )
            self.assertEqual(digest, new_digest)
        finally:
            tmp.cleanup()


    def test_key_amend_requires_explicit_flag_and_version_increment(self):
        old_authority = {
            "key": {
                "USER_INTENT": {
                    "value": "old",
                    "provenance": "USER_STATED",
                    "source_ref": "u:intent:1",
                    "scope": "task",
                    "version": 1,
                }
            },
            "source_registry": {
                "u:intent:1": {"actor": "USER", "kind": "statement"},
                "u:intent:2": {"actor": "USER", "kind": "statement"},
            },
        }
        tmp, ap, ep, rp, anchor, lock, old, runtime = self.make_state(old_authority)
        try:
            new_authority = {
                **old_authority,
                "key": {
                    "USER_INTENT": {
                        "value": "new",
                        "provenance": "USER_STATED",
                        "source_ref": "u:intent:2",
                        "scope": "task",
                        "version": 2,
                    }
                },
            }
            new_digest = authority_digest(new_authority)
            event = {
                "actor": "USER",
                "kind": "authority_rebind",
                "explicit": True,
                "event_ref": "user:key-amend:1",
                "authorized_new_digest": new_digest,
            }
            with self.assertRaises(StateIntegrityError):
                stage_authority_rebind(
                    runtime,
                    current_authority=old_authority,
                    new_authority=new_authority,
                    user_event=event,
                    event_verifier=lambda e: True,
                    verifier_id="ui-bridge",
                )

            event["key_amend"] = True
            staged = stage_authority_rebind(
                runtime,
                current_authority=old_authority,
                new_authority=new_authority,
                user_event=event,
                event_verifier=lambda e: True,
                verifier_id="ui-bridge",
            )
            diff = staged["authority_rebind_request"]["key_diff"]
            self.assertEqual(diff[0]["field"], "USER_INTENT")
            self.assertEqual(diff[0]["old_version"], 1)
            self.assertEqual(diff[0]["new_version"], 2)
        finally:
            tmp.cleanup()

    def test_key_amend_rejects_untrusted_source_ref(self):
        old_authority = {
            "key": {
                "USER_INTENT": {
                    "value": "old",
                    "provenance": "USER_STATED",
                    "source_ref": "u:intent:1",
                    "scope": "task",
                    "version": 1,
                }
            },
            "source_registry": {
                "u:intent:1": {"actor": "USER", "kind": "statement"},
            },
        }
        tmp, ap, ep, rp, anchor, lock, old, runtime = self.make_state(old_authority)
        try:
            new_authority = {
                "key": {
                    "USER_INTENT": {
                        "value": "new",
                        "provenance": "USER_CONFIRMED",
                        "source_ref": "ai:fake",
                        "scope": "task",
                        "version": 2,
                    }
                },
                "source_registry": {
                    "ai:fake": {"actor": "AI", "kind": "statement"},
                },
            }
            new_digest = authority_digest(new_authority)
            with self.assertRaises(StateIntegrityError):
                stage_authority_rebind(
                    runtime,
                    current_authority=old_authority,
                    new_authority=new_authority,
                    user_event={
                        "actor": "USER",
                        "kind": "authority_rebind",
                        "explicit": True,
                        "key_amend": True,
                        "event_ref": "user:key-amend:fake",
                        "authorized_new_digest": new_digest,
                    },
                    event_verifier=lambda e: True,
                    verifier_id="ui-bridge",
                )
        finally:
            tmp.cleanup()

    def test_key_amend_rejects_version_jump(self):
        old_authority = {
            "key": {
                "USER_INTENT": {
                    "value": "old",
                    "provenance": "USER_STATED",
                    "source_ref": "u:intent:1",
                    "scope": "task",
                    "version": 1,
                }
            },
            "source_registry": {
                "u:intent:1": {"actor": "USER", "kind": "statement"},
            },
        }
        tmp, ap, ep, rp, anchor, lock, old, runtime = self.make_state(old_authority)
        try:
            new_authority = {
                "key": {
                    "USER_INTENT": {
                        "value": "new",
                        "provenance": "USER_CONFIRMED",
                        "source_ref": "u:intent:2",
                        "scope": "task",
                        "version": 3,
                    }
                },
                "source_registry": {
                    "u:intent:2": {"actor": "USER", "kind": "confirmation"},
                },
            }
            new_digest = authority_digest(new_authority)
            with self.assertRaises(StateIntegrityError):
                stage_authority_rebind(
                    runtime,
                    current_authority=old_authority,
                    new_authority=new_authority,
                    user_event={
                        "actor": "USER",
                        "kind": "authority_rebind",
                        "explicit": True,
                        "key_amend": True,
                        "event_ref": "user:key-amend:jump",
                        "authorized_new_digest": new_digest,
                    },
                    event_verifier=lambda e: True,
                    verifier_id="ui-bridge",
                )
        finally:
            tmp.cleanup()


    def _prepared_external_review(self):
        base = trusted()
        runtime = runtime_state()
        p = {
            "task_id": "bridge-external-review",
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
                    "operations": ["single bounded external review"],
                    "batch_strategy": "single-batch",
                    "fallback": "HOLD",
                    "paid_api": False,
                },
            },
        }
        out = preflight(p, overlay_runtime(base, runtime))
        self.assertTrue(out["allowed"])
        self.assertTrue(out["call_allowed"])
        runtime = persist_preflight(runtime, out)
        invocation = {
            "provider": "anthropic",
            "method_or_tool": "claude",
            "call": dict(p["call"]),
            "argv": [
                "claude", "-p",
                "--model", "sonnet",
                "--effort", "medium",
                "review",
            ],
        }
        return runtime, out, invocation

    def test_external_executor_rejects_receipt_without_persisted_dry_run(self):
        runtime, out, invocation = self._prepared_external_review()
        receipt = runtime["preflight_receipts"][out["receipt_id"]]
        receipt["economy_evaluation"] = {"dry_run": None}
        with self.assertRaisesRegex(BridgeViolation, "persisted DRY_RUN_OK"):
            execute_with_receipt(
                runtime, out["receipt_id"], invocation,
                executor_id="claude-test",
                runner=lambda _: {"ok": True},
            )

    def test_external_executor_rejects_multi_call_receipt(self):
        runtime, out, invocation = self._prepared_external_review()
        receipt = runtime["preflight_receipts"][out["receipt_id"]]
        invocation["call"]["expected_calls"] = 2
        receipt["call_digest"] = stable_hash(dict(invocation["call"]))
        with self.assertRaisesRegex(BridgeViolation, "exactly one external invocation"):
            execute_with_receipt(
                runtime, out["receipt_id"], invocation,
                executor_id="claude-test",
                runner=lambda _: {"ok": True},
            )

    def test_packet_only_claude_requires_bound_toolless_stdin_packet(self):
        runtime, out, invocation = self._prepared_external_review()
        packet = "compact independent review packet"
        invocation["call"]["execution_mode"] = "PACKET_ONLY"
        invocation["call"]["packet_digest"] = stable_hash(packet)
        invocation["stdin_text"] = packet
        invocation["argv"] = [
            str((Path.home() / ".local" / "bin" / "claude.exe").resolve()),
            "-p",
            "--input-format", "text",
            "--output-format", "json",
            "--model", "sonnet",
            "--effort", "medium",
            "--tools", "",
            "--permission-prompts", "none",
            "--no-session-persistence",
            "--strict-mcp-config",
            "--setting-sources", "",
            "--settings", "{}",
        ]
        receipt = runtime["preflight_receipts"][out["receipt_id"]]
        receipt["call_digest"] = stable_hash(dict(invocation["call"]))
        updated, result = execute_with_receipt(
            runtime, out["receipt_id"], invocation,
            executor_id="claude-test",
            runner=lambda inv: {
                "ok": inv["stdin_text"] == packet,
                "cwd": inv.get("cwd"),
                "minimal_env": inv.get("minimal_env"),
            },
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["minimal_env"])
        self.assertTrue(result["cwd"])
        self.assertFalse(Path(result["cwd"]).exists())
        self.assertIn(out["receipt_id"], updated["execution_calls"])

    def test_subscription_route_rejects_api_key_injection(self):
        runtime, out, invocation = self._prepared_external_review()
        invocation["env"] = {"ANTHROPIC_API_KEY": "should-not-run"}
        with self.assertRaisesRegex(BridgeViolation, "does not allow env overrides"):
            execute_with_receipt(
                runtime, out["receipt_id"], invocation,
                executor_id="claude-test",
                runner=lambda _: {"ok": True},
            )

    def test_packet_only_rejects_non_hardened_executor(self):
        runtime, out, invocation = self._prepared_external_review()
        packet = "compact independent review packet"
        invocation["call"]["execution_mode"] = "PACKET_ONLY"
        invocation["call"]["packet_digest"] = stable_hash(packet)
        invocation["stdin_text"] = packet
        invocation["provider"] = "openai"
        invocation["method_or_tool"] = "codex"
        invocation["argv"] = ["codex", "exec", "-"]
        receipt = runtime["preflight_receipts"][out["receipt_id"]]
        receipt["call_digest"] = stable_hash(dict(invocation["call"]))
        active = runtime["active_attempts"][receipt["execution_key"]]
        active["attempt"]["method_or_tool"] = "codex"
        with self.assertRaisesRegex(BridgeViolation, "dedicated hardened verifier contract"):
            execute_with_receipt(
                runtime, out["receipt_id"], invocation,
                executor_id="codex-test",
                runner=lambda _: {"ok": True},
            )

    def test_codex_verify_only_hardened_packet_executes(self):
        runtime, out, invocation = self._prepared_external_review()
        packet = "compact codex verifier packet"
        invocation["call"]["model"] = "codex"
        invocation["call"]["execution_mode"] = "CODEX_VERIFY_ONLY"
        invocation["call"]["packet_digest"] = stable_hash(packet)
        invocation["stdin_text"] = packet
        invocation["provider"] = "openai"
        invocation["method_or_tool"] = "codex"
        invocation["argv"] = [
            str((Path.home() / "AppData" / "Roaming" / "npm" / "codex.cmd").resolve()),
            "exec",
            "--sandbox", "read-only",
            "--skip-git-repo-check",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--strict-config",
            "-c", "model_reasoning_effort=\"medium\"",
            "-c", "web_search=\"disabled\"",
            "--disable", "shell_tool",
            "--disable", "unified_exec",
            "--disable", "shell_snapshot",
            "--disable", "multi_agent",
            "--disable", "apps",
            "--disable", "hooks",
            "--disable", "remote_plugin",
            "-",
        ]
        receipt = runtime["preflight_receipts"][out["receipt_id"]]
        receipt["call_digest"] = stable_hash(dict(invocation["call"]))
        active = runtime["active_attempts"][receipt["execution_key"]]
        active["attempt"]["method_or_tool"] = "codex"

        updated, result = execute_with_receipt(
            runtime,
            out["receipt_id"],
            invocation,
            executor_id="codex-test",
            runner=lambda inv: {
                "ok": True,
                "argv": inv["argv"],
                "cwd": inv.get("cwd"),
                "minimal_env": inv.get("minimal_env"),
                "last_message_path": inv.get("_bridge_last_message_path"),
            },
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["minimal_env"])
        self.assertIn("-C", result["argv"])
        self.assertIn("--output-last-message", result["argv"])
        self.assertTrue(result["cwd"])
        self.assertTrue(result["last_message_path"])
        self.assertEqual(
            Path(result["last_message_path"]).parent,
            Path(result["cwd"]),
        )
        self.assertFalse(Path(result["cwd"]).exists())
        self.assertEqual(
            updated["execution_calls"][out["receipt_id"]]["status"],
            "RETURNED",
        )

    def test_codex_verify_only_rejects_argv_expansion(self):
        runtime, out, invocation = self._prepared_external_review()
        packet = "compact codex verifier packet"
        invocation["call"]["model"] = "codex"
        invocation["call"]["execution_mode"] = "CODEX_VERIFY_ONLY"
        invocation["call"]["packet_digest"] = stable_hash(packet)
        invocation["stdin_text"] = packet
        invocation["provider"] = "openai"
        invocation["method_or_tool"] = "codex"
        invocation["argv"] = [
            str((Path.home() / "AppData" / "Roaming" / "npm" / "codex.cmd").resolve()),
            "exec",
            "--sandbox", "read-only",
            "--skip-git-repo-check",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--strict-config",
            "-c", "model_reasoning_effort=\"medium\"",
            "-c", "web_search=\"disabled\"",
            "--disable", "shell_tool",
            "--disable", "unified_exec",
            "--disable", "shell_snapshot",
            "--disable", "multi_agent",
            "--disable", "apps",
            "--disable", "hooks",
            "--disable", "remote_plugin",
            "--add-dir", "C:\\",
            "-",
        ]
        receipt = runtime["preflight_receipts"][out["receipt_id"]]
        receipt["call_digest"] = stable_hash(dict(invocation["call"]))
        active = runtime["active_attempts"][receipt["execution_key"]]
        active["attempt"]["method_or_tool"] = "codex"
        with self.assertRaisesRegex(BridgeViolation, "exact hardened template"):
            execute_with_receipt(
                runtime,
                out["receipt_id"],
                invocation,
                executor_id="codex-test",
                runner=lambda _: {"ok": True},
            )

    def test_packet_only_claude_rejects_argv_model_mismatch(self):
        runtime, out, invocation = self._prepared_external_review()
        packet = "compact independent review packet"
        invocation["call"]["execution_mode"] = "PACKET_ONLY"
        invocation["call"]["packet_digest"] = stable_hash(packet)
        invocation["stdin_text"] = packet
        invocation["argv"] = [
            "claude", "-p",
            "--model", "opus",
            "--effort", "medium",
            "--tools", "",
            "--permission-prompts", "none",
            "--no-session-persistence",
            "--strict-mcp-config",
            "--bare",
        ]
        receipt = runtime["preflight_receipts"][out["receipt_id"]]
        receipt["call_digest"] = stable_hash(dict(invocation["call"]))
        with self.assertRaisesRegex(BridgeViolation, "argv model must match"):
            execute_with_receipt(
                runtime, out["receipt_id"], invocation,
                executor_id="claude-test",
                runner=lambda _: {"ok": True},
            )

    def test_persisted_claim_blocks_second_claim_and_finalizes_returned(self):
        runtime, out, invocation = self._prepared_external_review()
        reserved, claim_token = claim_execution_receipt(
            runtime,
            out["receipt_id"],
            executor_id="claude-test",
        )
        self.assertEqual(
            reserved["execution_calls"][out["receipt_id"]]["status"],
            "CLAIMED",
        )
        execution_key = reserved["preflight_receipts"][out["receipt_id"]]["execution_key"]
        self.assertEqual(reserved["active_attempts"][execution_key]["status"], "RESERVED")
        with self.assertRaisesRegex(BridgeViolation, "receipt already has an executor call"):
            claim_execution_receipt(
                reserved,
                out["receipt_id"],
                executor_id="claude-test",
            )

        checkpoints = []

        def checkpoint(candidate):
            checkpoints.append(
                (
                    candidate["execution_calls"][out["receipt_id"]]["status"],
                    candidate["active_attempts"][execution_key]["status"],
                )
            )
            return candidate

        updated, result = execute_with_receipt(
            reserved,
            out["receipt_id"],
            invocation,
            executor_id="claude-test",
            preclaimed=True,
            claim_token=claim_token,
            pre_run_checkpoint=checkpoint,
            runner=lambda _: {"returncode": 0, "stdout": "ok", "stderr": ""},
        )
        self.assertEqual(checkpoints, [("CALLING", "CALLING")])
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(updated["execution_calls"][out["receipt_id"]]["status"], "RETURNED")
        self.assertEqual(updated["active_attempts"][execution_key]["status"], "RETURNED")

    def test_external_preclaimed_execution_requires_durable_checkpoint(self):
        runtime, out, invocation = self._prepared_external_review()
        reserved, claim_token = claim_execution_receipt(
            runtime,
            out["receipt_id"],
            executor_id="claude-test",
        )
        seen = []
        with self.assertRaisesRegex(BridgeViolation, "durable pre-run checkpoint"):
            execute_with_receipt(
                reserved,
                out["receipt_id"],
                invocation,
                executor_id="claude-test",
                preclaimed=True,
                claim_token=claim_token,
                runner=lambda _: seen.append("called") or {"returncode": 0},
            )
        self.assertEqual(seen, [])

    def test_persisted_claim_requires_matching_token(self):
        runtime, out, invocation = self._prepared_external_review()
        reserved, _ = claim_execution_receipt(
            runtime,
            out["receipt_id"],
            executor_id="claude-test",
        )
        with self.assertRaisesRegex(BridgeViolation, "claim token mismatch"):
            execute_with_receipt(
                reserved,
                out["receipt_id"],
                invocation,
                executor_id="claude-test",
                preclaimed=True,
                claim_token="wrong-token",
                runner=lambda _: {"returncode": 0},
            )

    def test_reconcile_persisted_claim_terminalizes_failed(self):
        runtime, out, _ = self._prepared_external_review()
        reserved, _ = claim_execution_receipt(
            runtime,
            out["receipt_id"],
            executor_id="claude-test",
        )
        reconciled = reconcile_execution_claim(
            reserved,
            out["receipt_id"],
            reconciler_id="test-reconciler",
            reason="simulated interrupted runner",
        )
        execution_key = reconciled["preflight_receipts"][out["receipt_id"]]["execution_key"]
        self.assertEqual(
            reconciled["execution_calls"][out["receipt_id"]]["status"],
            "FAILED",
        )
        self.assertEqual(reconciled["active_attempts"][execution_key]["status"], "FAILED")

    def test_calling_reconcile_preserves_unknown_outcome_and_blocks_retry(self):
        runtime, out, invocation = self._prepared_external_review()
        reserved, _ = claim_execution_receipt(
            runtime,
            out["receipt_id"],
            executor_id="claude-test",
        )
        execution_key = reserved["preflight_receipts"][out["receipt_id"]]["execution_key"]
        reserved["execution_calls"][out["receipt_id"]].update({
            "provider": "anthropic",
            "model": "sonnet",
            "actual_calls": 1,
            "method_or_tool": "claude",
            "status": "CALLING",
        })
        reserved["active_attempts"][execution_key]["status"] = "CALLING"

        reconciled = reconcile_execution_claim(
            reserved,
            out["receipt_id"],
            reconciler_id="test-reconciler",
            reason="simulated process interruption after runner start",
        )
        self.assertEqual(
            reconciled["execution_calls"][out["receipt_id"]]["status"],
            "OUTCOME_UNKNOWN",
        )
        self.assertEqual(
            reconciled["active_attempts"][execution_key]["status"],
            "OUTCOME_UNKNOWN",
        )
        self.assertEqual(
            reconciled["execution_calls"][out["receipt_id"]]["result"]["returncode"],
            125,
        )

        trusted_runtime = overlay_runtime(trusted(), reconciled)
        retry = preflight({
            "task_id": "bridge-external-review-retry",
            "action_id": "review",
            "context": {"mode": "delta"},
            "attempt": {"target": "Q002", "method_or_tool": "claude"},
            "call": dict(invocation["call"]),
        }, trusted_runtime)
        self.assertFalse(retry["allowed"])
        self.assertEqual(retry["blocked_by"], "ROUTE")
        self.assertIn("unresolved attempt", retry["reason"])

    def test_minimal_packet_env_excludes_provider_credentials(self):
        env = _minimal_packet_env()
        upper = {key.upper() for key in env}
        self.assertFalse(any(key.startswith("ANTHROPIC_") for key in upper))
        self.assertFalse(any(key.startswith("OPENAI_") for key in upper))
        self.assertFalse(any(key.startswith("GEMINI_") for key in upper))
        self.assertFalse(any(key.startswith("GOOGLE_") for key in upper))
        self.assertNotIn("CLAUDE_CONFIG_DIR", upper)

    def test_reconcile_calling_claim_preserves_unknown_outcome(self):
        runtime, out, _ = self._prepared_external_review()
        reserved, _ = claim_execution_receipt(
            runtime,
            out["receipt_id"],
            executor_id="claude-test",
        )
        execution_key = reserved["preflight_receipts"][out["receipt_id"]]["execution_key"]
        reserved["execution_calls"][out["receipt_id"]].update({
            "actual_calls": 1,
            "status": "CALLING",
        })
        reserved["active_attempts"][execution_key]["status"] = "CALLING"
        reconciled = reconcile_execution_claim(
            reserved,
            out["receipt_id"],
            reconciler_id="test-reconciler",
            reason="simulated process interruption",
        )
        self.assertEqual(
            reconciled["execution_calls"][out["receipt_id"]]["status"],
            "OUTCOME_UNKNOWN",
        )
        self.assertEqual(
            reconciled["active_attempts"][execution_key]["status"],
            "OUTCOME_UNKNOWN",
        )
        self.assertEqual(
            reconciled["execution_calls"][out["receipt_id"]]["result"]["returncode"],
            125,
        )

    def test_executor_receipt_cannot_invoke_runner_twice(self):
        runtime, out, invocation = self._prepared_external_review()
        seen = []
        updated, _ = execute_with_receipt(
            runtime, out["receipt_id"], invocation,
            executor_id="claude-test",
            runner=lambda _: seen.append("called") or {"returncode": 0},
        )
        self.assertEqual(seen, ["called"])
        with self.assertRaisesRegex(BridgeViolation, "receipt already has an executor call"):
            execute_with_receipt(
                updated, out["receipt_id"], invocation,
                executor_id="claude-test",
                runner=lambda _: seen.append("called-again") or {"returncode": 0},
            )
        self.assertEqual(seen, ["called"])

    def test_runner_exception_consumes_receipt_as_unknown_outcome(self):
        runtime, out, invocation = self._prepared_external_review()

        def broken_runner(_):
            raise FileNotFoundError("simulated missing executor")

        updated, result = execute_with_receipt(
            runtime, out["receipt_id"], invocation,
            executor_id="claude-test",
            runner=broken_runner,
        )
        self.assertEqual(result["returncode"], 125)
        self.assertTrue(result["outcome_unknown"])
        self.assertEqual(
            updated["execution_calls"][out["receipt_id"]]["status"],
            "OUTCOME_UNKNOWN",
        )
        with self.assertRaisesRegex(BridgeViolation, "receipt already has an executor call"):
            execute_with_receipt(
                updated, out["receipt_id"], invocation,
                executor_id="claude-test",
                runner=lambda _: {"returncode": 0},
            )

    def test_external_nonzero_exit_is_unknown_without_confirmed_no_provider_call(self):
        runtime, out, invocation = self._prepared_external_review()
        updated, result = execute_with_receipt(
            runtime,
            out["receipt_id"],
            invocation,
            executor_id="claude-test",
            runner=lambda _: {
                "returncode": 1,
                "stdout": "",
                "stderr": "model cli exited nonzero",
            },
        )
        self.assertTrue(result["outcome_unknown"])
        self.assertEqual(
            updated["execution_calls"][out["receipt_id"]]["status"],
            "OUTCOME_UNKNOWN",
        )

    def test_external_nonzero_can_be_failed_when_no_provider_call_is_attested(self):
        runtime, out, invocation = self._prepared_external_review()
        updated, result = execute_with_receipt(
            runtime,
            out["receipt_id"],
            invocation,
            executor_id="claude-test",
            runner=lambda _: {
                "returncode": 2,
                "stdout": "",
                "stderr": "local argument validation failed",
                "provider_call_confirmed_absent": True,
            },
        )
        self.assertNotIn("outcome_unknown", result)
        self.assertEqual(
            updated["execution_calls"][out["receipt_id"]]["status"],
            "FAILED",
        )

    def test_packet_only_duplicate_flag_is_rejected(self):
        runtime, out, invocation = self._prepared_external_review()
        packet = "compact independent review packet"
        invocation["call"]["execution_mode"] = "PACKET_ONLY"
        invocation["call"]["packet_digest"] = stable_hash(packet)
        invocation["stdin_text"] = packet
        invocation["argv"] = [
            str((Path.home() / ".local" / "bin" / "claude.exe").resolve()),
            "-p",
            "--input-format", "text",
            "--output-format", "json",
            "--model", "sonnet",
            "--effort", "medium",
            "--tools", "",
            "--permission-prompts", "none",
            "--no-session-persistence",
            "--strict-mcp-config",
            "--setting-sources", "",
            "--settings", "{}",
            "--tools", "default",
        ]
        receipt = runtime["preflight_receipts"][out["receipt_id"]]
        receipt["call_digest"] = stable_hash(dict(invocation["call"]))
        with self.assertRaisesRegex(BridgeViolation, "exact hardened template"):
            execute_with_receipt(
                runtime, out["receipt_id"], invocation,
                executor_id="claude-test",
                runner=lambda _: {"returncode": 0},
            )

    def test_packet_only_claude_rejects_agentic_tool_access(self):
        runtime, out, invocation = self._prepared_external_review()
        packet = "compact independent review packet"
        invocation["call"]["execution_mode"] = "PACKET_ONLY"
        invocation["call"]["packet_digest"] = stable_hash(packet)
        invocation["stdin_text"] = packet
        invocation["argv"] = [
            str((Path.home() / ".local" / "bin" / "claude.exe").resolve()),
            "-p",
            "--input-format", "text",
            "--output-format", "json",
            "--model", "sonnet",
            "--effort", "medium",
            "--tools", "Read",
            "--permission-prompts", "none",
            "--no-session-persistence",
            "--strict-mcp-config",
            "--setting-sources", "",
            "--settings", "{}",
        ]
        receipt = runtime["preflight_receipts"][out["receipt_id"]]
        receipt["call_digest"] = stable_hash(dict(invocation["call"]))
        with self.assertRaisesRegex(BridgeViolation, "empty --tools"):
            execute_with_receipt(
                runtime, out["receipt_id"], invocation,
                executor_id="claude-test",
                runner=lambda _: {"ok": True},
            )


if __name__ == "__main__":
    unittest.main()


class EconomyDecisionBridgeTests(unittest.TestCase):
    def decision(self, ref="econ:bridge", kind="REUSE_SUFFICIENT"):
        return {
            "evidence_ref": ref,
            "decision_kind": kind,
            "acceptance_ref": "acceptance:test-quality",
            "source_or_artifact_ref": "runtime:economy-assessment",
            "revision_or_hash": "rev-1",
        }

    def test_quality_required_economy_decision_requires_acceptance_ref(self):
        from TAKY2.bridges import record_economy_decision

        base = trusted()
        runtime = runtime_state()
        action = base["action_registry"]["review"]
        decision = self.decision(ref="econ:missing-acceptance")
        decision.pop("acceptance_ref")
        with self.assertRaisesRegex(BridgeViolation, "acceptance_ref"):
            record_economy_decision(
                runtime,
                action,
                decision,
                verifier=lambda *_: True,
                verifier_id="savey-economy-verifier",
            )

    def test_verified_economy_decision_is_recorded_and_consumed(self):
        from TAKY2.bridges import record_economy_decision
        from TAKY2.enforcement import cost_gate

        base = trusted()
        runtime = runtime_state()
        action = base["action_registry"]["review"]
        updated = record_economy_decision(
            runtime,
            action,
            self.decision(),
            verifier=lambda decision, bound_action, state: (
                decision["decision_kind"] == "REUSE_SUFFICIENT"
                and bound_action is action
                and state["authority_digest"] == "auth1"
            ),
            verifier_id="savey-economy-verifier",
        )
        item = updated["economy_evidence_registry"]["econ:bridge"]
        self.assertTrue(item["verified"])
        self.assertEqual(item["acceptance_state"], "ACCEPTED")
        self.assertEqual(item["authority_digest"], "auth1")
        self.assertEqual(item["semantic_owner_ref"], action["semantic_owner_ref"])

        scoped = dict(base)
        scoped["economy_evidence_registry"] = updated["economy_evidence_registry"]
        result = cost_gate(
            scoped,
            action,
            {
                "reuse_decision_ref": "econ:bridge",
                "model": "sonnet",
                "effort": "medium",
                "expected_calls": 1,
                "context": "delta",
            },
        )
        self.assertTrue(result.allowed)
        self.assertEqual(result.state, "SKIP_CALL")

    def test_unverified_economy_decision_is_rejected(self):
        from TAKY2.bridges import record_economy_decision

        base = trusted()
        with self.assertRaisesRegex(BridgeViolation, "verification failed"):
            record_economy_decision(
                runtime_state(),
                base["action_registry"]["review"],
                self.decision(),
                verifier=lambda decision, action, state: False,
                verifier_id="savey-economy-verifier",
            )

    def test_invalid_economy_decision_kind_is_rejected(self):
        from TAKY2.bridges import record_economy_decision

        base = trusted()
        with self.assertRaisesRegex(BridgeViolation, "unsupported economy decision kind"):
            record_economy_decision(
                runtime_state(),
                base["action_registry"]["review"],
                self.decision(kind="FORCE_SKIP"),
                verifier=lambda decision, action, state: True,
                verifier_id="savey-economy-verifier",
            )

    def test_duplicate_economy_decision_ref_is_rejected(self):
        from TAKY2.bridges import record_economy_decision

        base = trusted()
        action = base["action_registry"]["review"]
        first = record_economy_decision(
            runtime_state(),
            action,
            self.decision(),
            verifier=lambda decision, bound_action, state: True,
            verifier_id="savey-economy-verifier",
        )
        with self.assertRaisesRegex(BridgeViolation, "already exists"):
            record_economy_decision(
                first,
                action,
                self.decision(),
                verifier=lambda decision, bound_action, state: True,
                verifier_id="savey-economy-verifier",
            )

    def test_economy_decision_cannot_be_reused_for_wrong_action(self):
        from TAKY2.bridges import record_economy_decision
        from TAKY2.enforcement import cost_gate

        base = trusted()
        review = base["action_registry"]["review"]
        other = base["action_registry"]["optional-review"]
        updated = record_economy_decision(
            runtime_state(),
            review,
            self.decision(),
            verifier=lambda decision, action, state: True,
            verifier_id="savey-economy-verifier",
        )
        scoped = dict(base)
        scoped["economy_evidence_registry"] = updated["economy_evidence_registry"]
        result = cost_gate(
            scoped,
            other,
            {
                "reuse_decision_ref": "econ:bridge",
                "model": "sonnet",
                "effort": "medium",
                "expected_calls": 1,
                "context": "delta",
            },
        )
        self.assertFalse(result.allowed)
        self.assertIn("action binding mismatch", result.reason)


def test_subprocess_runner_closes_stdin_for_noninteractive_receipt_execution(monkeypatch):
    import subprocess as _subprocess
    from TAKY2.bridges import subprocess_runner

    seen = {}
    class Result:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(argv, **kwargs):
        seen["argv"] = argv
        seen.update(kwargs)
        return Result()

    monkeypatch.setattr(_subprocess, "run", fake_run)
    result = subprocess_runner({"argv": ["dummy", "arg"]})
    assert result["returncode"] == 0
    assert seen["stdin"] is _subprocess.DEVNULL
    assert seen["shell"] is False
    assert seen["capture_output"] is True


def test_subprocess_runner_real_stdin_reader_gets_eof_immediately():
    import sys
    from TAKY2.bridges import subprocess_runner

    result = subprocess_runner({
        "argv": [
            sys.executable,
            "-c",
            "import sys; d=sys.stdin.read(); print('EOF' if d == '' else 'DATA')",
        ],
        "timeout_sec": 5,
    })
    assert result["returncode"] == 0
    assert result["stdout"].strip() == "EOF"


def test_subprocess_runner_recovers_bridge_owned_last_message_when_stdout_is_empty():
    import sys
    from TAKY2.bridges import subprocess_runner

    with tempfile.TemporaryDirectory(prefix="TAKY2_LAST_MESSAGE_TEST_") as root:
        final_path = Path(root) / "codex-last-message.txt"
        result = subprocess_runner({
            "argv": [
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; import sys; "
                    "Path(sys.argv[1]).write_text('VERDICT: PASS\\n', encoding='utf-8')"
                ),
                str(final_path),
            ],
            "cwd": root,
            "_bridge_last_message_path": str(final_path),
            "timeout_sec": 5,
        })
        assert result["returncode"] == 0
        assert result["stdout"] == "VERDICT: PASS\n"


def test_subprocess_runner_rejects_last_message_path_outside_bridge_cwd():
    import pytest
    import sys
    from TAKY2.bridges import BridgeViolation, subprocess_runner

    with tempfile.TemporaryDirectory(prefix="TAKY2_LAST_MESSAGE_ROOT_") as root:
        outside = str(Path(root).parent / "outside-verdict.txt")
        with pytest.raises(BridgeViolation, match="must stay inside cwd"):
            subprocess_runner({
                "argv": [sys.executable, "-c", "pass"],
                "cwd": root,
                "_bridge_last_message_path": outside,
                "timeout_sec": 5,
            })


def test_subprocess_runner_times_out_noninteractive_hang_instead_of_waiting_forever():
    import sys
    from TAKY2.bridges import subprocess_runner

    result = subprocess_runner({
        "argv": [sys.executable, "-c", "import time; time.sleep(5)"],
        "timeout_sec": 0.1,
    })
    assert result["returncode"] == 124
    assert result["timed_out"] is True
    assert result["outcome_unknown"] is True
    assert result["timeout_sec"] == 0.1
    assert "TAKY_NONINTERACTIVE_TIMEOUT" in result["stderr"]


def test_subprocess_runner_rejects_invalid_noninteractive_timeout():
    import pytest
    from TAKY2.bridges import BridgeViolation, subprocess_runner

    with pytest.raises(BridgeViolation, match="timeout_sec"):
        subprocess_runner({"argv": ["dummy"], "timeout_sec": 0})
    with pytest.raises(BridgeViolation, match="timeout_sec"):
        subprocess_runner({"argv": ["dummy"], "timeout_sec": 301})
