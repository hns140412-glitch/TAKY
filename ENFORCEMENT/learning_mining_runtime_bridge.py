#!/usr/bin/env python3
"""Learning evidence-gap route -> Mining V2 runtime bridge.

This bridge preserves owner boundaries:
- Learning emits a gap, never authorizes Mining directly.
- Index broker decides MINING_REQUEST only after Index insufficiency.
- Mining V2 plans/advances provider work.
- This bridge performs no network I/O and no canonical promotion.
"""
from __future__ import annotations
from typing import Any
from mining_run_orchestrator import orchestrate, advance_provider_batch

VERSION="TAKY_LEARNING_MINING_RUNTIME_BRIDGE_V1"

def _task_from_route(route:dict[str,Any])->dict[str,Any]:
    req=route.get("mining_request") or {}
    terms=[str(x).strip() for x in (req.get("query_terms") or []) if str(x).strip()]
    scope=req.get("scope") or {}
    goal="Acquire external reference evidence for Learning gap"
    if terms:
        goal += ": " + " ".join(terms)
    return {
        "task_family":"LEARNING_ENGINE",
        "goal":goal,
        "unknown":terms or [str(req.get("gap_type") or "learning evidence gap")],
        "critical_requirements":[str(req.get("requested_capability") or "EXTERNAL_REFERENCE_EVIDENCE")],
        "minimum_authority":(req.get("acceptable_authority_classes") or [None])[0],
        "learning_context":scope,
        "route_signature":"learning-gap:index-first",
        "source_constraints":{
            "acceptable_source_families":req.get("acceptable_source_families") or [],
            "acceptable_authority_classes":req.get("acceptable_authority_classes") or [],
            "required_provenance":req.get("required_provenance") or [],
        },
        "gap_id":req.get("gap_id"),
    }

def plan(route:dict[str,Any],*,index_rows=None,memory=None)->dict[str,Any]:
    if not isinstance(route,dict) or route.get("pass") is not True:
        return {"pass":False,"version":VERSION,"reason":"VALID_GAP_ROUTE_REQUIRED"}
    if route.get("decision")!="MINING_REQUEST" or route.get("index_sufficient") is not False:
        return {"pass":True,"version":VERSION,"mining_required":False,
                "reason":"GAP_ROUTE_DOES_NOT_REQUIRE_MINING","mining":None}
    if not isinstance(route.get("mining_request"),dict):
        return {"pass":False,"version":VERSION,"reason":"MINING_REQUEST_PAYLOAD_REQUIRED"}
    payload={"task":_task_from_route(route),"index_rows":index_rows or [],"memory":memory or {}}
    mining=orchestrate(payload)
    return {
        "pass":True,"version":VERSION,"mining_required":True,
        "gap_id":route.get("gap_id"),"mining":mining,
        "next_run_input":payload,
        "guards":{"network_io_performed":False,"canonical_promotion":False,
                  "index_gate_preserved":True,"learning_does_not_mine_directly":True},
    }

def advance(route:dict[str,Any],runtime_results:dict[str,Any],*,index_rows=None,memory=None,
            prior_run_input=None)->dict[str,Any]:
    prepared=plan(route,index_rows=index_rows,memory=memory)
    if not prepared.get("pass") or not prepared.get("mining_required"):
        return prepared
    payload=dict(prior_run_input or prepared["next_run_input"])
    result=advance_provider_batch(payload,runtime_results or {})
    return {
        "pass":True,"version":VERSION,"mining_required":True,
        "gap_id":route.get("gap_id"),"advance":result,
        "guards":{"network_io_performed_by_bridge":False,"canonical_promotion":False,
                  "provider_results_must_be_runtime_supplied":True},
    }
