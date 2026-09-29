#!/usr/bin/env python3
"""Evidence-backed operational research assurance; never promotes a Mining candidate.

Separates an assessed Core checkpoint, actually recovered source bytes,
an exact quoted span, and an independently supplied claim-review receipt.
A provider's own metadata/direct_support claim cannot fill the latter two.
This module is read-only; Index retains identity and domain owners retain use.
"""
from __future__ import annotations

from datetime import date
import hashlib


ACTION = {
    "CHECKPOINT_UNAVAILABLE": "RESUME_OR_CREATE_CORE_CHECKPOINT",
    "REQUIRED_SCOPE_MISSING": "RECOVER_REQUIRED_GOAL_ITEM",
    "EVIDENCE_MISSING": "ACQUIRE_SOURCE_CANDIDATES",
    "CORE_ITEM_OPEN": "CONTINUE_RESEARCH_OR_CONFLICT_RESOLUTION",
    "CORE_CONFLICT": "CROSS_VALIDATE_CONTRADICTORY_CLAIMS",
    "SOURCE_POINTER_MISSING": "RECOVER_SOURCE_LOCATOR",
    "SOURCE_NOT_RETRIEVED": "FETCH_OR_RECOVER_ORIGINAL_SOURCE",
    "SNAPSHOT_INVALID": "REACQUIRE_INTACT_SOURCE",
    "EXACT_SPAN_MISSING": "RECOVER_EXACT_PASSAGE",
    "CLAIM_SUPPORT_UNREVIEWED": "VERIFY_CLAIM_AGAINST_EXACT_SOURCE",
    "CLAIM_NOT_SUPPORTED": "CORRECT_CLAIM_AND_REOPEN_RESEARCH",
    "FRESHNESS_UNVERIFIED": "CHECK_OFFICIAL_CURRENT_VERSION",
    "STALE_SOURCE": "REACQUIRE_CURRENT_SOURCE",
    "ACCESS_HOLD": "PRESERVE_HOLD_AND_FIND_AUTHORIZED_ALTERNATIVE",
    "SOURCE_GROUNDED": "NO_RESEARCH_ACTION",
}


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _date(value):
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def _required_items(task, full_frontier):
    required=task.get("required_frontier_ids")
    if required is None:
        required=[x.get("id") for x in full_frontier
                  if x.get("origin")!="GENERIC_SCAFFOLD"]
    result=list(dict.fromkeys(str(x) for x in required or [] if x))
    # Keep explicitly named critical items even if a caller provided a stale
    # incomplete required list. Missing IDs must surface, not disappear.
    for x in task.get("critical_frontier_ids",[]) or []:
        if str(x) not in result: result.append(str(x))
    return result


def _proof(evidence, snapshot_by_id, reviews_by_id, trusted_reviewers, task):
    sid=str(evidence.get("source_id") or "")
    locator=str(evidence.get("source_url") or evidence.get("source_locator") or "").strip()
    if not sid or not locator or locator.lower() in {"none","null","https://example.com"}:
        return "SOURCE_POINTER_MISSING", sid
    snap=snapshot_by_id.get(sid)
    if not isinstance(snap,dict) or snap.get("retrieval_state")!="FETCHED":
        return "SOURCE_NOT_RETRIEVED", sid
    raw=snap.get("source_text")
    if not isinstance(raw,str) or not raw.strip():
        return "SNAPSHOT_INVALID", sid
    sha=_digest(raw)
    if (snap.get("source_sha256") != sha or
        str(snap.get("source_locator") or "") != locator or
        not snap.get("retrieved_at")):
        return "SNAPSHOT_INVALID", sid
    excerpt=evidence.get("excerpt_text")
    if (not isinstance(excerpt,str) or not excerpt.strip() or excerpt not in raw
            or not evidence.get("excerpt_ref")):
        return "EXACT_SPAN_MISSING", sid
    eid=str(evidence.get("evidence_id") or "")
    review=reviews_by_id.get(eid, {}) if eid else {}
    if (not review or review.get("schema")!="TAKY_MINING_CLAIM_REVIEW_V1"
        or str(review.get("frontier_id") or "")!=str(evidence.get("frontier_id") or "")
        or str(review.get("source_id") or "")!=sid
        or review.get("source_sha256")!=sha
        or review.get("excerpt_sha256")!=_digest(excerpt)
        or review.get("excerpt_ref")!=evidence.get("excerpt_ref")
        or str(review.get("reviewer_id") or "") not in trusted_reviewers
        or not review.get("reviewed_at")):
        return "CLAIM_SUPPORT_UNREVIEWED", sid
    if review.get("claim_supported") is not True:
        return "CLAIM_NOT_SUPPORTED", sid
    if task.get("freshness_required"):
        latest=_date(snap.get("source_updated_at"))
        as_of=_date(task.get("freshness_as_of"))
        try: window=int(task.get("max_source_age_days"))
        except (ValueError,TypeError): window=None
        if not latest or not as_of or window is None or window < 0:
            return "FRESHNESS_UNVERIFIED",sid
        if latest>as_of or (as_of-latest).days>window:
            return "STALE_SOURCE",sid
    return "SOURCE_GROUNDED",sid


def audit_research(task:dict, full_frontier:list[dict], checkpoint=None, *,
                   source_snapshots=None, claim_reviews=None, trusted_reviewer_ids=None,
                   source_access_results=None)->dict:
    """Audit all required goal IDs, even if a depth cap omitted an item.

    Input snapshots/reviews must be supplied by the actual source reader and
    a separately authorized validator. This function checks exact bytes and
    scope but cannot authenticate remote publisher identity by itself.
    """
    from mining_core import normalize_goal
    from mining_pending_actions import _ids
    tasks=_required_items(task,full_frontier)
    checkpoint_ok=(isinstance(checkpoint,dict) and
        checkpoint.get("schema")=="TAKY_MINING_CORE_CHECKPOINT_V1" and
        (checkpoint.get("goal") or {}).get("goal_id")==normalize_goal(task)["goal_id"])
    by_item={}
    for row in full_frontier:
        for fid in _ids(row): by_item[fid]=row
    assessed={str(x.get("id")):x for x in (checkpoint or {}).get("frontier",[])
              if isinstance(x,dict)} if checkpoint_ok else {}
    evidence=(checkpoint or {}).get("evidence",[]) if checkpoint_ok else []
    snapshots={str(x.get("source_id")):x for x in (source_snapshots or [])
               if isinstance(x,dict) and x.get("source_id")}
    reviews={str(x.get("evidence_id")):x for x in (claim_reviews or [])
             if isinstance(x,dict) and x.get("evidence_id")}
    allowed={str(x) for x in (trusted_reviewer_ids or []) if x}
    access={str(x.get("frontier_id")):x for x in (source_access_results or [])
            if isinstance(x,dict) and x.get("frontier_id")}
    items=[]
    for fid in tasks:
        item=by_item.get(fid)
        actual_id=str((item or {}).get("id") or fid)
        row=assessed.get(actual_id)
        if not checkpoint_ok: state="CHECKPOINT_UNAVAILABLE"; sid=""
        elif item is None: state="REQUIRED_SCOPE_MISSING"; sid=""
        elif (access.get(actual_id) or {}).get("state") in {
            "ACCESS_DENIED","AUTH_REQUIRED","PERMISSION_DENIED","ACCESS_HOLD"}:
            state="ACCESS_HOLD"; sid=""
        elif row is None: state="REQUIRED_SCOPE_MISSING"; sid=""
        elif row.get("status")=="CONFLICT": state="CORE_CONFLICT"; sid=""
        elif row.get("status")!="CLOSED": state="CORE_ITEM_OPEN"; sid=""
        else:
            candidates=[e for e in evidence if isinstance(e,dict)
                        and str(e.get("frontier_id")) in _ids(item)]
            if not candidates: state="EVIDENCE_MISSING";sid=""
            else:
                proofs=[_proof(e,snapshots,reviews,allowed,task) for e in candidates]
                state,sid=next((p for p in proofs if p[0]=="SOURCE_GROUNDED"),proofs[0])
                if state!="SOURCE_GROUNDED":
                    # An explicit failed independent claim check outranks any
                    # merely missing snapshot/claim review.
                    failed=next((p for p in proofs if p[0]=="CLAIM_NOT_SUPPORTED"),None)
                    if failed: state,sid=failed
        items.append({"frontier_id":actual_id,"required_id":fid,
                      "state":state,"next_action":ACTION[state],
                      "source_id":sid or None,
                      "owner":"MINING","automatic_promotion_allowed":False})
    incomplete=[x for x in items if x["state"]!="SOURCE_GROUNDED"]
    return {
        "schema":"TAKY_MINING_RESEARCH_ASSURANCE_V1",
        "required_total":len(tasks),
        "source_grounded":len(items)-len(incomplete),
        "pending_count":len(incomplete),
        "items":items,
        "operational_research_ready":bool(tasks) and checkpoint_ok and not incomplete
            and bool(checkpoint.get("goal_sufficiency",{}).get("goal_sufficient")),
        "next_actions":[x for x in incomplete],
        "real_user_outcome_countable":False,
        "guards":{
            "source_snapshot_bytes_checked":True,
            "publisher_authenticity_not_inferred_from_payload":True,
            "provider_self_review_not_accepted":True,
            "checkpoint_label_alone_not_sufficient":True,
            "missing_required_item_cannot_be_silently_dropped":True,
            "output_never_contains_raw_snapshot_text":True,
        },
    }
