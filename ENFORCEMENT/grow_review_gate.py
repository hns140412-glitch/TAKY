#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any

from growth_lineage_engine import growth_decision

REVIEW_STATES={"HOLD","STRATEGY_EXPERIMENT_READY","PROMOTION_REVIEW_READY"}

def _clean(v:object)->str:
    return str(v or "").strip()

def classify_candidate(candidate:dict[str,Any], evidence:dict[str,Any]|None=None)->dict[str,Any]:
    evidence=evidence or {}
    payload=candidate.get("payload") if isinstance(candidate.get("payload"),dict) else {}
    grow_domain=_clean(candidate.get("grow_domain")).upper()
    event_id=_clean(candidate.get("event_id"))
    authority=_clean(candidate.get("authority"))
    issues=[]

    if candidate.get("promotion_authorized") is not False:
        issues.append("PROMOTION_AUTHORITY_MUST_BE_FALSE")
    if candidate.get("authority_transfer") is not False:
        issues.append("AUTHORITY_TRANSFER_MUST_BE_FALSE")
    if not event_id:
        issues.append("EVENT_ID_MISSING")

    if issues:
        return {
            "event_id":event_id,
            "review_state":"HOLD",
            "issues":issues,
            "promotion_gate_invoked":False,
            "promotion_authorized":False,
            "next_required":"RESOLVE_CANDIDATE_CONTRACT_ISSUES",
        }

    # Learning-system aggregate evidence is only a signal to design/verify a strategy experiment.
    if grow_domain=="LEARNING_GROW" and payload.get("scope_kind")=="SYSTEM_AGGREGATE":
        members=int(payload.get("member_count") or 0)
        verified=int(payload.get("verified_outcome_count") or 0)
        if members < 3 or verified < 6:
            return {
                "event_id":event_id,"review_state":"HOLD","issues":issues+["SYSTEM_AGGREGATE_THRESHOLD_NOT_MET"],
                "promotion_gate_invoked":False,"promotion_authorized":False,
                "next_required":"MORE_PRIVACY_SAFE_VERIFIED_AGGREGATE_EVIDENCE"
            }
        strategy_outcomes=evidence.get("strategy_outcomes") if isinstance(evidence.get("strategy_outcomes"),list) else []
        regressions=evidence.get("regressions") if isinstance(evidence.get("regressions"),list) else []
        if not strategy_outcomes:
            return {
                "event_id":event_id,"review_state":"STRATEGY_EXPERIMENT_READY","issues":issues,
                "promotion_gate_invoked":False,"promotion_authorized":False,
                "next_required":"RUN_BOUNDED_STRATEGY_EXPERIMENT_AND_CAPTURE_VERIFIED_SYSTEM_OUTCOMES"
            }
        target=_clean(evidence.get("target_state")).upper() or "CURRENT_BEST"
        gate=growth_decision(
            {
                "target_state":target,
                "evidence_refs":evidence.get("evidence_refs") or [event_id],
                "external_evidence_verified":False,
                "design_parity_claim":evidence.get("design_parity_claim"),
                "design_user_signoff_ref":evidence.get("design_user_signoff_ref"),
            },
            strategy_outcomes,
            regressions,
        )
        return {
            "event_id":event_id,
            "review_state":"PROMOTION_REVIEW_READY" if gate.get("pass") else "HOLD",
            "issues":issues+list(gate.get("blockers") or []),
            "promotion_gate_invoked":True,
            "promotion_authorized":False,
            "growth_gate":gate,
            "next_required":"HUMAN_REVIEW" if gate.get("pass") else "RESOLVE_GROWTH_GATE_BLOCKERS"
        }

    # Other domains/candidates require explicit system outcome evidence before shared promotion review.
    outcomes=evidence.get("strategy_outcomes") if isinstance(evidence.get("strategy_outcomes"),list) else []
    regressions=evidence.get("regressions") if isinstance(evidence.get("regressions"),list) else []
    if not outcomes:
        return {
            "event_id":event_id,"review_state":"HOLD","issues":issues+["SYSTEM_OUTCOME_EVIDENCE_REQUIRED"],
            "promotion_gate_invoked":False,"promotion_authorized":False,
            "next_required":"VERIFIED_SYSTEM_OUTCOME_EVIDENCE"
        }
    target=_clean(evidence.get("target_state")).upper() or "CURRENT_BEST"
    gate=growth_decision(
        {
            "target_state":target,
            "evidence_refs":evidence.get("evidence_refs") or [event_id],
            "design_parity_claim":evidence.get("design_parity_claim"),
            "design_user_signoff_ref":evidence.get("design_user_signoff_ref"),
        },
        outcomes,regressions
    )
    return {
        "event_id":event_id,
        "review_state":"PROMOTION_REVIEW_READY" if gate.get("pass") else "HOLD",
        "issues":issues+list(gate.get("blockers") or []),
        "promotion_gate_invoked":True,
        "promotion_authorized":False,
        "growth_gate":gate,
        "next_required":"HUMAN_REVIEW" if gate.get("pass") else "RESOLVE_GROWTH_GATE_BLOCKERS"
    }

def evaluate_queue(queue:dict[str,Any], evidence_by_event:dict[str,Any]|None=None)->dict[str,Any]:
    evidence_by_event=evidence_by_event or {}
    results=[]
    for candidate in queue.get("candidates") or []:
        eid=_clean(candidate.get("event_id"))
        results.append(classify_candidate(candidate,evidence_by_event.get(eid) or {}))
    return {
        "schema":"TAKY_GROW_REVIEW_GATE_V1",
        "authoritative":False,
        "promotion_authorized":False,
        "candidate_count":len(results),
        "results":results,
        "states":{s:sum(1 for r in results if r.get("review_state")==s) for s in sorted(REVIEW_STATES)}
    }

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--queue",type=Path,required=True)
    p.add_argument("--evidence",type=Path)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    queue=json.loads(args.queue.read_text(encoding="utf-8"))
    evidence={}
    if args.evidence:
        evidence=json.loads(args.evidence.read_text(encoding="utf-8"))
    result=evaluate_queue(queue,evidence.get("by_event_id") if isinstance(evidence,dict) else {})
    text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding="utf-8")
    else:
        print(text,end="")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
