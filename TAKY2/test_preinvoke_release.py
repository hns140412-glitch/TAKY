"""Pre-execution release tests. All data synthetic; no model or runtime write."""
import unittest
from TAKY2.orchestrator import preflight, persist_preflight, release_uninvoked_preflight
from TAKY2.test_orchestrator import plan, runtime_state
from TAKY2.test_enforcement import trusted
from TAKY2.bridges import BridgeViolation, claim_execution_receipt


def fixture():
    before = preflight(plan(task_id="release-fixture"), trusted())
    assert before["allowed"]
    return before, persist_preflight(runtime_state(), before)


class ReleaseTests(unittest.TestCase):
    def test_no_call_release_preserves_ledger(self):
        p, r = fixture()
        rid = p["receipt_id"]
        scope = p["execution_scope"]
        r["route_ledgers"][scope]["failed_signatures"].append("older-failure")
        released = release_uninvoked_preflight(
            r, rid, reason="LOCAL_RESOURCE_GUARD_BEFORE_CLAIM")
        self.assertEqual(released["execution_outcomes"][rid], "PREINVOKE_RELEASED")
        self.assertNotIn(p["execution_key"], released["active_attempts"])
        self.assertTrue(released["preflight_receipts"][rid]["consumed"])
        self.assertIn("older-failure", released["route_ledgers"][scope]["failed_signatures"])
        self.assertEqual(r["route_ledgers"], released["route_ledgers"])
        self.assertFalse(r["preflight_receipts"][rid]["consumed"])
        self.assertTrue(released["preinvoke_releases"][rid]["no_execution_claim_at_release"])

    def test_claimed_receipt_cannot_be_released(self):
        p, r = fixture()
        r["execution_calls"] = {p["receipt_id"]: {"status": "CLAIMED"}}
        with self.assertRaisesRegex(ValueError, "execution call"):
            release_uninvoked_preflight(r, p["receipt_id"], reason="WRAPPER_INTERRUPTED_BEFORE_CLAIM")

    def test_release_and_claim_are_mutually_exclusive(self):
        p, runtime = fixture()
        rid = p["receipt_id"]
        claimed, _ = claim_execution_receipt(runtime, rid, executor_id="fixture-executor")
        with self.assertRaises(ValueError):
            release_uninvoked_preflight(
                claimed, rid, reason="WRAPPER_INTERRUPTED_BEFORE_CLAIM")
        released = release_uninvoked_preflight(
            runtime, rid, reason="WRAPPER_INTERRUPTED_BEFORE_CLAIM")
        with self.assertRaises(BridgeViolation):
            claim_execution_receipt(released, rid, executor_id="fixture-executor")

    def test_calling_cannot_be_released(self):
        p, r = fixture()
        r["active_attempts"][p["execution_key"]]["status"] = "CALLING"
        with self.assertRaises(ValueError):
            release_uninvoked_preflight(r, p["receipt_id"], reason="WRAPPER_INTERRUPTED_BEFORE_CLAIM")

    def test_unknown_outcome_cannot_be_released(self):
        p, r = fixture()
        r["active_attempts"][p["execution_key"]]["status"] = "OUTCOME_UNKNOWN"
        with self.assertRaises(ValueError):
            release_uninvoked_preflight(r, p["receipt_id"], reason="WRAPPER_INTERRUPTED_BEFORE_CLAIM")

    def test_existing_outcome_or_completion_block_release(self):
        p, r = fixture()
        r["execution_outcomes"][p["receipt_id"]] = "FAILED"
        with self.assertRaises(ValueError):
            release_uninvoked_preflight(r, p["receipt_id"], reason="ABANDONED_PRECHECK_BEFORE_CLAIM")
        p, r = fixture()
        r["completion_registry"][p["receipt_id"]] = {}
        with self.assertRaises(ValueError):
            release_uninvoked_preflight(r, p["receipt_id"], reason="ABANDONED_PRECHECK_BEFORE_CLAIM")

    def test_scope_and_route_binding_fail_closed(self):
        p, r = fixture()
        r["active_attempts"][p["execution_key"]]["execution_scope"] = "wrong"
        with self.assertRaises(ValueError):
            release_uninvoked_preflight(r, p["receipt_id"], reason="WRAPPER_INTERRUPTED_BEFORE_CLAIM")
        p, r = fixture()
        r["active_attempts"][p["execution_key"]]["route_fp"] = "wrong"
        with self.assertRaises(ValueError):
            release_uninvoked_preflight(r, p["receipt_id"], reason="WRAPPER_INTERRUPTED_BEFORE_CLAIM")

    def test_cannot_repeat_or_invent_reason(self):
        p, r = fixture()
        with self.assertRaises(ValueError):
            release_uninvoked_preflight(r, p["receipt_id"], reason="SUCCESS")
        released = release_uninvoked_preflight(r, p["receipt_id"], reason="WRAPPER_INTERRUPTED_BEFORE_CLAIM")
        with self.assertRaises(ValueError):
            release_uninvoked_preflight(released, p["receipt_id"], reason="WRAPPER_INTERRUPTED_BEFORE_CLAIM")


if __name__ == "__main__":
    unittest.main()
