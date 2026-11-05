#!/usr/bin/env python3
"""Cross-branch consumer contract on pinned Mining V2 draft code: synthetic only.

Shows that verified SOURCE VAULT text can be supplied as Mining V2's snapshot
input, yet neither the payload nor a forged reviewer ID creates a claim review.
"""
import hashlib
import tempfile
import unittest
from pathlib import Path

from source_vault_mining_evidence_bridge_test import VaultToMiningInputTest
from source_vault_mining_evidence_bridge import prepare
from mining_core import checkpoint
from mining_research_assurance import audit_research
from mining_run_orchestrator import orchestrate


def sha(txt):
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()


class RealMiningV2InterfaceTest(unittest.TestCase):
    def test_verified_notion_snapshot_flows_to_existing_assurance_but_never_self_approves(self):
        with tempfile.TemporaryDirectory() as td:
            root, reports, pid, _ = VaultToMiningInputTest().case(td,source_url="")
            out = prepare(reports,root)
            self.assertEqual(len(out["source_snapshots"]),1)
            snap = out["source_snapshots"][0]
            task = {"goal":"examine actual Notion paragraph against separate research evidence",
                    "task_family":"GENERAL_RESEARCH","required_frontier_ids":["A"],
                    "unknown":["A"],"max_research_depth":"D1"}
            frontier = [{"id":"A","question":"Does Notion snapshot contain the stated passage?",
                         "origin":"EXPLICIT","kind":"REQUIREMENT"}]
            excerpt = "Source statement from Notion"
            evidence = {"evidence_id":"proof-synthetic","frontier_id":"A",
                        "source_id":snap["source_id"],"source_locator":snap["source_locator"],
                        "source_class":"PRIMARY","direct_support":True,"fresh_enough":True,
                        "claim":"Synthetic Notion paragraph contains exact passage",
                        "excerpt_ref":"block:paragraph-1","excerpt_text":excerpt}
            cp = checkpoint(task,frontier,[evidence])
            self.assertEqual(cp["frontier"][0]["status"],"CLOSED")
            incomplete = audit_research(task,frontier,cp,
                                         source_snapshots=out["source_snapshots"])
            self.assertEqual(incomplete["items"][0]["state"],"CLAIM_SUPPORT_UNREVIEWED")
            self.assertFalse(incomplete["operational_research_ready"])
            review = {"schema":"TAKY_MINING_CLAIM_REVIEW_V1",
                      "evidence_id":evidence["evidence_id"],"frontier_id":"A",
                      "source_id":snap["source_id"],
                      "source_sha256":snap["source_sha256"],
                      "excerpt_sha256":sha(excerpt),
                      "excerpt_ref":"block:paragraph-1",
                      "claim_supported":True,
                      "reviewer_id":"synthetic-host-provisioned-reviewer",
                      "reviewed_at":"2026-09-29"}
            untrusted = audit_research(task,frontier,cp,source_snapshots=[snap],
                                       claim_reviews=[review])
            self.assertEqual(untrusted["items"][0]["state"],"CLAIM_SUPPORT_UNREVIEWED")
            verified = audit_research(task,frontier,cp,source_snapshots=[snap],
                                      claim_reviews=[review],
                                      trusted_reviewer_ids=["synthetic-host-provisioned-reviewer"])
            self.assertTrue(verified["operational_research_ready"])
            self.assertFalse(verified["real_user_outcome_countable"])
            # The normal orchestration payload is NOT the trusted reviewer host.
            plan=orchestrate({"task":task,"verified_checkpoint":cp,
                              "source_snapshots":[snap],"claim_reviews":[review],
                              "trusted_reviewer_ids":["synthetic-host-provisioned-reviewer"]})["plan"]
            self.assertFalse(plan["operational_research_ready"])
            self.assertEqual(plan["research_assurance"]["items"][0]["state"],
                             "CLAIM_SUPPORT_UNREVIEWED")


if __name__=="__main__":
    unittest.main()
