"""Bind a pre-existing local TAKY goal to canonical registered WORK_IDs.

Read-only planner: local Reason transport selects the intent; no arbitrary
payload from Reason becomes a command, new task, approval, model call, or DONE.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys


def resolve_prepared_goal(repo: Path, local: Path, queue_id: str, message_id: str) -> dict:
    intent_path = local / ("taky-goal-intent-" + queue_id + ".json")
    if not intent_path.is_file() or intent_path.is_symlink():
        return {"status":"REASON_PREPARED_MANIFEST_MISSING","dispatched":False}
    try:
        if intent_path.resolve().parent != local.resolve() or intent_path.stat().st_size > 4096:
            raise ValueError("UNTRUSTED_GOAL_INTENT")
        intent_bytes = intent_path.read_bytes()
        intent = json.loads(intent_bytes.decode("utf-8"))
        if (not isinstance(intent,dict)
                or set(intent) != {"schema","queue_id","goal_text"}
                or intent["schema"]!="TAKY_GOAL_INTENT_V1"
                or intent["queue_id"]!=queue_id
                or not isinstance(intent["goal_text"],str)
                or not 1<=len(intent["goal_text"].strip())<=500):
            raise ValueError("GOAL_CONTRACT_INVALID")
        tool_dir = repo / "TOOLS"
        if str(tool_dir) not in sys.path:
            sys.path.insert(0,str(tool_dir))
        from TAKY_ORCHESTRATION_GOAL_ROUTER import (
            route_goal_to_existing_work, DEFAULT_BOARD, EVIDENCE)
        board_bytes = DEFAULT_BOARD.read_bytes()
        board = json.loads(board_bytes.decode("utf-8-sig"))
        if not isinstance(board, dict):
            raise ValueError("CANONICAL_BOARD_SCHEMA_INVALID")
        routed=route_goal_to_existing_work(intent["goal_text"],board,EVIDENCE)
        if (routed.get("status")!="CANONICAL_WORK_ROUTED_NOT_DONE"
                or not routed.get("next_work_id")):
            return {"status":"REASON_GOAL_NO_CANONICAL_MATCH",
                    "dispatched":False}
        routed_hash=hashlib.sha256(json.dumps(
            routed, ensure_ascii=False, sort_keys=True,
            separators=(",",":")).encode("utf-8")).hexdigest()
        binding=hashlib.sha256(
            intent_bytes + b"\0" + board_bytes + b"\0" +
            routed_hash.encode("ascii")).hexdigest()
        result_path=local/("taky-goal-plan-"+message_id+".json")
        if result_path.is_file() or result_path.is_symlink():
            if result_path.is_symlink():
                raise ValueError("PLAN_SYMLINK")
            prior=json.loads(result_path.read_text(encoding="utf-8"))
            if (prior.get("schema")!="TAKY_REASON_GOAL_PLAN_V1"
                    or prior.get("binding_sha256")!=binding
                    or prior.get("queue_id")!=queue_id
                    or prior.get("message_id")!=message_id):
                return {"status":"REASON_GOAL_CHANGED_REPLAN_REQUIRED",
                        "dispatched":False}
            return {"status":"REASON_GOAL_PLAN_REUSED","dispatched":False,
                    "next_work_id":prior.get("next_work_id"),
                    "next_internal_action":prior.get("next_internal_action")}
        record={"schema":"TAKY_REASON_GOAL_PLAN_V1",
                "queue_id":queue_id,"message_id":message_id,
                "binding_sha256":binding,
                "canonical_board_sha256":hashlib.sha256(board_bytes).hexdigest(),
                "status":routed.get("status"),
                "next_work_id":routed.get("next_work_id"),
                "next_internal_action":routed.get("next_internal_action"),
                "steps":routed.get("steps",[]),
                "model_calls":0,"done_claim":False,
                "registered_work_ids_only":True}
        with result_path.open("x",encoding="utf-8") as stream:
            stream.write(json.dumps(record,ensure_ascii=False,indent=2)+"\n")
        return {"status":"REASON_GOAL_ROUTED_TO_CANONICAL_WORK",
                "dispatched":False,
                "next_work_id":record["next_work_id"],
                "next_internal_action":record["next_internal_action"],
                "local_plan_receipt":str(result_path.resolve().relative_to(repo.resolve()))}
    except (OSError,ValueError,TypeError,UnicodeError,KeyError) as error:
        return {"status":"REASON_PREPARED_GOAL_INVALID",
                "error_class":type(error).__name__, "dispatched":False}
