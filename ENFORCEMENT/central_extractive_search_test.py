"""Real Central read-only coverage for mixed RAW line and PDF page search."""
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch

import central_extractive_search as target
import taky_central_source_factory as factory


class CentralExtractiveSearch(unittest.TestCase):
    def setUp(self):
        self.c=sqlite3.connect(factory.DB.as_uri()+"?mode=ro",uri=True,timeout=10)
        self.addCleanup(self.c.close)
        self.c.row_factory=sqlite3.Row

    def test_live_pdf_and_text_sha_verified_in_one_query(self):
        result=target.search(self.c,"환경",limit=8)
        self.assertEqual(result["status"],"SOURCE_HASH_VERIFIED_UNREVIEWED_RESULTS")
        self.assertEqual(result["returned_count"],8)
        self.assertGreater(result["text_count"],0)
        self.assertGreater(result["pdf_count"],0)
        for x in result["hits"]:
            self.assertEqual(len(x["raw_sha256"]),64)
            self.assertEqual(len(x["content_sha256"]),64)
            self.assertFalse(x["semantic_authority"])
            self.assertEqual(x["review_state"],"EXTRACTIVE_UNREVIEWED")
            self.assertIn(x["media"],("TEXT","PDF","HTML"))
            self.assertTrue(x["excerpt"])
        self.assertFalse(result["semantic_approval"])
        self.assertFalse(result["knowledge_promotion"])
        self.assertTrue(result["database_read_only"])

    def test_live_html_visible_text_is_source_bound(self):
        result=target.search(self.c,"바이브코딩",limit=12)
        self.assertGreater(result["html_count"],0)
        html=[x for x in result["hits"] if x["media"]=="HTML"]
        self.assertTrue(all(x["review_state"]=="EXTRACTIVE_UNREVIEWED"
                         and x["semantic_authority"] is False
                         and x["anchor"]["segment_no"]>=1 for x in html))
        with patch("central_extractive_search.html_capture.read_verified",
                   return_value=None):
            with self.assertRaisesRegex(ValueError,"HTML_DETAIL_SOURCE_NOT_VERIFIED"):
                target.search(self.c,"바이브코딩",limit=12)

    def test_untrusted_source_reference_cannot_fake_verification(self):
        with patch("central_extractive_search.factory.read_verified_evidence_unit",
                   return_value=None):
            with self.assertRaisesRegex(ValueError,"TEXT_DETAIL_SOURCE_NOT_VERIFIED"):
                target.search(self.c,"환경",limit=8)
        with patch("central_extractive_search.pdf.read_verified_page",
                   return_value=None):
            with self.assertRaisesRegex(ValueError,"PDF_DETAIL_SOURCE_NOT_VERIFIED"):
                target.search(self.c,"환경",limit=8)

    def test_bounded_search_and_literally_escaped_wildcards(self):
        with self.assertRaisesRegex(ValueError,"CENTRAL_SEARCH_LIMIT_INVALID"):
            target.search(self.c,"환경",limit=100)
        with self.assertRaisesRegex(ValueError,"CENTRAL_SEARCH_QUERY_INVALID"):
            target.search(self.c," ",limit=8)
        literal=target.search(self.c,"%_",limit=8)
        self.assertLessEqual(literal["returned_count"],8)
        self.assertTrue(literal["database_read_only"])


if __name__=="__main__":
    unittest.main()
