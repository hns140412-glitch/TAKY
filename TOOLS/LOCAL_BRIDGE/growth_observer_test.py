import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from growth_observer import observe, manifest


class GrowthObservationTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.base = Path(t.name)
        self.source = self.base / "vault"
        self.source.mkdir()
        (self.source / "source.txt").write_text("original", encoding="utf-8")
        self.config = {"schema": "TAKY_OBSERVATION_SCOPE_V1",
                       "source_root": str(self.source),
                       "sources": [{"source_id": "S-1", "relative_path": "source.txt",
                                    "owner": "MINING", "kind": "SOURCE_RAW"}]}

    def test_first_then_unchanged_then_changed(self):
        a = observe(self.config, self.base / "a")
        self.assertEqual(a["entries"][0]["status"], "FIRST_OBSERVATION")
        self.assertFalse(a["canonical_promotion"])
        self.assertFalse(a["learning_verified"])
        self.assertEqual(a["drive_sync_freshness"], "NOT_VERIFIED")
        prior = self.base / "a" / "OBSERVATION_RECEIPT.json"
        b = observe(self.config, self.base / "b", prior)
        self.assertEqual(b["entries"][0]["status"], "UNCHANGED")
        (self.source / "source.txt").write_text("changed", encoding="utf-8")
        c = observe(self.config, self.base / "c", self.base / "b" / "OBSERVATION_RECEIPT.json")
        self.assertEqual(c["entries"][0]["status"], "CHANGED")
        self.assertEqual(c["entries"][0]["route_hint"], "MINING_OWNER_REVIEW")
        self.assertFalse(c["entries"][0]["content_exported"])

    def test_missing_does_not_become_new(self):
        self.config["sources"][0]["relative_path"] = "not-there.txt"
        result = observe(self.config, self.base / "report")
        self.assertEqual(result["entries"][0]["status"], "MISSING")
        self.assertIsNone(result["entries"][0]["sha256"])

    def test_scope_change_refuses_false_delta(self):
        observe(self.config, self.base / "a")
        self.config["sources"][0]["owner"] = "INDEX"
        with self.assertRaisesRegex(ValueError, "PREVIOUS_SCOPE_MISMATCH"):
            observe(self.config, self.base / "b", self.base / "a" / "OBSERVATION_RECEIPT.json")

    def test_reject_root_escapes_and_duplicates(self):
        self.config["sources"][0]["relative_path"] = "../secret.txt"
        with self.assertRaises(ValueError):
            manifest(self.config)
        self.config["sources"][0]["relative_path"] = "source.txt"
        self.config["sources"].append(dict(self.config["sources"][0]))
        with self.assertRaisesRegex(ValueError, "INVALID_OR_DUPLICATE"):
            manifest(self.config)

    def test_no_write_to_source_or_overwrite_reports(self):
        result = observe(self.config, self.base / "report")
        self.assertEqual((self.source / "source.txt").read_text(), "original")
        with self.assertRaisesRegex(ValueError, "REPORT_ALREADY_EXISTS"):
            observe(self.config, self.base / "report")
        with self.assertRaisesRegex(ValueError, "REPORT_INSIDE_SOURCE_ROOT"):
            observe(self.config, self.source / "report")

    def test_owner_routes_are_hints_not_engine_result(self):
        rows = []
        for i, kind in enumerate(("SOURCE_RAW", "INDEX_OWNER_RECEIPT", "LEARNING_VERIFIED_RECEIPT", "OUTCOME_EVIDENCE", "CURRENT_CHECKPOINT")):
            filename = f"s{i}.txt"
            (self.source / filename).write_text(kind)
            rows.append({"source_id": f"ID-{i}", "relative_path": filename, "owner": kind, "kind": kind})
        self.config["sources"] = rows
        result = observe(self.config, self.base / "report")
        self.assertEqual(len(result["entries"]), 5)
        self.assertTrue(all(not x["owner_promotion_authorized"] for x in result["entries"]))
        self.assertTrue(all(x["route_hint"].endswith("_OWNER_REVIEW") for x in result["entries"]))


if __name__ == "__main__":
    unittest.main()
