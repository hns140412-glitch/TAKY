"""Real verified Play Camp browser receipt -> transient central events -> durable candidate."""
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import global_source_live_consumer as live
import local_feedback_candidate_journal as journal

class RealBrowserFeedbackE2ETest(unittest.TestCase):
    def test_existing_browser_receipt_survives_disposable_db_cleanup(self):
        import central_review_source_intake as intake
        import taky_central_source_factory as factory
        with tempfile.TemporaryDirectory(prefix="taky_feedback_real_e2e_") as tmp:
            db=Path(tmp)/"test.sqlite3"
            with closing(factory.connect(db)) as c, c:
                intake.advance_verified_review_pipeline(c,intake.verified_documents())
                verified=live.reconcile_verified_live_receipts(c)
            self.assertGreaterEqual(verified["run_count"],1)
            destination=Path(tmp)/"journal"
            with patch.object(journal,"JOURNAL",destination):
                outcome=journal.persist(verified,destination)
                self.assertGreaterEqual(outcome["new_files"],1)
                self.assertEqual(journal.persist(verified,destination)["new_files"],0)
            self.assertFalse(verified["run_details"][0]["semantic_approved"])
            self.assertFalse(verified["run_details"][0]["knowledge_approved"])
            self.assertTrue(destination.is_dir())
            self.assertEqual(len(list(destination.glob("*.json"))),verified["run_count"])
            self.assertEqual(outcome["educational_learning_updates"],0)

if __name__=="__main__":
    unittest.main()
