#!/usr/bin/env python3
import hashlib,json,tempfile,unittest
from pathlib import Path
from raw_source_resume_audit import audit
def h(b): return hashlib.sha256(b).hexdigest()
class RawResumeAuditTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name)
  self.raw=self.root/"raw.md";self.raw.write_text("Original decision A.\nLater correction B.\n",encoding="utf-8")
  self.m=self.root/"raw_manifest.json";self.i=self.root/"inventory.json";self.o=self.root/"coverage.json"
  self.items=[{"source_id":"D1","raw_source_id":"R1","exact_quote":"Original decision A.","content_sha256":h(b"Original decision A."),"classification":"PRESERVE","type":"DECISION"},
   {"source_id":"C2","raw_source_id":"R1","exact_quote":"Later correction B.","content_sha256":h(b"Later correction B."),"classification":"ADJUST","type":"CORRECTION","correction_targets":["D1"]}]
  self.manifest={"scope_id":"case-1","scope_boundary":"fixture raw.md only","unavailable_sources":[],"raw_sources":[{"source_id":"R1","path":"raw.md","sha256":h(self.raw.read_bytes())}],"material_items":self.items}
  self.inventory={"source_scope":"case-1","source_revision":"rev1","coverage_status":"SOURCE_RECOVERED","source_items":[{"source_id":x["source_id"],"source_pointer":f"raw:R1#{x['source_id']}","content_sha256":x["content_sha256"],"classification":x["classification"]} for x in self.items]}
  self.coverage={"source_revision":"rev1","coverage_items":[{"source_id":x["source_id"],"content_sha256":x["content_sha256"],"classification":x["classification"],"handoff_location":f"HANDOFF.md#{x['source_id']}",**({"correction_linkage":["D1"]} if x["source_id"]=="C2" else {})} for x in self.items]}
 def run_audit(self):
  self.m.write_text(json.dumps(self.manifest),encoding="utf-8")
  self.inventory["raw_manifest_sha256"]=h(self.m.read_bytes())
  self.i.write_text(json.dumps(self.inventory),encoding="utf-8")
  self.coverage["inventory_sha256"]=h(self.i.read_bytes())
  self.o.write_text(json.dumps(self.coverage),encoding="utf-8")
  return audit(self.root,self.m,self.i,self.o)
 def test_valid_recovered_scope(self):self.assertEqual([],self.run_audit())
 def test_raw_file_mutation(self):
  self.raw.write_text("Original decision A.\nDifferent correction B.\n")
  self.assertTrue(any("RAW_SOURCE_DRIFT" in x for x in self.run_audit()))
 def test_manifest_item_missing_from_inventory(self):
  self.inventory["source_items"].pop()
  self.assertTrue(any("RAW_MANIFEST_ITEM_OMITTED_FROM_INVENTORY" in x for x in self.run_audit()))
 def test_inventory_item_missing_from_handoff(self):
  self.coverage["coverage_items"].pop()
  self.assertTrue(any("OMITTED_SOURCE_ITEM" in x for x in self.run_audit()))
 def test_fake_raw_pointer(self):
  self.inventory["source_items"][0]["source_pointer"]="raw:fake"
  self.assertTrue(any("RAW_POINTER_MISMATCH" in x for x in self.run_audit()))
 def test_correction_target_wrong(self):
  self.coverage["coverage_items"][1]["correction_linkage"]=["wrong"]
  self.assertTrue(any("CORRECTION_LINEAGE_DRIFT" in x for x in self.run_audit()))
 def test_unavailable_source_blocks_full_pass(self):
  self.manifest["unavailable_sources"]=["conversation:missing"]
  self.assertTrue(any("UNAVAILABLE_SOURCES" in x for x in self.run_audit()))
 def test_missing_quote(self):
  self.items[1]["exact_quote"]="Never said this"
  self.assertTrue(any("RAW_QUOTE_NOT_UNIQUE_OR_MISSING" in x for x in self.run_audit()))
 def test_unresolved_correction_target(self):
  self.items[1]["correction_targets"]=["unknown"]
  self.assertTrue(any("CORRECTION_TARGET_UNRESOLVED" in x for x in self.run_audit()))
if __name__=="__main__":unittest.main()
