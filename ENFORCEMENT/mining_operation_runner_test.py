#!/usr/bin/env python3
"""The runner invokes real registered callables, not pre-injected fake dispatch claims."""
import unittest
from mining_operation_runner import run_with_providers


def payload(*questions, memory=None, route=None):
    return {
        "task":{"goal":"obtain verified references","task_family":"GENERAL_RESEARCH",
                "unknown":list(questions or ("question-A",)),
                "max_research_depth":"D1",
                **({"route_signature":route} if route else {})},
        "memory":memory or {},
    }


def found(request):
    fid=request["frontier_id"]
    return {"state":"SUCCESS","response":{"results":[{
        "source_id":"source:"+fid,"url":"https://public.example/"+fid,
        "title":"source","source_class":"PRIMARY",
        "claim":"source answers "+fid,"direct_support":True,
        "excerpt_ref":"paragraph:1",
    }]}}


class OperationRunnerTest(unittest.TestCase):
    def test_no_provider_registered_does_not_claim_network_execution(self):
        output=run_with_providers(payload("A"),{})
        self.assertEqual(output["state"],"HOLD_PROVIDER_ADAPTER_UNAVAILABLE")
        self.assertEqual(output["invocations"],0)
        self.assertFalse(output["operational_research_ready"])

    def test_failure_invokes_different_provider_and_retains_evidence(self):
        events=[]
        def web(req):
            events.append("WEB");return {"state":"FAILED","error":"TIMEOUT"}
        def public(req):
            events.append("PUBLIC_DATA");return found(req)
        output=run_with_providers(payload("A"),{
            "WEB":web,"PUBLIC_DATA":public,"GITHUB":lambda r:found(r)
        })
        self.assertEqual(events,["WEB","PUBLIC_DATA"])
        self.assertEqual(output["invocations"],2)
        self.assertEqual(len(output["checkpoint"]["evidence"]),1)
        self.assertEqual(output["checkpoint"]["frontier"][0]["status"],"CLOSED")
        self.assertFalse(output["operational_research_ready"])
        self.assertFalse(output["real_user_outcome_countable"])

    def test_transport_success_with_zero_rows_is_empty_and_switches_provider(self):
        events=[]
        def empty(request):
            events.append("WEB");return {"state":"SUCCESS","response":{"results":[]}}
        def public(request):
            events.append("PUBLIC_DATA");return found(request)
        output=run_with_providers(payload("A"),{
            "WEB":empty,"PUBLIC_DATA":public,"GITHUB":lambda r:found(r)
        })
        self.assertEqual(events,["WEB","PUBLIC_DATA"])
        self.assertEqual(output["events"][0]["reported_state"],"SUCCESS")
        self.assertEqual(output["next_run_input"]["provider_attempts"][0]["state"],"EMPTY")

    def test_all_distinct_routes_exhaust_without_same_route_loop(self):
        order=[]
        def fail(req):
            order.append(req["provider"])
            return {"state":"FAILED","error":"NO_RESULTS"}
        output=run_with_providers(payload("A"),{p:fail for p in
                                  ("WEB","PUBLIC_DATA","GITHUB")},max_rounds=6)
        self.assertEqual(order,["WEB","PUBLIC_DATA","GITHUB"])
        self.assertEqual(output["invocations"],3)
        self.assertEqual(output["state"],"HOLD_NO_ACTION")
        self.assertEqual({x["provider"] for x in output["events"]},
                         {"WEB","PUBLIC_DATA","GITHUB"})

    def test_one_failed_child_preserves_successful_sibling_and_recovers_only_gap(self):
        calls=[]
        def web(req):
            calls.append(("WEB",req["frontier_id"]))
            return found(req) if req["frontier_id"]=="A" else {"state":"FAILED","error":"TIMEOUT"}
        def public(req):
            calls.append(("PUBLIC_DATA",req["frontier_id"]))
            return found(req)
        output=run_with_providers(payload("A","B"),{
            "WEB":web,"PUBLIC_DATA":public,"GITHUB":lambda req:found(req)
        })
        self.assertEqual(calls,[("WEB","A"),("WEB","B"),("PUBLIC_DATA","B")])
        self.assertEqual({x["frontier_id"] for x in output["checkpoint"]["evidence"]},{"A","B"})
        self.assertEqual(output["invocations"],3)

    def test_access_hold_is_not_bypassed_by_third_provider(self):
        calls=[]
        def blocked(req):
            calls.append(req["provider"])
            return {"state":"FAILED","error":"AUTH_REQUIRED"}
        output=run_with_providers(payload("A"),{p:blocked for p in
                                  ("WEB","PUBLIC_DATA","GITHUB")})
        self.assertEqual(output["state"],"HOLD_ACCESS")
        self.assertEqual(calls,["WEB"])
        self.assertEqual(output["invocations"],1)

    def test_provider_exception_does_not_become_success_and_uses_alternative(self):
        def crashed(req):
            raise RuntimeError("secret-in-error-text")
        output=run_with_providers(payload("A"),{
            "WEB":crashed,"PUBLIC_DATA":found,"GITHUB":found
        })
        self.assertEqual(output["invocations"],2)
        self.assertEqual(output["events"][0]["error"],"PROVIDER_EXECUTION_EXCEPTION")
        self.assertNotIn("secret-in-error-text",str(output))
        self.assertEqual(len(output["checkpoint"]["evidence"]),1)

    def test_budget_preserves_intermediate_failure_checkpoint(self):
        def fail(req):return {"state":"FAILED","error":"TIMEOUT"}
        out=run_with_providers(payload("A"),{p:fail for p in
                               ("WEB","PUBLIC_DATA","GITHUB")},max_calls=1)
        self.assertEqual(out["state"],"HOLD_BUDGET")
        self.assertEqual(out["invocations"],1)
        self.assertEqual(len(out["next_run_input"]["provider_attempts"]),1)

    def test_memory_replacement_is_actual_invoked_provider_not_just_plan_text(self):
        memory={"failures":[{
            "failure_id":"F-stale","state":"OPEN","task_family":"GENERAL_RESEARCH",
            "route_signature":"search:stale","new_evidence_required":True,
            "replacement_routes":["search:official"],
        }]}
        order=[]
        def web(req):
            order.append("WEB");return found(req)
        def public(req):
            order.append("PUBLIC_DATA");return found(req)
        result=run_with_providers(payload("A",memory=memory,route="search:stale"),{
            "WEB":web,"PUBLIC_DATA":public,"GITHUB":web
        })
        self.assertEqual(order,["PUBLIC_DATA"])
        self.assertEqual(result["events"][0]["provider"],"PUBLIC_DATA")
        self.assertFalse(result["operational_research_ready"])


if __name__=="__main__": unittest.main()
