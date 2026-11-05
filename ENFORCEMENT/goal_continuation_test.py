"""Tests the existing TAKY entrypoint's bounded goal-continuation path.

No model, Reason, provider, network, API, Git mutation or deployment.
"""
import contextlib
import io
import json
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
import unittest
from runtime_orchestrator import main, summarize_goal_continuation

ROOT = Path(__file__).resolve().parents[1]


class GoalContinuationTests(unittest.TestCase):
    def setUp(self):
        folder = ROOT / ".local"
        folder.mkdir(exist_ok=True)
        import hashlib
        token = uuid4().hex
        self.record = folder / f"test-auto-goal-record-{token}.json"
        self.handoff = folder / f"test-auto-goal-handoff-{token}.json"
        record = {"task_id": "toy-intent-" + token, "policy": "preserve"}
        prepared = {"status": "PREPARED_NOT_DISPATCHED"}
        self.record.write_text(json.dumps(record), encoding="utf-8")
        self.handoff.write_text(json.dumps({"prepared": prepared}), encoding="utf-8")
        material = json.dumps({"task_id": record["task_id"], "record": record,
                               "prepared": prepared}, ensure_ascii=False,
                              sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
        self.claim = folder / ("taky-goal-claim-" + digest + ".json")
        self.receipts = []
        self.addCleanup(self.cleanup)

    def cleanup(self):
        for p in [self.record, self.handoff, self.claim, *self.receipts]:
            p.unlink(missing_ok=True)

    def drive(self, sample, extra=()):
        buffer = io.StringIO()
        argv = ["--repo-root", str(ROOT), "--record", str(self.record),
                "--prepared-handoff", str(self.handoff),
                "--auto-continue", *extra]
        with patch("runtime_orchestrator.run_guided_steering_cycle", return_value=sample) as runner:
            with contextlib.redirect_stdout(buffer):
                ret = main(argv)
        output = json.loads(buffer.getvalue())
        receipt = ROOT / output["local_cycle_receipt"]
        self.receipts.append(receipt)
        return ret, runner, output, json.loads(receipt.read_text(encoding="utf-8"))

    def test_successfully_runs_three_stages_and_reports_only_once(self):
        sample = {
            "status": "GUIDED_REDIRECT_PROPOSED_NOT_APPLIED",
            "claude_receipt": {"status": "CLI_OUTPUT_RECEIVED_UNREVIEWED"},
            "codex_receipt": {"status": "CODEX_TEXT_RECEIVED_UNVERIFIED"},
            "f1_followup_execution": {
                "status": "READ_ONLY_EXECUTED_WITH_EVIDENCE",
                "next_task": {"next_role": "CLAUDE_CODE",
                              "action_code": "FIX_LOCAL_F1_PROBE_FAILURE"}},
            "user_goal_complete": False,
        }
        ret,runner,out,stored = self.drive(sample)
        self.assertEqual(ret, 0)
        self.assertEqual(runner.call_count, 1)
        self.assertTrue(runner.call_args.kwargs["execute_f1_followup"])
        self.assertEqual(out["controller_state"], "CONTINUE_INTERNAL")
        self.assertEqual(out["next_role"], "CLAUDE_CODE")
        self.assertEqual(out["objective_status"], "NOT_VERIFIED_DONE")
        self.assertFalse(out["user_facing_progress_report_required"])
        self.assertEqual(stored["goal_continuation"]["next_action"], "FIX_LOCAL_F1_PROBE_FAILURE")
        self.assertIn("claude_receipt", stored)
        self.assertNotIn("claude_receipt", out)

    def test_provider_unavailable_stops_without_second_model_call(self):
        ret,runner,out,_ = self.drive({
            "status": "CLAUDE_EXECUTION_NOT_AVAILABLE",
            "claude_receipt": {"status": "CLAUDE_SESSION_LIMIT"},
            "codex_receipt": None, "user_goal_complete": False,
        })
        self.assertEqual(ret, 1)
        self.assertEqual(runner.call_count, 1)
        self.assertEqual(out["controller_state"], "RECOVER_EXECUTOR_INTERNAL")
        self.assertIsNone(out["codex_observed"])
        self.assertFalse(out["user_decision_required"])

    def test_review_unavailable_routes_to_internal_evidence(self):
        result = summarize_goal_continuation({
            "status": "INDEPENDENT_REVIEW_NOT_AVAILABLE",
            "codex_receipt": {"status": "CLI_TIMEOUT_OUTCOME_UNKNOWN"},
        })
        self.assertEqual(result["controller_state"], "RECOVER_VERIFIER_INTERNAL")
        self.assertTrue(result["no_retry_without_material_delta"])

    def test_model_claim_cannot_promote_done(self):
        result = summarize_goal_continuation({
            "status": "GUIDED_REDIRECT_PROPOSED_NOT_APPLIED",
            "claude_receipt": {"status": "PASS"},
            "codex_receipt": {"status": "PASS"},
            "user_goal_complete": True,
            "f1_followup_execution": {"status": "READ_ONLY_EXECUTED_WITH_EVIDENCE"}
        })
        self.assertEqual(result["objective_status"], "NOT_VERIFIED_DONE")
        self.assertTrue(result["evidence_only"])

    def test_replay_reuses_receipt_without_recalling_models(self):
        sample = {"status": "GUIDED_REDIRECT_PROPOSED_NOT_APPLIED",
                  "claude_receipt": {"status": "CLI_OUTPUT_RECEIVED_UNREVIEWED"},
                  "codex_receipt": {"status": "CODEX_TEXT_RECEIVED_UNVERIFIED"},
                  "user_goal_complete": False}
        first, runner, initial, _ = self.drive(sample)
        self.assertEqual(first, 0)
        self.assertEqual(runner.call_count, 1)
        self.assertTrue(self.claim.exists())
        output = io.StringIO()
        with patch("runtime_orchestrator.run_guided_steering_cycle",
                   side_effect=AssertionError("duplicate provider call")):
            with contextlib.redirect_stdout(output):
                code = main(["--repo-root", str(ROOT), "--record", str(self.record),
                             "--prepared-handoff", str(self.handoff),
                             "--auto-continue"])
        replay = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertTrue(replay["reused_verified_cycle"])
        self.assertEqual(replay["local_cycle_receipt"], initial["local_cycle_receipt"])
        self.assertEqual(replay["objective_status"], "NOT_VERIFIED_DONE")

    def test_interrupted_claim_recovers_saved_cycle_without_model_call(self):
        sample = {"schema": "TAKY_BORDER_COLLIE_GUIDED_CYCLE_V1",
                  "status": "GUIDED_REDIRECT_PROPOSED_NOT_APPLIED",
                  "claude_receipt": {"status": "CLI_OUTPUT_RECEIVED_UNREVIEWED"},
                  "codex_receipt": {"status": "CODEX_TEXT_RECEIVED_UNVERIFIED"}}
        first, runner, previous, _ = self.drive(sample)
        self.assertEqual(first, 0)
        claim = json.loads(self.claim.read_text(encoding="utf-8"))
        self.assertEqual(claim["state"], "RECEIPT_RECORDED")
        claim["state"] = "CLAIMED_OUTCOME_UNKNOWN"
        claim.pop("local_cycle_receipt", None)
        claim.pop("receipt_sha256", None)
        self.claim.write_text(json.dumps(claim), encoding="utf-8")
        output = io.StringIO()
        with patch("runtime_orchestrator.run_guided_steering_cycle",
                   side_effect=AssertionError("must recover, not invoke models")):
            with contextlib.redirect_stdout(output):
                code = main(["--repo-root", str(ROOT), "--record", str(self.record),
                             "--prepared-handoff", str(self.handoff),
                             "--auto-continue"])
        recovered = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertTrue(recovered["reused_verified_cycle"])
        self.assertEqual(recovered["local_cycle_receipt"],
                         previous["local_cycle_receipt"])
        self.assertEqual(json.loads(self.claim.read_text(encoding="utf-8"))["state"],
                         "RECEIPT_RECORDED")

    def test_tampered_orphan_never_replays_model(self):
        sample = {"schema": "TAKY_BORDER_COLLIE_GUIDED_CYCLE_V1",
                  "status": "GUIDED_REDIRECT_PROPOSED_NOT_APPLIED"}
        self.drive(sample)
        claim = json.loads(self.claim.read_text(encoding="utf-8"))
        claim["state"] = "CLAIMED_OUTCOME_UNKNOWN"
        self.claim.write_text(json.dumps(claim), encoding="utf-8")
        source = json.loads(self.receipts[0].read_text(encoding="utf-8"))
        source["goal_claim_binding_sha256"] = "0"*64
        self.receipts[0].write_text(json.dumps(source), encoding="utf-8")
        output = io.StringIO()
        with patch("runtime_orchestrator.run_guided_steering_cycle",
                   side_effect=AssertionError("tampered receipt cannot re-execute")):
            with contextlib.redirect_stdout(output):
                code = main(["--repo-root", str(ROOT), "--record", str(self.record),
                             "--prepared-handoff", str(self.handoff),
                             "--auto-continue"])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())["controller_state"],
                         "OUTCOME_UNKNOWN_RECONCILE")

    def test_pending_claim_never_automatically_retries(self):
        self.claim.write_text(json.dumps({"state":"CLAIMED_OUTCOME_UNKNOWN"}),
                              encoding="utf-8")
        output = io.StringIO()
        with patch("runtime_orchestrator.run_guided_steering_cycle",
                   side_effect=AssertionError("unknown attempt must not repeat")):
            with contextlib.redirect_stdout(output):
                code = main(["--repo-root", str(ROOT), "--record", str(self.record),
                             "--prepared-handoff", str(self.handoff),
                             "--auto-continue"])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())["controller_state"],
                         "OUTCOME_UNKNOWN_RECONCILE")

    def test_tampered_receipt_halts_without_reexecution(self):
        sample = {"status": "GUIDED_REDIRECT_PROPOSED_NOT_APPLIED",
                  "claude_receipt": {"status": "CLI_OUTPUT_RECEIVED_UNREVIEWED"},
                  "codex_receipt": {"status": "CODEX_TEXT_RECEIVED_UNVERIFIED"}}
        self.drive(sample)
        self.receipts[0].write_text(self.receipts[0].read_text(encoding="utf-8")
                                    + "\n", encoding="utf-8")
        output = io.StringIO()
        with patch("runtime_orchestrator.run_guided_steering_cycle",
                   side_effect=AssertionError("tampered receipt must not retry")):
            with contextlib.redirect_stdout(output):
                code = main(["--repo-root", str(ROOT), "--record", str(self.record),
                             "--prepared-handoff", str(self.handoff),
                             "--auto-continue"])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())["controller_state"],
                         "OUTCOME_UNKNOWN_RECONCILE")

    def test_only_machine_readable_protected_gate_prompts_user(self):
        sample = {"status": "GUIDED_REVIEW_NEEDS_ADDITIONAL_EVIDENCE",
                  "post_review_continuation": {
                      "next_task": {"action_code":"PAID_PROVIDER_HANDOFF",
                                    "next_role":"TAKY_ORCHESTRATOR",
                                    "decision_gate":"PAID_API"}}}
        ret, runner, output, _ = self.drive(sample)
        self.assertEqual(ret, 1)
        self.assertEqual(runner.call_count, 1)
        self.assertEqual(output["controller_state"], "USER_DECISION_REQUIRED")
        self.assertTrue(output["user_decision_required"])
        self.assertTrue(output["user_facing_progress_report_required"])

    def test_incompatible_mode_rejected_before_any_provider(self):
        with patch("runtime_orchestrator.run_guided_steering_cycle") as runner:
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as exc:
                    main(["--auto-continue", "--continue-post-review"])
        self.assertEqual(exc.exception.code, 2)
        runner.assert_not_called()


if __name__ == "__main__":
    unittest.main()
