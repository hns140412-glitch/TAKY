#!/usr/bin/env python3
"""Live provider execution coordinator for TAKY Mining Engine.

Consumes prepared provider requests plus runtime responses. It records success,
empty, and failure outcomes without losing the Mining checkpoint.
"""
from __future__ import annotations
from mining_provider_executor import provider_response_to_receipt

TERMINAL_PROVIDER_STATES={"SUCCESS","EMPTY","FAILED"}

def normalize_runtime_result(request:dict,runtime_result:dict)->dict:
    state=str((runtime_result or {}).get("state") or "").upper()
    if state not in TERMINAL_PROVIDER_STATES:
        state="FAILED"
    response=(runtime_result or {}).get("response") or {}
    error=(runtime_result or {}).get("error")
    receipt=provider_response_to_receipt(request,response) if state in {"SUCCESS","EMPTY"} else {
        "frontier_id":request.get("frontier_id"),
        "query":request.get("query"),
        "adapter":request.get("provider"),
        "request_id":request.get("request_id"),
        "results":[],
    }
    return {
        "schema":"TAKY_MINING_LIVE_EXECUTION_RESULT_V1",
        "request_id":request.get("request_id"),
        "provider":request.get("provider"),
        "frontier_id":request.get("frontier_id"),
        "state":state,
        "error":error,
        "receipt":receipt,
        "guards":{
            "provider_failure_does_not_drop_checkpoint":True,
            "empty_result_is_not_success_evidence":True,
            "runtime_result_is_not_canonical":True,
        },
    }

def execute_batch(requests:list[dict], runtime_results:dict)->dict:
    results=[]
    receipts=[]
    failed=[]
    empty=[]
    for req in requests or []:
        rid=req.get("request_id")
        rr=(runtime_results or {}).get(rid,{"state":"FAILED","error":"MISSING_RUNTIME_RESULT"})
        item=normalize_runtime_result(req,rr)
        results.append(item)
        if item["state"]=="FAILED":
            failed.append(rid)
        elif item["state"]=="EMPTY":
            empty.append(rid)
            receipts.append(item["receipt"])
        else:
            receipts.append(item["receipt"])
    return {
        "schema":"TAKY_MINING_LIVE_EXECUTION_BATCH_V1",
        "results":results,
        "receipts":receipts,
        "failed_request_ids":failed,
        "empty_request_ids":empty,
        "successful_request_ids":[x["request_id"] for x in results if x["state"]=="SUCCESS"],
        "continue_allowed":True,
    }
