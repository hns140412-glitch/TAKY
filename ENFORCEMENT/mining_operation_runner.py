#!/usr/bin/env python3
"""Synchronous, bounded Mining provider handoff that actually invokes registered tools.

A plan/receipt is not an execution. The host supplies explicit authorized
provider functions keyed WEB/GITHUB/PUBLIC_DATA; this driver calls them and
feeds their observed results into the existing Core/checkpoint path.
No provider implementation, credentials, network privileges, canonical write
or task-family ownership is invented by this helper.
"""
from __future__ import annotations
from collections.abc import Callable
from mining_run_orchestrator import orchestrate, advance_provider_batch
from mining_provider_executor import SUPPORTED_PROVIDERS


def _selected_requests(plan):
    requests=list(plan.get("planned_provider_requests") or [])
    follow=plan.get("follow_up_activation") or {}
    if not requests and follow.get("state")=="READY_NEXT_BATCH":
        requests=list(follow.get("planned_provider_requests") or [])
    chosen={}
    for request in requests:
        fid=str(request.get("frontier_id") or "")
        if fid and fid not in chosen:
            chosen[fid]=request
    return list(chosen.values())


def _result(state, *, current, plan, events, reason=None, last=None):
    return {
        "schema":"TAKY_MINING_OPERATION_RUNNER_V1",
        "state":state,
        "reason":reason,
        "invocations":sum(1 for event in events if event.get("callback_invoked") is True),
        "attempt_records":len(events),
        "source_files_preserved":sum(
            1 for event in events
            if (event.get("source_acquisition") or {}).get("state")=="ACQUIRED_AND_PRESERVED"
        ),
        "events":events,
        "checkpoint":(last or {}).get("checkpoint") or current.get("verified_checkpoint"),
        "next_run_input":(last or {}).get("next_run_input") or current,
        "plan":plan,
        "operational_research_ready":bool(plan and plan.get("operational_research_ready")),
        "real_user_outcome_countable":False,
        "guards":{
            "host_supplies_authorized_provider_functions":True,
            "no_network_without_registered_provider":True,
            "no_auto_current_write_or_promotion":True,
            "provider_result_is_evidence_candidate":True,
            "failed_and_successful_siblings_preserved":True,
        },
    }


def run_with_providers(payload:dict, providers:dict[str,Callable],
                       *, max_rounds:int=6, max_calls:int=12)->dict:
    """Run actual callable provider attempts and bounded different-route fallbacks.

    State may be RESOLVED_FOR_SOURCE_REVIEW, NEEDS_EVIDENCE_VERIFICATION,
    HOLD_ACCESS, HOLD_PROVIDER_ADAPTER_UNAVAILABLE, HOLD_BUDGET,
    HOLD_NO_ACTION, or HOLD_RUN_STATE. No state claims source bytes were
    fetched, verified, or a user outcome observed merely from search rows.
    """
    if max_rounds < 1 or max_calls < 1:
        raise ValueError("PROVIDER_BUDGET_MUST_BE_POSITIVE")
    provider_map={str(k).upper():v for k,v in (providers or {}).items()
                  if str(k).upper() in SUPPORTED_PROVIDERS and callable(v)}
    current=dict(payload)
    events=[]
    last=None
    for _round in range(max_rounds):
        plan=orchestrate(current)["plan"]
        if not plan["execution_allowed"]:
            return _result("HOLD_NO_ACTION",current=current,plan=plan,
                           events=events,reason="FAILED_ROUTE_REQUIRES_NEW_METHOD",last=last)
        requests=_selected_requests(plan)
        if not requests:
            state=("RESOLVED_FOR_SOURCE_REVIEW" if
                   plan.get("operational_research_ready") else
                   "NEEDS_EVIDENCE_VERIFICATION" if
                   plan.get("research_complete_eligible") or
                   any(x.get("classification") in {"PROVIDER_RESULT_UNVERIFIED",
                       "INDEX_EVIDENCE_UNVERIFIED"} for x in
                       (plan.get("pending_actions") or {}).get("items",[]))
                   else "HOLD_NO_ACTION")
            return _result(state,current=current,plan=plan,events=events,
                           reason="NO_EXECUTABLE_PROVIDER_ACTION",last=last)
        if not provider_map:
            return _result("HOLD_PROVIDER_ADAPTER_UNAVAILABLE",current=current,
                           plan=plan,events=events,
                           reason="NO_AUTHORIZED_PROVIDER_REGISTERED",last=last)
        callable_requests=[r for r in requests if
                           str(r.get("provider") or "").upper() in provider_map]
        invoked=sum(1 for event in events if event.get("callback_invoked") is True)
        # Do not abandon an available sibling merely because another branch
        # has no registered adapter. Missing adapters are explicit noncalls.
        if invoked+len(callable_requests)>max_calls:
            return _result("HOLD_BUDGET",current=current,plan=plan,events=events,
                           reason="MAX_PROVIDER_CALLS_REACHED",last=last)
        runtime_results={}
        for request in requests:
            provider=str(request["provider"]).upper()
            was_called=provider in provider_map
            if not was_called:
                output={"state":"FAILED","error":"PROVIDER_ADAPTER_UNAVAILABLE"}
            else:
                try:
                    output=provider_map[provider](dict(request))
                    if not isinstance(output,dict) or str(output.get("state") or "").upper() not in {
                        "SUCCESS","EMPTY","FAILED"
                    }:
                        output={"state":"FAILED","error":"INVALID_PROVIDER_RESULT"}
                except Exception as exc:
                    # Never treat a child exception as research completion.
                    # Avoid copying exception text (may carry credentials).
                    output={"state":"FAILED","error":"PROVIDER_EXECUTION_EXCEPTION",
                            "error_type":type(exc).__name__}
            runtime_results[str(request["request_id"])]=output
            proof=output.get("source_acquisition")
            events.append({
                "request_id":request["request_id"],
                "frontier_id":request["frontier_id"],
                "provider":provider,
                "reported_state":str(output["state"]).upper(),
                "error":output.get("error"),
                "callback_invoked":was_called,
                "external_fetch_performed":output.get("external_fetch_performed") is True,
                # Physical acquisition receipt is distinct from claim support.
                **({"source_acquisition":{
                    key:proof.get(key) for key in (
                        "state","sha256","size_bytes","preserved_path","final_url",
                        "content_type","canonical_promotion")
                }} if isinstance(proof,dict) else {}),
            })
        step=advance_provider_batch(current,runtime_results)
        last=step
        if step.get("state")!="RECONCILED":
            return _result("HOLD_RUN_STATE",current=current,plan=plan,events=events,
                           reason=step.get("state"),last=last)
        current=step["next_run_input"]
        if any(x.get("state") in {"FAILED","EMPTY"} and str(x.get("error") or "").upper() in {
                "ACCESS_DENIED","AUTH_REQUIRED","LOGIN_REQUIRED","PERMISSION_DENIED",
                "RESTRICTED","PAYWALL","ACCESS_HOLD",
            } for x in step["execution_batch"].get("results", [])):
            return _result("HOLD_ACCESS",current=current,plan=step["plan"],
                           events=events,reason="AUTHORIZED_ROUTE_REQUIRED",last=last)
    return _result("HOLD_BUDGET",current=current,plan=orchestrate(current)["plan"],
                   events=events,reason="MAX_ROUNDS_REACHED",last=last)
