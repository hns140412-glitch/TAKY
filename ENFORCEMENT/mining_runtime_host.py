#!/usr/bin/env python3
"""Actual invocation boundary for Mining provider adapters.

The Mining engine plans provider requests. This host is the single place that
invokes registered provider adapters. Provider adapters may perform network I/O;
the host itself grants no source/index/learning authority.
"""
from __future__ import annotations
from typing import Any, Callable

VERSION="TAKY_MINING_RUNTIME_HOST_V1"
TERMINAL_STATES={"SUCCESS","EMPTY","FAILED"}

def _normalize_executor_result(raw:Any)->dict[str,Any]:
    if isinstance(raw,dict) and str(raw.get("state") or "").upper() in TERMINAL_STATES:
        state=str(raw.get("state")).upper()
        return {"state":state,"response":raw.get("response") or {},"error":raw.get("error")}
    if isinstance(raw,dict):
        return {"state":"SUCCESS","response":raw,"error":None}
    return {"state":"FAILED","response":{},"error":"PROVIDER_EXECUTOR_RESULT_INVALID"}

def execute_provider_requests(
    requests:list[dict[str,Any]],
    executors:dict[str,Callable[[dict[str,Any]],Any]],
)->dict[str,Any]:
    if not isinstance(executors,dict):
        return {"pass":False,"version":VERSION,"reason":"PROVIDER_EXECUTOR_REGISTRY_REQUIRED"}

    runtime_results={}
    invocations=[]
    errors=[]
    for request in requests or []:
        request_id=str(request.get("request_id") or "")
        provider=str(request.get("provider") or "").upper()
        if not request_id or not provider:
            errors.append("PROVIDER_REQUEST_INVALID")
            continue
        executor=executors.get(provider)
        if not callable(executor):
            runtime_results[request_id]={"state":"FAILED","response":{},"error":"PROVIDER_EXECUTOR_NOT_BOUND"}
            errors.append(f"PROVIDER_EXECUTOR_NOT_BOUND:{provider}")
            continue
        try:
            normalized=_normalize_executor_result(executor(dict(request)))
        except Exception as exc:  # fail closed at the host boundary
            normalized={"state":"FAILED","response":{},"error":f"PROVIDER_EXECUTOR_EXCEPTION:{type(exc).__name__}"}
        runtime_results[request_id]=normalized
        invocations.append({
            "request_id":request_id,
            "provider":provider,
            "state":normalized["state"],
        })

    return {
        "pass":not errors,
        "version":VERSION,
        "runtime_results":runtime_results,
        "invocations":invocations,
        "errors":errors,
        "guards":{
            "host_invokes_provider_adapter":True,
            "provider_result_is_candidate_only":True,
            "provider_cannot_write_mining_index_authority":True,
            "provider_cannot_write_learning_index_authority":True,
            "provider_cannot_write_learner_state":True,
        }
    }
