#!/usr/bin/env python3
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from source_inventory_omission_gate import check

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class InventoryOmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.inv = root / "independent-source-inventory.json"
        self.out = root / "candidate-coverage.json"
        self.source = {"source_scope":"conversation:1-2", "source_revision":"rev-1",
            "coverage_status":"SOURCE_RECOVERED","source_items":[
                {"source_id":"D1","type":"DECISION","source_pointer":"conversation:1",
                 "content_sha256":"a"*64,"classification":"PRESERVE"},
                {"source_id":"C2","type":"CORRECTION","source_pointer":"conversation:2",
                 "content_sha256":"b"*64,"classification":"ADJUST"}]}
        self.inv.write_text(json.dumps(self.source),encoding="utf-8")
        self.coverage = {"source_revision":"rev-1","inventory_sha256":sha(self.inv),
            "coverage_items":[
                {"source_id":"D1","content_sha256":"a"*64,"classification":"PRESERVE",
                 "recoverable_pointer":"snapshot:D1"},
                {"source_id":"C2","content_sha256":"b"*64,"classification":"ADJUST",
                 "handoff_location":"HANDOFF.md#correction","correction_linkage":["D1"]}]}
    def run_gate(self):
        self.out.write_text(json.dumps(self.coverage),encoding="utf-8")
        return check(self.inv,self.out)
    def test_complete_pass(self):
        self.assertEqual(self.run_gate(),[])
    def test_silent_omission_fails_even_if_candidate_self_counts_pass(self):
        self.coverage["coverage_items"].pop()
        self.assertTrue(any("OMITTED_SOURCE_ITEM: C2" in e for e in self.run_gate()))
    def test_correction_linkage_fails(self):
        self.coverage["coverage_items"][1].pop("correction_linkage")
        self.assertTrue(any("CORRECTION_LINKAGE_MISSING" in e for e in self.run_gate()))
    def test_content_drift_fails(self):
        self.coverage["coverage_items"][0]["content_sha256"]="x"*64
        self.assertTrue(any("SOURCE_CONTENT_DRIFT" in e for e in self.run_gate()))
    def test_inventory_change_requires_reconciliation(self):
        self.source["source_items"].append({"source_id":"D3","type":"DECISION",
          "source_pointer":"conversation:3","content_sha256":"c"*64,"classification":"PRESERVE"})
        self.inv.write_text(json.dumps(self.source),encoding="utf-8")
        errors=self.run_gate()
        self.assertTrue(any("OMITTED_SOURCE_ITEM: D3" in e for e in errors))
        self.assertIn("inventory_sha256 mismatch: candidate must bind to frozen source inventory",errors)
    def test_unrecovered_scope_cannot_pass(self):
        self.source["coverage_status"]="PARTIAL"
        self.inv.write_text(json.dumps(self.source),encoding="utf-8")
        self.coverage["inventory_sha256"]=sha(self.inv)
        self.assertTrue(any("source coverage not established" in e for e in self.run_gate()))

if __name__ == "__main__":
    unittest.main()
