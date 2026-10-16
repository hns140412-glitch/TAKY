#!/usr/bin/env python3
import unittest
from TAKY_GOVERNED_ROUTE_HEALTH import route_health, ALLOWED_REPOS
from TAKY_TRUSTED_KERNEL_IMPORT import ensure_trusted_taky2
ensure_trusted_taky2()
from TAKY2.orchestrator import _execution_identity
from TAKY2.enforcement import record_failure

REPO = r"D:\Git PWA\TAKY"
ACTION = {"execution_scope": "codex-verifier-review"}


def prepared():
    return {"action_registry": {"verify:codex-packet": ACTION}}, {
        "active_attempts": {}, "execution_calls": {}, "route_ledgers": {}
    }


class GateHealthTest(unittest.TestCase):
    def test_clean_signed_route_ready(self):
        authority, runtime = prepared()
        result = route_health("Codex", REPO, authority, runtime)
        self.assertEqual(result["status"], "READY_FOR_EXISTING_COST_AND_APPROVAL_GATES")
        self.assertFalse(result["modelCallConfirmed"])

    def test_pending_owned_route_blocks_before_any_call(self):
        authority, runtime = prepared()
        _, _, key = _execution_identity(ACTION, {"target": REPO, "method_or_tool": "codex"})
        runtime["active_attempts"][key] = {
            "status": "PENDING", "receipt_id": "pf:old-id", "task_id": "old"}
        r = route_health("Codex", REPO, authority, runtime)
        self.assertEqual(r["reason"], "UNRESOLVED_GOVERNED_EXECUTION")

    def test_signed_returned_call_does_not_falsely_block(self):
        authority, runtime = prepared()
        _, _, key = _execution_identity(ACTION, {"target": REPO, "method_or_tool": "codex"})
        runtime["active_attempts"][key] = {"status": "PENDING", "receipt_id": "pf:returned"}
        runtime["execution_calls"]["pf:returned"] = {"status": "RETURNED"}
        self.assertEqual(route_health("Codex", REPO, authority, runtime)["status"],
                         "READY_FOR_EXISTING_COST_AND_APPROVAL_GATES")

    def test_same_failed_route_stays_blocked(self):
        authority, runtime = prepared()
        attempt = {"target": REPO, "method_or_tool": "codex"}
        ledger = {"route_budget": 3, "seen_routes": [], "failed_signatures": [],
                  "transient_failures": {}, "last_failure_by_route": {}}
        runtime["route_ledgers"]["codex-verifier-review"] = record_failure(
            ledger, attempt, "ENVIRONMENT")
        self.assertEqual(route_health("Codex", REPO, authority, runtime)["reason"],
                         "ROUTE_GATE_BLOCKED")

    def test_stale_ephemeral_failure_does_not_mask_real_codex_route(self):
        authority, runtime = prepared()
        attempt = {"target": REPO, "method_or_tool": "codex-ephemeral"}
        ledger = {"route_budget": 3, "seen_routes": [], "failed_signatures": [],
                  "transient_failures": {}, "last_failure_by_route": {}}
        runtime["route_ledgers"]["codex-verifier-review"] = record_failure(
            ledger, attempt, "ENVIRONMENT")
        self.assertEqual(route_health("Codex", REPO, authority, runtime)["status"],
                         "READY_FOR_EXISTING_COST_AND_APPROVAL_GATES")

    def test_unknown_authority_holds(self):
        self.assertEqual(route_health("Codex", REPO, {}, {})["reason"],
                         "TRUSTED_ACTION_MISSING")

    def test_other_repository_holds(self):
        authority, runtime = prepared()
        self.assertEqual(route_health("Codex", r"C:\Temp", authority, runtime)["status"], "HOLD")

    def test_no_trusted_scope_holds(self):
        authority, runtime = prepared()
        authority["action_registry"]["verify:codex-packet"] = {}
        self.assertEqual(route_health("Codex", REPO, authority, runtime)["reason"],
                         "NO_TRUSTED_EXECUTION_SCOPE")


if __name__ == "__main__":
    unittest.main()
