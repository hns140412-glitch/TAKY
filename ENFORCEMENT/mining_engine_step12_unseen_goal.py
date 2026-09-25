#!/usr/bin/env python3
"""STEP 12: unseen-goal generalization benchmark for Mining Engine V2."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from mining_run_orchestrator import orchestrate

def _ids(frontier):
    return {str(x.get("id")) for x in frontier if isinstance(x,dict) and x.get("id")}

def evaluate_case(case: dict) -> dict:
    result=orchestrate({"task":case.get("task",{}),"memory":case.get("memory",{})})
    plan=result["plan"]; gold=case.get("gold",{})
    produced=_ids(plan.get("search_frontier",[])); expected={str(x) for x in gold.get("expected_frontier_ids",[])}
    useful=len(produced & expected)
    precision=useful/len(produced) if produced else (1.0 if not expected else 0.0)
    recall=useful/len(expected) if expected else 1.0
    depth_ok=plan.get("research_depth_decision")==gold.get("expected_depth")
    route_ok=(not gold.get("expected_route")) or plan.get("selected_route")==gold.get("expected_route")
    no_leak=not bool(result.get("memory_prior",{}).get("strategy_memory",{}).get("selected")) if gold.get("expect_no_memory_strategy") else True
    allowed_ok=plan.get("execution_allowed")==gold.get("execution_allowed",True)
    passed=precision>=gold.get("min_precision",0.75) and recall>=gold.get("min_recall",0.75) and depth_ok and route_ok and no_leak and allowed_ok
    return {"case_id":case.get("case_id"),"task_family":case.get("task",{}).get("task_family"),"pass":passed,"precision":round(precision,4),"recall":round(recall,4),"depth_ok":depth_ok,"route_ok":route_ok,"no_cross_family_memory_leak":no_leak,"execution_allowed_ok":allowed_ok,"plan":plan}

def run_benchmark(payload: dict) -> dict:
    results=[evaluate_case(c) for c in payload.get("cases",[])]
    families={r["task_family"] for r in results if r.get("task_family")}
    passed=sum(1 for r in results if r["pass"])
    minimum=int(payload.get("minimum_distinct_families",3))
    ok=bool(results) and passed==len(results) and len(families)>=minimum
    return {"schema":"TAKY_MINING_ENGINE_STEP12_UNSEEN_GOAL_V1","pass":ok,"passed":passed,"total":len(results),"distinct_families":sorted(families),"minimum_distinct_families":minimum,"results":results,"guard":"Benchmark pass demonstrates only the declared unseen fixtures; it is not universal generalization proof."}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",type=Path,required=True); a=p.parse_args()
    r=run_benchmark(json.loads(a.input.read_text(encoding="utf-8"))); print(json.dumps(r,ensure_ascii=False,indent=2)); return 0 if r["pass"] else 1
if __name__=="__main__": raise SystemExit(main())
