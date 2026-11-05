"""Read-only goal routing into the existing TAKY canonical WORK_ID register.
Never creates work, alters CURRENT, dispatches models or grants approvals.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from TAKY_ORCHESTRATION_ADVANCE import choose, read_json, DEFAULT_BOARD, EVIDENCE

GOAL_ALIASES = {
    "오케스트라": ("INT-001", "CLN-002", "GATE-001"),
    "오케스트레이션": ("INT-001", "CLN-002", "GATE-001"),
    "reason": ("INT-001", "MCP-002", "MCP-001"),
    "리슨": ("INT-001", "MCP-002", "MCP-001"),
    "자동 진행": ("INT-001", "GATE-001"),
    "자동 인계": ("INT-001", "GATE-001"),
    "연결": ("INT-001", "MCP-001", "MCP-002"),
    "대청소": ("CLN-001", "CLN-002", "CLN-009"),
    "중복": ("CLN-001", "CLN-002"),
    "스킬": ("SKL-001", "SKL-002"),
    "사용량": ("OPS-001",),
    "가족": ("FAMILY-DURABLE-001",),
    "학습": ("FAMILY-DURABLE-001",),
}


def route_goal_to_existing_work(goal_text: str, board: dict,
                                evidence: Path | None=None,
                                *, limit: int=6) -> dict:
    """A read-only, source-bound objective projection, not a new task owner.

    Scores existing WORK_IDs only. If no locally executable step is safe,
    returns a concrete correction/evidence route instead of a user-stop or
    an invented new project. No model text or word match grants approval.
    """
    import unicodedata
    if (not isinstance(goal_text, str) or not goal_text.strip()
            or len(goal_text) > 500 or type(limit) is not int
            or not 1 <= limit <= 10):
        return {"schema":"TAKY_GOAL_TO_WORK_ID_V1", "status":"GOAL_INVALID"}
    goal = unicodedata.normalize("NFKC", goal_text).casefold()
    current = choose(board, evidence)
    members = {r["task_id"]: r for r in current["considered"]}
    score: dict[str, int] = {}
    # An explicit canonical WORK_ID is stronger than fuzzy title/alias scoring.
    # Match the complete identifier (never TAKY-001 inside TAKY-0012).
    explicit = []
    for work_id in members:
        found = re.search(r"(?<![a-z0-9-])" + re.escape(work_id.casefold())
                          + r"(?![a-z0-9-])", goal)
        if found:
            explicit.append((found.start(), work_id))
    for rank, (_position, work_id) in enumerate(sorted(explicit)):
        score[work_id] = score.get(work_id, 0) + max(80, 100-rank)
    for key, ids in GOAL_ALIASES.items():
        match=(re.search(r"(?<![a-z0-9])"+re.escape(key)+r"(?![a-z0-9])",goal)
               if key.isascii() else key in goal)
        if match:
            for idx, work_id in enumerate(ids):
                if work_id in members:
                    score[work_id] = score.get(work_id, 0) + max(1, 10-2*idx)
    # Scope only to canonical titles and ids; zero fuzzy ownership claims.
    words = set(re.findall(r"[a-z0-9가-힣]{3,}",goal))
    for work_id, row in members.items():
        heading = unicodedata.normalize("NFKC",str(row.get("title") or "")).casefold()
        matched = sum(1 for word in words if word in heading or word == work_id.casefold())
        if matched:
            score[work_id] = score.get(work_id, 0) + min(6, matched*2)
    if not score:
        return {"schema":"TAKY_GOAL_TO_WORK_ID_V1",
                "status":"NO_EXACT_CANONICAL_MATCH_ROUTE_TO_EXISTING_PLANNER",
                "goal_text":goal_text, "next_internal_action":
                    "USE_EXISTING_PORTFOLIO_PRIORITIES_AND_CURRENT;DO_NOT_INVENT_TASK",
                "existing_planner_selected":current.get("selected"),
                "model_calls":0, "done_claim":False}
    route_action = {
        "READY_FOR_LOCAL_EXECUTION": "EXECUTE_REGISTERED_SAFE_LOCAL_CHECK",
        "LOCAL_SLICE_NEEDS_CORRECTION": "RECONCILE_EXISTING_FAILED_EVIDENCE",
        "LOCAL_SLICE_ALREADY_EVIDENCED": "REUSE_EXISTING_EVIDENCE",
        "NEEDS_DEPENDENCY_EVIDENCE": "RESOLVE_VERIFIED_UPSTREAM_DEPENDENCY",
        "REQUIRES_APPROVAL": "OBTAIN_SPECIFIC_USER_APPROVAL_IF_NECESSARY",
        "LOCAL_EXECUTOR_NOT_BOUND": "DESIGN_EXECUTOR_THROUGH_EXISTING_GATES",
    }
    readiness = {
        "LOCAL_SLICE_NEEDS_CORRECTION":0,
        "READY_FOR_LOCAL_EXECUTION":1,
        "LOCAL_SLICE_ALREADY_EVIDENCED":2,
        "NEEDS_DEPENDENCY_EVIDENCE":3,
        "LOCAL_EXECUTOR_NOT_BOUND":4,
        "REQUIRES_APPROVAL":5,
    }
    chosen = sorted(score,key=lambda k:(-score[k],readiness.get(
        members[k]["route"], 8),k))[:limit]
    steps=[]
    for work_id in chosen:
        row=members[work_id]
        steps.append({"work_id":work_id,"priority_score":score[work_id],
                      "route":row["route"],
                      "next_internal_action":route_action.get(
                          row["route"],"INSPECT_EXISTING_WORK_AUTHORITY"),
                      "unresolved":row.get("unresolved",[]),
                      "source_evidence":row.get("existing_evidence"),
                      "model_calls_authorized":False,
                      "automatic_done":False})
    # The user's closest matching objective outranks the easiest unrelated
    # action. Report a blocked primary objective without inventing DONE.
    priority = steps[0]
    return {"schema":"TAKY_GOAL_TO_WORK_ID_V1",
            "status":"CANONICAL_WORK_ROUTED_NOT_DONE",
            "goal_text":goal_text,"steps":steps,
            "next_internal_action":priority["next_internal_action"],
            "next_work_id":priority["work_id"],
            "model_calls":0,"new_work_ids":0,
            "authority_changed":False,"done_claim":False}




def main():
    ap=argparse.ArgumentParser(description="Map a goal onto current registered TAKY work")
    ap.add_argument("--goal",required=True)
    ap.add_argument("--board",type=Path,default=DEFAULT_BOARD)
    ap.add_argument("--evidence",type=Path,default=EVIDENCE)
    args=ap.parse_args()
    print(json.dumps(route_goal_to_existing_work(args.goal,read_json(args.board),args.evidence),ensure_ascii=False))

if __name__=="__main__":
    main()
