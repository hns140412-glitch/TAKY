#!/usr/bin/env python3
"""Builds executable provider requests from Mining Core next queries."""
from __future__ import annotations
from mining_provider_executor import build_execution_request

DEFAULT_PROVIDER_ORDER={
 "PRIMARY":["WEB","PUBLIC_DATA","GITHUB"],
 "OFFICIAL":["PUBLIC_DATA","WEB","GITHUB"],
 "ACADEMIC":["WEB","PUBLIC_DATA","GITHUB"],
 "IMPLEMENTATION":["GITHUB","WEB","PUBLIC_DATA"],
 "COMMUNITY":["WEB","GITHUB","PUBLIC_DATA"],
 "UNKNOWN":["WEB","GITHUB","PUBLIC_DATA"],
}

def choose_providers(query_plan:dict)->list[str]:
    prefs=[str(x).upper() for x in (query_plan.get("prefer") or query_plan.get("preferred_source_classes") or [])]
    out=[]
    for source_class in prefs or ["UNKNOWN"]:
        for provider in DEFAULT_PROVIDER_ORDER.get(source_class,DEFAULT_PROVIDER_ORDER["UNKNOWN"]):
            if provider not in out: out.append(provider)
    return out

def build_requests(next_queries:list[dict],max_providers_per_query:int=2)->list[dict]:
    requests=[]
    for q in next_queries or []:
        for provider in choose_providers(q)[:max_providers_per_query]:
            req=build_execution_request(q,provider)
            if req.get("schema")=="TAKY_MINING_PROVIDER_REQUEST_V1":
                requests.append(req)
    return requests
