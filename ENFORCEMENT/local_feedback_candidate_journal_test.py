"""Durable local feedback candidates stay outside CURRENT and learner data."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import local_feedback_candidate_journal as journal
import global_source_live_consumer as live
import global_source_learning_feedback as flow


class CandidateJournalTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="taky_feedback_journal_")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/"journal"
        self.sha="a"*64
        self.run="taky-live-test-journal-001"
        self.detail={
            "status":"NEW_LOCAL_BROWSER_RUN_FEEDBACK_RECORDED",
            "run_id":self.run,"receipt_sha256":self.sha,
            "source_id":"raw:"+"b"*64,"raw_sha256":"b"*64,
            "anchor_sha256":"c"*64,"forming_revision":"d"*64,
            "consumer_code_sha256":flow.sha(flow.CODE.read_bytes()),
            "before":"LOCAL_EVALUATION_REQUIRED","after":"REUSE_CANDIDATE",
            "semantic_approved":False,"knowledge_approved":False,
            "production_rollout":False,"current_written":False,
            "operational_db_written":False,"live_browser_evidence":True}
        self.input={"status":"VERIFIED_LOCAL_RECEIPTS_RECONCILED",
                    "run_count":1,"run_details":[self.detail]}
        self.journal_patch=patch.object(journal,"JOURNAL",self.root)
        self.journal_patch.start()
        self.addCleanup(self.journal_patch.stop)
        self.receipt_patch=patch.object(live,"_live_evidence",return_value=self.sha)
        self.receipt_patch.start()
        self.addCleanup(self.receipt_patch.stop)

    def test_append_only_replay_is_idempotent_and_non_authoritative(self):
        first=journal.persist(self.input,self.root)
        second=journal.persist(self.input,self.root)
        self.assertEqual((first["new_files"],second["new_files"]),(1,0))
        self.assertEqual(second["replayed_existing"],1)
        path=Path(first["journal_paths"][0])
        item=json.loads(path.read_text(encoding="utf-8"))
        expected=item.pop("manifest_sha256")
        self.assertEqual(journal.digest(item),expected)
        self.assertFalse(item["educational_learning"])
        self.assertFalse(item["app_consumption_approved"])
        self.assertEqual(item["authority"],"REVIEW_CANDIDATE_NOT_APPROVED")

    def test_fake_runtime_receipt_and_fake_approval_are_rejected(self):
        with patch.object(live,"_live_evidence",return_value="0"*64):
            with self.assertRaisesRegex(ValueError,"RUNTIME_RECEIPT_INVALID"):
                journal.persist(self.input,self.root)
        self.detail["semantic_approved"]=True
        with self.assertRaisesRegex(ValueError,"AUTHORITY_BOUNDARY_FAILED"):
            journal.persist(self.input,self.root)
        self.assertFalse(self.root.exists())

    def test_old_run_id_new_content_is_replay_conflict(self):
        journal.persist(self.input,self.root)
        self.detail["anchor_sha256"]="1"*64
        with self.assertRaisesRegex(ValueError,"FEEDBACK_JOURNAL_REPLAY_CONFLICT"):
            journal.persist(self.input,self.root)
        self.assertEqual(len(list(self.root.glob("*.json"))),1)

    def test_caller_cannot_redirect_journal(self):
        with self.assertRaisesRegex(ValueError,"NOT_CANONICAL"):
            journal.persist(self.input,Path(self.tmp.name)/"wrong")


if __name__=="__main__":
    unittest.main()
