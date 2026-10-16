"""Full original 12 document integration into disposable central SQLite only."""
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
import central_review_source_intake as intake
import taky_central_source_factory as central

class CentralReviewIntake(unittest.TestCase):
    def test_sources_are_persisted_without_semantic_approval(self):
        docs=intake.verified_documents()
        self.assertEqual(len(docs),12)
        self.assertEqual(sum(x["mined_units"] for x in docs),332)
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/"central_review.sqlite3"
            with closing(central.connect(db)) as c, c:
                before=central.report(c)["source_records"]
                first=intake.ingest(c,docs)
                self.assertEqual(first["created"],12)
                self.assertEqual(first["forming_promoted"],0)
                self.assertEqual(first["learning_consumed"],0)
                detail=intake.index_extractive_details(c,docs)
                self.assertEqual(detail["units_new"],332)
                self.assertEqual(detail["semantically_reviewed"],0)
                self.assertEqual(intake.index_extractive_details(c,docs)["units_new"],0)
                # Entire hash-verified section must be searchable, not just
                # first 2,000 chars: 35 real sections exceed that cap.
                self.assertEqual(c.execute(
                    "SELECT COUNT(*) FROM evidence_unit WHERE LENGTH(excerpt)>2000"
                    ).fetchone()[0],35)
                longrow=c.execute("""SELECT source_id,unit_id,content_sha256,excerpt
                  FROM evidence_unit WHERE LENGTH(excerpt)>4000 LIMIT 1""").fetchone()
                import re
                match=re.search(r"[A-Za-z0-9_-]{12,}",longrow["excerpt"][2600:])
                self.assertIsNotNone(match)
                tail_term=match.group(0)
                self.assertTrue(any(x["unit_id"]==longrow["unit_id"] for x in
                   central.find_evidence_units(c,tail_term,
                     source_id=longrow["source_id"])))
                # Repair a known legacy prefix-only entry from trusted RAW.
                c.execute("UPDATE evidence_unit SET excerpt=? WHERE source_id=? AND unit_id=?",
                    (longrow["excerpt"][:2000],longrow["source_id"],longrow["unit_id"]))
                self.assertFalse(any(x["unit_id"]==longrow["unit_id"] for x in
                    central.find_evidence_units(c,tail_term,
                      source_id=longrow["source_id"])))
                self.assertEqual(intake.index_extractive_details(c,docs)["units_new"],1)
                self.assertTrue(any(x["unit_id"]==longrow["unit_id"] for x in
                    central.find_evidence_units(c,tail_term,
                      source_id=longrow["source_id"])))
                source_id="raw:"+docs[7]["raw_sha256"]
                hits=central.find_evidence_units(c,"structured accessibility",source_id=source_id)
                self.assertGreaterEqual(len(hits),1)
                original=central.read_verified_evidence_unit(c,source_id,hits[0]["unit_id"])
                self.assertIn("structured accessibility snapshots",original["content"])
                self.assertEqual(original["source_authority"],"UNREVIEWED")
                self.assertFalse(original["forming_authorized"])
                before_sha=hits[0]["content_sha256"]
                c.execute("UPDATE evidence_unit SET content_sha256=? WHERE source_id=? AND unit_id=?",
                  ("0"*64,source_id,hits[0]["unit_id"]))
                with self.assertRaisesRegex(ValueError,"DETAIL_SOURCE_UNIT_HASH_MISMATCH"):
                    central.read_verified_evidence_unit(c,source_id,hits[0]["unit_id"])
                c.execute("UPDATE evidence_unit SET content_sha256=? WHERE source_id=? AND unit_id=?",
                  (before_sha,source_id,hits[0]["unit_id"]))
                self.assertIn("structured accessibility",central.read_verified_evidence_unit(
                  c,source_id,hits[0]["unit_id"])["content"])
                reviewed=intake.attach_selected_semantic_claims(c,docs)
                self.assertEqual(reviewed["updated"],12)
                self.assertEqual(reviewed["claim_count"],12)
                self.assertEqual(intake.attach_selected_semantic_claims(c,docs)["updated"],0)
                analyze=c.execute(
                  "SELECT receipt_json FROM stage WHERE source_id=? AND stage='ANALYZE'",
                  ("raw:"+docs[7]["raw_sha256"],)).fetchone()
                candidate=__import__("json").loads(analyze["receipt_json"])
                self.assertIn("structured accessibility snapshots",candidate["claim_phrase"])
                self.assertFalse(candidate["independent_semantic_approval"])
                feedback=intake.record_existing_adoption_observation(c)
                self.assertEqual(feedback["observed_local_scenarios"],4)
                self.assertEqual(feedback["observed_local_steps"],14)
                self.assertFalse(feedback["learning_promoted"])
                self.assertTrue(feedback["inserted_new_event"])
                again=intake.record_existing_adoption_observation(c)
                self.assertEqual(again["event_id"],feedback["event_id"])
                self.assertFalse(again["inserted_new_event"])
                learning=intake.learn_from_observed_local_method(c)
                self.assertEqual(learning["reference_learning_state"],"EVIDENCE_CANDIDATE")
                self.assertTrue(learning["inserted_new_learning_event"])
                self.assertEqual(learning["origin_consumption_event_id"],feedback["event_id"])
                self.assertEqual(learning["learned_reference"]["canonical_promotion"],False)
                repeated_learning=intake.learn_from_observed_local_method(c)
                self.assertFalse(repeated_learning["inserted_new_learning_event"])
                self.assertEqual(repeated_learning["learning_event_id"],learning["learning_event_id"])
                item_id="raw:"+docs[7]["raw_sha256"]
                source_claim=c.execute("SELECT receipt_json FROM stage WHERE source_id=? AND stage='ANALYZE'",(item_id,)).fetchone()["receipt_json"]
                modified=__import__("json").loads(source_claim)
                modified["source_chunk_sha256"]="0"*64
                c.execute("UPDATE stage SET receipt_json=? WHERE source_id=? AND stage='ANALYZE'",
                    (__import__("json").dumps(modified),item_id))
                with self.assertRaisesRegex(ValueError,"CENTRAL_DETAIL_ANCHOR_REQUIRED"):
                    intake.learn_from_observed_local_method(c)
                c.execute("UPDATE stage SET receipt_json=? WHERE source_id=? AND stage='ANALYZE'",
                    (source_claim,item_id))
                # Without a Central DETAIL unit even authentic RAW is not
                # enough to sneak into SYSTEM_GROW Learning.
                c.execute("SAVEPOINT missing_index_detail")
                c.execute("DELETE FROM evidence_unit WHERE source_id=? AND content_sha256=?",
                   (item_id,before_sha))
                with self.assertRaisesRegex(ValueError,"CENTRAL_DETAIL_ANCHOR_REQUIRED"):
                    intake.learn_from_observed_local_method(c)
                c.execute("ROLLBACK TO SAVEPOINT missing_index_detail")
                c.execute("RELEASE SAVEPOINT missing_index_detail")
                self.assertFalse(intake.learn_from_observed_local_method(c)["inserted_new_learning_event"])
                full=intake.advance_verified_review_pipeline(c,docs)
                self.assertEqual(full["verified_source_count"],12)
                self.assertEqual(full["created_sources"],0)
                self.assertEqual(full["new_analysis_reviews"],0)
                self.assertEqual(full["new_detail_units"],0)
                self.assertEqual(full["durable_detail_units"],332)
                self.assertFalse(full["new_consumption_event"])
                self.assertFalse(full["new_learning_event"])
                self.assertEqual(full["local_consumption_event_id"],feedback["event_id"])
                self.assertEqual(full["global_ai_learning_event_id"],learning["learning_event_id"])
                status=intake.readback(c,docs)
                self.assertEqual(len(status),12)
                self.assertEqual(central.report(c)["source_records"]-before,12)
            with closing(sqlite3.connect(str(db))) as c, c:
                self.assertEqual(c.execute("SELECT COUNT(*) FROM event WHERE kind='ANCHOR_VERIFIED_REVIEW_SOURCE_IMPORTED'").fetchone()[0],12)
                self.assertEqual(c.execute("SELECT COUNT(*) FROM event WHERE kind='LOCAL_TECHNIQUE_USE_FEEDBACK_CANDIDATE'").fetchone()[0],1)
                self.assertEqual(c.execute("SELECT COUNT(*) FROM evidence_unit").fetchone()[0],332)
            with closing(central.connect(db)) as c, c:
                second=intake.ingest(c,docs)
                self.assertEqual(second["created"],0)
                self.assertEqual(second["reused"],12)
                self.assertEqual(central.report(c)["source_records"],12)
            with closing(central.connect(db)) as c, c:
                altered=[dict(x) for x in docs]
                altered[5]["raw_sha256"]="0"*64
                with self.assertRaises(ValueError):
                    with c:
                        intake.ingest(c,altered)
                self.assertEqual(central.report(c)["source_records"],12)
            with closing(central.connect(db)) as c, c:
                self.assertEqual(intake.readback(c,docs)[7]["source_id"],
                    "USER_REVIEW:1fe7096c36a73359acf8")
            print("CENTRAL_REVIEW_SOURCE_INGEST_PASS source=12 anchored_units=332 idempotence=yes stage_authority=UNREVIEWED db=temp_only")
    def test_global_entrypoint_reconciles_new_live_receipts(self):
        docs=intake.verified_documents()
        with tempfile.TemporaryDirectory() as tmp:
            with closing(central.connect(Path(tmp)/"global_live.sqlite3")) as c, c:
                first=intake.advance_verified_review_pipeline(
                    c,docs,reconcile_live_feedback=True)
                second=intake.advance_verified_review_pipeline(
                    c,docs,reconcile_live_feedback=True)
                initial=first["live_feedback_reconciliation"]
                after=second["live_feedback_reconciliation"]
                self.assertIn("taky-live-playcamp-20261014-1512",
                              initial["run_ids"])
                self.assertGreaterEqual(initial["new_feedback_event_count"],1)
                self.assertEqual(after["new_feedback_event_count"],0)
                self.assertTrue(initial["all_semantic_approval_blocked"])
                self.assertFalse(first["forming_promoted"])
                self.assertEqual(first["durable_detail_units"],332)
                self.assertEqual(second["new_detail_units"],0)

    def test_feedback_cli_requires_disposable_storage(self):
        import subprocess
        import sys
        result=subprocess.run([sys.executable,"-B",str(Path(intake.__file__)),
             "--advance-existing-pipeline","--replay-verified-local-feedback"],
             capture_output=True,text=True,encoding="utf-8",timeout=20)
        self.assertEqual(result.returncode,2)
        self.assertIn("disposable --db",result.stderr)

    def test_optional_consumer_feedback_in_existing_pipeline(self):
        import global_source_learning_feedback as feedback
        docs=intake.verified_documents()
        with tempfile.TemporaryDirectory() as tmp:
            with closing(central.connect(Path(tmp)/"isolated.sqlite3")) as c, c:
                first=intake.advance_verified_review_pipeline(
                    c,docs,replay_verified_local_feedback=True)
                second=intake.advance_verified_review_pipeline(
                    c,docs,replay_verified_local_feedback=True)
                item=first["verified_local_feedback"]
                self.assertEqual((item["before"],item["after"]),
                                 ("LOCAL_EVALUATION_REQUIRED","REUSE_CANDIDATE"))
                self.assertEqual(item["feedback_event_id"],
                                 second["verified_local_feedback"]["feedback_event_id"])
                self.assertEqual(second["new_detail_units"],0)
                self.assertEqual(c.execute("SELECT COUNT(*) FROM event WHERE kind=?",
                                 (feedback.FEEDBACK_KIND,)).fetchone()[0],1)
                self.assertFalse(item["semantic_approved"])
                self.assertFalse(item["global_knowledge_approved"])

if __name__=="__main__":unittest.main()
