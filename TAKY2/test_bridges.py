import json
from pathlib import Path
import tempfile
import unittest

from TAKY2.bridges import (
    BridgeViolation,
    bind_account_attestation,
    execute_with_receipt,
    record_user_confirmation,
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
from TAKY2.test_enforcement import trusted
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
            "source": "oauth-session",
            "evidence_ref": "auth:e1",
            "session_id": "session-1",
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
        runtime = bind_account_attestation(
            runtime_state(),
            trusted(),
            self.evidence(),
            verifier=lambda evidence: evidence["authenticated"] is True,
            verifier_id="auth-bridge",
        )
        attestation = runtime["runtime"]["account_attestation"]
        self.assertTrue(attestation["verified"])
        self.assertEqual(attestation["account"], "HNS")
        self.assertEqual(attestation["verified_by"], "auth-bridge")


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
                "source": "oauth-session",
                "evidence_ref": "auth:e1",
                "session_id": "session-1",
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

        runtime = verify_execution(
            runtime,
            rid,
            verifier=lambda call, receipt: {
                "passed": call["result"]["returncode"] == 0,
                "evidence_ref": "ev:e2e",
                "evidence_type": "runtime_test",
                "key_match": True,
                "required_verifications": ["technical", "intent"],
                "passed_verifications": ["technical", "intent"],
                "critical_gaps": [],
            },
            verifier_id="verifier-1",
        )

        delivered = finalize(
            {"preflight_receipt": rid, "evidence_refs": ["ev:e2e"]},
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
            {"preflight_receipt": rid, "evidence_refs": ["ev:e2e"]},
            overlay_runtime(base, runtime),
        )
        self.assertTrue(confirmed["allowed"])
        self.assertEqual(confirmed["state"], "USER_CONFIRMED")


class AuthorityRebindTests(unittest.TestCase):
    def make_state(self):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        old_authority = {"key": {"generation": 1}}
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


if __name__ == "__main__":
    unittest.main()
