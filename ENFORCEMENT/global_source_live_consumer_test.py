"""Live local Playwright evidence -> source-anchored candidate feedback checks.

Reads a real new loopback browser receipt. Uses disposable Central SQLite only.
"""
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import central_review_source_intake as intake
import global_source_learning_feedback as flow
import global_source_live_consumer as live
import taky_central_source_factory as factory

RUN = "taky-live-playcamp-20261014-1512"


class LocalLiveConsumer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "central.sqlite3"
        self.c = factory.connect(self.db)
        self.addCleanup(self.c.close)
        docs = intake.verified_documents()
        self.original = intake.advance_verified_review_pipeline(self.c, docs)
        self.source_before = [tuple(r) for r in self.c.execute("SELECT * FROM source")]
        self.stages_before = [tuple(r) for r in self.c.execute("SELECT * FROM stage")]

    def test_new_browser_receipt_integrates_and_remains_idempotent(self):
        receipt_hash = live._live_evidence(RUN)
        self.assertEqual(len(receipt_hash), 64)
        self.assertEqual(self.original["verified_source_count"], 12)
        self.assertEqual(self.original["durable_detail_units"], 332)
        first = live.consume_live_runtime(self.c, RUN)
        self.assertEqual(first["before"], "LOCAL_EVALUATION_REQUIRED")
        self.assertEqual(first["after"], "REUSE_CANDIDATE")
        self.assertTrue(first["live_browser_evidence"])
        self.assertFalse(first["semantic_approved"])
        self.assertFalse(first["knowledge_approved"])
        self.assertFalse(first["production_rollout"])
        self.c.commit()
        with closing(sqlite3.connect(self.db)) as persisted:
            persisted.row_factory = sqlite3.Row
            after = flow.technical_method_decision(
                persisted, outcome_verifier=live.verify_local_outcome)
            self.assertEqual(after["decision"], "REUSE_CANDIDATE")
            second = live.consume_live_runtime(persisted, RUN)
            self.assertEqual(first["decision_event_id"], second["decision_event_id"])
            self.assertEqual(first["feedback_event_id"], second["feedback_event_id"])
            self.assertEqual(persisted.execute(
                "SELECT COUNT(*) FROM event WHERE kind=?", (flow.FEEDBACK_KIND,)
            ).fetchone()[0], 1)
            self.assertEqual(persisted.execute(
                "SELECT COUNT(*) FROM event WHERE kind=?", (flow.DECISION_KIND,)
            ).fetchone()[0], 1)
        self.assertEqual([tuple(r) for r in self.c.execute("SELECT * FROM stage")],
                         self.stages_before)
        self.assertEqual([tuple(r) for r in self.c.execute("SELECT * FROM source")],
                         self.source_before)

    def test_forged_receipt_and_run_id_rejected(self):
        binding = flow.technical_method_decision(self.c)["binding"]
        self.assertFalse(live.verify_local_outcome(
            {"run_id": RUN, "outcome": "SUCCESS", "evidence_sha256": "0"*64},
            binding))
        with self.assertRaisesRegex(ValueError, "LIVE_RUN_ID_INVALID"):
            live._live_evidence("../../etc")
        with self.assertRaisesRegex(ValueError, "LIVE_RECEIPT_MISSING_OR_OVERSIZED"):
            live._live_evidence("taky-live-not-found-888")
        with patch("global_source_live_consumer._browser_runtime_receipt_verified",
                   return_value=False):
            with self.assertRaisesRegex(ValueError, "LIVE_BROWSER_INDEPENDENT_GUARD_REJECTED"):
                live._live_evidence(RUN)
        count_before = self.c.execute("SELECT COUNT(*) FROM event").fetchone()[0]
        with patch("global_source_live_consumer._browser_runtime_receipt_verified",
                   return_value=False):
            with self.assertRaisesRegex(ValueError, "LIVE_BROWSER_INDEPENDENT_GUARD_REJECTED"):
                live.consume_live_runtime(self.c, RUN)
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM event").fetchone()[0],
                         count_before)

    def test_bounded_reconciliation_is_idempotent(self):
        first = live.reconcile_verified_live_receipts(self.c)
        self.assertIn(RUN, first["run_ids"])
        self.assertEqual(first["new_feedback_event_count"], 1)
        self.assertTrue(first["all_semantic_approval_blocked"])
        second = live.reconcile_verified_live_receipts(self.c)
        self.assertEqual(second["new_feedback_event_count"], 0)
        self.assertEqual(second["already_recorded_count"], first["run_count"])
        self.assertEqual(self.c.execute(
            "SELECT COUNT(*) FROM event WHERE kind=?", (flow.FEEDBACK_KIND,)
        ).fetchone()[0], 1)

    def test_bad_reconciliation_rolls_back_all_feedback(self):
        with tempfile.TemporaryDirectory() as root:
            for name in ("taky-live-valid-one", "taky-live-valid-two"):
                (Path(root) / name).mkdir()
            before = self.c.execute("SELECT COUNT(*) FROM event").fetchone()[0]
            def partial_then_fail(conn, name):
                if name.endswith("two"):
                    raise ValueError("SIMULATED_SECOND_RUN_INVALID")
                sid = conn.execute("SELECT id FROM source LIMIT 1").fetchone()[0]
                factory.event(conn, sid, "NEVER_RETAIN_PARTIAL", {})
            with patch.object(live, "RUN_ROOT", Path(root)), patch.object(
                live, "consume_live_runtime", side_effect=partial_then_fail
            ):
                with self.assertRaisesRegex(ValueError, "SIMULATED_SECOND_RUN_INVALID"):
                    live.reconcile_verified_live_receipts(self.c)
            self.assertEqual(self.c.execute("SELECT COUNT(*) FROM event").fetchone()[0],
                             before)

    def test_scheduled_local_collector_wiring_contract(self):
        collector = Path(r"D:\Git PWA\TAKY-SOURCE-VAULT\RUN_LOCAL_COLLECTOR_12H.ps1")
        original = Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\90_ARCHIVE\TAKY_COLLECTOR_HOOK_ORIGINAL_20261014\RUN_LOCAL_COLLECTOR_12H.ps1")
        import hashlib
        old = original.read_bytes()
        current = collector.read_text(encoding="utf-8-sig")
        self.assertEqual(hashlib.sha256(old).hexdigest(),
                         "326586584100b764bdd07f9517fdfaec2d2ad6d128a96920f8cd1b2f27b66185")
        self.assertIn("global_source_live_consumer.py", current)
        self.assertIn("--reconcile-existing", current)
        self.assertIn("NOT_AUTHORITATIVE", current)
        self.assertIn("Remove-Item -LiteralPath $tempPath", current)
        self.assertIn("exit $collectorExit", current)
        self.assertNotIn("Start-ScheduledTask", current)
        self.assertNotIn("Register-ScheduledTask", current)

    def test_operational_db_disallowed_before_browser_capture(self):
        proc = subprocess.run(
            [sys.executable, "-B", str(Path(live.__file__).resolve()),
             "--db", str(factory.DB),
             "--capture-config", "C:/Windows/win.ini"],
            capture_output=True, text=True, encoding="utf-8", timeout=15)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("LIVE_FEEDBACK_DISPOSABLE_DB_REQUIRED", proc.stderr)


if __name__ == "__main__":
    unittest.main()
