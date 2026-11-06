#!/usr/bin/env python3
"""Focused tests for TAKY_WORK_CONTINUATION_30M (fixtures + mocked subprocess; no real work)."""
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import TAKY_WORK_CONTINUATION_30M as M  # noqa: E402

REFRESH_OK = {"schema": "TAKY_CONVERSATION_REFRESH_LOCAL_V1", "mode": "LOCAL_DERIVED_REFRESH",
              "stages": [{"stage": "a"}], "native_chat_coverage": M.EXPORT_ONLY,
              "canonical_modified": False, "git_push_merge_deploy": False, "paid_api_calls": 0}
ADVANCE_OK = {"schema": "TAKY_LOCAL_CONTINUATION_V1", "status": "BOUNDED_LOCAL_CONTINUATION_FINISHED",
              "actions": [{"task_id": "CLN-001", "status": "LOCAL_CHECKS_PASSED"},
                          {"task_id": "MCP-001", "status": "LOCAL_EXECUTION_NEEDS_RECOVERY"}],
              "remaining_ready": 0, "remaining_unbound": 3, "remaining_dep_wait": 1,
              "no_model_calls": True, "portfolio_done_claimed": False, "no_push_merge_deploy": True}


def proc(obj, rc=0):
    out = obj if isinstance(obj, str) else json.dumps(obj)
    return subprocess.CompletedProcess([], rc, stdout="noise\n" + out + "\n", stderr="err")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.repo = t / "repo"
        (self.repo / "MASTER").mkdir(parents=True)
        (self.repo / "STATE.md").write_text("# TAKY CANONICAL RUNTIME STATE\n", encoding="utf-8")
        (self.repo / "MASTER" / "MASTER_LOGIC.md").write_text("# TAKY GRAND MASTER LOGIC\n", encoding="utf-8")
        self.reg = t / "reg.json"
        self.write_reg({"schema": M.REGISTRY_SCHEMA, "tasks": [{"id": "INT-001"}, {"id": "CLN-001"}]})
        self.ctl = t / "ctl"

    def tearDown(self):
        self.tmp.cleanup()

    def write_reg(self, obj):
        self.reg.write_text(json.dumps(obj), encoding="utf-8")

    def main(self, *argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = M.main(list(argv), control_dir=self.ctl, registry=self.reg, repo=self.repo)
        return code, json.loads(buf.getvalue().strip().splitlines()[-1])

    def latest(self):
        return json.loads((self.ctl / "latest.json").read_text(encoding="utf-8"))


class Tests(Base):
    def test_check_only_no_actions_no_writes(self):
        with mock.patch.object(M.subprocess, "run") as run:
            code, out = self.main("--check-only")
        self.assertEqual((code, out["status"]), (0, "CHECK_ONLY_OK"))
        run.assert_not_called()
        self.assertFalse(self.ctl.exists())

    def test_valid_tick_writes_receipt_and_timeouts(self):
        with mock.patch.object(M.subprocess, "run", side_effect=[proc(REFRESH_OK), proc(ADVANCE_OK)]) as run:
            code, out = self.main()
        self.assertEqual((code, out["status"]), (0, "TICK_OK"))
        self.assertEqual([c.kwargs["timeout"] for c in run.call_args_list], [150, 180])
        self.assertIn("--continue", run.call_args_list[1].args[0])
        r = self.latest()
        self.assertEqual(r["work_ids"], ["CLN-001", "MCP-001"])
        self.assertEqual(r["needs_recovery"], 1)
        self.assertFalse(r["portfolio_done_claimed"])
        self.assertEqual(r["paid_api_calls"], 0)
        self.assertTrue(r["source_limitations"])
        self.assertEqual(list(self.ctl.glob("*.tmp")), [])

    def run_tick(self, adv):
        with mock.patch.object(M.subprocess, "run", side_effect=[proc(REFRESH_OK), proc(adv)]):
            code, out = self.main()
        return code, out, self.latest()

    def test_no_actions_with_unbound_is_no_product_progress(self):
        adv = dict(ADVANCE_OK, actions=[], remaining_unbound=7, remaining_dep_wait=2)
        code, out, r = self.run_tick(adv)
        self.assertEqual((code, r["status"]), (0, "TICK_OK"))
        self.assertEqual(r["progress_status"], "NO_PRODUCT_PROGRESS")
        self.assertEqual(r["action_count"], 0)
        self.assertIs(r["actual_product_implementation"], False)
        self.assertEqual((r["advance"]["remaining_unbound"], r["advance"]["remaining_dep_wait"]), (7, 2))
        self.assertIn("remaining_unbound=7", r["blocked_progress_reason"])
        self.assertIn("no automatic Claude/Codex", r["next_action"])
        self.assertFalse(r["portfolio_done_claimed"])

    def test_no_actions_no_holds_has_no_block_reason(self):
        _, _, r = self.run_tick(dict(ADVANCE_OK, actions=[], remaining_unbound=0, remaining_dep_wait=0))
        self.assertEqual(r["progress_status"], "NO_PRODUCT_PROGRESS")
        self.assertNotIn("blocked_progress_reason", r)
        self.assertNotIn("next_action", r)

    def test_readonly_checks_only_and_positive_actions(self):
        checks = dict(ADVANCE_OK, actions=[{"task_id": "CLN-001", "status": "LOCAL_CHECKS_PASSED"}])
        _, _, r = self.run_tick(checks)
        self.assertEqual((r["progress_status"], r["action_count"]), ("READONLY_CHECKS_ONLY", 1))
        self.assertNotIn("blocked_progress_reason", r)
        pos = dict(ADVANCE_OK, actions=[{"task_id": "CLN-001", "status": "LOCAL_CHECKS_PASSED"},
                                        {"task_id": "INT-001", "status": "LOCAL_EXECUTION_COMPLETED"}])
        _, _, r = self.run_tick(pos)
        self.assertEqual((r["progress_status"], r["action_count"]), ("READONLY_ACTIONS_EXECUTED", 2))
        self.assertIs(r["actual_product_implementation"], False)
        self.assertFalse(r["portfolio_done_claimed"])

    def test_recovery_path_is_not_productive(self):
        rec = dict(ADVANCE_OK, actions=[{"task_id": "MCP-001", "status": "LOCAL_EXECUTION_NEEDS_RECOVERY"}])
        code, _, r = self.run_tick(rec)
        self.assertEqual((code, r["status"], r["needs_recovery"]), (0, "TICK_OK", 1))
        self.assertEqual(r["progress_status"], "READONLY_CHECKS_ONLY")
        self.assertIs(r["actual_product_implementation"], False)

    def test_hold_never_claims_product(self):
        with mock.patch.object(M.subprocess, "run", side_effect=[proc(REFRESH_OK), proc(ADVANCE_OK, rc=1)]):
            code, _ = self.main()
        r = self.latest()
        self.assertEqual((code, r["status"]), (2, "HOLD"))
        self.assertIs(r["actual_product_implementation"], False)
        self.assertNotIn("progress_status", r)

    def test_malformed_registry_fails_closed(self):
        cases = [{"schema": "WRONG", "tasks": [{"id": "INT-001"}]},
                 {"schema": M.REGISTRY_SCHEMA, "tasks": [{"id": "INT-001"}, {"id": "INT-001"}]},
                 {"schema": M.REGISTRY_SCHEMA, "tasks": [{"id": "CLN-001"}]}]
        for bad in cases:
            self.write_reg(bad)
            with mock.patch.object(M.subprocess, "run") as run:
                code, out = self.main()
            self.assertEqual((code, out["status"]), (2, "HOLD"))
            run.assert_not_called()
            self.assertEqual(self.latest()["status"], "HOLD")
        self.reg.write_text("{not json", encoding="utf-8")
        self.assertEqual(self.main("--check-only")[0], 2)

    def test_malformed_receipts_hold(self):
        bad_refresh = [dict(REFRESH_OK, paid_api_calls=1), dict(REFRESH_OK, canonical_modified=True),
                       dict(REFRESH_OK, mode="CHECK_ONLY"), dict(REFRESH_OK, native_chat_coverage="ALL"),
                       dict(REFRESH_OK, git_push_merge_deploy=True), "not json"]
        for b in bad_refresh:
            with mock.patch.object(M.subprocess, "run", side_effect=[proc(b)]) as run:
                code, _ = self.main()
            self.assertEqual(code, 2)
            self.assertEqual(run.call_count, 1)  # advance never runs after refresh HOLD
        bad_adv = [dict(ADVANCE_OK, schema="X"), dict(ADVANCE_OK, no_model_calls=False),
                   dict(ADVANCE_OK, portfolio_done_claimed=True), dict(ADVANCE_OK, no_push_merge_deploy=False)]
        for b in bad_adv:
            with mock.patch.object(M.subprocess, "run", side_effect=[proc(REFRESH_OK), proc(b)]):
                code, _ = self.main()
            self.assertEqual((code, self.latest()["status"]), (2, "HOLD"))

    def test_timeout_and_nonzero_exit_hold(self):
        with mock.patch.object(M.subprocess, "run", side_effect=subprocess.TimeoutExpired("x", 150)):
            code, out = self.main()
        self.assertEqual(code, 2)
        self.assertIn("TIMEOUT", out["reason"])
        with mock.patch.object(M.subprocess, "run", side_effect=[proc(REFRESH_OK), proc(ADVANCE_OK, rc=1)]):
            self.assertEqual(self.main()[0], 2)

    def test_locked_overlap_skips_safely(self):
        held = M.Lock(self.ctl / "tick.lock")
        self.assertTrue(held.acquire())
        try:
            (self.ctl / "latest.json").write_text('{"keep": true}', encoding="utf-8")
            with mock.patch.object(M.subprocess, "run") as run:
                code, out = self.main()
            self.assertEqual((code, out["status"]), (0, "SKIPPED_BUSY"))
            run.assert_not_called()
            self.assertEqual(self.latest(), {"keep": True})
        finally:
            held.release()
        with mock.patch.object(M.subprocess, "run", side_effect=[proc(REFRESH_OK), proc(ADVANCE_OK)]):
            self.assertEqual(self.main()[1]["status"], "TICK_OK")  # lock released after skip/hold

    def test_run_json_passes_no_window_flag(self):
        with mock.patch.object(M.subprocess, "CREATE_NO_WINDOW", 0x08000000, create=True), \
                mock.patch.object(M.subprocess, "run", return_value=proc(REFRESH_OK)) as run:
            M.run_json(["x"], 5, "T")
        self.assertEqual(run.call_args.kwargs.get("creationflags"), 0x08000000)

    def test_run_json_non_windows_flag_is_zero(self):
        with mock.patch.object(M.subprocess, "run", return_value=proc(REFRESH_OK)) as run:
            if hasattr(M.subprocess, "CREATE_NO_WINDOW"):
                with mock.patch.object(M.subprocess, "CREATE_NO_WINDOW", 0):
                    M.run_json(["x"], 5, "T")
            else:
                M.run_json(["x"], 5, "T")
        self.assertEqual(run.call_args.kwargs.get("creationflags"), 0)

    def test_all_subprocess_run_sites_suppress_console(self):
        import ast
        here = Path(__file__).resolve().parent
        names = ("TAKY_WORK_CONTINUATION_30M.py", "TAKY_CONVERSATION_REFRESH_LOCAL.py",
                 "TAKY_CONVERSATION_PROGRESS_BOARD.py")
        for name in names:
            src = (here / name).read_text(encoding="utf-8")
            sites = [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Call)
                     and isinstance(n.func, ast.Attribute) and n.func.attr in ("run", "Popen", "check_output")
                     and isinstance(n.func.value, ast.Name) and n.func.value.id == "subprocess"]
            self.assertTrue(sites, name)
            for call in sites:
                kw = {k.arg: ast.unparse(k.value) for k in call.keywords}
                self.assertIn("CREATE_NO_WINDOW", kw.get("creationflags", ""), "%s:%d" % (name, call.lineno))


if __name__ == "__main__":
    unittest.main(verbosity=1)
