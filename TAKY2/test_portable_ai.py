from __future__ import annotations
from http.server import ThreadingHTTPServer
import json
import subprocess
from unittest.mock import patch
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import urlopen, Request
from urllib.error import HTTPError

from TAKY2.portable_ai.__main__ import (
    Dashboard, PortableError, attach, doctor, execute_gated, show, submit, tasks,
)

class PortableAITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "store"
        self.sources = Path(self.temp.name) / "sources"
        self.sources.mkdir()

    def new(self):
        return submit(self.root, title="<script>alert(1)</script>", owner="CODEX", scope="Review & verify.")

    def test_submit_read_list_integrity(self):
        item = self.new()
        tid = item["task_id"]
        self.assertEqual(show(self.root, tid), item)
        self.assertEqual(len(tasks(self.root)), 1)
        path = self.root / "tasks" / f"{tid}.json"
        altered = json.loads(path.read_text(encoding="utf-8"))
        altered["status"] = "VERIFIED"
        path.write_text(json.dumps(altered), encoding="utf-8")
        with self.assertRaisesRegex(PortableError, "integrity"):
            show(self.root, tid)

    def test_invalid_ids_rejected(self):
        with self.assertRaises(PortableError):
            show(self.root, "../state/authority.json")

    def test_evidence_records_review_only(self):
        item = self.new()
        source = self.sources / "report.txt"
        source.write_text("test output", encoding="utf-8")
        ev = attach(self.root, item["task_id"], str(source), source_root=self.sources)
        recorded = show(self.root, item["task_id"])
        self.assertEqual(recorded["status"], "REVIEW_PENDING")
        self.assertFalse(recorded["verified"])
        data = (self.root / "artifacts" / item["task_id"] / (ev["evidence_id"] + ".bin")).read_bytes()
        self.assertEqual(data, source.read_bytes())

    def test_disallow_credentials_and_external_sources(self):
        item = self.new()
        bad = self.sources / "credentials.json"
        bad.write_text("secret", encoding="utf-8")
        with self.assertRaises(PortableError):
            attach(self.root, item["task_id"], str(bad), self.sources)
        other = self.sources / "harmless.txt"
        other.write_text("test", encoding="utf-8")
        with self.assertRaises(PortableError):
            attach(self.root, item["task_id"], str(other))

    def test_doctor_no_provider_calls(self):
        info = doctor(self.root)
        self.assertEqual(info["ide_dependency"], "NONE")
        self.assertEqual(info["external_calls_performed"], 0)

    def test_execute_invalid_contract_fails_closed(self):
        item = self.new()
        with self.assertRaises(PortableError):
            execute_gated(self.root, item["task_id"], "../secrets.json", "../secrets.json")
        self.assertEqual(show(self.root, item["task_id"])["status"], "SUBMITTED")

    def test_preflight_timeout_never_becomes_retryable(self):
        item = self.new()
        plan = self.sources / 'plan.json'
        inv = self.sources / 'invoke.json'
        plan.write_text(json.dumps({'call': {'model': 'codex'}}), encoding='utf-8')
        inv.write_text(json.dumps({'call': {'model': 'codex'}}), encoding='utf-8')
        with patch('TAKY2.portable_ai.__main__._validate_local_json', side_effect=[plan, inv]):
            with patch('TAKY2.portable_ai.__main__.subprocess.run', side_effect=subprocess.TimeoutExpired('preflight', 1)):
                with self.assertRaises(subprocess.TimeoutExpired):
                    execute_gated(self.root, item['task_id'], str(plan), str(inv))
        self.assertEqual(show(self.root, item['task_id'])['execution']['state'], 'PREFLIGHT_ATTEMPTED_OUTCOME_UNKNOWN')

    def test_dashboard_is_escaped_and_read_only(self):
        self.new()
        class Local(Dashboard):
            root = self.root
        server = ThreadingHTTPServer(("127.0.0.1", 0), Local)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        url = "http://127.0.0.1:{}/".format(server.server_port)
        with urlopen(url, timeout=5) as reply:
            body = reply.read().decode("utf-8")
            self.assertEqual(reply.headers["X-Content-Type-Options"], "nosniff")
        self.assertNotIn("<script>alert(1)</script>", body)
        self.assertIn("&lt;script&gt;", body)
        with self.assertRaises(HTTPError) as err:
            urlopen(Request(url, data=b"edit", method="POST"), timeout=5)
        self.assertEqual(err.exception.code, 405)
        err.exception.close()

if __name__ == "__main__":
    unittest.main()
