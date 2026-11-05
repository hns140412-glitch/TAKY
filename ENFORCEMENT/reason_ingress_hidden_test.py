"""Tests for the hidden TAKY Reason task entrypoint; zero real subprocesses."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).with_name("reason_ingress_hidden.pyw")
loader = importlib.machinery.SourceFileLoader("taky_reason_hidden_test_subject", str(SOURCE))
spec = importlib.util.spec_from_loader(loader.name, loader)
module = importlib.util.module_from_spec(spec)
loader.exec_module(module)


class HiddenReasonIngressTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.local = self.root / ".local"
        self.local.mkdir()
        patcher = patch.object(module, "LOCAL", self.local)
        patcher.start()
        self.addCleanup(patcher.stop)
        repo_patcher = patch.object(module, "REPO", self.root)
        repo_patcher.start()
        self.addCleanup(repo_patcher.stop)
        dependency=patch.object(module,"run_dependency_progress",
            return_value={"status":"BOUNDED_DEPENDENCY_OBSERVATION",
                          "new_attempts":0,"uncertain":0})
        dependency.start()
        self.addCleanup(dependency.stop)
        canonical=patch.object(module,"run_canonical_progress",
            return_value={"schema":"TAKY_LOCAL_CONTINUATION_V1",
                          "status":"BOUNDED_LOCAL_CONTINUATION_FINISHED",
                          "actions":[],"no_model_calls":True,
                          "portfolio_done_claimed":False})
        canonical.start()
        self.addCleanup(canonical.stop)

    def run_mock(self, payload, returncode=0):
        result = subprocess.CompletedProcess(module.COMMAND, returncode,
                                             stdout=json.dumps(payload),
                                             stderr="")
        with patch.object(module.subprocess, "run", return_value=result) as invoked:
            code = module.main()
        self.assertEqual(invoked.call_count, 1)
        self.assertLessEqual(invoked.call_args.kwargs["timeout"], 3600)
        self.assertEqual(invoked.call_args.kwargs["creationflags"],
                         module.FLAGS)
        return code

    def test_idle_does_not_poll_or_append_micro_logs(self):
        result = self.run_mock({
            "status":"REASON_BURST_DRAINED_NO_MORE_MESSAGES",
            "messages_observed":0,"messages_dispatched":0,
            "messages_recovered":0})
        self.assertEqual(result,0)
        self.assertFalse((self.local/"taky-reason-ingress-runs.jsonl").exists())

    def test_real_observation_saved_compactly(self):
        result = self.run_mock({
            "status":"REASON_BURST_LIMIT_REACHED",
            "messages_observed":1,"messages_dispatched":1,
            "messages_recovered":0,
            "observations":[{"queue_id":"toy1",
                             "queue_status":"QUEUE_PARTIAL_RECOVERY_DEFERRED"}]})
        self.assertEqual(result,0)
        path=self.local/"taky-reason-ingress-runs.jsonl"
        record=json.loads(path.read_text(encoding="utf-8").strip())
        self.assertEqual(record["messages_dispatched"],1)
        self.assertEqual(record["queue_statuses"],["QUEUE_PARTIAL_RECOVERY_DEFERRED"])
        self.assertNotIn("prompt",record)
        self.assertNotIn("sender",record)

    def test_untrusted_output_is_error_without_retry(self):
        with patch.object(module.subprocess,"run",
                          return_value=subprocess.CompletedProcess(
                              module.COMMAND,0,stdout="[]",stderr="")) as call:
            code=module.main()
        self.assertEqual(code,2)
        # The launcher should not treat syntactically valid but wrong-shaped
        # CLI output as a completed successful ingestion.
        record=json.loads((self.local/"taky-reason-ingress-runs.jsonl")
                          .read_text(encoding="utf-8").strip())
        self.assertEqual(record["state"],"INGRESS_OUTPUT_UNVERIFIED")
        self.assertEqual(call.call_count,1)

    def test_provider_timeout_is_outcome_unknown_not_busy_retry(self):
        with patch.object(module.subprocess,"run",
                          side_effect=subprocess.TimeoutExpired(
                              cmd="ingress",timeout=3600)) as invoked:
            code=module.main()
        self.assertEqual(code,2)
        self.assertEqual(invoked.call_count,1)
        rec=json.loads((self.local/"taky-reason-ingress-runs.jsonl")
                       .read_text(encoding="utf-8").strip())
        self.assertEqual(rec["state"],"INGRESS_OUTCOME_UNKNOWN_RECONCILE")

    def test_symlinked_runtime_log_cannot_append_to_original_file(self):
        outside=self.root/"precious-original.json"
        outside.write_text('{"do_not_change":true}',encoding="utf-8")
        trap=self.local/"taky-reason-ingress-runs.jsonl"
        try:
            trap.symlink_to(outside)
        except (OSError,NotImplementedError):
            self.skipTest("Windows symlink privilege unavailable")
        before=outside.read_bytes()
        output={"status":"REASON_BURST_LIMIT_REACHED",
                "messages_observed":1,"messages_dispatched":0}
        self.assertEqual(self.run_mock(output),2)
        self.assertEqual(outside.read_bytes(),before)

    def test_reason_idle_still_runs_canonical_local_work_without_fake_done(self):
        result={
            "status":"REASON_BURST_DRAINED_NO_MORE_MESSAGES",
            "messages_observed":0,"messages_dispatched":0}
        with patch.object(module,"run_canonical_progress",return_value={
             "schema":"TAKY_LOCAL_CONTINUATION_V1",
             "status":"BOUNDED_LOCAL_CONTINUATION_FINISHED",
             "no_model_calls":True,"portfolio_done_claimed":False,
             "actions":[{"task_id":"CLN-001","status":"LOCAL_SLICE_VERIFIED_NOT_PORTFOLIO_DONE"}]
        }) as pumped:
            state=self.run_mock(result)
        self.assertEqual(state,0)
        self.assertEqual(pumped.call_count,1)
        log=self.local/"taky-reason-ingress-runs.jsonl"
        receipt=json.loads(log.read_text(encoding="utf-8"))
        self.assertEqual(receipt["state"],"REASON_BURST_DRAINED_NO_MORE_MESSAGES")
        self.assertEqual(receipt["canonical_local_actions"],
            [{"work_id":"CLN-001","state":"LOCAL_SLICE_VERIFIED_NOT_PORTFOLIO_DONE"}])
        self.assertNotIn("portfolio_done",str(receipt))

    def test_canonical_exception_is_actionable_not_success(self):
        with patch.object(module,"run_canonical_progress",
                          side_effect=ValueError("invalid canonical task")):
            state=self.run_mock({
               "status":"REASON_BURST_DRAINED_NO_MORE_MESSAGES",
               "messages_observed":0})
        self.assertEqual(state,2)
        record=json.loads((self.local/"taky-reason-ingress-runs.jsonl")
                          .read_text(encoding="utf-8"))
        self.assertEqual(record["canonical_local_state"],
                         "CANONICAL_LOCAL_PROGRESS_REQUIRES_RECOVERY")

    def test_task_is_one_message_per_execution_with_trusted_gates(self):
        self.assertIn("--drain", module.COMMAND)
        self.assertEqual(module.COMMAND[module.COMMAND.index("--max-messages")+1],"4")
        self.assertIn("--execute", module.COMMAND)
        self.assertIn("reason_queue_ingress.py",str(module.INGRESS))
        self.assertEqual(module.TIMEOUT_SECONDS,3600)


if __name__ == "__main__":
    unittest.main()
