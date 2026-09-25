#!/usr/bin/env python3
"""Heterogeneous end-to-end benchmark for TAKY Mining Engine.

Exercises the full pipeline using declared runtime responses:
Goal → Orchestrator → Provider requests → Runtime batch → External ingest
→ Mining Core checkpoint → Synthesis → Outcome → Growth proposal.

The benchmark may use live-captured or fixture runtime responses. The result
explicitly records which mode was used and does not claim universal validity.
"""
from __future__ import annotations

from mining_run_orchestrator import orchestrate
from mining_provider_execution_loop import build_requests
from mining_live_execution import execute_batch
from mining_core import checkpoint, apply_external_receipts, synthesize_checkpoint
from mining_growth_loop import propose_growth

def run_case(case:dict)->dict:
    task=dict(case.get("task",{}))
    memory=case.get("memory",{})
    orch=orchestrate({"task":task,"memory":memory})

    next_queries=[]
    for item in orch["plan"].get("search_frontier",[]):
        next_queries.append({
            "frontier_id":item.get("id"),
            "query":item.get("question") or item.get("id"),
            "prefer":case.get("provider_preferences",{}).get(item.get("id"),["OFFICIAL","IMPLEMENTATION"]),
            "purpose":"FILL_EVIDENCE_GAP",
        })

    requests=build_requests(next_queries,max_providers_per_query=int(case.get("max_providers_per_query",2)))
    runtime_results=case.get("runtime_results",{})
    batch=execute_batch(requests,runtime_results)

    base_cp=checkpoint(task,orch["plan"].get("search_frontier",[]),[])
    cp=apply_external_receipts(base_cp,batch.get("receipts",[]))
    synthesis=synthesize_checkpoint(cp)["synthesis"]

    outcome=case.get("outcome",{})
    growth=propose_growth({
        "task_family":task.get("task_family"),
        "goal":task.get("goal"),
        "selected_route":orch["plan"].get("selected_route"),
    },outcome) if outcome else None

    expected=case.get("expected",{})
    checks={
        "execution_allowed":orch["plan"].get("execution_allowed")==expected.get("execution_allowed",True),
        "min_evidence":len(cp.get("evidence",[]))>=int(expected.get("min_evidence",0)),
        "stop":cp.get("stop")==expected.get("stop",cp.get("stop")),
        "ready_for_recommendation_review":synthesis.get("ready_for_recommendation_review")==expected.get("ready_for_recommendation_review",synthesis.get("ready_for_recommendation_review")),
        "growth_type":True if not expected.get("growth_type") else (growth and growth.get("proposal",{}).get("type")==expected.get("growth_type")),
    }
    passed=all(checks.values())
    return {
        "case_id":case.get("case_id"),
        "task_family":task.get("task_family"),
        "mode":case.get("mode","FIXTURE_RUNTIME"),
        "pass":passed,
        "checks":checks,
        "provider_requests":requests,
        "runtime_batch":batch,
        "checkpoint":cp,
        "synthesis":synthesis,
        "growth":growth,
    }

def run_benchmark(payload:dict)->dict:
    results=[run_case(c) for c in payload.get("cases",[])]
    families={r.get("task_family") for r in results if r.get("task_family")}
    required=int(payload.get("minimum_distinct_families",3))
    live_count=sum(1 for r in results if r.get("mode")=="LIVE_CAPTURED_RUNTIME")
    ok=bool(results) and all(r["pass"] for r in results) and len(families)>=required
    return {
        "schema":"TAKY_MINING_E2E_BENCHMARK_V1",
        "pass":ok,
        "total":len(results),
        "passed":sum(1 for r in results if r["pass"]),
        "distinct_families":sorted(families),
        "minimum_distinct_families":required,
        "live_captured_case_count":live_count,
        "results":results,
        "guard":"Fixture-runtime success proves pipeline integration only; live-captured cases are tracked separately.",
    }
