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
  self.manifest={"scope_id":"case-1","scope_boundary":"fixture raw.md only","unavailable_sources":[],"excluded_lines":[],"raw_sources":[{"source_id":"R1","path":"raw.md","sha256":h(self.raw.read_bytes())}],"material_items":self.items}
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
 def test_unlisted_raw_line_fails_even_when_inventory_and_handoff_agree(self):
  self.raw.write_text("Original decision A.\nLater correction B.\nForgotten requirement C.\n")
  self.manifest["raw_sources"][0]["sha256"]=h(self.raw.read_bytes())
  self.assertTrue(any("UNACCOUNTED_RAW_LINE: R1:3" in x for x in self.run_audit()))
 def test_unlisted_material_same_line_fails(self):
  # A quote covering any part of a line must not certify the rest of that line.
  self.raw.write_text("Original decision A. Forgotten requirement C.\nLater correction B.\n",encoding="utf-8")
  self.manifest["raw_sources"][0]["sha256"]=h(self.raw.read_bytes())
  self.assertTrue(any("PARTIAL_RAW_LINE_COVERAGE: R1:1" in x for x in self.run_audit()))
 def test_partial_quote_cannot_be_hidden_by_whole_line_exclusion(self):
  self.raw.write_text("Original decision A. Hidden requirement C.\nLater correction B.\n",encoding="utf-8")
  self.manifest["raw_sources"][0]["sha256"]=h(self.raw.read_bytes())
  self.manifest["excluded_lines"]=[{"raw_source_id":"R1","line":1,"reason":"ignore rest"}]
  self.assertTrue(any("EXCLUDED_BUT_MATERIAL: R1:1" in x for x in self.run_audit()))
 def test_exclusion_requires_reason(self):
  self.raw.write_text("Original decision A.\nLater correction B.\nNonmaterial greeting.\n")
  self.manifest["raw_sources"][0]["sha256"]=h(self.raw.read_bytes())
  self.manifest["excluded_lines"]=[{"raw_source_id":"R1","line":3,"reason":""}]
  self.assertTrue(any("INVALID_EXCLUSION" in x for x in self.run_audit()))
 def test_explicit_nonmaterial_exclusion_passes(self):
  self.raw.write_text("Original decision A.\nLater correction B.\nNonmaterial greeting.\n")
  self.manifest["raw_sources"][0]["sha256"]=h(self.raw.read_bytes())
  self.manifest["excluded_lines"]=[{"raw_source_id":"R1","line":3,"reason":"nonmaterial greeting"}]
  self.assertEqual([],self.run_audit())
 def test_missing_quote(self):
  self.items[1]["exact_quote"]="Never said this"
  self.assertTrue(any("RAW_QUOTE_NOT_UNIQUE_OR_MISSING" in x for x in self.run_audit()))
 def test_unresolved_correction_target(self):
  self.items[1]["correction_targets"]=["unknown"]
  self.assertTrue(any("CORRECTION_TARGET_UNRESOLVED" in x for x in self.run_audit()))
 def test_real_repo_command_contract_scope_detects_three_handoff_omissions(self):
  # An actual checked-out source section, not a handwritten synthetic conversation.
  # Claim boundary: this section only; not all chat history or a full bundle acceptance.
  contract=(Path(__file__).resolve().parents[1]/"OS"/"COMMAND_INTERACTION.md").read_text(encoding="utf-8")
  heading="## 0.3 Natural `재개` / `재개준비` command — HARD LOCK"
  self.assertIn(heading,contract)
  excerpt=contract[contract.index(heading):].split("## 1. COMMAND DISCOVERY",1)[0]
  lines=[line for line in excerpt.splitlines() if line.strip()]
  self.assertEqual(len(lines),len(set(lines)),"source quotes must be unique")
  self.raw.write_text(excerpt,encoding="utf-8")
  self.items=[{"source_id":f"CMD03-L{n}","raw_source_id":"CMD03",
               "exact_quote":line,"content_sha256":h(line.encode("utf-8")),
               "classification":"PRESERVE","type":"DECISION"}
              for n,line in enumerate(lines,1)]
  self.manifest={"scope_id":"repo:OS/COMMAND_INTERACTION.md#0.3",
                 "scope_boundary":"checked-out actual command contract section 0.3 only; no historical chat coverage claim",
                 "unavailable_sources":[],"excluded_lines":[],
                 "raw_sources":[{"source_id":"CMD03","path":"raw.md","sha256":h(self.raw.read_bytes())}],
                 "material_items":self.items}
  self.inventory={"source_scope":self.manifest["scope_id"],"source_revision":"checked-out-0.3",
                  "coverage_status":"SOURCE_RECOVERED","source_items":[
                   {"source_id":x["source_id"],"source_pointer":f'raw:CMD03#{x["source_id"]}',
                    "content_sha256":x["content_sha256"],"classification":"PRESERVE"}
                    for x in self.items]}
  self.coverage={"source_revision":"checked-out-0.3","coverage_items":[
                 {"source_id":x["source_id"],"content_sha256":x["content_sha256"],
                  "classification":"PRESERVE","recoverable_pointer":f'raw:CMD03#{x["source_id"]}'}
                  for x in self.items]}
  self.assertEqual([],self.run_audit())
  for label,needle in (("decision","A standalone `재개`"),
                       ("latest override","Read the ENTIRE latest relevant HANDOFF"),
                       ("user correction","Do not stop at a status recital.")):
   with self.subTest(omission=label):
    candidate=next(x for x in self.items if needle in x["exact_quote"])
    old=self.coverage["coverage_items"]
    self.coverage["coverage_items"]=[x for x in old if x["source_id"]!=candidate["source_id"]]
    errors=self.run_audit()
    self.assertIn(f'OMITTED_SOURCE_ITEM: {candidate["source_id"]}',errors)
    self.coverage["coverage_items"]=old
if __name__=="__main__":unittest.main()
