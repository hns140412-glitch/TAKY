"""Bounded TAKY queue acceptance; fake dispatch, no model or deployment."""
import contextlib
import io
import json
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
import unittest
from runtime_orchestrator import run_bounded_goal_queue, main

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local"


class GoalQueueTests(unittest.TestCase):
    def setUp(self):
        self.marker = uuid4().hex
        self.paths = []
        self.items = [self.create_item(1), self.create_item(2)]
        self.manifest = self.write_json("manifest", {
            "schema": "TAKY_GOAL_QUEUE_V1", "queue_id": "acceptance-" + self.marker,
            "items": self.items})
        self.addCleanup(self.cleanup)

    def write_json(self, label, value):
        LOCAL.mkdir(exist_ok=True)
        path = LOCAL / f"test-goal-queue-{self.marker}-{label}.json"
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        self.paths.append(path)
        return path

    def create_item(self, n):
        task = f"acceptance-{self.marker}-{n}"
        record = self.write_json(f"record-{n}", {"task_id": task})
        handoff = self.write_json(f"handoff-{n}",
                                  {"prepared": {"status": "PREPARED_NOT_DISPATCHED"}})
        return {"task_id": task,
                "record": ".local/" + record.name,
                "prepared_handoff": ".local/" + handoff.name,
                "independent": True}

    def cleanup(self):
        for path in self.paths:
            path.unlink(missing_ok=True)

    def execute(self, outputs):
        calls = []
        def fake(argv):
            calls.append(argv)
            item = dict(outputs[len(calls)-1])
            item.setdefault("user_decision_required", False)
            item.setdefault("schema", "TAKY_GOAL_CONTINUATION_DECISION_V1")
            path = self.write_json("fake-cycle-"+str(len(calls)), {})
            relative = ".local/" + path.name
            item["local_cycle_receipt"] = relative
            cycle = {"schema": "TAKY_BORDER_COLLIE_GUIDED_CYCLE_V1",
                     "local_cycle_receipt": relative,
                     "goal_continuation": {
                         "schema": "TAKY_GOAL_CONTINUATION_DECISION_V1",
                         "controller_state": item.get("controller_state"),
                         "user_decision_required": item["user_decision_required"]}}
            path.write_text(json.dumps(cycle), encoding="utf-8")
            print(json.dumps(item))
            return 0 if item.get("controller_state") == "CONTINUE_INTERNAL" else 1
        value = run_bounded_goal_queue(self.manifest, ROOT, invoke=fake)
        if "local_queue_receipt" in value:
            path = ROOT / value["local_queue_receipt"]
            self.paths.append(path)
            self.assertTrue(path.is_file())
            on_disk = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(on_disk["items"], value["items"])
        return value,calls

    def test_two_independent_tasks_in_order_without_micro_reports(self):
        status = {"controller_state": "CONTINUE_INTERNAL",
                  "objective_status": "NOT_VERIFIED_DONE",
                  "user_decision_required": False}
        value,calls = self.execute([status,status])
        self.assertEqual(value["status"], "QUEUE_ITEMS_OBSERVED_GOALS_OPEN")
        self.assertEqual(value["items_executed"], 2)
        self.assertEqual([x["task_id"] for x in value["items"]],
                         [x["task_id"] for x in self.items])
        self.assertEqual(value["goals_verified_done"],0)
        self.assertEqual(len(calls),2)
        self.assertTrue(all("--auto-continue" in args for args in calls))

    def test_protected_approval_defers_only_affected_task(self):
        value,calls = self.execute([
            {"controller_state":"USER_DECISION_REQUIRED",
             "user_decision_required":True},
            {"controller_state":"CONTINUE_INTERNAL"}])
        self.assertEqual(value["status"], "QUEUE_PARTIAL_USER_DECISION")
        self.assertEqual(value["items_executed"],2)
        self.assertEqual(value["items_deferred"],1)
        self.assertEqual(value["user_decision_task_ids"],[self.items[0]["task_id"]])
        self.assertEqual(len(calls),2)

    def test_unresolved_executor_continues_unaffected_tasks(self):
        value,calls = self.execute([
            {"controller_state":"RECOVER_EXECUTOR_INTERNAL"},
            {"controller_state":"CONTINUE_INTERNAL"}])
        self.assertEqual(value["status"], "QUEUE_PARTIAL_RECOVERY_DEFERRED")
        self.assertEqual(value["items_deferred"],1)
        self.assertEqual(value["items_executed"],2)
        self.assertEqual(len(calls),2)

    def test_session_limit_trips_provider_circuit_without_busy_retries(self):
        value,calls = self.execute([
            {"controller_state": "RECOVER_EXECUTOR_INTERNAL",
             "claude_observed": "CLAUDE_SESSION_LIMIT"},
        ])
        self.assertEqual(value["status"], "QUEUE_PARTIAL_RECOVERY_DEFERRED")
        self.assertEqual(value["provider_circuit_breaker"],
                         "CLAUDE_CAPACITY_OR_TIMEOUT")
        self.assertEqual(value["items_executed"], 1)
        self.assertEqual(value["items_deferred"], 2)
        self.assertFalse(value["items"][1]["attempted"])
        self.assertEqual(value["items"][1]["controller_state"],
                         "DEFERRED_PROVIDER_UNAVAILABLE")
        self.assertEqual(len(calls), 1)

    def test_model_timeout_trips_same_provider_circuit(self):
        value,calls = self.execute([
            {"controller_state": "RECOVER_EXECUTOR_INTERNAL",
             "claude_observed": "CLI_TIMEOUT_OUTCOME_UNKNOWN"},
        ])
        self.assertEqual(value["items_executed"], 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(value["items_deferred"], 2)
        self.assertEqual(value["items"][0]["next_safe_action"],
                         "INSPECT_EXISTING_RECEIPT_NO_BLIND_RETRY")

    def test_codex_timeout_avoids_waiting_on_same_verifier_repeatedly(self):
        value,calls = self.execute([
            {"controller_state": "RECOVER_VERIFIER_INTERNAL",
             "codex_observed": "CODEX_CLI_TIMEOUT_OUTCOME_UNKNOWN"},
        ])
        self.assertEqual(value["provider_circuit_breaker"],
                         "CODEX_CAPACITY_OR_TIMEOUT")
        self.assertEqual(value["items_deferred"], 2)
        self.assertEqual(value["items_executed"], 1)
        self.assertEqual(len(calls), 1)

    def test_unknown_state_defers_only_one_and_continues_other_task(self):
        value,calls = self.execute([
            {"controller_state": "OUTCOME_UNKNOWN_RECONCILE"},
            {"controller_state": "CONTINUE_INTERNAL"},
        ])
        self.assertEqual(value["items_deferred"], 1)
        self.assertEqual(value["items_executed"], 2)
        self.assertEqual(len(calls), 2)

    def test_unknown_or_nondict_output_fails_closed(self):
        calls=[]
        def fail(_):
            calls.append("once")
            print("[]")
            return 0
        out=run_bounded_goal_queue(self.manifest,ROOT,invoke=fail)
        if out.get("local_queue_receipt"):
            self.paths.append(ROOT / out["local_queue_receipt"])
        self.assertEqual(out["status"],"QUEUE_PARTIAL_RECOVERY_DEFERRED")
        self.assertEqual(out["items_deferred"],2)
        self.assertEqual(calls,["once","once"])

    def test_dependency_requires_done_evidence(self):
        obj=json.loads(self.manifest.read_text(encoding="utf-8"))
        obj["items"][1]["independent"]=False
        self.manifest.write_text(json.dumps(obj), encoding="utf-8")
        value=run_bounded_goal_queue(
            self.manifest,ROOT,invoke=lambda _: self.fail("Must not dispatch"))
        self.assertEqual(value["status"], "QUEUE_DEPENDENCY_REQUIRES_VERIFIED_DONE")
        self.assertEqual(value["items_executed"],0)

    def test_duplicate_task_and_wrong_binding_rejected(self):
        obj=json.loads(self.manifest.read_text(encoding="utf-8"))
        obj["items"][1]["task_id"]=obj["items"][0]["task_id"]
        self.manifest.write_text(json.dumps(obj),encoding="utf-8")
        value=run_bounded_goal_queue(self.manifest,ROOT)
        self.assertEqual(value["status"],"QUEUE_SCHEMA_INVALID")
        obj["items"][1]["task_id"]="different-task"
        self.manifest.write_text(json.dumps(obj),encoding="utf-8")
        value=run_bounded_goal_queue(self.manifest,ROOT)
        self.assertEqual(value["status"],"QUEUE_AUTHORITY_BINDING_MISMATCH")

    def test_path_traversal_and_extra_fields_rejected(self):
        obj=json.loads(self.manifest.read_text(encoding="utf-8"))
        obj["items"][0]["record"]=".local/../CURRENT/secret.json"
        self.manifest.write_text(json.dumps(obj),encoding="utf-8")
        self.assertEqual(run_bounded_goal_queue(self.manifest,ROOT)["status"],
                         "QUEUE_INPUT_UNTRUSTED")
        obj["items"][0]["record"]=self.items[0]["record"]
        obj["items"][0]["command"]="powershell -nop"
        self.manifest.write_text(json.dumps(obj),encoding="utf-8")
        self.assertEqual(run_bounded_goal_queue(self.manifest,ROOT)["status"],
                         "QUEUE_DEPENDENCY_REQUIRES_VERIFIED_DONE")

    def test_real_entrypoint_routes_two_items_via_existing_cycle(self):
        # Model workers are stubbed, but both queue dispatch and real CLI
        # claim/receipt handling execute, not a shadow parallel executor.
        result = {"schema": "TAKY_BORDER_COLLIE_GUIDED_CYCLE_V1",
                  "status": "GUIDED_REDIRECT_PROPOSED_NOT_APPLIED",
                  "claude_receipt": {"status": "CLI_OUTPUT_RECEIVED_UNREVIEWED"},
                  "codex_receipt": {"status": "CODEX_TEXT_RECEIVED_UNVERIFIED"},
                  "user_goal_complete": False}
        output = io.StringIO()
        from unittest.mock import patch
        from runtime_orchestrator import _goal_continuation_claim
        with patch("runtime_orchestrator.run_guided_steering_cycle",
                   return_value=result) as worker:
            with contextlib.redirect_stdout(output):
                code = main(["--repo-root", str(ROOT),
                             "--auto-queue", str(self.manifest)])
        data = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(worker.call_count, 2)
        self.assertEqual(data["status"], "QUEUE_ITEMS_OBSERVED_GOALS_OPEN")
        self.assertEqual(data["items_executed"], 2)
        self.assertEqual(data["goals_verified_done"], 0)
        if data.get("local_queue_receipt"):
            self.paths.append(ROOT / data["local_queue_receipt"])
        import hashlib
        for i, entry in enumerate(self.items):
            self.assertEqual(data["items"][i]["task_id"],entry["task_id"])
            receipt = data["items"][i]["local_cycle_receipt"]
            self.paths.append(ROOT / receipt)
            record = json.loads((ROOT / entry["record"]).read_text(encoding="utf-8"))
            handoff = json.loads((ROOT / entry["prepared_handoff"]).read_text(encoding="utf-8"))
            content = json.dumps({"task_id":entry["task_id"],"record":record,
                                  "prepared":handoff["prepared"]}, ensure_ascii=False,
                                 sort_keys=True,separators=(",",":"))
            binding=hashlib.sha256(content.encode("utf-8")).hexdigest()
            self.paths.append(LOCAL / ("taky-goal-claim-"+binding+".json"))

    def test_cli_routes_to_existing_queue_adapter(self):
        with patch("runtime_orchestrator.run_bounded_goal_queue",
                   return_value={"status":"QUEUE_ITEMS_OBSERVED_GOALS_OPEN",
                                 "items_executed":2}) as adapter:
            output=io.StringIO()
            with contextlib.redirect_stdout(output):
                code=main(["--repo-root",str(ROOT),"--auto-queue",str(self.manifest)])
        self.assertEqual(code,0)
        adapter.assert_called_once()
        self.assertEqual(json.loads(output.getvalue())["items_executed"],2)


if __name__ == "__main__":
    unittest.main()
