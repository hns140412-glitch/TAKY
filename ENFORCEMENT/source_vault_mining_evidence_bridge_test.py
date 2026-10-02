#!/usr/bin/env python3
"""Offline only. Synthetic local fixtures; no real Notion bodies, secrets, or network."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from source_vault_mining_evidence_bridge import prepare, verified_text, InputError
from source_vault_external_acquisition import OUTPUT, SCHEMA as LEDGER_SCHEMA
from source_vault_handoff_bridge import REQUIRED


def sha(b):
    return hashlib.sha256(b).hexdigest()


class VaultToMiningInputTest(unittest.TestCase):
    def case(self, td, *, child=False, source_url="https://example.org/official"):
        root=Path(td)
        pid="synthetic-page-1"
        fingerprint="a"*64
        folder=root/"data"/"notion_incremental"/"snapshots"/pid/fingerprint
        folder.mkdir(parents=True)
        block={"id":"paragraph-1", "type":"paragraph",
               "paragraph":{"rich_text":[{"plain_text":"Source statement from Notion"}]},
               "has_children":False}
        if child:
            block={"id":"child-1","type":"child_page","child_page":{"title":"other"},"has_children":False}
        original=json.dumps([block]).encode("utf8")
        (folder/"blocks.json").write_bytes(original)
        report=root/"reports";report.mkdir()
        row={"notion_page_id":pid,"block_status":"OK","mining_status":"PENDING_NOT_PROMOTED",
             "block_snapshot_folder":str(folder),"url":source_url}
        (report/"INCREMENTAL_QUEUE.json").write_text(json.dumps([row]),encoding="utf8")
        (report/"MINING_INBOX_HANDOFF.json").write_text(json.dumps({"items":[row]}),encoding="utf8")
        (report/"INCREMENTAL_SUMMARY.json").write_text(json.dumps({"queue_count":1,"notion_total":1}),encoding="utf8")
        current=root/"data"/"notion_incremental"/"CURRENT.json"
        current.parent.mkdir(parents=True,exist_ok=True)
        current.write_text(json.dumps({"entries":{pid:{
            "block_status":"OK","block_fingerprint":fingerprint,
            "block_snapshot_folder":str(folder),
            "checked_at":"2026-09-28T01:00:00Z"}}}),encoding="utf8")
        return root,report,pid,sha(original)

    def ledger(self,root,report,pid,*,body=b"<html><p>External original</p><script>IGNORE_ME</script></html>",
               content_type="text/html",url="https://example.org/official"):
        rel=Path("data")/"notion_incremental"/"acquired_external"/"fake-source"/"original.html"
        target=root/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
        hashes={name:sha((report/name).read_bytes()) for name in REQUIRED}
        event={"event_id":"synthetic-event-1","source_id":"notion:"+pid,"url":url,
               "state":"ACQUIRED_AND_PRESERVED","sha256":sha(body),
               "preserved_relative_path":str(rel),"recorded_at":"2026-09-29T00:00:00Z",
               "content_type":content_type}
        (report/OUTPUT).write_text(json.dumps({"schema":LEDGER_SCHEMA,"append_only":True,
            "last_input_hashes":hashes,"entries":[event]}),encoding="utf8")
        return target

    def test_notions_verified_bytes_are_only_candidate_not_external_original(self):
        with tempfile.TemporaryDirectory() as td:
            root,report,pid,hash_original=self.case(td)
            before={name:sha((report/name).read_bytes()) for name in REQUIRED}
            receipt=prepare(report,root)
            self.assertEqual(receipt["counts"],{"notion_blocks":1,"public_original":0,"held":1})
            snap=receipt["source_snapshots"][0]
            self.assertEqual(snap["schema"],"TAKY_MINING_SOURCE_SNAPSHOT_V1")
            self.assertEqual(snap["source_id"],"notion:"+pid+":notion_blocks")
            self.assertEqual(snap["source_locator"],"notion:"+pid)
            self.assertEqual(snap["source_scope"],"NOTION_BLOCK_TEXT_ONLY")
            self.assertEqual(snap["original_sha256"],hash_original)
            self.assertEqual(snap["source_sha256"],sha(snap["source_text"].encode("utf8")))
            self.assertIsNone(snap["source_updated_at"])
            self.assertEqual(snap["fragment_anchors"][0]["block_id"],"paragraph-1")
            for key in ("semantic_mining_executed","indexing_executed","queue_acknowledged","canonical_promotion","mining_frontier_generated"):
                self.assertFalse(receipt[key],key)
            self.assertEqual(receipt["claim_reviews"],[])
            self.assertEqual({name:sha((report/name).read_bytes()) for name in REQUIRED},before)

    def test_adapter_time_does_not_fake_old_capture_recency(self):
        with tempfile.TemporaryDirectory() as td:
            root, report, pid, _ = self.case(td, source_url="")
            receipt = prepare(report, root)
            snapshot = receipt["source_snapshots"][0]
            self.assertEqual(snapshot["retrieved_at"],"2026-09-28T01:00:00+00:00")
            self.assertNotEqual(snapshot["retrieved_at"],receipt["created_at"])
            self.assertEqual(snapshot["retrieval_state"],"FETCHED")
            (root/"data"/"notion_incremental"/"CURRENT.json").unlink()
            unknown = prepare(report, root)
            self.assertIsNone(unknown["source_snapshots"][0]["retrieved_at"])
            self.assertEqual(unknown["source_snapshots"][0]["retrieval_state"],
                             "CAPTURE_TIME_UNVERIFIED")
            self.assertIn("NOTION_CAPTURE_TIME_NOT_MATCHED_TO_CURRENT_STATE",
                          unknown["held"][0]["reason"])

    def test_partial_text_kept_with_media_gap_and_not_fake_full(self):
        with tempfile.TemporaryDirectory() as td:
            root, report, pid, _ = self.case(td, source_url="")
            queue=json.loads((report/"INCREMENTAL_QUEUE.json").read_text())
            folder=Path(queue[0]["block_snapshot_folder"])
            blocks=json.loads((folder/"blocks.json").read_text())
            blocks.append({"id":"image-1","type":"image",
                           "image":{"file":{"url":"https://signed.invalid/example"},"caption":[]},
                           "has_children":False})
            (folder/"blocks.json").write_text(json.dumps(blocks),encoding="utf8")
            receipt=prepare(report,root)
            self.assertEqual(receipt["counts"]["notion_blocks"],1)
            snapshot=receipt["source_snapshots"][0]
            self.assertEqual(snapshot["source_scope"],"NOTION_BLOCK_TEXT_PARTIAL")
            self.assertEqual(snapshot["source_completeness"],"PARTIAL_UNRESOLVED_CONTENT")
            self.assertIn("IMAGE_CONTENT_NOT_OCR_EXTRACTED",snapshot["unresolved_parts"])
            self.assertEqual(snapshot["source_text"],"Source statement from Notion")
            self.assertTrue(any(x["part"]=="UNRESOLVED_NOTION_MATERIAL"
                                for x in receipt["held"]))
            self.assertFalse(receipt["semantic_mining_executed"])

    def test_verified_public_bytes_separate_and_script_invisible(self):
        with tempfile.TemporaryDirectory() as td:
            root,report,pid,_=self.case(td)
            self.ledger(root,report,pid)
            r=prepare(report,root)
            self.assertEqual(r["counts"],{"notion_blocks":1,"public_original":1,"held":0})
            snap=next(x for x in r["source_snapshots"] if x["source_scope"]=="PUBLIC_TEXT_ORIGINAL")
            self.assertEqual(snap["source_locator"],"https://example.org/official")
            self.assertEqual(snap["source_id"],"notion:"+pid+":public_original")
            self.assertIn("External original",snap["source_text"])
            self.assertNotIn("IGNORE_ME",snap["source_text"])
            self.assertNotEqual(snap["source_sha256"],snap["original_sha256"])
            self.assertFalse(r["semantic_mining_executed"])
            self.assertEqual(r["claim_reviews"],[])

    def test_replaced_or_missing_original_never_counts_as_acquired(self):
        with tempfile.TemporaryDirectory() as td:
            root,report,pid,_=self.case(td)
            target=self.ledger(root,report,pid)
            target.write_text("tampered bytes",encoding="utf8")
            r=prepare(report,root)
            self.assertEqual(r["counts"]["public_original"],0)
            self.assertIn("EXTERNAL_BYTES_MISSING_OR_HASH_CHANGED",r["held"][-1]["reason"])

    def test_stale_ledger_input_revision_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root,report,pid,_=self.case(td)
            self.ledger(root,report,pid)
            (report/"INCREMENTAL_SUMMARY.json").write_text(json.dumps({
                "queue_count":1,"notion_total":1,"changed_since_prior":True}),encoding="utf8")
            with self.assertRaisesRegex(InputError,"EXTERNAL_LEDGER_INPUT_REVISION_MISMATCH"):
                prepare(report,root)

    def test_child_page_is_not_claimed_as_full_page(self):
        with tempfile.TemporaryDirectory() as td:
            root,report,pid,_=self.case(td,child=True,source_url="")
            r=prepare(report,root)
            self.assertEqual(r["counts"]["notion_blocks"],0)
            self.assertTrue(any("CHILD_PAGE_NOT_RECURSIVELY_ACQUIRED" in x["reason"] for x in r["held"]))
            self.assertEqual(r["source_snapshots"],[])

    def test_bad_media_or_decoding_stays_hold(self):
        for body,mime in [(b"\x00\x01fake","application/pdf"),(b"\xff\xfe","text/plain")]:
            with self.subTest(mime=mime):
                with tempfile.TemporaryDirectory() as td:
                    root,report,pid,_=self.case(td)
                    self.ledger(root,report,pid,body=body,content_type=mime)
                    r=prepare(report,root)
                    self.assertEqual(r["counts"]["public_original"],0)
                    self.assertEqual(r["counts"]["notion_blocks"],1)
                    self.assertEqual(r["counts"]["held"],1)

    def test_unequal_url_flags_not_silently_selected(self):
        with tempfile.TemporaryDirectory() as td:
            root,report,pid,_=self.case(td)
            q=json.loads((report/"INCREMENTAL_QUEUE.json").read_text())
            q[0]["normalized_url"]="https://unrelated.example/alternate"
            for name,data in (("INCREMENTAL_QUEUE.json",q),("MINING_INBOX_HANDOFF.json",{"items":q})):
                (report/name).write_text(json.dumps(data),encoding="utf8")
            r=prepare(report,root)
            self.assertEqual(r["counts"]["public_original"],0)
            self.assertEqual(r["counts"]["notion_blocks"],1)
            self.assertEqual(r["claim_reviews"],[])
            self.assertFalse(r["canonical_promotion"])

    def test_report_location_must_be_inside_vault(self):
        with tempfile.TemporaryDirectory() as td:
            root,report,pid,_=self.case(td)
            with self.assertRaisesRegex(InputError,"REPORTS_OUTSIDE_VAULT"):
                prepare(Path(td).parent,root)


if __name__=="__main__":
    unittest.main()
