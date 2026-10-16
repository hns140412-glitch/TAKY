"""Full coverage, immutability, and explicit no-approval regression checks."""
import copy
import json
import sqlite3
import unittest
from pathlib import Path

import central_full_anchor_review as full
import central_forming_review_queue as base
import taky_central_source_factory as factory


class FullReviewEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((full.DEST/
          "TAKY_FULL_ANCHOR_REVIEW_875283c73ce17d400ac9.json"
          ).read_text(encoding="utf-8"))
        cls.queue=json.loads((base.EVIDENCE/
          "TAKY_FORMING_REVIEW_QUEUE_4a7c2de00d2e9fc12821.json"
          ).read_text(encoding="utf-8"))

    def test_all_954_anchors_have_unique_original_positions(self):
        d=self.data
        self.assertEqual(base.digest({k:v for k,v in d.items()
            if k!="manifest_sha256"}),d["manifest_sha256"])
        self.assertEqual(d["verified_anchor_count"],954)
        self.assertEqual(d["review_ready_sources"],143)
        self.assertEqual(d["source_count"],166)
        self.assertEqual(len(d["existing_holds"]),23)
        self.assertFalse(d["forming_approved"])
        self.assertFalse(d["learning_consumed"])
        counts={"TEXT_LINE":0,"PDF_PAGE":0}
        positions=set()
        for s in d["projected_sources"]:
            self.assertEqual(len(s["anchors"]),s["full_anchor_count"])
            self.assertEqual(s["review_state"],
                "INDEPENDENT_OWNER_REVIEW_NOT_COMPLETED")
            self.assertEqual(s["approved_claims"],[])
            for a in s["anchors"]:
                counts[a["kind"]]+=1
                pos=(s["source_id"],a["kind"],a["id"])
                self.assertNotIn(pos,positions)
                positions.add(pos)
                self.assertEqual(len(a["content_sha256"]),64)
                for marker in a["lexical_signals"]:
                    self.assertEqual(marker["content_sha256"],
                                     a["content_sha256"])
                    self.assertFalse(marker["legal_validity_verified"])
        self.assertEqual(counts,{"TEXT_LINE":724,"PDF_PAGE":230})
        self.assertEqual(d["verbatim_reference_mentions"],359)

    def test_source_inventory_and_readonly_alignment(self):
        with sqlite3.connect(factory.DB.as_uri()+"?mode=ro",uri=True,
                             timeout=10) as c:
            records={
                "TEXT_LINE":c.execute(
                    "SELECT COUNT(*) FROM evidence_unit").fetchone()[0],
                "PDF_PAGE":c.execute(
                    "SELECT COUNT(*) FROM pdf_page_evidence").fetchone()[0]}
            baseline={"TEXT_LINE":724,"PDF_PAGE":230}
            self.assertTrue(all(records[k]>=v for k,v in baseline.items()))
            self.assertEqual(
                c.execute("SELECT COUNT(*) FROM source WHERE authoritative_review!='UNREVIEWED'").fetchone()[0],0)
            self.assertGreaterEqual(
                c.execute("SELECT COUNT(*) FROM stage WHERE stage='INDEX' AND state IN "
                          "('TECHNICAL_INDEX_READY','TECHNICAL_PDF_INDEX_READY')").fetchone()[0],
                self.data["source_count"])

    def test_queue_mutation_must_fail(self):
        with sqlite3.connect(factory.DB.as_uri()+"?mode=ro",uri=True,
                             timeout=10) as c:
            c.row_factory=sqlite3.Row
            bad=copy.deepcopy(self.queue)
            bad["review_packets"][0]["verified_extracts"][0]["excerpt"]="FORGED"
            with self.assertRaisesRegex(ValueError,"FORMING_QUEUE_MANIFEST_TAMPERED"):
                full.project(c,bad)


if __name__=="__main__":
    unittest.main()
