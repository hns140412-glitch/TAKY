#!/usr/bin/env python3
"""Targeted regression for unprocessed Mining classification, action and resume."""
import unittest
from mining_run_orchestrator import orchestrate, advance_provider_batch
from mining_core import checkpoint as mining_checkpoint, apply_external_receipts


def plan(task, **kwargs):
    return orchestrate({"task": task, "memory": kwargs.pop("memory", {}),
                        **kwargs})["plan"]


def find_by_question(result, q):
    return next(x for x in result["pending_actions"]["items"] if x["question"] == q)


class PendingActionTest(unittest.TestCase):
    def test_critical_overflow_has_classification_and_next_batch(self):
        task = {"task_family": "GENERAL_RESEARCH", "goal": "three critical sources",
                "critical_requirements": ["source A", "source B", "source C"],
                "max_research_depth": "D1"}
        p = plan(task)
        self.assertEqual([x["question"] for x in p["search_frontier"]], ["source A", "source B"])
        entry = find_by_question(p, "source C")
        self.assertEqual(entry["classification"], "DEPTH_DEFERRED")
        self.assertEqual(entry["next_action"]["type"], "QUEUE_NEXT_BOUNDED_BATCH")
        self.assertEqual(p["next_batch_preview"], [entry["frontier_id"]])
        self.assertIn(entry["frontier_id"], p["unplanned_critical_frontier_ids"])
        self.assertFalse(p["research_complete_eligible"])
        self.assertTrue(entry["completion_evidence"])

    def test_explicit_foundation_and_unknown_overflow_do_not_vanish(self):
        p = plan({"task_family": "GENERAL_RESEARCH", "goal": "bounded audit",
                  "unknown": ["u1", "u2", "u3"],
                  "foundation_requirements": ["f1"], "max_research_depth": "D1"})
        pending = p["pending_actions"]["items"]
        self.assertEqual(len(pending), 4)
        self.assertEqual(len(p["search_frontier"]), 2)
        self.assertEqual(len(p["unplanned_required_frontier_ids"]), 2)
        self.assertEqual(find_by_question(p, "f1")["classification"], "DEPTH_DEFERRED")

    def test_index_found_is_still_an_actionable_evidence_review(self):
        p = plan({"task_family": "GENERAL_RESEARCH", "goal": "verify",
                  "unknown": ["fraction standard"]},
                 index_rows=[{"source_id": "OFF1", "canonical_title": "fraction standard",
                              "short_summary": "fraction standard", "authority_class": "OFFICIAL"}])
        item = find_by_question(p, "fraction standard")
        self.assertEqual(item["classification"], "INDEX_EVIDENCE_UNVERIFIED")
        self.assertEqual(item["next_action"]["type"], "VERIFY_INDEX_SOURCE_AND_EXACT_ANCHOR")
        self.assertEqual(item["source_ids"], ["OFF1"])
        self.assertFalse(p["research_complete_eligible"])
        self.assertEqual(p["planned_provider_requests"], [])

    def test_stale_source_routes_refresh_and_index_metadata_handoff(self):
        p = plan({"task_family": "GENERAL_RESEARCH", "goal": "freshness",
                  "unknown": ["latest standard"]},
                 index_rows=[{"source_id": "OLD", "canonical_title": "latest standard",
                              "short_summary": "latest standard", "authority_class": "OFFICIAL",
                              "stale_state": "STALE"}])
        item = find_by_question(p, "latest standard")
        self.assertEqual(item["classification"], "SOURCE_REFRESH_REQUIRED")
        self.assertEqual(item["handoff_to"], "INDEXING")
        self.assertEqual(item["excluded_source_candidates"][0]["reason"], "STALE")
        self.assertTrue(p["planned_provider_requests"])

    def test_existing_source_strategy_actually_changes_dispatched_provider_by_need(self):
        cases=[
            ("official regulation latest text","RULE","PUBLIC_DATA"),
            ("runtime implementation example in repository","IMPLEMENTATION","GITHUB"),
            ("community experience review","EXPERIENCE","WEB"),
        ]
        for question,need,provider in cases:
            with self.subTest(question=question):
                p=plan({"task_family":"GENERAL_RESEARCH","goal":"compare evidence routes",
                        "unknown":[question],"max_research_depth":"D1"})
                entry=find_by_question(p,question)
                self.assertEqual(entry["query_plan"]["evidence_need"],need)
                self.assertEqual(p["planned_provider_requests"][0]["provider"],provider)
                self.assertEqual(p["planned_provider_requests"][0]["frontier_id"],question)

    def test_explicit_exact_file_goes_to_authoritative_discovery_before_generic_web(self):
        question="초등 수학과 서논술형 평가 도움자료.pdf"
        p=plan({"task_family":"SOURCE_ACQUISITION","goal":"recover original attachment",
                "unknown":[question],"exact_source_targets":[question]})
        self.assertEqual(find_by_question(p,question)["query_plan"]["prefer"][0],"OFFICIAL")
        self.assertEqual(p["planned_provider_requests"][0]["provider"],"PUBLIC_DATA")

    def test_conflict_requires_independent_counterevidence_not_a_false_close(self):
        p = plan({"task_family": "GENERAL_RESEARCH", "goal": "conflicting guidance",
                  "conflict": ["two official sources disagree"]})
        item = find_by_question(p, "two official sources disagree")
        self.assertEqual(item["classification"], "CONFLICT_UNRESOLVED")
        self.assertEqual(item["next_action"]["type"], "CROSS_VALIDATE_INDEPENDENT_COUNTEREVIDENCE")
        self.assertEqual(item["query_plan"]["purpose"], "RESOLVE_CONFLICT")

    def test_explicit_access_hold_and_failed_route_are_not_blindly_retried(self):
        task = {"task_family": "GENERAL_RESEARCH", "goal": "retrieve",
                "unknown": ["restricted attachment"]}
        access = plan(task, provider_results={
            "restricted attachment": {"state": "FAILED", "error_code": "ACCESS_DENIED",
                                      "provider": "WEB"}
        })
        item = find_by_question(access, "restricted attachment")
        self.assertEqual(item["classification"], "ACCESS_HOLD")
        self.assertEqual(item["state"], "HOLD")
        self.assertFalse(access["planned_provider_requests"])
        failed = plan(task, provider_results={
            "restricted attachment": {"state": "FAILED", "error": "NETWORK_FAILURE",
                                      "provider": "WEB", "next_provider": "WEB"}
        })
        item = find_by_question(failed, "restricted attachment")
        self.assertEqual(item["classification"], "PROVIDER_FAILURE")
        self.assertEqual(item["next_action"]["type"], "HOLD_FAILED_ROUTE")
        self.assertEqual(item["state"], "HOLD")

    def test_successful_provider_receipt_requires_further_evidence_validation(self):
        p = plan({"task_family": "GENERAL_RESEARCH", "goal": "source validation",
                  "unknown": ["official data"]},
                 provider_results={"official data": {
                     "state": "SUCCESS", "provider": "PUBLIC_DATA",
                     "receipt": {"results": [{"source_id": "C1", "claim": "candidate"}]}
                 }})
        item = find_by_question(p, "official data")
        self.assertEqual(item["classification"], "PROVIDER_RESULT_UNVERIFIED")
        self.assertEqual(item["next_action"]["type"], "VALIDATE_PROVIDER_RECEIPT_AND_EXACT_EVIDENCE")
        self.assertIn("C1", item["source_ids"])
        self.assertFalse(item["automatic_promotion_allowed"])

    def test_old_failed_route_holds_all_active_and_does_not_execute(self):
        fail = {"failures": [{"state": "OPEN", "failure_id": "F1",
                             "route_signature": "search:same", "task_family": "GENERAL_RESEARCH",
                             "new_evidence_required": True, "replacement_routes": []}]}
        p = plan({"task_family": "GENERAL_RESEARCH", "goal": "audit",
                  "route_signature": "search:same", "unknown": ["source A"]}, memory=fail)
        self.assertEqual(find_by_question(p, "source A")["classification"], "ROUTE_BLOCKED")
        self.assertFalse(p["execution_allowed"])
        self.assertEqual(p["planned_provider_requests"], [])

    def test_next_batch_requires_real_source_anchored_checkpoint(self):
        task = {"task_family": "GENERAL_RESEARCH", "goal": "three sources",
                "critical_requirements": ["source A", "source B", "source C"],
                "max_research_depth": "D1"}
        p = plan(task)
        self.assertEqual(p["follow_up_activation"]["state"], "WAIT_VERIFIED_CHECKPOINT")
        selected = p["search_frontier"]
        start = mining_checkpoint(task, selected, [])

        def receipt(item, number):
            return {"frontier_id": item["id"], "query": item["question"], "adapter": "WEB",
                    "results": [{"source_id": "OFF-" + str(number),
                                 "url": "https://example.gov/source/" + str(number),
                                 "source_identity": "official-" + str(number),
                                 "source_class": "PRIMARY", "direct_support": True,
                                 "claim": "Evidence for " + item["question"],
                                 "excerpt_ref": "page:" + str(number) + "#paragraph:1",
                                 "independent_support_count": 2}]}

        one = apply_external_receipts(start, [receipt(selected[0], 1)])
        waiting = plan(task, verified_checkpoint=one)["follow_up_activation"]
        self.assertEqual(waiting["state"], "WAIT_CURRENT_BATCH_EVIDENCE")
        two = apply_external_receipts(one, [receipt(selected[1], 2)])
        self.assertFalse(two["stop"],"Deferred source C must keep entire goal OPEN")
        ready = plan(task, verified_checkpoint=two)["follow_up_activation"]
        self.assertEqual(ready["state"], "READY_NEXT_BATCH")
        self.assertEqual([x["question"] for x in ready["frontier"]], ["source C"])
        self.assertEqual(ready["checkpoint_resume_key"], two["resume_key"])
        self.assertFalse(ready["external_execution_performed"])

    def test_activated_batch_queries_index_before_proposing_provider_calls(self):
        task = {"task_family": "GENERAL_RESEARCH", "goal": "three research inputs",
                "critical_requirements": ["alpha", "beta", "gamma"],
                "max_research_depth": "D1"}
        initial = plan(task)
        selected = initial["search_frontier"]
        checkpoint = mining_checkpoint(task, selected, [])
        receipts = [
            {"frontier_id": item["id"], "query": item["question"], "adapter": "WEB",
             "results": [{"source_id": "S-" + item["question"], "source_class": "PRIMARY",
                          "url": "https://example.gov/" + item["question"],
                          "claim": item["question"], "direct_support": True,
                          "excerpt_ref": "page:1#paragraph:1", "independent_support_count": 2}]}
            for item in selected
        ]
        verified = apply_external_receipts(checkpoint, receipts)
        no_index = plan(task, verified_checkpoint=verified)["follow_up_activation"]
        self.assertEqual(no_index["state"], "READY_NEXT_BATCH")
        self.assertTrue(no_index["planned_provider_requests"])
        self.assertFalse(no_index["external_execution_performed"])
        with_index = plan(
            task, verified_checkpoint=verified,
            index_rows=[{"source_id": "S-gamma", "canonical_title": "gamma",
                         "short_summary": "gamma", "authority_class": "OFFICIAL"}]
        )["follow_up_activation"]
        self.assertEqual(with_index["state"], "READY_NEXT_BATCH")
        self.assertEqual([x["question"] for x in with_index["verification_frontier"]], ["gamma"])
        self.assertEqual(with_index["planned_provider_requests"], [])
        self.assertEqual(with_index["pending_actions"]["items"][0]["classification"],
                         "INDEX_EVIDENCE_UNVERIFIED")

    def test_forged_closed_status_and_unanchored_source_cannot_activate_next_batch(self):
        task = {"task_family": "GENERAL_RESEARCH", "goal": "bounded evidence",
                "critical_requirements": ["a", "b", "c"], "max_research_depth": "D1"}
        p = plan(task)
        ids = [x["id"] for x in p["search_frontier"]]
        from mining_core import normalize_goal
        alleged = {"schema": "TAKY_MINING_CORE_CHECKPOINT_V1", "resume_key": "unverified",
                   "goal": normalize_goal(task),
                   "frontier": [{"id": fid, "status": "CLOSED", "evidence_count": 1,
                                 "best_evidence_score": 0.925} for fid in ids],
                   "evidence": []}
        out = plan(task, verified_checkpoint=alleged)["follow_up_activation"]
        self.assertNotEqual(out["state"], "READY_NEXT_BATCH")
        alleged["evidence"] = [{"frontier_id": fid, "source_id": "OFF" + fid,
                                 "source_class": "PRIMARY", "claim": "a candidate claim",
                                 "direct_support": True, "fresh_enough": True,
                                 "independent_support_count": 2} for fid in ids]
        out = plan(task, verified_checkpoint=alleged)["follow_up_activation"]
        self.assertEqual(out["state"], "WAIT_SOURCE_ANCHOR")
        self.assertEqual(set(out["missing_anchor_ids"]), set(ids))

    def test_weak_anchor_cannot_launder_high_score_unanchored_closure(self):
        task={"goal":"verify three primary findings","task_family":"GENERAL_RESEARCH",
              "critical_requirements":["A","B","C"],"max_research_depth":"D1"}
        current=plan(task)
        first,second=current["search_frontier"]
        fid=first["id"]
        strong_unanchored={"frontier_id":fid,"source_id":"UNANCHORED",
                           "source_class":"OFFICIAL","claim":"high score, no excerpt",
                           "direct_support":True,"fresh_enough":True}
        weak_anchored={"frontier_id":fid,"source_id":"LOW-QUALITY",
                       "source_class":"COMMUNITY","claim":"low score but has excerpt",
                       "excerpt_ref":"page:1#p:1","direct_support":True,
                       "fresh_enough":True}
        good_second={"frontier_id":second["id"],"source_id":"GOOD-B",
                     "source_class":"OFFICIAL","claim":"source B",
                     "excerpt_ref":"page:2#p:1","direct_support":True,
                     "fresh_enough":True}
        cp=mining_checkpoint(task,current["search_frontier"],
                             [strong_unanchored,weak_anchored,good_second])
        self.assertEqual(cp["frontier"][0]["status"],"CLOSED",
                         "This reproduces Core scoring a strong unanchored row.")
        first_pending=plan(task,verified_checkpoint=cp)
        self.assertNotEqual(find_by_question(first_pending,"A")["classification"],
                            "EVIDENCE_VERIFIED")
        self.assertEqual(first_pending["follow_up_activation"]["state"],"WAIT_SOURCE_ANCHOR")
        self.assertIn(fid,first_pending["follow_up_activation"]["missing_anchor_ids"])
        self.assertFalse(first_pending["research_complete_eligible"])
        corrected={**strong_unanchored,"excerpt_ref":"page:3#p:2"}
        repaired=mining_checkpoint(task,current["search_frontier"],
                                  [corrected,weak_anchored,good_second])
        resumed=plan(task,verified_checkpoint=repaired)
        self.assertEqual(find_by_question(resumed,"A")["classification"],
                         "EVIDENCE_VERIFIED")
        self.assertEqual(resumed["follow_up_activation"]["state"],"READY_NEXT_BATCH")

    def test_deferred_exact_source_preserves_file_identity_on_activation(self):
        files=["First.pdf","Second.pdf","Third.pdf"]
        task={"goal":"acquire three original sources","task_family":"SOURCE_ACQUISITION",
              "unknown":files,"exact_source_targets":files,"max_research_depth":"D1"}
        initial=plan(task)
        cp=mining_checkpoint(task,initial["search_frontier"],[
            {"frontier_id":row["id"],"source_id":"S-"+row["id"],
             "source_class":"OFFICIAL","claim":"original",
             "excerpt_ref":"file:0-20","direct_support":True,"fresh_enough":True}
            for row in initial["search_frontier"]
        ])
        nxt=plan(task,verified_checkpoint=cp)["follow_up_activation"]
        self.assertEqual(nxt["state"],"READY_NEXT_BATCH")
        self.assertEqual(nxt["frontier"][0]["expected_source_filename"],"Third.pdf")
        self.assertTrue(nxt["index_first"]["trace"][0]["exact_identity_match_required"])
        self.assertEqual(nxt["planned_provider_requests"][0]["provider"],"PUBLIC_DATA")

    def test_verified_first_item_is_not_requeued_after_resume(self):
        task={"task_family":"GENERAL_RESEARCH","goal":"verify two required facts",
              "unknown":["first fact","second fact"],"max_research_depth":"D1"}
        original=plan(task)
        first=original["search_frontier"][0]
        cp=mining_checkpoint(task,original["search_frontier"],[])
        cp=apply_external_receipts(cp,[{
            "frontier_id":first["id"],"query":first["question"],"adapter":"WEB",
            "results":[{"source_id":"SRC-1","source_identity":"SRC-1","url":"https://example.gov/first",
                        "claim":"first fact","source_class":"PRIMARY","direct_support":True,
                        "fresh_enough":True,"excerpt_ref":"page:1#p:1","independent_support_count":2}]
        }])
        resumed=plan(task,verified_checkpoint=cp)
        completed=find_by_question(resumed,"first fact")
        remaining=find_by_question(resumed,"second fact")
        self.assertEqual(completed["classification"],"EVIDENCE_VERIFIED")
        self.assertEqual(completed["state"],"CLOSED")
        self.assertIsNone(completed["query_plan"])
        self.assertEqual(remaining["classification"],"SOURCE_GAP")
        self.assertEqual({x["frontier_id"] for x in resumed["planned_provider_requests"]},{"second fact"})
        self.assertFalse(resumed["research_complete_eligible"])

    def test_all_required_anchored_closure_eliminates_redundant_queries(self):
        task={"task_family":"GENERAL_RESEARCH","goal":"verify two facts",
              "unknown":["A","B"],"max_research_depth":"D1"}
        original=plan(task)
        cp=mining_checkpoint(task,original["search_frontier"],[])
        receipts=[{
            "frontier_id":x["id"],"query":x["question"],"adapter":"WEB",
            "results":[{"source_id":"S-"+x["id"],"source_identity":"S-"+x["id"],
                        "url":"https://example.gov/"+x["id"],"claim":"Verified "+x["question"],
                        "source_class":"PRIMARY","direct_support":True,"fresh_enough":True,
                        "excerpt_ref":"page:1#p:1","independent_support_count":2}]
        } for x in original["search_frontier"]]
        cp=apply_external_receipts(cp,receipts)
        resumed=plan(task,verified_checkpoint=cp)
        self.assertTrue(resumed["research_complete_eligible"])
        self.assertEqual(resumed["planned_provider_requests"],[])
        self.assertEqual(resumed["pending_actions"]["counts"]["required_open"],0)
        self.assertEqual(resumed["follow_up_activation"]["state"],"NO_DEFERRED_REQUIRED")

    def test_forged_closed_does_not_skip_next_search(self):
        task={"task_family":"GENERAL_RESEARCH","goal":"verify official claim",
              "unknown":["claim"],"max_research_depth":"D1"}
        original=plan(task)
        forged={"schema":"TAKY_MINING_CORE_CHECKPOINT_V1","frontier":[
            {"id":"claim","status":"CLOSED","evidence_count":1,"best_evidence_score":1.0}],
            "evidence":[],"resume_key":"fake"}
        resumed=plan(task,verified_checkpoint=forged)
        self.assertNotEqual(find_by_question(resumed,"claim")["classification"],"EVIDENCE_VERIFIED")
        self.assertTrue(resumed["planned_provider_requests"])
        self.assertFalse(resumed["research_complete_eligible"])

    def test_failed_provider_next_route_is_concrete_and_not_same_provider(self):
        task={"task_family":"GENERAL_RESEARCH","goal":"find one source","unknown":["official answer"]}
        failed={"official answer":{"state":"FAILED","provider":"WEB",
                                   "error":"TEMPORARY_NETWORK_FAILURE","next_provider":"GITHUB"}}
        p=plan(task,provider_results=failed)
        item=find_by_question(p,"official answer")
        self.assertEqual(item["classification"],"PROVIDER_FAILURE")
        self.assertEqual(item["next_action"]["type"],"TRY_NEXT_PROVIDER")
        self.assertEqual([r["provider"] for r in p["planned_provider_requests"]],["GITHUB"])
        self.assertEqual(len(p["planned_provider_requests"]),1)

    def test_provider_batch_reconciles_verified_success_and_empty_gap(self):
        task={"task_family":"GENERAL_RESEARCH","goal":"compare two source claims",
              "unknown":["official A","official B"],"max_research_depth":"D1"}
        initial=orchestrate({"task":task,"memory":{}})
        reqs=initial["plan"]["planned_provider_requests"]
        first={}
        for request in reqs:
            first.setdefault(request["frontier_id"],request)
        self.assertEqual(len(first),2)
        self.assertEqual({r["provider"] for r in first.values()},{"PUBLIC_DATA"})
        runtime={}
        for fid,req in first.items():
            if fid=="official A":
                runtime[req["request_id"]]={"state":"SUCCESS","response":{"results":[
                    {"source_id":"A-ORIGINAL","url":"https://example.gov/original",
                     "claim":"Original A","source_class":"PRIMARY",
                     "direct_support":True,"fresh_enough":True,
                     "excerpt_ref":"page:1#p:1","independent_support_count":2}]}}
            else:
                runtime[req["request_id"]]={"state":"EMPTY","response":{"results":[]}}
        result=advance_provider_batch({"task":task,"memory":{}},runtime)
        self.assertEqual(result["state"],"RECONCILED")
        self.assertTrue(result["checkpoint"]["evidence"])
        self.assertEqual(find_by_question(result["plan"],"official A")["classification"],"EVIDENCE_VERIFIED")
        self.assertEqual(find_by_question(result["plan"],"official B")["classification"],"EMPTY_PROVIDER_RESULT")
        self.assertEqual({r["frontier_id"] for r in result["plan"]["planned_provider_requests"]},{"official B"})
        self.assertEqual({r["provider"] for r in result["plan"]["planned_provider_requests"]},{"WEB"})
        self.assertFalse(result["plan"]["research_complete_eligible"])
        self.assertFalse(result["guards"]["network_calls_performed_by_orchestrator"])

    def test_empty_provider_uses_changed_route_or_waits_for_revised_query(self):
        task={"task_family":"GENERAL_RESEARCH","goal":"find one source",
              "unknown":["source Z"],"max_research_depth":"D1"}
        original=orchestrate({"task":task,"memory":{}})
        primary=original["plan"]["planned_provider_requests"][0]
        out=advance_provider_batch({"task":task,"memory":{}},{
            primary["request_id"]:{"state":"EMPTY","response":{"results":[]}}
        })
        item=find_by_question(out["plan"],"source Z")
        self.assertEqual(item["classification"],"EMPTY_PROVIDER_RESULT")
        self.assertEqual(item["next_action"]["type"],"TRY_NEXT_PROVIDER")
        self.assertEqual([x["provider"] for x in out["plan"]["planned_provider_requests"]],["PUBLIC_DATA"])
        held=plan(task,provider_results={"source Z":{
            "state":"EMPTY","provider":"WEB","next_provider":"WEB","receipt":{"results":[]}
        }})
        item=find_by_question(held,"source Z")
        self.assertEqual(item["state"],"HOLD")
        self.assertEqual(held["planned_provider_requests"],[])

    def test_provider_failure_prepares_different_fallback_without_retrying_same_provider(self):
        task={"task_family":"GENERAL_RESEARCH","goal":"find one official source",
              "unknown":["official claim"],"max_research_depth":"D1"}
        initial=orchestrate({"task":task,"memory":{}})
        first=initial["plan"]["planned_provider_requests"][0]
        self.assertEqual(first["provider"],"PUBLIC_DATA")
        out=advance_provider_batch({"task":task,"memory":{}},{
            first["request_id"]:{"state":"FAILED","error":"NETWORK_FAILURE"}
        })
        self.assertEqual(out["state"],"RECONCILED")
        item=find_by_question(out["plan"],"official claim")
        self.assertEqual(item["next_action"]["type"],"TRY_NEXT_PROVIDER")
        self.assertEqual([r["provider"] for r in out["plan"]["planned_provider_requests"]],["WEB"])
        self.assertNotEqual(out["plan"]["planned_provider_requests"][0]["request_id"],first["request_id"])
        self.assertEqual(len(out["execution_batch"]["results"]),1)

    def test_access_denial_holds_instead_of_bypassing_provider(self):
        task={"task_family":"GENERAL_RESEARCH","goal":"retrieve protected material",
              "unknown":["protected PDF"]}
        first=orchestrate({"task":task,"memory":{}})["plan"]["planned_provider_requests"][0]
        out=advance_provider_batch({"task":task,"memory":{}},{
            first["request_id"]:{"state":"FAILED","error":"ACCESS_DENIED"}
        })
        item=find_by_question(out["plan"],"protected PDF")
        self.assertEqual(item["classification"],"ACCESS_HOLD")
        self.assertEqual(item["state"],"HOLD")
        self.assertEqual(out["plan"]["planned_provider_requests"],[])

    def test_provider_success_without_exact_anchor_is_not_evidence_completion(self):
        task={"task_family":"GENERAL_RESEARCH","goal":"find source","unknown":["source X"]}
        first=orchestrate({"task":task,"memory":{}})["plan"]["planned_provider_requests"][0]
        out=advance_provider_batch({"task":task,"memory":{}},{
            first["request_id"]:{"state":"SUCCESS","response":{"results":[
                {"source_id":"X","url":"https://example.gov/x","claim":"X","source_class":"PRIMARY",
                 "direct_support":True,"independent_support_count":2}]}}
        })
        self.assertEqual(find_by_question(out["plan"],"source X")["classification"],
                         "PROVIDER_RESULT_UNVERIFIED")
        self.assertFalse(out["plan"]["research_complete_eligible"])

    def test_previous_checkpoint_from_another_goal_is_rejected(self):
        task={"task_family":"GENERAL_RESEARCH","goal":"goal one","unknown":["source X"]}
        old=mining_checkpoint({"task_family":"GENERAL_RESEARCH","goal":"another goal"},[],[])
        result=advance_provider_batch({"task":task,"memory":{},"verified_checkpoint":old},{})
        self.assertEqual(result["state"],"HOLD_CHECKPOINT_GOAL_MISMATCH")
        self.assertEqual(result["execution_batch"],None)

    def test_provider_batch_current_success_not_full_goal_success_if_deferred_critical(self):
        task={"task_family":"GENERAL_RESEARCH","goal":"three official inputs",
              "critical_requirements":["source A","source B","source C"],
              "max_research_depth":"D1"}
        first=orchestrate({"task":task,"memory":{}})["plan"]
        requests={}
        for req in first["planned_provider_requests"]:
            requests.setdefault(req["frontier_id"],req)
        injected={req["request_id"]:{"state":"SUCCESS","response":{"results":[{
            "source_id":"SRC-"+fid,"source_identity":"SRC-"+fid,
            "url":"https://example.gov/"+fid.replace(" ","-"),
            "source_class":"PRIMARY","claim":"verified "+fid,"direct_support":True,
            "fresh_enough":True,"excerpt_ref":"page:1#paragraph:1",
            "independent_support_count":2}]}}
            for fid,req in requests.items()}
        result=advance_provider_batch({"task":task,"memory":{}},injected)
        self.assertEqual(result["state"],"RECONCILED")
        self.assertFalse(result["checkpoint"]["stop"])
        self.assertFalse(result["plan"]["research_complete_eligible"])
        self.assertEqual(result["plan"]["follow_up_activation"]["state"],"READY_NEXT_BATCH")
        self.assertEqual([x["question"] for x in result["plan"]["follow_up_activation"]["frontier"]],["source C"])

    def test_two_stage_receipts_finish_three_required_sources_without_researching_closed_ones(self):
        task={"task_family":"GENERAL_RESEARCH","goal":"3 independent required documents",
              "critical_requirements":["source A","source B","source C"],
              "max_research_depth":"D1"}
        input_state={"task":task,"memory":{}}
        def runtime_for_requests(reqs):
            chosen={}
            for req in reqs:
                chosen.setdefault(req["frontier_id"],req)
            return {req["request_id"]:{"state":"SUCCESS","response":{"results":[{
                "source_id":"ID-"+str(idx),"source_identity":"ID-"+str(idx),
                "url":"https://example.gov/doc/"+str(idx),
                "claim":"document for "+fid,"source_class":"PRIMARY",
                "direct_support":True,"fresh_enough":True,
                "excerpt_ref":"page:1#paragraph:1","independent_support_count":2}]}}
                for idx,(fid,req) in enumerate(chosen.items(),1)}
        stage_one=advance_provider_batch(
            input_state,
            runtime_for_requests(orchestrate(input_state)["plan"]["planned_provider_requests"]))
        self.assertFalse(stage_one["checkpoint"]["stop"])
        follow=stage_one["plan"]["follow_up_activation"]
        self.assertEqual(follow["state"],"READY_NEXT_BATCH")
        self.assertEqual([x["question"] for x in follow["frontier"]],["source C"])
        stage_two=advance_provider_batch(
            stage_one["next_run_input"],
            runtime_for_requests(follow["planned_provider_requests"]))
        self.assertEqual(stage_two["state"],"RECONCILED")
        self.assertEqual({x["frontier_id"] for x in stage_two["execution_batch"]["results"]},
                         {follow["frontier"][0]["id"]})
        self.assertEqual(len(stage_two["checkpoint"]["frontier"]),3)
        self.assertEqual(len(stage_two["checkpoint"]["evidence"]),3)
        self.assertTrue(stage_two["checkpoint"]["stop"])
        self.assertTrue(stage_two["plan"]["research_complete_eligible"])
        self.assertEqual(stage_two["plan"]["planned_provider_requests"],[])
        self.assertEqual(stage_two["plan"]["follow_up_activation"]["state"],"NO_DEFERRED_REQUIRED")

    def test_known_complete_cannot_silently_override_new_explicit_gap(self):
        p = plan({"task_family": "GENERAL_RESEARCH", "goal": "already complete",
                  "known_complete": True, "critical_requirements": ["new official evidence"]})
        self.assertEqual(p["search_frontier"], [])
        self.assertEqual(find_by_question(p, "new official evidence")["classification"], "DEPTH_CONFLICT")
        self.assertFalse(p["research_complete_eligible"])


if __name__ == "__main__":
    unittest.main()
