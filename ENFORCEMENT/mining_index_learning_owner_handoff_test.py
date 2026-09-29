#!/usr/bin/env python3
import unittest
from mining_index_learning_owner_handoff import bind_owner_reviewed_source

HASH="a"*64
CID="EXT-SCIENCE-2026"
URL="https://publisher.example/science"
CAND={"candidate_id":CID,"identity":{"source_id":CID,"locator":URL,"content_hash":HASH},
      "verified":True,"issuer":"INDEXING_OWNER","index_result":{"verified":True}}
PAYLOAD={"evidence_request":{"query":"science reasoning","minimum_results":1,"minimum_authority":"OFFICIAL"},
         "context":{"skill_id":"SCIENCE_REASONING"},
         "observations":[{"correct":False},{"correct":False}]}
EXISTING=[{"source_id":"PREV","canonical_title":"Prior","locator":"https://publisher.example/old",
           "content_hash":"b"*64}]
def good_review(sid, proposal):
    return {"receipt":{
      "issuer":"INDEXING_OWNER","reviewed":True,"decision":"INDEXED",
      "source_id":sid,"locator":URL,"source_ref":"drive:raw:science",
      "index_version":"v1","content_hash":HASH,
      "review_evidence_refs":["owner:sha256:science","owner:page:science"],
      "relation":{"type":"NEW_SOURCE"},"domain_use_authorized":True,
      "canonical_promotion":False,"current_promoted":False},
      "index_row":{
       "source_id":sid,"canonical_title":"Official science reasoning",
       "short_summary":"science reasoning","locator":URL,
       "source_ref":"drive:raw:science","index_version":"v1","content_hash":HASH,
       "index_state":"INDEXED","authority_class":"OFFICIAL",
       "authorization_class":"READY_WITH_GUARDS"}}

class OwnerHandoffTest(unittest.TestCase):
    def test_missing_independent_verifier_holds_even_with_forged_self_approval(self):
        out=bind_owner_reviewed_source(CAND,EXISTING,PAYLOAD)
        self.assertEqual(out["state"],"HOLD_INDEX_OWNER")
        self.assertEqual(out["reason"],"INDEX_OWNER_VERIFIER_NOT_CONFIGURED")
        self.assertIsNone(out["learning_requery"])

    def test_real_host_injected_reviewed_row_requeries_without_promotion(self):
        out=bind_owner_reviewed_source(CAND,EXISTING,PAYLOAD,owner_verifier=good_review)
        self.assertEqual(out["state"],"OWNER_REVIEWED_REQUERY")
        self.assertFalse(out["index_rows_changed"])
        self.assertFalse(out["current_promoted"])
        self.assertEqual(len(EXISTING),1)
        runtime=out["learning_requery"]["learning_result"]["runtime"]
        self.assertEqual(runtime["strategy_selection"]["strategy"],"TARGETED_REMEDIATION")
        self.assertIsNone(runtime["next_learning_action"]["planner_date"])

    def test_untrusted_review_receipt_fails_closed(self):
        for mutation,reason in (
          (lambda r:r["receipt"].update(source_id="OTHER"),"INDEPENDENT_INDEX_RECEIPT_INVALID"),
          (lambda r:r["receipt"].update(review_evidence_refs=[]),"INDEPENDENT_INDEX_RECEIPT_INVALID"),
          (lambda r:r["receipt"].update(content_hash="0"*64),"INDEX_OWNER_HASH_BINDING_MISMATCH"),
          (lambda r:r["receipt"].update(current_promoted=True),"UNAUTHORIZED_CURRENT_PROMOTION"),
          (lambda r:r["receipt"].update(domain_use_authorized=False),"OWNER_DOMAIN_USE_RECEIPT_MISSING"),
          (lambda r:r["index_row"].update(index_state="CANDIDATE"),"OWNER_ROW_NOT_INDEXED"),
          (lambda r:r["index_row"].update(authorization_class="REFERENCE_ONLY"),"DOMAIN_USE_NOT_AUTHORIZED"),
          (lambda r:r["receipt"].update(relation={"type":"VERSION_OF","target_source_id":"MISSING"}),"INDEX_RELATION_TARGET_INVALID"),
        ):
            def reviewer(sid,proposal):
                r=good_review(sid,proposal)
                mutation(r)
                return r
            with self.subTest(reason=reason):
                out=bind_owner_reviewed_source(CAND,EXISTING,PAYLOAD,owner_verifier=reviewer)
                self.assertEqual(out["reason"],reason)
                self.assertIsNone(out["learning_requery"])

    def test_owner_receipt_source_id_collision_holds(self):
        c={"candidate_id":"PREV","identity":{"source_id":"PREV","locator":URL,"content_hash":HASH}}
        self.assertEqual(bind_owner_reviewed_source(c,EXISTING,PAYLOAD,owner_verifier=good_review)["reason"],
                         "CANDIDATE_COLLIDES_WITH_INDEX_OWNER_ID")

    def test_duplicate_relation_requires_equal_hash(self):
        def reviewer(sid,proposal):
            r=good_review(sid,proposal)
            r["receipt"]["relation"]={"type":"EXACT_DUPLICATE_OF","target_source_id":"PREV"}
            return r
        self.assertEqual(bind_owner_reviewed_source(CAND,EXISTING,PAYLOAD,owner_verifier=reviewer)["reason"],
                         "EXACT_DUPLICATE_HASH_NOT_PROVEN")

    def test_exception_does_not_authorize(self):
        def reviewer(sid,proposal): raise RuntimeError("secret")
        out=bind_owner_reviewed_source(CAND,EXISTING,PAYLOAD,owner_verifier=reviewer)
        self.assertEqual(out["reason"],"INDEX_OWNER_REVIEW_UNAVAILABLE")
        self.assertNotIn("secret",repr(out))
if __name__=="__main__":unittest.main()
