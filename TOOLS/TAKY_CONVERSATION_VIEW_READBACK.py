#!/usr/bin/env python3
"""Safely refresh local DERIVED conversation views, preserving rollback evidence.

This never writes TAKY CURRENT, raw conversations, Drive, model outputs, or deployment.
Windows may deny rename-overwrite while allowing a guarded in-place write. On any
failure, restore previous bytes and reject unsupported claims.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\00_CONTROL")
STAGE=ROOT/"CHAT_INGEST"/"REVIEW"
VIEWS=(
    ("CONVERSATION_TOPIC_PROJECTION.review.json","CONVERSATION_TOPIC_PROJECTION.json"),
    ("CONVERSATION_TOPIC_OVERVIEW.review.json","CONVERSATION_TOPIC_OVERVIEW.json"),
    ("CONVERSATION_TOPIC_VIEWER.review.html","CONVERSATION_TOPIC_VIEWER.html"),
    ("CONVERSATION_UNCLASSIFIED_USER_QUEUE.review.json","CONVERSATION_UNCLASSIFIED_USER_QUEUE.json"),
)

def digest(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def verify_stage(stage:Path=STAGE):
    p=json.loads((stage/VIEWS[0][0]).read_text(encoding="utf-8-sig"))
    v=json.loads((stage/VIEWS[1][0]).read_text(encoding="utf-8-sig"))
    h=BeautifulSoup((stage/VIEWS[2][0]).read_text(encoding="utf-8-sig"),"html.parser")
    q=json.loads((stage/VIEWS[3][0]).read_text(encoding="utf-8-sig"))
    if q.get("schema")!="TAKY_CHAT_UNCLASSIFIED_USER_REVIEW_QUEUE_V1" or q.get("authority")!="REVIEW_QUEUE_DERIVED_NOT_CANONICAL":
        raise ValueError("REVIEW_QUEUE_SCHEMA_OR_AUTHORITY_INVALID")
    if q.get("count")!=v.get("archive_unclassified_user_message_count") or len(q.get("items",[]))!=q["count"]:
        raise ValueError("REVIEW_QUEUE_COVERAGE_COUNT_MISMATCH")
    if q.get("original_text_stored_in_queue") is not False or any("text" in x for x in q["items"]):
        raise ValueError("REVIEW_QUEUE_MUST_NOT_DUPLICATE_CONVERSATION_TEXT")
    if p["schema"]!="TAKY_CONVERSATION_TOPIC_PROJECTION_V1" or p.get("authority")!="REBUILDABLE_VIEW_NOT_CANONICAL":
        raise ValueError("DERIVED_PROJECTION_AUTHORITY_INVALID")
    if v.get("archive_source_count")!=25 or v.get("distinct_backing_chat_count")!=25:
        raise ValueError("ARCHIVE_SOURCE_SCOPE_MISMATCH")
    if v.get("archive_message_count")!=sum(c["messages"] for c in v["chats"]):
        raise ValueError("MESSAGE_COUNT_MISMATCH")
    if len(p["chats"])!=25 or len(p["topics"])!=len(v["topics"]):
        raise ValueError("PROJECTED_TOPIC_INCONSISTENT")
    if any(c.get("title_fallback",0)!=0 for c in v["chats"]) or v.get("title_fallback_message_count")!=0:
        raise ValueError("TITLE_AS_MESSAGE_TOPIC_REINTRODUCED")
    if v.get("classification_approved_count")!=0 or v["topic_classification"]!="CANDIDATE_RULE_BASED_NOT_USER_CONFIRMED":
        raise ValueError("UNVERIFIED_CLASSIFICATION_PROMOTION")
    if p["ai_workbench"]["topic_linked"]!=v["ai_jobs_linked_to_verified_chat_work_id"]:
        raise ValueError("UNPROVEN_AI_WORK_ID_LINK")
    if len(h.select(".topic-filter"))!=len(v["topics"]):
        raise ValueError("UI_TOPIC_CARD_COUNT_MISMATCH")
    if len(h.select("#results .entry"))!=len(v["chats"]):
        raise ValueError("UI_CHAT_CARD_COUNT_MISMATCH")
    if not h.select_one("#clear-topic") or not h.select_one("#active-filter") or not h.select_one("#q"):
        raise ValueError("UI_TOPIC_SEARCH_CONTROLS_MISSING")
    if any(not x.get("topic_transitions") and x.get("topic_transition_candidate_count") for x in v["chats"]):
        raise ValueError("TOPIC_TRANSITION_EVIDENCE_MISSING")
    if sum(c["topic_transition_candidate_count"] for c in v["chats"])!=p["counts"]["transitions"]:
        raise ValueError("TOPIC_TRANSITION_SUM_MISMATCH")
    if v.get("existing_topic_map_reference",{}).get("authority")!="REFERENCE_ONLY_NOT_CANONICAL":
        raise ValueError("EXISTING_TOPIC_MAP_MISSING")
    return {"chats":25,"messages":v["archive_message_count"],"topic_candidates":len(v["topics"]),
            "transitions":p["counts"]["transitions"],"unclassified":v["unclassified_message_count"],
            "user_messages":v["archive_user_message_count"],
            "unclassified_user_messages":v["archive_unclassified_user_message_count"],
            "work_ids_unlinked":len(v["ai_jobs_unlinked"]),
            "browser_ui":"STRUCTURE_ONLY_NO_INTERACTION_ASSERTED"}

def guarded_write(dest:Path,source:bytes,backup_path:Path):
    if not dest.is_file():
        temp=dest.with_name(dest.name+".promote-temp")
        try:
            temp.write_bytes(source)
            os.replace(temp,dest)
        finally:
            temp.unlink(missing_ok=True)
        if digest(dest.read_bytes())!=digest(source):
            raise IOError("NEW_FILE_READBACK_FAILED:"+dest.name)
        return {"name":dest.name,"method":"CREATE_NEW","old_sha256":None,"new_sha256":digest(source)}
    old=dest.read_bytes()
    if old==source:
        return {"name":dest.name,"method":"UNCHANGED","old_sha256":digest(old),"new_sha256":digest(source)}
    if backup_path.exists() and backup_path.read_bytes()!=old:
        # A previous local refresh already consumed the default backup path.
        # Give each previous derived revision its own content-addressed rollback;
        # never overwrite or treat old rollback as the current destination.
        backup_path=backup_path.with_name(backup_path.name+"."+digest(old)[:16])
    if backup_path.exists():
        if backup_path.read_bytes()!=old:
            raise RuntimeError("ROLLBACK_HASH_COLLISION:"+dest.name)
    else:
        backup_path.write_bytes(old)
        if backup_path.read_bytes()!=old:
            raise IOError("ROLLBACK_BACKUP_NOT_VERIFIED:"+dest.name)
    try:
        # Prefer the normal atomic replace. If Windows refuses because the
        # derived-view file has an open no-delete handle, use an in-place write
        # only after a SHA-backed rollback copy and a readback comparison.
        temp=dest.with_name(dest.name+".promote-temp")
        try:
            temp.write_bytes(source)
            try:
                os.replace(temp,dest)
                method="ATOMIC_REPLACE"
            except PermissionError:
                if dest.read_bytes()!=old:
                    raise RuntimeError("DESTINATION_CHANGED_DURING_PROMOTION")
                with dest.open("r+b") as f:
                    f.write(source)
                    f.truncate()
                    f.flush()
                    os.fsync(f.fileno())
                method="GUARDED_IN_PLACE_COPY"
        finally:
            temp.unlink(missing_ok=True)
        if digest(dest.read_bytes())!=digest(source):
            raise IOError("POST_WRITE_READBACK_MISMATCH")
        return {"name":dest.name,"method":method,"old_sha256":digest(old),"new_sha256":digest(source)}
    except Exception:
        with dest.open("r+b") as f:
            f.write(old)
            f.truncate()
            f.flush()
            os.fsync(f.fileno())
        if dest.read_bytes()!=old:
            raise RuntimeError("CRITICAL_ROLLBACK_FAILED:"+dest.name)
        raise

def run(stage:Path=STAGE,root:Path=ROOT,promote:bool=False):
    result=verify_stage(stage)
    receipt={"schema":"TAKY_CHAT_LOCAL_DERIVED_VIEW_READBACK_V1",
             "preview_verification":result,
             "raw_conversation_changed":False,"canonical_current_changed":False,
             "model_calls":0,"remote_deployment":False,"file_updates":[]}
    if promote:
        rollback=stage/"_rollback_previous_derived"
        rollback.mkdir(exist_ok=True)
        for src,dst in VIEWS:
            receipt["file_updates"].append(guarded_write(root/dst,(stage/src).read_bytes(),rollback/dst))
        receipt["status"]="LOCAL_DERIVED_VIEWS_REFRESHED_READBACK_VERIFIED"
        receipt["reviewer_verified_decisions"]=False
    else:
        receipt["status"]="REVIEW_ONLY_NO_PRODUCTION_PROJECTION_CHANGED"
    out=stage/"READBACK_RECEIPT.json"
    out.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return receipt

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--promote-local-derived",action="store_true")
    args=parser.parse_args()
    print(json.dumps(run(promote=args.promote_local_derived),ensure_ascii=False))
