#!/usr/bin/env python3
import unittest
from mining_source_watch import plan_source_work
from mining_run_orchestrator import orchestrate

A = "a" * 64
B = "b" * 64


def source(item="post/1", digest=A, **kwargs):
    row = {"namespace": "CREATOR", "author_id": "creator", "content_id": item,
           "original_url": "https://example.org/" + item, "public_source": True,
           "content_kind": "POST", "title": "Real item", "content_sha256": digest,
           "source_version": "v1", "observed_at": "2026-09-30"}
    row.update(kwargs)
    return row


def baseline(item="post/1", digest=A, **kwargs):
    row = source(item, digest, baseline_state="DEEP_VERIFIED",
                 evidence_refs=["original:p1#claim"])
    row.update(kwargs)
    return row


class SourceWatchTest(unittest.TestCase):
    def test_shallow_watchlist_cannot_skip_baseline(self):
        b = baseline(baseline_state="WATCHLIST")
        p = plan_source_work({"baselines": [b], "observations": [source()]})
        self.assertEqual(p["selected"][0]["state"], "BASELINE_DEEP_DIVE")

    def test_proven_deep_snapshot_unchanged_not_researched(self):
        p = plan_source_work({"baselines": [baseline()], "observations": [source()]})
        self.assertFalse(p["selected"])
        self.assertEqual(p["counts"]["unchanged"], 1)

    def test_changed_original_gets_delta(self):
        p = plan_source_work({"baselines": [baseline()], "observations": [source(digest=B)]})
        self.assertEqual(p["selected"][0]["state"], "DELTA_DEEP_DIVE")
        self.assertIn("https://example.org/post/1", p["selected"][0]["question"])

    def test_no_current_bytes_never_called_unchanged(self):
        p = plan_source_work({"baselines": [baseline()], "observations": [source(digest=None)]})
        self.assertEqual(p["selected"][0]["state"], "SNAPSHOT_REQUIRED")

    def test_same_bytes_changed_version_requires_review(self):
        p = plan_source_work({"baselines": [baseline()], "observations": [source(source_version="v2")]})
        self.assertEqual(p["selected"][0]["state"], "VERSION_OR_PROVENANCE_REVIEW")

    def test_author_identifies_distinct_posts_not_just_account(self):
        p = plan_source_work({"baselines": [baseline()], "observations": [
            source(), source("post/2", digest=A)]})
        self.assertEqual(p["counts"]["unchanged"], 1)
        self.assertEqual(p["selected"][0]["content_id"], "post/2")

    def test_profile_discovery_not_deep_content(self):
        p = plan_source_work({"observations": [source(content_kind="PROFILE")]})
        self.assertEqual(p["items"][0]["state"], "DISCOVERY_ONLY_PROFILE")
        self.assertEqual(p["selected"], [])

    def test_duplicate_url_fragment_not_new_content(self):
        o = source()
        second = source(original_url="https://example.org/post/1#carousel")
        p = plan_source_work({"observations": [o, second]})
        self.assertEqual(p["counts"]["duplicate_observations"], 1)
        self.assertEqual(len(p["selected"]), 1)

    def test_conflicting_snapshots_or_baselines_fail_closed(self):
        p = plan_source_work({"observations": [source(), source(digest=B)]})
        self.assertEqual(p["items"][0]["state"], "HOLD_CONFLICTING_OBSERVATIONS")
        self.assertEqual(p["selected"], [])
        p = plan_source_work({"baselines": [baseline(), baseline(digest=B)],
                              "observations": [source()]})
        self.assertEqual(p["items"][0]["state"], "HOLD_CONFLICTING_BASELINES")

    def test_private_or_token_url_and_invalid_hash_held(self):
        p = plan_source_work({"observations": [
            source(public_source=False),
            source(original_url="https://example.org/post/1?access_token=x"),
            source(digest="not_sha256")]})
        self.assertEqual(p["counts"]["holds"], 3)
        self.assertFalse(p["selected"])

    def test_bounded_selection_deferred_visible(self):
        p = plan_source_work({"observations": [source("post/" + str(i)) for i in range(5)]})
        self.assertEqual(len(p["selected"]), 3)
        self.assertEqual(sum(x["state"].startswith("DEFERRED_") for x in p["items"]), 2)

    def test_missing_evidence_or_wrong_baseline_status_not_trusted(self):
        p = plan_source_work({"baselines": [baseline(evidence_refs=[])],
                              "observations": [source()]})
        self.assertEqual(p["selected"][0]["state"], "BASELINE_DEEP_DIVE")

    def test_actual_orchestrator_consumes_watch_without_overwriting_user_intent(self):
        payload = {"task": {"goal": "deep creator mining", "task_family": "AI_RESEARCH",
                             "critical_requirements": ["preserve explicit intent"],
                             "max_research_depth": "D2"},
                   "source_watch": {"baselines": [], "observations": [source()]}}
        plan = orchestrate(payload)["plan"]
        self.assertEqual(plan["source_watch_plan"]["selected"][0]["state"], "BASELINE_DEEP_DIVE")
        self.assertEqual(plan["search_frontier"][0]["kind"], "CRITICAL")
        self.assertTrue(any("https://example.org/post/1" in x["question"]
                            for x in plan["search_frontier"]))
        self.assertTrue(plan["planned_provider_requests"])
        self.assertFalse(plan["source_watch_plan"]["canonical_promotion"])

    def test_changed_same_url_cannot_reuse_old_checkpoint_frontier_id(self):
        task = {"goal": "monitor one known source", "task_family": "AI_RESEARCH",
                "max_research_depth": "D2"}
        first = orchestrate({"task": task,
                             "source_watch": {"observations": [source(digest=A)]}})["plan"]
        changed = orchestrate({"task": task,
                               "source_watch": {"observations": [source(digest=B)]}})["plan"]
        original_id = next(x["id"] for x in first["search_frontier"]
                           if x["kind"] == "REQUIREMENT")
        changed_id = next(x["id"] for x in changed["search_frontier"]
                          if x["kind"] == "REQUIREMENT")
        self.assertNotEqual(original_id, changed_id)
        self.assertNotEqual(first["source_watch_plan"]["selected"][0]["selection_fingerprint"],
                            changed["source_watch_plan"]["selected"][0]["selection_fingerprint"])

    def test_legacy_orchestrator_unchanged_when_no_watch(self):
        plan = orchestrate({"task": {"goal": "ordinary discovery",
                                     "task_family": "GENERAL_RESEARCH"}})["plan"]
        self.assertIsNone(plan["source_watch_plan"])
        self.assertNotIn("source_watch", str(plan["search_frontier"]))


if __name__ == "__main__":
    unittest.main()
