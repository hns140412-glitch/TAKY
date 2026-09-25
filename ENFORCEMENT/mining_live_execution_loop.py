#!/usr/bin/env python3
"""Fallback policy for TAKY live Mining provider execution."""
from __future__ import annotations

def next_requests_after_batch(requests:list[dict],batch:dict)->list[dict]:
    failed=set(batch.get("failed_request_ids",[]) or [])
    empty=set(batch.get("empty_request_ids",[]) or [])
    retryable=failed|empty
    # Requests are pre-ordered by provider preference. If one provider for a
    # frontier fails/returns empty, expose only the next request for that same
    # frontier. Successful frontiers do not continue unnecessarily.
    success_frontiers={x.get("frontier_id") for x in batch.get("results",[]) if x.get("state")=="SUCCESS" and x.get("receipt",{}).get("results")}
    out=[]; seen=set()
    for req in requests or []:
        fid=req.get("frontier_id")
        rid=req.get("request_id")
        if fid in success_frontiers: continue
        if rid not in retryable: continue
        # caller supplies the remaining provider requests; this function only
        # marks the frontier as needing fallback, never repeats same request.
        if fid not in seen:
            seen.add(fid)
            out.append({"frontier_id":fid,"after_request_id":rid,"action":"TRY_NEXT_PROVIDER"})
    return out
