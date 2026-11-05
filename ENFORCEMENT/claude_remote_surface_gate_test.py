"""Evaluate the installed Claude PreToolUse hook with fake tool events.

No real remote operations, Git pushes, file modifications or model calls.
A passing hook only covers a Claude session registering this hook; ChatGPT host
and arbitrary independent desktop processes remain outside that boundary.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HOOK = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "taky_hook.py"
ROOT = HOOK.parents[2]


class RemoteSurfaceGateTests(unittest.TestCase):
    def setUp(self):
        self.profile = tempfile.TemporaryDirectory(prefix="TAKY_HOOK_FIXTURE_")
        self.addCleanup(self.profile.cleanup)

    def decide(self, tool: str, tool_input: dict) -> str:
        sample = {
            "hook_event_name": "PreToolUse", "session_id": "remote-hook-fixture",
            "cwd": str(ROOT), "tool_name": tool, "tool_input": tool_input,
        }
        env = dict(os.environ)
        env["USERPROFILE"] = self.profile.name
        env["HOME"] = self.profile.name
        env["TAKY_MAX_REMOTE_CALLS_PER_PROMPT"] = "25"
        p = subprocess.run(
            [sys.executable, str(HOOK)], input=json.dumps(sample),
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8", env=env, timeout=8, check=True,
        )
        if not p.stdout.strip():
            return "allow"
        result = json.loads(p.stdout)
        return result.get("hookSpecificOutput", {}).get("permissionDecision", "allow")

    def test_protected_master_edit_from_remote_connector_needs_approval(self):
        self.assertEqual(self.decide(
            "mcp__Remote_Desktop_Commander__edit_block",
            {"file_path": str(ROOT / "MASTER" / "MASTER_LOGIC.md"),
             "old_string": "keep", "new_string": "rewrite"}), "ask")

    def test_remote_git_internal_write_denied(self):
        self.assertEqual(self.decide(
            "mcp__Remote_Desktop_Commander__write_file",
            {"path": str(ROOT / ".git" / "config"), "content": "bad"}), "deny")

    def test_remote_protected_shell_change_needs_approval(self):
        self.assertEqual(self.decide(
            "mcp__Remote_Desktop_Commander__start_process",
            {"command": "Set-Content -Path 'MASTER/MASTER_LOGIC.md' -Value 'new'"}), "ask")

    def test_remote_git_push_needs_approval(self):
        self.assertEqual(self.decide(
            "mcp__Remote_Desktop_Commander__start_process",
            {"command": "git -C 'D:\\Git PWA\\TAKY' push origin main"}), "ask")

    def test_remote_read_of_secret_needs_approval(self):
        self.assertEqual(self.decide(
            "mcp__Remote_Desktop_Commander__read_file",
            {"path": str(ROOT / ".env.local")}), "ask")

    def test_normal_remote_local_build_work_can_proceed(self):
        self.assertEqual(self.decide(
            "mcp__Remote_Desktop_Commander__start_process",
            {"command": "python -m py_compile TOOLS/TAKY_SCOPED_EDIT_APPLY.py"}), "allow")


if __name__ == "__main__":
    unittest.main()
