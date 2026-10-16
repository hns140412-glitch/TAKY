"""Use the existing local Mining goal evaluator for RAW candidate coverage."""
from pathlib import Path
import sys

MINING_MODULE=Path(__file__).resolve().parents[2]/"TAKY"/".local"/"TAKY_MINING_V2_SOURCE_CONSUMER_ISOLATED_20260929"/"ENFORCEMENT"

def evaluate_raw_goal(requirement_ids, verified_raw_ids):
    ids=list(requirement_ids)
    verified=set(verified_raw_ids)
    if not ids or any(not isinstance(x,str) or not x.strip() for x in ids):
        return {"status":"INVALID","raw_goal_sufficient":False}
    if not (MINING_MODULE/"mining_goal_sufficiency.py").is_file():
        return {"status":"EVALUATOR_UNAVAILABLE","raw_goal_sufficient":False}
    if str(MINING_MODULE) not in sys.path:
        sys.path.insert(0,str(MINING_MODULE))
    from mining_goal_sufficiency import evaluate
    assessed=[{"id":rid,"status":"CLOSED" if rid in verified else "OPEN"} for rid in ids]
    result=evaluate({"required_frontier_ids":ids},assessed)
    return {"status":"RAW_HASH_CANDIDATE_ONLY",
            "raw_goal_sufficient":result["goal_sufficient"],
            "raw_coverage":result["coverage"],
            "missing_ids":result["missing_required"],
            "unresolved_ids":result["unresolved_required"],
            "content_goal_sufficient":False,"release_approved":False}
