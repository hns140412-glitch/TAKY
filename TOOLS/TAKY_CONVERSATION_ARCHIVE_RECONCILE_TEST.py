#!/usr/bin/env python3
"""Local regression: historical evidence classification stays provisional."""
import unittest
import TAKY_CONVERSATION_ARCHIVE_RECONCILE as r

class ArchiveReviewTests(unittest.TestCase):
    def test_title_fallback_is_narrow(self):
        self.assertEqual(r.title_seed("Ready & Set 로직")["project"],"READY-SET")
        self.assertIsNone(r.title_seed("최신 타키 기준 재개"))
        self.assertIsNone(r.title_seed("구성중"))
    def test_legacy_zpd_never_auto_merged_with_hide(self):
        self.assertEqual(r.title_seed("ZPD Word 로직")["project"],"LEGACY-ZPD-WORD")
    def test_keyword_candidate_preserved_over_title(self):
        row={"event_id":"e","topic_refs":[{"project":"TAKY","topic_key":"notion-workspace","label":"Notion"}]}
        result=r.enrich_rows([row],"id",{"id":"Ready & Set 로직"})[0]
        self.assertEqual(result["topic_refs"],row["topic_refs"])
        self.assertEqual(result["classification_source"],"MESSAGE_RULE_CANDIDATE")
        self.assertTrue(result["review_required"])
    def test_unclassified_not_force_seeded_by_generic_name(self):
        row={"event_id":"e","topic_refs":[]}
        result=r.enrich_rows([row],"id",{"id":"마스터 로직 OLD"})[0]
        self.assertEqual(result["topic_refs"],[])
        self.assertEqual(result["classification_source"],"UNCLASSIFIED_MANUAL_REVIEW")
    def test_title_hint_never_promotes_message_topic(self):
        row={"event_id":"e","topic_refs":[],"primary_topic_key":None}
        result=r.enrich_rows([row],"id",{"id":"Snap & Pop 로직"})[0]
        self.assertEqual(result["chat_title_hint"]["project"],"SNAP-POP")
        self.assertEqual(result["chat_title_hint_status"],"TITLE_ONLY_NOT_MESSAGE_CLASSIFICATION")
        self.assertEqual(result["topic_refs"],[])
        self.assertIsNone(result["primary_topic_key"])
        self.assertEqual(result["classification_source"],"UNCLASSIFIED_MANUAL_REVIEW")
        self.assertTrue(result["review_required"])
    def test_different_titles_do_not_force_same_owner(self):
        self.assertNotEqual(r.title_seed("문구 검토 Translate")["project"],
                            r.title_seed("설계개요 엑셀 작성")["project"])
if __name__=="__main__":
    unittest.main()
