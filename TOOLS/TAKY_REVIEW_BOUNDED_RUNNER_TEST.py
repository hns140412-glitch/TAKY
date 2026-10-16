#!/usr/bin/env python3
"""Local-only tests: no Claude/Codex calls, credentials, or remote API use."""
import sys
import os
import json
import shutil
import unittest
from unittest.mock import patch
from TAKY_REVIEW_BOUNDED_RUNNER import run_bounded, execute_request, release_if_proven_preinvoke, OUTPUT_LIMIT


class BoundedRunnerTests(unittest.TestCase):
    def test_clean_preinvoke_releases_through_official_cli_only(self):
        task_id = "f" * 32
        receipt = "pf:external-review-" + task_id + ":abcdef1234567890"
        report = {"task_id": task_id, "status": "OUTCOME_UNKNOWN_RESOURCE_LIMIT",
                  "governedReceipt": {"receipt_id": receipt}}
        signed = {"state": "PREFLIGHT_ONLY", "receiptId": receipt, "preflightAllowed": True}
        proof = json.dumps({"allowed": True, "state": "PREINVOKE_RELEASED",
                            "receipt_id": receipt, "model_call_registered": False,
                            "route_failure_recorded": False}).encode()
        from subprocess import CompletedProcess
        with patch("TAKY_REVIEW_BOUNDED_RUNNER.subprocess.run",
                   return_value=CompletedProcess([], 0, proof)) as call:
            result = release_if_proven_preinvoke(report, signed)
        self.assertEqual(result["state"], "PREINVOKE_RELEASED")
        args = call.call_args.args[0]
        self.assertEqual(args[2:5], ["TAKY2.orchestrator", "release-uninvoked", receipt])
        self.assertIn("LOCAL_RESOURCE_GUARD_BEFORE_CLAIM", args)
        self.assertNotIn("exec", args)

    def test_claim_or_missing_receipt_blocks_release(self):
        task_id = "f" * 32
        receipt = "pf:external-review-" + task_id + ":abcdef1234567890"
        report = {"task_id": task_id, "status": "OUTCOME_UNKNOWN_TIMEOUT",
                  "governedReceipt": {"receipt_id": receipt}}
        with patch("TAKY_REVIEW_BOUNDED_RUNNER.subprocess.run") as call:
            self.assertNotEqual(release_if_proven_preinvoke(report, {
                "state": "EXECUTION_OUTCOME_UNKNOWN_NO_RETRY",
                "receiptId": receipt, "preflightAllowed": True})["state"],
                "PREINVOKE_RELEASED")
            self.assertNotEqual(release_if_proven_preinvoke(report, {
                "state": "PREFLIGHT_ONLY", "receiptId": "wrong",
                "preflightAllowed": True})["state"], "PREINVOKE_RELEASED")
            call.assert_not_called()

    def test_powershell_7_is_callable_without_model(self):
        shell = shutil.which("pwsh.exe")
        if not shell:
            self.skipTest("PowerShell 7 not installed")
        report = run_bounded([shell, "-NoLogo", "-NoProfile", "-NonInteractive",
                              "-Command", "Write-Output 'PWSH7_OFFLINE_OK'"],
                             timeout=15)
        self.assertEqual(report["returncode"], 0)
        self.assertIn("PWSH7_OFFLINE_OK", report["stdout"])
        self.assertFalse(report["modelCallConfirmed"])

    def test_local_stdout_capture_and_unverified_state(self):
        report = run_bounded([sys.executable, "-c", "print('BOUND_OK')"], timeout=3)
        self.assertEqual(report["status"], "RETURNED_UNVERIFIED")
        self.assertEqual(report["returncode"], 0)
        self.assertIn("BOUND_OK", report["stdout"])
        self.assertFalse(report["modelCallConfirmed"])

    @unittest.skipUnless(os.name == "nt", "Windows resource sampling only")
    def test_windows_resource_sampling(self):
        from TAKY_REVIEW_BOUNDED_RUNNER import _windows_process_resources
        reading = _windows_process_resources(os.getpid())
        self.assertIsNotNone(reading)
        self.assertGreater(reading[0], 0)
        self.assertGreaterEqual(reading[1], 0)

    @unittest.skipUnless(os.name == "nt", "Windows process resource gate only")
    def test_runaway_child_memory_is_terminated(self):
        script = "import time; data=bytearray(75*1024*1024);time.sleep(8)"
        with patch("TAKY_REVIEW_BOUNDED_RUNNER.MAX_CHILD_MEMORY_MB", 45):
            result = run_bounded([sys.executable, "-c", script], timeout=10)
        self.assertEqual(result["status"], "OUTCOME_UNKNOWN_RESOURCE_LIMIT")
        self.assertEqual(result["resourceLimitBreach"], "CHILD_MEMORY_LIMIT")
        self.assertIsNone(result["returncode"])
        self.assertFalse(result["modelCallConfirmed"])
        self.assertLess(result["elapsedSeconds"], 7)

    def test_local_nonzero_not_success(self):
        report = run_bounded([sys.executable, "-c", "raise SystemExit(7)"], timeout=3)
        self.assertEqual(report["status"], "FAILED_OR_BLOCKED")
        self.assertEqual(report["returncode"], 7)

    def test_local_timeout_is_unknown_not_failed(self):
        report = run_bounded([sys.executable, "-c", "import time;time.sleep(10)"], timeout=0.25)
        self.assertEqual(report["status"], "OUTCOME_UNKNOWN_TIMEOUT")
        self.assertIsNone(report["returncode"])
        self.assertTrue(report["timeout"])

    def test_oversized_stdout_is_truncated_and_bounded(self):
        report = run_bounded([sys.executable, "-c", "print('x'*28000)"], timeout=3)
        self.assertTrue(report["outputTruncated"])
        self.assertLessEqual(len(report["stdout"]), OUTPUT_LIMIT)

    def test_capture_signed_receipt_marker_from_local_fixture(self):
        script = (
            "import json,sys,pathlib;"
            "pathlib.Path(sys.argv[-1]).write_text("
            "json.dumps({'task_id':'" + "a" * 32 +
            "','receipt_id':'pf:external-review-" + "a" * 32 +
            ":abcd1234','provider':'codex','executor_state':'RETURNED'}));"
            "print('FIXTURE_OK')"
        )
        result = run_bounded([sys.executable, "-c", script], timeout=3,
                             capture_receipt=True)
        self.assertEqual(result["status"], "RETURNED_UNVERIFIED")
        self.assertEqual(result["governedReceipt"]["task_id"], "a" * 32)
        self.assertTrue(result["governedReceipt"]["receipt_id"].startswith("pf:external-review-"))

    def test_local_marker_preserves_bounded_source_manifest(self):
        marker = {
            "task_id": "c" * 32,
            "receipt_id": "pf:external-review-" + "c" * 32 + ":abcd1234567890ef",
            "provider": "claude",
            "executor_state": "RETURNED",
            "packet_digest": "a" * 20,
            "source_manifest": [{
                "path": "TOOLS/example.py", "sha256": "b" * 64,
                "includedLines": 2, "totalLines": 7}],
            "skill_manifest": [
                {"name": "authority-check", "sha256": "c" * 64},
                {"name": "cross-model-review", "sha256": "d" * 64}],
        }
        program = ("import sys,pathlib;pathlib.Path(sys.argv[-1]).write_text("
                   + repr(json.dumps(marker)) + ");print('LOCAL_ONLY')")
        result = run_bounded([sys.executable, "-c", program],
                             timeout=3, capture_receipt=True)
        self.assertEqual(result["status"], "RETURNED_UNVERIFIED")
        self.assertEqual(result["governedReceipt"]["source_manifest"],
                         marker["source_manifest"])
        self.assertEqual(result["governedReceipt"]["packet_digest"], "a" * 20)
        self.assertEqual(result["governedReceipt"]["skill_manifest"],
                         marker["skill_manifest"])

    def test_local_timeout_preserves_preflight_correlation(self):
        script = (
            "import sys,json,pathlib,time;"
            "pathlib.Path(sys.argv[-1]).write_text(json.dumps({"
            "'task_id':'" + "b" * 32 +
            "','receipt_id':'pf:external-review-" + "b" * 32 +
            ":ef123456','provider':'claude','executor_state':'AUTHORIZED_NOT_YET_CONFIRMED_INVOKED'}));"
            "time.sleep(10)"
        )
        result = run_bounded([sys.executable, "-c", script], timeout=0.7,
                             capture_receipt=True)
        self.assertEqual(result["status"], "OUTCOME_UNKNOWN_TIMEOUT")
        self.assertEqual(result["governedReceipt"]["task_id"], "b" * 32)
        self.assertIsNone(result["returncode"])

    def test_runner_passes_same_task_id_to_existing_governed_script(self):
        request = {"provider": "codex", "repo": r"D:\Git PWA\TAKY",
                   "prompt": "Review only one bounded packet", "task_id": "c" * 32}
        with patch.dict("os.environ", {"TAKY_USER_EXPLICIT_AUTHORIZATION": "1"}):
            with patch("TAKY_REVIEW_BOUNDED_RUNNER.run_bounded",
                       return_value={"status": "RETURNED_UNVERIFIED"}) as stub:
                outcome = execute_request(request)
        argv = stub.call_args.args[0]
        self.assertEqual(argv[argv.index("-TaskId") + 1], request["task_id"])
        self.assertTrue(stub.call_args.kwargs["capture_receipt"])
        self.assertEqual(outcome["task_id"], request["task_id"])

    def test_small_review_has_short_outer_timeout(self):
        request = {"provider": "codex", "repo": r"D:\Git PWA\TAKY",
                   "prompt": "bounded test", "task_id": "d" * 32,
                   "timeoutSeconds": 90}
        with patch.dict("os.environ", {"TAKY_USER_EXPLICIT_AUTHORIZATION": "1"}):
            with patch("TAKY_REVIEW_BOUNDED_RUNNER.run_bounded",
                       return_value={"status": "FAILED_OR_BLOCKED"}) as runner:
                with patch("TAKY_SIGNED_EXECUTION_READBACK.read_signed",
                           return_value={"state": "SIGNED_PREFLIGHT_NOT_FOUND"}):
                    outcome = execute_request(request)
        self.assertEqual(runner.call_args.kwargs["timeout"], 90)
        self.assertEqual(outcome["signedReadback"]["state"], "SIGNED_PREFLIGHT_NOT_FOUND")

    def test_invalid_timeout_cannot_extend_or_skip_limit(self):
        request = {"provider": "codex", "repo": r"D:\Git PWA\TAKY",
                   "prompt": "bounded test", "task_id": "d" * 32,
                   "timeoutSeconds": 230}
        with patch.dict("os.environ", {"TAKY_USER_EXPLICIT_AUTHORIZATION": "1"}):
            with self.assertRaisesRegex(ValueError, "INVALID_REVIEW_TIME_BUDGET"):
                execute_request(request)

    def test_rejects_missing_correlatable_task_id(self):
        request = {"provider": "codex", "repo": r"D:\Git PWA\TAKY",
                   "prompt": "bounded fixture"}
        with self.assertRaisesRegex(ValueError, "TASK_ID_REQUIRED_FOR_CORRELATION"):
            execute_request(request)

    def test_rejects_invalid_timeouts(self):
        with self.assertRaises(ValueError):
            run_bounded([sys.executable], timeout=500)
        with self.assertRaises(ValueError):
            run_bounded([], timeout=1)

    def test_rejects_unapproved_provider(self):
        with self.assertRaises(ValueError):
            execute_request({"provider": "random", "repo": "X", "prompt": "test"})

    def test_rejects_unapproved_repository(self):
        with self.assertRaises(ValueError):
            execute_request({"provider": "codex", "repo": "X", "prompt": "test"})

    def test_rejects_missing_approval_without_running_any_model(self):
        with patch.dict("os.environ", {"TAKY_USER_EXPLICIT_AUTHORIZATION": ""}):
            with self.assertRaises(ValueError):
                execute_request({"provider": "codex", "repo": r"D:\Git PWA\TAKY", "prompt": "test"})


if __name__ == "__main__":
    unittest.main()
