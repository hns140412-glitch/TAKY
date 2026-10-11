#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

from claude_lifecycle_receipt import build_receipt, persist_receipt

ROOT=Path(__file__).resolve().parents[1]
SETTINGS=ROOT/".claude"/"settings.json"
HOOK=ROOT/".claude"/"hooks"/"taky_hook.py"

class ClaudeLifecycleReceiptTest(unittest.TestCase):
    def test_resume_is_minimal_and_non_authoritative(self):
        r = build_receipt({
            "hook_event_name":"SessionStart",
            "source":"resume",
            "session_id":"SHOULD_NOT_APPEAR",
            "transcript_path":"SHOULD_NOT_APPEAR",
            "cwd":"SHOULD_NOT_APPEAR"
        })
        self.assertIsNotNone(r)
        raw=json.dumps(r,ensure_ascii=False)
        self.assertNotIn("SHOULD_NOT_APPEAR",raw)
        self.assertEqual(r["role"],"WRITE_ONLY_LIFECYCLE_RECEIPT")
        self.assertEqual(r["authority_reload_hint"],"DOMAIN/GROW_DOMAIN_REGISTRY.json#shared_core.current_index")
        self.assertFalse(r["semantic_authority"])
        self.assertFalse(r["promotion_authorized"])
        self.assertFalse(r["contains_session_content"])
        self.assertFalse(r["contains_identity"])
        self.assertFalse(r["contains_path"])

    def test_compact_supported(self):
        r=build_receipt({"hook_event_name":"SessionStart","source":"compact"})
        self.assertEqual(r["source"],"compact")

    def test_precompact_trigger_payload_supported(self):
        r=build_receipt({"hook_event_name":"PreCompact","trigger":"manual"})
        self.assertEqual(r["hook_event_name"],"PreCompact")
        self.assertEqual(r["source"],"manual")

    def test_unrelated_event_ignored(self):
        self.assertIsNone(build_receipt({"hook_event_name":"PostToolUse","source":"resume"}))

    def test_settings_matchers_cover_resume_compact_and_precompact(self):
        d=json.loads(SETTINGS.read_text(encoding="utf-8-sig"))
        hooks=d["hooks"]
        self.assertIn("resume",hooks["SessionStart"][0]["matcher"])
        self.assertIn("compact",hooks["SessionStart"][0]["matcher"])
        self.assertEqual(hooks["PreCompact"][0]["matcher"],"manual|auto")
        self.assertIn("taky_hook.py",hooks["SessionStart"][0]["hooks"][0]["command"])
        self.assertIn("taky_hook.py",hooks["PreCompact"][0]["hooks"][0]["command"])

    def test_hook_integration_writes_receipt_and_emits_current_index_hint(self):
        with tempfile.TemporaryDirectory(prefix="taky-hook-lifecycle-") as td:
            env=os.environ.copy()
            env["TAKY_CLAUDE_LIFECYCLE_RECEIPT_DIR"]=td
            payload={
                "hook_event_name":"SessionStart",
                "source":"resume",
                "session_id":"PRIVATE_SHOULD_NOT_PERSIST",
                "transcript_path":"PRIVATE_SHOULD_NOT_PERSIST",
                "cwd":str(ROOT),
            }
            cp=subprocess.run(
                [sys.executable,str(HOOK)],
                input=json.dumps(payload,ensure_ascii=False),
                cwd=str(ROOT),
                env=env,
                text=True,
                encoding="utf-8",
                errors="strict",
                capture_output=True,
                check=True,
            )
            self.assertIn("shared_core.current_index",cp.stdout)
            files=list(Path(td).glob("receipt-*.json"))
            self.assertEqual(len(files),1)
            raw=files[0].read_text(encoding="utf-8")
            self.assertNotIn("PRIVATE_SHOULD_NOT_PERSIST",raw)
            self.assertIn("WRITE_ONLY_LIFECYCLE_RECEIPT",raw)

    def test_precompact_hook_integration_writes_receipt(self):
        with tempfile.TemporaryDirectory(prefix="taky-hook-precompact-") as td:
            env=os.environ.copy()
            env["TAKY_CLAUDE_LIFECYCLE_RECEIPT_DIR"]=td
            payload={
                "hook_event_name":"PreCompact",
                "trigger":"auto",
                "session_id":"PRIVATE_SHOULD_NOT_PERSIST",
                "cwd":str(ROOT),
            }
            cp=subprocess.run(
                [sys.executable,str(HOOK)],
                input=json.dumps(payload,ensure_ascii=False),
                cwd=str(ROOT),
                env=env,
                text=True,
                encoding="utf-8",
                errors="strict",
                capture_output=True,
                check=True,
            )
            self.assertEqual(cp.stdout,"")
            files=list(Path(td).glob("receipt-*.json"))
            self.assertEqual(len(files),1)
            d=json.loads(files[0].read_text(encoding="utf-8"))
            self.assertEqual(d["hook_event_name"],"PreCompact")
            self.assertEqual(d["source"],"auto")
            self.assertEqual(d["role"],"WRITE_ONLY_LIFECYCLE_RECEIPT")

    def test_persist_and_bounded_cleanup(self):
        with tempfile.TemporaryDirectory(prefix="taky-lifecycle-") as td:
            with patch.dict(os.environ,{"TAKY_CLAUDE_LIFECYCLE_RECEIPT_DIR":td}):
                for _ in range(5):
                    persist_receipt({"hook_event_name":"SessionStart","source":"resume"},max_files=3)
                files=list(Path(td).glob("receipt-*.json"))
                self.assertLessEqual(len(files),3)
                for p in files:
                    d=json.loads(p.read_text(encoding="utf-8"))
                    self.assertFalse(d["semantic_authority"])
                    self.assertFalse(d["promotion_authorized"])

if __name__=="__main__":
    unittest.main()
