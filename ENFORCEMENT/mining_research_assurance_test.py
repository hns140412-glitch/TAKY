#!/usr/bin/env python3
"""Regression: reported research success must retain exact source and claim proof."""
import hashlib
import json
import unittest
from mining_core import checkpoint
from mining_research_assurance import audit_research


def sha(text): return hashlib.sha256(text.encode("utf-8")).hexdigest()


TASK={"goal":"verify two independent source facts","task_family":"GENERAL_RESEARCH",
      "required_frontier_ids":["A","B"]}
FRONTIER=[{"id":"A","question":"source fact A","origin":"EXPLICIT"},
          {"id":"B","question":"source fact B","origin":"EXPLICIT"}]


def evidence(fid):
    return {"evidence_id":"e-"+fid,"frontier_id":fid,"source_id":"s-"+fid,
            "source_url":"https://official.test/"+fid,"source_class":"PRIMARY",
            "claim":"Fact "+fid,"direct_support":True,"fresh_enough":True,
            "excerpt_ref":"paragraph:1","excerpt_text":"Exact fact "+fid,
            "independent_support_count":2}


def source(fid, *, text=None):
    raw=text if text is not None else "Page heading\nExact fact "+fid+"\nfooter"
    return {"schema":"TAKY_MINING_SOURCE_SNAPSHOT_V1","source_id":"s-"+fid,
            "retrieval_state":"FETCHED","source_locator":"https://official.test/"+fid,
            "source_text":raw,"source_sha256":sha(raw),"retrieved_at":"2026-09-29",
            "source_updated_at":"2026-09-27"}


def review(fid, snap=None, *, reviewer="trusted-source-validator", supported=True):
    s=snap or source(fid)
    return {"schema":"TAKY_MINING_CLAIM_REVIEW_V1",
            "evidence_id":"e-"+fid,"frontier_id":fid,"source_id":"s-"+fid,
            "excerpt_ref":"paragraph:1","excerpt_sha256":sha("Exact fact "+fid),
            "source_sha256":s["source_sha256"],"claim_supported":supported,
            "reviewer_id":reviewer,"reviewed_at":"2026-09-29"}


def run(task=None, frontier=None, rows=None, snaps=None, reviews=None, access=None):
    task=task or TASK; frontier=FRONTIER if frontier is None else frontier
    cp=checkpoint(task,frontier,list(rows or []))
    return audit_research(task,frontier,cp,source_snapshots=snaps,
                          claim_reviews=reviews,trusted_reviewer_ids=["trusted-source-validator"],
                          source_access_results=access)


class ResearchAssuranceTest(unittest.TestCase):
    def test_checkpoint_missing_never_completes(self):
        out=audit_research(TASK,FRONTIER,None)
        self.assertFalse(out["operational_research_ready"])
        self.assertEqual(out["pending_count"],2)
        self.assertEqual(out["items"][0]["state"],"CHECKPOINT_UNAVAILABLE")

    def test_core_closed_flag_does_not_substitute_for_source_bytes(self):
        out=run(rows=[evidence("A"),evidence("B")])
        self.assertFalse(out["operational_research_ready"])
        self.assertTrue(all(x["state"]=="SOURCE_NOT_RETRIEVED" for x in out["items"]))

    def test_exact_text_is_not_a_reviewer_verdict(self):
        out=run(rows=[evidence("A"),evidence("B")],
                snaps=[source("A"),source("B")])
        self.assertEqual({x["state"] for x in out["items"]},{"CLAIM_SUPPORT_UNREVIEWED"})

    def test_all_required_source_bytes_and_trusted_claim_reviews_enable_domain_review(self):
        out=run(rows=[evidence("A"),evidence("B")],
                snaps=[source("A"),source("B")],
                reviews=[review("A"),review("B")])
        self.assertTrue(out["operational_research_ready"])
        self.assertEqual(out["source_grounded"],2)
        self.assertFalse(out["real_user_outcome_countable"])
        self.assertEqual(out["next_actions"],[])
        self.assertNotIn("Exact fact",json.dumps(out))

    def test_wrong_snapshot_hash_or_absent_span_never_passes(self):
        a=source("A");a["source_sha256"]="0"*64
        out=run(rows=[evidence("A"),evidence("B")],
                snaps=[a,source("B")],reviews=[review("A"),review("B")])
        self.assertEqual(out["items"][0]["state"],"SNAPSHOT_INVALID")
        out=run(rows=[evidence("A"),evidence("B")],
                snaps=[source("A",text="unrelated source text"),source("B")],
                reviews=[review("A"),review("B")])
        self.assertEqual(out["items"][0]["state"],"EXACT_SPAN_MISSING")

    def test_fake_reviewer_and_provider_self_review_are_not_accepted(self):
        out=run(rows=[{**evidence("A"),"claim_supported":True,
                       "reviewer_id":"trusted-source-validator"},evidence("B")],
                snaps=[source("A"),source("B")],
                reviews=[review("A",reviewer="provider-self"),review("B")])
        self.assertEqual(out["items"][0]["state"],"CLAIM_SUPPORT_UNREVIEWED")
        self.assertEqual(out["items"][1]["state"],"SOURCE_GROUNDED")
        self.assertFalse(out["operational_research_ready"])

    def test_unsupported_review_requires_correction(self):
        out=run(rows=[evidence("A"),evidence("B")],
                snaps=[source("A"),source("B")],
                reviews=[review("A",supported=False),review("B")])
        self.assertEqual(out["items"][0]["state"],"CLAIM_NOT_SUPPORTED")
        self.assertEqual(out["items"][0]["next_action"],"CORRECT_CLAIM_AND_REOPEN_RESEARCH")

    def test_freshness_is_explicit_not_inferred_from_retrieval_date(self):
        task={**TASK,"freshness_required":True}
        kwargs={"task":task,"rows":[evidence("A"),evidence("B")],
                "snaps":[source("A"),source("B")],
                "reviews":[review("A"),review("B")]}
        self.assertEqual(run(**kwargs)["items"][0]["state"],"FRESHNESS_UNVERIFIED")
        recent={**task,"freshness_as_of":"2026-09-29","max_source_age_days":5}
        self.assertTrue(run(**{**kwargs,"task":recent})["operational_research_ready"])
        stale={**recent,"max_source_age_days":1}
        self.assertEqual(run(**{**kwargs,"task":stale})["items"][0]["state"],"STALE_SOURCE")

    def test_missing_deferred_required_item_does_not_vanish(self):
        out=run(frontier=FRONTIER[:1],rows=[evidence("A")],
                snaps=[source("A")],reviews=[review("A")])
        self.assertEqual(out["source_grounded"],1)
        self.assertEqual(out["items"][1]["state"],"REQUIRED_SCOPE_MISSING")
        self.assertFalse(out["operational_research_ready"])

    def test_access_hold_is_not_missing_source(self):
        out=run(access=[{"frontier_id":"A","state":"ACCESS_DENIED"}])
        self.assertEqual(out["items"][0]["state"],"ACCESS_HOLD")
        self.assertEqual(out["items"][0]["next_action"],
                         "PRESERVE_HOLD_AND_FIND_AUTHORIZED_ALTERNATIVE")

    def test_checkpoint_from_different_goal_cannot_be_reused(self):
        cp=checkpoint({"goal":"some other goal","task_family":"GENERAL_RESEARCH"},
                      FRONTIER,[evidence("A"),evidence("B")])
        out=audit_research(TASK,FRONTIER,cp,source_snapshots=[source("A"),source("B")],
                           claim_reviews=[review("A"),review("B")],
                           trusted_reviewer_ids=["trusted-source-validator"])
        self.assertEqual(out["pending_count"],2)
        self.assertFalse(out["operational_research_ready"])


if __name__=="__main__": unittest.main()
