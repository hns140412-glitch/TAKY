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
from pathlib import Path
import hashlib
from urllib.parse import urlsplit
from mining_run_orchestrator import orchestrate, advance_provider_batch
from mining_provider_executor import SUPPORTED_PROVIDERS

MAX_ORIGINAL_RECEIPT_BYTES = 25 * 1024 * 1024


def _verified_acquisition(proof):
    """Verify actual file bytes independently of a provider's claimed state.

    This is a *local integrity* check, not proof of publisher identity,
    permission, download transport, or domain approval.
    """
    if not isinstance(proof,dict) or proof.get("state")!="ACQUIRED_AND_PRESERVED":
        return None
    try:
        size=int(proof.get("size_bytes"))
        digest=str(proof.get("sha256") or "")
        path=Path(proof["preserved_path"])
        final=str(proof.get("final_url") or "")
        parsed=urlsplit(final)
        if (not 0 < size <= MAX_ORIGINAL_RECEIPT_BYTES or len(digest)!=64
                or not all(c in "0123456789abcdef" for c in digest.lower())
                or parsed.scheme.lower() not in {"http","https"} or not parsed.hostname
                or proof.get("canonical_promotion") is not False
                or not path.is_file() or path.stat().st_size!=size):
            return None
        h=hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b""):
                h.update(chunk)
        if h.hexdigest()!=digest.lower():
            return None
        return {key:proof.get(key) for key in (
            "state","sha256","size_bytes","preserved_path","final_url",
            "content_type","canonical_promotion")}
    except (OSError,ValueError,TypeError,KeyError):
        return None


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
            "source_files_preserved_requires_independent_local_sha_check":True,
            "local_integrity_not_publisher_authenticity":True,
        },
    }


def run_with_providers(payload:dict, providers:dict[str,Callable],
                       *, max_rounds:int=6, max_calls:int=12,
                       journal=None)->dict:
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
    if journal is not None:
        from mining_core import normalize_goal
        if getattr(journal,"goal_id",None)!=normalize_goal(payload.get("task") or {})["goal_id"]:
            return _result("HOLD_RUN_STATE",current=current,plan=None,events=[],
                           reason="JOURNAL_GOAL_MISMATCH")
    for _round in range(max_rounds):
        plan=orchestrate(current)["plan"]
        if not plan["execution_allowed"]:
            return _result("HOLD_NO_ACTION",current=current,plan=plan,
                           events=events,reason="FAILED_ROUTE_REQUIRES_NEW_METHOD",last=last)
        requests=_selected_requests(plan)
        if not requests:
            access_still_held=any(
                x.get("classification")=="ACCESS_HOLD" for x in
                (plan.get("pending_actions") or {}).get("items",[])
            )
            uncertain_still_held=any(
                x.get("classification")=="IN_FLIGHT_HOLD" for x in
                (plan.get("pending_actions") or {}).get("items",[])
            )
            state=("HOLD_IN_FLIGHT_UNCERTAIN" if uncertain_still_held else
                   "HOLD_ACCESS" if access_still_held else
                   "RESOLVED_FOR_SOURCE_REVIEW" if
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
        # Receipt replay consumes zero provider calls. Reserve only genuinely
        # new attempts; otherwise resuming with a small budget could fail even
        # though every selected request is already safely cached.
        new_calls=(sum(1 for request in callable_requests
                       if journal.will_invoke(request))
                   if journal is not None else len(callable_requests))
        if invoked+new_calls>max_calls:
            return _result("HOLD_BUDGET",current=current,plan=plan,events=events,
                           reason="MAX_PROVIDER_CALLS_REACHED",last=last)
        runtime_results={}
        for request in requests:
            provider=str(request["provider"]).upper()
            journal_replay=False
            if journal is not None:
                output,was_called,journal_replay=journal.execute(
                    request,provider_map.get(provider))
            else:
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
            claimed_proof=output.get("source_acquisition")
            proof=_verified_acquisition(claimed_proof)
            events.append({
                "request_id":request["request_id"],
                "frontier_id":request["frontier_id"],
                "provider":provider,
                "reported_state":str(output["state"]).upper(),
                "error":output.get("error"),
                "callback_invoked":was_called,
                "replayed_from_local_journal":journal_replay,
                "external_fetch_performed":output.get("external_fetch_performed") is True,
                "source_acquisition_integrity":(
                    "VERIFIED_LOCAL_BYTES" if proof else
                    "REJECTED_UNVERIFIED_RECEIPT" if isinstance(claimed_proof,dict)
                    else "NOT_CLAIMED"),
                # Provider metadata does not count as physical acquisition proof.
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
        if any(str(x.get("error") or "").upper() in {
                "IN_FLIGHT_UNCERTAIN","CORRUPT_ATTEMPT_JOURNAL",
                "SOURCE_RECEIPT_STALE"
            } for x in step["execution_batch"].get("results", [])):
            if not _selected_requests(step["plan"]):
                return _result("HOLD_IN_FLIGHT_UNCERTAIN",current=current,plan=step["plan"],
                               events=events,reason="RECONCILE_ATTEMPT_BEFORE_REPLAY",last=last)
        if any(x.get("state") in {"FAILED","EMPTY"} and str(x.get("error") or "").upper() in {
                "ACCESS_DENIED","AUTH_REQUIRED","LOGIN_REQUIRED","PERMISSION_DENIED",
                "RESTRICTED","PAYWALL","ACCESS_HOLD",
            } for x in step["execution_batch"].get("results", [])):
            # An access hold applies to that frontier, not unrelated branches.
            # Continue only already permitted, independently ready requests.
            if not _selected_requests(step["plan"]):
                return _result("HOLD_ACCESS",current=current,plan=step["plan"],
                               events=events,reason="AUTHORIZED_ROUTE_REQUIRED",last=last)
    return _result("HOLD_BUDGET",current=current,plan=orchestrate(current)["plan"],
                   events=events,reason="MAX_ROUNDS_REACHED",last=last)
