#!/usr/bin/env python3
"""Learning -> Learning Index -> Mining Index -> Mining -> reindex -> Learning requery.

This module is a bounded cross-engine host. It calls engines/adapters but owns
none of their semantic authority.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Callable

from data_index_search import load_index
from learning_evidence_gap_broker import route_gap
from learning_mining_runtime_bridge import plan as plan_learning_mining
from learning_mining_runtime_bridge import advance as advance_learning_mining
from mining_runtime_host import execute_provider_requests

VERSION="TAKY_LEARNING_MINING_CLOSED_LOOP_HOST_V1"

def _planned_requests(prepared:dict[str,Any])->list[dict[str,Any]]:
    mining=prepared.get("mining") or {}
    plan=mining.get("plan") or {}
    requests=list(plan.get("planned_provider_requests") or [])
    if requests:
        return requests
    follow=plan.get("follow_up_activation") or {}
    return list(follow.get("planned_provider_requests") or [])

def _receipts(advanced:dict[str,Any])->list[dict[str,Any]]:
    step=advanced.get("advance") or {}
    batch=step.get("execution_batch") or {}
    return list(batch.get("receipts") or [])

def run_reference_gap(
    gap:dict[str,Any],
    *,
    index_path:Path,
    provider_executors:dict[str,Callable[[dict[str,Any]],Any]],
    index_owner_apply:Callable[[list[dict[str,Any]],dict[str,Any],Path],dict[str,Any]],
    learning_requery:Callable[[dict[str,Any],list[dict[str,Any]]],Any],
    memory:dict[str,Any]|None=None,
    min_results:int=1,
)->dict[str,Any]:
    if not callable(index_owner_apply):
        return {"pass":False,"version":VERSION,"reason":"MINING_INDEX_OWNER_CALLBACK_REQUIRED"}
    if not callable(learning_requery):
        return {"pass":False,"version":VERSION,"reason":"LEARNING_REQUERY_CALLBACK_REQUIRED"}

    route=route_gap(gap,index_path=index_path,min_results=min_results,consumer="LEARNING_ENGINE")
    if not route.get("pass"):
        return {"pass":False,"version":VERSION,"stage":"GAP_ROUTE","detail":route}

    if route.get("decision")=="SPECIALIST_EVIDENCE_REQUEST":
        return {
            "pass":True,"version":VERSION,"state":"SPECIALIST_EVIDENCE_REQUIRED",
            "route":route,"provider_host":None,"index_owner":None,"learning_requery":None,
            "guards":{"learner_performance_gap_never_calls_external_mining":True}
        }

    if route.get("decision")=="INDEX_REQUERY":
        result=learning_requery(route,load_index(index_path))
        return {
            "pass":True,"version":VERSION,"state":"LEARNING_REQUERY_COMPLETE",
            "route":route,"provider_host":None,"index_owner":None,"learning_requery":result
        }

    if route.get("decision")!="MINING_REQUEST":
        return {"pass":False,"version":VERSION,"reason":"UNSUPPORTED_GAP_ROUTE","route":route}

    index_rows=load_index(index_path)
    prepared=plan_learning_mining(route,index_rows=index_rows,memory=memory or {})
    if not prepared.get("pass") or not prepared.get("mining_required"):
        return {"pass":False,"version":VERSION,"stage":"MINING_PLAN","detail":prepared}

    requests=_planned_requests(prepared)
    if not requests:
        return {
            "pass":False,"version":VERSION,"stage":"MINING_PLAN",
            "reason":"NO_PROVIDER_REQUESTS_FOR_REQUIRED_MINING","detail":prepared
        }

    host=execute_provider_requests(requests,provider_executors)
    if not host.get("pass"):
        return {"pass":False,"version":VERSION,"stage":"PROVIDER_HOST","detail":host}

    advanced=advance_learning_mining(
        route,
        host["runtime_results"],
        index_rows=index_rows,
        memory=memory or {},
        prior_run_input=prepared.get("next_run_input"),
    )
    if not advanced.get("pass"):
        return {"pass":False,"version":VERSION,"stage":"MINING_ADVANCE","detail":advanced}

    receipts=_receipts(advanced)
    index_result=index_owner_apply(receipts,route,index_path)
    if not isinstance(index_result,dict) or index_result.get("pass") is not True:
        return {"pass":False,"version":VERSION,"stage":"MINING_INDEX_OWNER","detail":index_result}

    reroute=route_gap(gap,index_path=index_path,min_results=min_results,consumer="LEARNING_ENGINE")
    if not reroute.get("pass"):
        return {"pass":False,"version":VERSION,"stage":"POST_INDEX_ROUTE","detail":reroute}
    if reroute.get("decision")!="INDEX_REQUERY":
        return {
            "pass":True,"version":VERSION,"state":"INDEX_UPDATED_BUT_REFERENCE_GAP_REMAINS",
            "route":route,"provider_host":host,"mining":advanced,"index_owner":index_result,
            "post_index_route":reroute,"learning_requery":None,
            "guards":{"mining_cannot_self_authorize_index":True,"learning_requery_requires_index_sufficiency":True}
        }

    learning_result=learning_requery(reroute,load_index(index_path))
    return {
        "pass":True,"version":VERSION,"state":"CLOSED_LOOP_COMPLETE",
        "route":route,
        "provider_host":host,
        "mining":advanced,
        "index_owner":index_result,
        "post_index_route":reroute,
        "learning_requery":learning_result,
        "guards":{
            "learning_does_not_mine_directly":True,
            "mining_index_owner_is_independent":True,
            "learning_index_requery_after_index_update":True,
            "no_schedule_authority":True,
        }
    }
