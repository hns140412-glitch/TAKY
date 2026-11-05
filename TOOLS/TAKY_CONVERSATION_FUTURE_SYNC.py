#!/usr/bin/env python3
"""Repeatable, source-limited October-and-future ChatGPT export ingestion.

Never calls undocumented ChatGPT APIs and never invents chat source IDs.
Watches a local intake folder only, preserving archives and CURRENT unchanged.
No work item is inferred from ordinary chat text; WORK_ID requires literal ID.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime, timezone
import TAKY_CONVERSATION_SOURCE_BRIDGE as bridge

ROOT=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\00_CONTROL")
INBOX=ROOT/"CHAT_INGEST"/"ACCOUNT_EXPORTS"
OUT=ROOT/"CONVERSATION_2026_10_ONWARD_TOPIC_INDEX.json"
ASSIGN=ROOT/"AI_WORK_ASSIGNMENTS.json"
START="2026-10-01"
MAX_BYTES=200_000_000

def eligible_date(when:str)->bool:
    if not when:return False
    try:
        dt=datetime.fromisoformat(when.replace("Z","+00:00"))
        return dt.astimezone(timezone.utc).date().isoformat()>=START
    except (ValueError,TypeError,OverflowError):
        return False

def parse_file(path:Path):
    if path.suffix.lower()==".zip":
        with zipfile.ZipFile(path) as z:
            candidates=[i for i in z.infolist()
                        if not i.is_dir() and (i.filename=="conversations.json"
                        or i.filename.endswith("/conversations.json"))]
            if len(candidates)!=1:
                raise ValueError("EXPECTED_ONE_CONVERSATIONS_JSON_IN_EXPORT_ZIP")
            part=candidates[0]
            if part.file_size>MAX_BYTES:raise ValueError("EXPORT_TOO_LARGE")
            with z.open(part) as f:
                payload=f.read(MAX_BYTES+1)
            if len(payload)>MAX_BYTES:raise ValueError("EXPORT_TOO_LARGE")
        # From_export operates on an explicit source file; temporary copy
        # contains only ChatGPT's account export bytes and is removed immediately.
        with tempfile.TemporaryDirectory(prefix="taky-chat-export-") as t:
            extracted=Path(t)/"conversations.json"
            extracted.write_bytes(payload)
            rows=bridge.from_export(extracted)
        for row in rows:
            row["source_ref"]="archive:"+str(path)+"#"+str(row["conversation_id"])+"/"+row["event_id"]
            row["source_kind"]="ACCOUNT_EXPORT_ZIP_EXACT_NATIVE_MESSAGE"
        return rows
    if path.name=="conversations.json" or path.name.endswith(".conversations.json"):
        return bridge.from_export(path)
    raise ValueError("UNSUPPORTED_EXPORT_NAME")

def main(inbox=INBOX,out=OUT,assign=ASSIGN):
    if not inbox.is_dir():raise FileNotFoundError("INTAKE_INBOX_MISSING:"+str(inbox))
    paths=sorted(p for p in inbox.iterdir() if p.is_file() and
                 (p.suffix.lower()==".zip" or p.name=="conversations.json" or p.name.endswith(".conversations.json")))
    all_events,manifest,holds=[],[],[]
    for path in paths:
        meta={"source":str(path),"file_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
              "size":path.stat().st_size}
        try:
            rows=parse_file(path)
            all_events.extend(rows)
            meta["parsed_messages"]=len(rows)
            meta["state"]="SOURCE_PARSED"
        except (ValueError,KeyError,TypeError,json.JSONDecodeError,zipfile.BadZipFile,UnicodeError) as e:
            holds.append({"source":str(path),"reason":type(e).__name__+":"+str(e)[:160]})
            meta["state"]="HOLD"
        manifest.append(meta)
    matched=[x for x in all_events if eligible_date(x.get("captured_at",""))]
    undated=[x for x in all_events if not x.get("captured_at")]
    view=bridge.merge_events([],matched)
    assignment=json.loads(assign.read_text(encoding="utf-8-sig"))
    view=bridge.attach_ai_assignments(view,assignment)
    view["schema"]="TAKY_CONVERSATION_2026_10_ONWARD_SOURCE_LIMITED_V1"
    view["source_coverage"]="ONLY_AUTHENTICATED_NATIVE_EXPORT_FILES_IN_LOCAL_INBOX"
    view["account_wide_coverage_verified"]=False
    view["unseen_live_chat_conversations"]="UNKNOWN"
    view["original_export_sources"]=manifest
    view["parsed_messages_outside_date_range"]=len(all_events)-len(matched)-len(undated)
    view["undated_messages_hold"]=len(undated)
    view["source_holds"]=holds
    view["future_sync_intent"]="REBUILD_WHEN_NEW_NATIVE_EXPORT_AVAILABLE"
    view["no_completion_inferred"]=True
    raw=json.dumps(view,ensure_ascii=False,indent=2)+"\n"
    if not out.parent.is_dir():raise FileNotFoundError("OUTPUT_PARENT_MISSING")
    changed=not out.is_file() or out.read_text(encoding="utf-8")!=raw
    if changed:
        temp=out.with_name(out.name+".candidate")
        try:
            temp.write_text(raw,encoding="utf-8")
            os.replace(temp,out)
        finally:temp.unlink(missing_ok=True)
    check=json.loads(out.read_text(encoding="utf-8"))
    if check["source_coverage"]!=view["source_coverage"] or check["counts"]!=view["counts"]:
        raise RuntimeError("READBACK_FAILED")
    return {"source_files":len(paths),"messages":len(matched),
            "chats_with_proven_native_id":view["counts"]["chat"],
            "topic_candidates":view["counts"]["topic"],
            "topic_switches":view["counts"]["transitions"],
            "work_ids_matched":view["ai_workbench"]["topic_linked"],
            "source_holds":len(holds),"undated_hold":len(undated),
            "changed":changed,"output":str(out),"account_wide_verified":False}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--inbox",type=Path,default=INBOX)
    parser.add_argument("--output",type=Path,default=OUT)
    args=parser.parse_args()
    print(json.dumps(main(inbox=args.inbox,out=args.output),ensure_ascii=False))
