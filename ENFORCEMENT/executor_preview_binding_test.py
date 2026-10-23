#!/usr/bin/env python3
"""Regression: executor return cannot bypass revision-bound visual proof."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from codex_task_contract_builder import build
from codex_task_contract_validator import validate
from executor_review_loop import review
from result_preview_gate import validate_preview


def sha(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class PreviewBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "src").mkdir()
        self.html = self.root / "src" / "view.html"
        self.html.write_text("<main>Home</main>", encoding="utf-8")
        self.witness = self.root / "mobile.png"
        self.witness.write_bytes(b"\x89PNG\r\n\x1a\n" + b"local-browser-witness")
        self.task = {
            "task_id": "TAKY-UI-1",
            "change_scope": {"allowed": ["src/view.html"]},
            "acceptance_tests": [],
            "validation": {"required": [], "artifact_kind": "ui", "result_preview_required": True},
            "human_approval": {"merge_required": False},
        }
        preview = {
            "preview_version": "1.0",
            "task_id": "TAKY-UI-1",
            "preview_required": True,
            "result_path": "src/view.html",
            "result_revision_hash": sha(self.html),
            "preview_surface": "local-browser",
            "preview_evidence": [{
                "evidence_path": "mobile.png",
                "evidence_sha256": sha(self.witness),
            }],
            "acceptance_result": "PASS",
            "acceptance_method": "RUNTIME_VALIDATION",
            "reviewer_ref": "local-verifier",
        }
        self.report = {
            "task_id": "TAKY-UI-1",
            "changed_files": ["src/view.html"],
            "commit_ref": "local-only-unmerged",
            "result_preview": validate_preview(preview, self.root),
        }

    def run_review(self):
        return review(self.task, self.report, self.root)

    def codes(self):
        return [d["code"] for d in self.run_review()["defects"]]

    def test_verified_artifact_stops_at_human_approval_never_merged(self):
        result = self.run_review()
        self.assertTrue(result["pass"], result["defects"])
        self.assertEqual(result["review_decision"], "HUMAN_APPROVAL")
        self.assertIn("revision_bound_preview", [x["kind"] for x in result["evidence"]])

    def test_unverified_pass_text_is_not_evidence(self):
        self.report["result_preview"] = {"acceptance_result": "PASS"}
        self.assertIn("RESULT_PREVIEW_NOT_VERIFIED", self.codes())

    def test_missing_receipt_is_rework(self):
        self.report.pop("result_preview")
        self.assertIn("RESULT_PREVIEW_EVIDENCE_MISSING", self.codes())

    def test_tampered_file_fails_even_with_pass_receipt(self):
        self.html.write_text("<main>Old UI</main>", encoding="utf-8")
        self.assertIn("RESULT_PREVIEW_NOT_VERIFIED", self.codes())

    def test_wrong_task_id_cannot_reuse_receipt(self):
        self.report["result_preview"]["task_id"] = "OTHER"
        self.assertIn("RESULT_PREVIEW_RECEIPT_BINDING_MISMATCH", self.codes())

    def test_unapproved_change_scope_cannot_claim_completion(self):
        self.task["change_scope"]["allowed"] = ["src/unrelated.html"]
        self.assertIn("RESULT_PREVIEW_OUTSIDE_CHANGE_SCOPE", self.codes())

    def test_builder_auto_enforces_preview_for_ui_or_mobile(self):
        record = {
            "task_id": "TAKY-UI-1", "project": "Hide",
            "repository": "local", "base_branch": "main",
            "verified_base_head": "abc", "allowed_change_scope": ["src/view.html"],
            "acceptance_tests": ["Chrome renders"],
            "working_model": {"primary_outcome": "Browser UI works", "protected_state": []},
            "artifact_kind": "ui",
        }
        built = build(record)
        self.assertTrue(built["pass"], built["detected"])
        self.assertTrue(built["task_contract"]["validation"]["result_preview_required"])
        broken = copy.deepcopy(built["task_contract"])
        broken["validation"]["result_preview_required"] = False
        self.assertIn("RESULT_PREVIEW_GATE_REQUIRED", validate(broken))
        mobile = {**record, "artifact_kind": "code", "mobile_runtime_required": True}
        self.assertTrue(build(mobile)["task_contract"]["validation"]["result_preview_required"])

    def make_executor_return(self):
        from executor_transport import build_envelope
        envelope = build_envelope(self.task)["dispatch_envelope"]
        result = {
            "task_id": self.task["task_id"],
            "task_contract_sha256": envelope["task_contract_sha256"],
            "provider": "CODEX",
            "completion_report": self.report,
        }
        return envelope, result

    def test_real_envelope_ingest_review_transition_stops_before_merge(self):
        from executor_cycle import run
        envelope, reply = self.make_executor_return()
        outcome = run(envelope, reply, self.root)
        self.assertTrue(outcome["pass"], outcome)
        self.assertEqual(outcome["stage"], "REVIEW_COMPLETE")
        self.assertEqual(outcome["transition"]["current_state"], "HUMAN_APPROVAL")
        self.assertEqual(outcome["next_action"], "AWAIT_HUMAN_APPROVAL")
        self.assertFalse(outcome["external_executor_invocation_verified"])

    def test_independent_evidence_hold_is_not_misreported_as_rework(self):
        from unittest.mock import patch
        from executor_cycle import run
        envelope, reply = self.make_executor_return()
        pending = {
            "pass": False, "review_decision": "HOLD",
            "state_transition": {"current_state": "TAKY_REVIEW", "requested_state": "TAKY_REVIEW"},
            "defects": [], "holds": [{"code": "REVIEWER_IDENTITY_UNAUTHENTICATED"}],
            "acceptance_delta": [], "evidence": []
        }
        with patch("executor_cycle.review", return_value=pending), \
             patch("executor_cycle.transition") as transition_mock:
            outcome = run(envelope, reply, self.root)
            transition_mock.assert_not_called()
        self.assertFalse(outcome["pass"])
        self.assertEqual(outcome["stage"], "REVIEW_HOLD")
        self.assertIsNone(outcome["transition"])
        self.assertEqual(outcome["next_action"], "RECOVER_INDEPENDENT_EVIDENCE")
        self.assertFalse(outcome["recovery_plan"]["stop_entire_task"])
        self.assertEqual(outcome["recovery_plan"]["next_owner"], "ORCHESTRATOR")

    def test_tamper_flows_to_rework_in_full_executor_cycle(self):
        from executor_cycle import run
        envelope, reply = self.make_executor_return()
        self.witness.write_bytes(b"tampered screenshot")
        outcome = run(envelope, reply, self.root)
        self.assertFalse(outcome["pass"])
        self.assertEqual(outcome["review"]["review_decision"], "REWORK")
        self.assertEqual(outcome["transition"]["current_state"], "REWORK")
        self.assertEqual(outcome["next_action"], "RETURN_REWORK_TO_EXECUTOR")
        plan = outcome["recovery_plan"]
        self.assertFalse(plan["stop_entire_task"])
        self.assertFalse(plan["same_condition_blind_retry"])
        self.assertEqual(plan["routes"][0]["route"], "LOCAL_RESULT_INSPECTION")
        self.assertIn("browser", plan["routes"][0]["action"])

    def test_rework_preserves_scope_boundary_but_guides_alternative(self):
        from executor_cycle import run
        self.report["changed_files"] = ["private/unapproved.js"]
        envelope, reply = self.make_executor_return()
        outcome = run(envelope, reply, self.root)
        self.assertFalse(outcome["pass"])
        self.assertTrue(outcome["recovery_plan"]["approval_boundary"])
        self.assertFalse(outcome["recovery_plan"]["stop_entire_task"])
        self.assertIn("PRESERVE_AND_RECONCILE_SCOPE", [x["route"] for x in outcome["recovery_plan"]["routes"]])

    def test_ingest_mismatch_recovers_envelope_instead_of_declaring_goal_failed(self):
        from executor_cycle import run
        envelope, reply = self.make_executor_return()
        reply["task_contract_sha256"] = "wrong"
        outcome = run(envelope, reply, self.root)
        self.assertEqual(outcome["stage"], "INGEST")
        self.assertEqual(outcome["recovery_plan"]["current_route_state"], "INTEGRITY_RECONCILIATION_REQUIRED")
        self.assertFalse(outcome["recovery_plan"]["stop_entire_task"])

    def test_queue_consumer_routes_unverified_ui_result_to_rework(self):
        import json
        from executor_transport import build_envelope
        from github_issue_executor_queue import issue_payload, BEGIN_RESULT, END_RESULT
        from github_queue_consumer import consume
        env = build_envelope(self.task, transport="GITHUB_ISSUE_QUEUE")["dispatch_envelope"]
        payload = issue_payload(env)["issue"]
        incomplete = {**self.report, "result_preview": {"acceptance_result": "PASS"}}
        result = {
            "task_id": self.task["task_id"],
            "provider": "CODEX",
            "task_contract_sha256": env["task_contract_sha256"],
            "completion_report": incomplete,
        }
        event = {
            "_event_name": "issue_comment",
            "issue": payload,
            "comment": {
                "body": BEGIN_RESULT + "\n" + json.dumps(result) + "\n" + END_RESULT,
                "author": {"login": "github-actions[bot]"},
            },
        }
        out = consume(event)
        self.assertEqual(out["action"], "RESULT_TO_REWORK")
        self.assertIn("LOCAL_RESULT_INSPECTION", out["comment"])
        self.assertIn('"goal_complete": false', out["comment"])
        self.assertIn('"validated_result_pass": false', out["comment"])

    def test_queue_distinguishes_review_hold_from_rework_or_success(self):
        import json
        from unittest.mock import patch
        from executor_transport import build_envelope
        from github_issue_executor_queue import issue_payload, BEGIN_RESULT, END_RESULT
        from github_queue_consumer import consume
        env = build_envelope(self.task, transport="GITHUB_ISSUE_QUEUE")["dispatch_envelope"]
        result = {
            "task_id": self.task["task_id"],
            "provider": "CODEX",
            "task_contract_sha256": env["task_contract_sha256"],
            "completion_report": self.report,
        }
        event = {
            "_event_name": "issue_comment",
            "issue": issue_payload(env)["issue"],
            "comment": {"body": BEGIN_RESULT + "\n" + json.dumps(result) + "\n" + END_RESULT,
                        "author": {"login": "github-actions[bot]"}},
        }
        hold = {"pass": False, "review": {"review_decision": "HOLD"},
                "next_action": "RECOVER_INDEPENDENT_EVIDENCE",
                "detected": [{"code": "REVIEWER_IDENTITY_UNAUTHENTICATED"}],
                "transition": None, "recovery_plan": {"stop_entire_task": False}}
        with patch("github_queue_consumer.run_executor_cycle", return_value=hold):
            out = consume(event)
        self.assertEqual(out["action"], "RESULT_REVIEW_HOLD")
        self.assertTrue(out["pass"])  # The queue message is routed, not the task approved.
        self.assertIn('"validated_result_pass": false', out["comment"])
        self.assertIn('"goal_complete": false', out["comment"])
        self.assertIn("RECOVER_INDEPENDENT_EVIDENCE", out["comment"])

    def test_cli_returns_failure_when_report_needs_rework(self):
        import contextlib
        import io
        import json
        import sys
        from unittest.mock import patch
        from executor_cycle import main
        envelope, reply = self.make_executor_return()
        env = self.root / "envelope.json"
        result_file = self.root / "result.json"
        env.write_text(json.dumps(envelope), encoding="utf-8")
        result_file.write_text(json.dumps(reply), encoding="utf-8")
        argv = ["executor_cycle", "--envelope", str(env), "--result", str(result_file), "--root", str(self.root)]
        with patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(), 0)
        self.html.write_text("changed after verification", encoding="utf-8")
        with patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
            self.assertNotEqual(main(), 0)


if __name__ == "__main__":
    unittest.main()
