#!/usr/bin/env python3
"""Incrementally inventory October 2026 TAKY conversation-adjacent evidence.

STRICT: relay events and execution receipts are NOT native ChatGPT transcripts.
Do not create CHAT_ID or promote a receipt to conversational/user approval evidence.
Source stays unchanged; write only a deterministic, rebuildable Workbench view.
Future same-format records are picked up on rerun; any native ChatGPT export must
go through TAKY_CONVERSATION_SOURCE_BRIDGE.py first.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import re
import os
from pathlib import Path

ROOT=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\00_CONTROL")
LOG=ROOT/"CHAT_INGEST"/"AI_SHARED_CHAT_LOG_2026-10_source.md"
HISTORY=Path(r"F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\04_HISTORY")
ASSIGN=ROOT/"AI_WORK_ASSIGNMENTS.json"
OUT=ROOT/"OCTOBER_CONVERSATION_EVIDENCE_INDEX.json"
HEADER=re.compile(r"(?m)^## seq\s+(\d+)\s*[·—-]\s*(.+?)\s*$")
FIELD=re.compile(r"^\s*-\s+([a-z_]+):\s*(.*)$")
WORK=re.compile(r"^TAKY-CHAT-[0-9a-f]{32}$",re.I)

RULES=[
 ("TAKY-MOBILE","webapp-management","모바일 웹앱·배포",r"TAKY.?MOBILE|타키 모바일|웹앱|배포|모바일"),
 ("PLAY-CAMP","learning-experience","Play Camp",r"PLAY.?CAMP|플레이.?캠프|수련.?캠프"),
 ("READY-SET","app","Ready & Set",r"READY.?SET|Ready\s*&\s*Set|래디앤셋|레디앤셋"),
 ("HIDE-SEEK","app","Hide & Seek",r"HIDE.?SEEK|하이드.?앤.?씩|하이드.?앤.?시크"),
 ("SNAP-POP","app","Snap & Pop",r"SNAP.?POP|스냅.?앤.?팝"),
 ("SAVEY","finance-app","SAVEY",r"SAVEY|세이비"),
 ("TAKY_ARCHI-GROW","architecture","Archi Grow",r"ARCHI.?GROW|아키.?그로우|강북[57]구역"),
 ("TAKY","notion-workspace","Notion·연동",r"NOTION|노션"),
 ("TAKY","source-pipeline","원문·마이닝",r"MINING|COLLECTOR|INDEXING|FORMING|마이닝|수집기"),
 ("TAKY","orchestrator-kernel","TAKY 오케스트레이션",r"ORCHESTRAT|오케스트라|하네스|KERNEL|ENFORCEMENT|재개|HANDOFF|C2S|AI.?SHARED|공용.?로그|대화.?연속"),
]
def hash_text(text:str)->str:return hashlib.sha256(text.encode("utf-8")).hexdigest()
def hash_bytes(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def topics_for(text:str):
    from TAKY_CONVERSATION_TOPIC_PROJECTION import stable_topic_id
    out=[]
    for project,key,label,pattern in RULES:
        if re.search(pattern,text,re.I):
            out.append({"topic_id":stable_topic_id(project,key),"project":project,
                        "topic_key":key,"label":label,"classification":"KEYWORD_CANDIDATE_NOT_SEMANTIC_DECISION"})
    return out
def parse_relay(src:Path):
    raw=src.read_text(encoding="utf-8-sig")
    heads=list(HEADER.finditer(raw))
    results=[]
    for i,h in enumerate(heads):
        body=raw[h.end():heads[i+1].start() if i+1<len(heads) else len(raw)]
        metadata={}
        for line in body.splitlines():
            m=FIELD.match(line)
            if m and m.group(1) not in metadata:
                metadata[m.group(1)]=m.group(2).strip()
        eid=h.group(2).strip()
        task_id=metadata.get("task_id","")
        probe=task_id+" "+metadata.get("body","")[:300]
        topics=topics_for(probe)
        results.append({
            "record_id":"RELAY-"+hash_text(eid+"\x00"+str(i)+"\x00"+h.group(0))[:24],
            "reported_seq":int(h.group(1)),
            "event_id":eid,"source":"AI_SHARED_CHAT_LOG_2026-10",
            "source_ref":str(src)+"#"+eid,
            "when":metadata.get("ts",""),
            "event_kind":metadata.get("kind","UNKNOWN"),
            "sender":metadata.get("from",""),"receivers":metadata.get("to",""),
            "task_id":task_id,
            "reported_status":metadata.get("status","UNKNOWN"),
            "topic_candidates":topics,
            "unverified_semantics":True,"is_chat_message":False,
            "native_chat_id":None,"canonical_decision_verified":False,
            "metadata_hash":hash_text(body),
        })
    return results
def parse_receipts(folder:Path):
    out=[]
    for f in sorted(folder.glob("TAKY_CHAT_ORCH_*.json")):
        a=json.loads(f.read_text(encoding="utf-8-sig"))
        if a.get("schema")!="TAKY_CHAT_ORCH_V1":raise ValueError("UNEXPECTED_RECEIPT_SCHEMA:"+f.name)
        when=str(a.get("started_utc") or "")
        if not when.startswith("2026-10-"):continue
        work_id=str(a.get("work_id") or "").strip()
        task_id=str(a.get("task_id") or "").strip()
        if work_id and not WORK.fullmatch(work_id):
            # External task identifiers are still retained but do not count as native WORK_ID.
            work_status="NON_CANONICAL_WORK_ID"
        else:work_status="EXPLICIT_WORK_ID" if work_id else "NOT_PRESENT"
        topics=topics_for(task_id) if task_id else []
        out.append({
            "record_id":"ORCH-"+str(a.get("id") or f.stem.removeprefix("TAKY_CHAT_ORCH_")),
            "source":"TAKY_CHAT_ORCH_V1",
            "source_ref":str(f),"when":when,
            "action":a.get("action"),"executor":a.get("executor"),
            "reported_status":a.get("status"),
            "model_called":a.get("model_called"),
            "work_id":work_id or None,"work_id_evidence":work_status,
            "task_id":task_id or None,
            "topic_candidates":topics,
            "native_chat_id":None,"is_chat_message":False,
            "execution_verified":False,
            "status_basis":"SINGLE_RECEIPT_CLAIM_NOT_RUNTIME_VERIFICATION",
            "source_file_sha256":hash_bytes(f.read_bytes())
        })
    return out
def main(log:Path=LOG,history:Path=HISTORY,assign:Path=ASSIGN,output:Path=OUT):
    if not log.is_file():raise FileNotFoundError("OCTOBER_RELAY_LOG_NOT_CAPTURED:"+str(log))
    relay=parse_relay(log)
    receipts=parse_receipts(history)
    records=relay+receipts
    ids=[x["record_id"] for x in records]
    if len(ids)!=len(set(ids)):raise ValueError("SOURCE_EVENT_ID_COLLISION")
    assignments=json.loads(assign.read_text(encoding="utf-8-sig")).get("tasks",[])
    registry={r["work_id"]:r for r in assignments if r.get("work_id")}
    if len(registry)!=len([r for r in assignments if r.get("work_id")]):
        raise ValueError("ASSIGNMENT_WORK_ID_CONFLICT")
    recorded=set()
    explicitly_linked=[]
    for r in receipts:
        w=r.get("work_id")
        if w and r["work_id_evidence"]=="EXPLICIT_WORK_ID":
            recorded.add(w)
            if w in registry:
                explicitly_linked.append({"work_id":w,"receipt_ref":r["source_ref"],
                                          "basis":"EXACT_WORK_ID_WITH_AI_REGISTRY_ONLY",
                                          "native_chat_id":None})
    seq_count=collections.Counter(r["reported_seq"] for r in relay)
    reported_duplicate_seqs=sorted(k for k,v in seq_count.items() if v>1)
    id_count=collections.Counter(r["event_id"] for r in relay)
    duplicate_relay_ids=sorted(k for k,v in id_count.items() if v>1)
    no_topic=sum(not r["topic_candidates"] for r in relay)
    summary={
        "schema":"TAKY_OCTOBER_CONVERSATION_EVIDENCE_V1",
        "authority":"DERIVED_EVIDENCE_INDEX_NOT_CURRENT",
        "scope":"2026-10_READABLE_AI_RELAY_AND_LOCAL_ORCHESTRATOR_RECEIPTS_ONLY",
        "account_wide_chat_coverage_verified":False,
        "native_chat_transcripts_ingested":0,
        "chat_ids_bound":0,
        "log_entries":len(relay),
        "execution_receipts":len(receipts),
        "total_evidence_records":len(records),
        "relay_duplicate_sequence_numbers":reported_duplicate_seqs,
        "relay_duplicate_event_ids":duplicate_relay_ids,
        "relay_topic_unclassified":no_topic,
        "work_ids_observed_in_receipts":len(recorded),
        "work_ids_exact_matched_assignment_registry":len(set(x["work_id"] for x in explicitly_linked)),
        "work_receipt_matches":explicitly_linked,
        "assignment_count":len(registry),
        "receipt_statuses":dict(sorted(collections.Counter(str(r["reported_status"]) for r in receipts).items())),
        "receipt_dates":dict(sorted(collections.Counter(r["when"][:10] for r in receipts).items())),
        "relay_dates":dict(sorted(collections.Counter(r["when"][:10] for r in relay).items())),
        "topics_suggested_by_log":sorted(set(t["topic_id"] for r in relay for t in r["topic_candidates"])),
        "source_manifest":[{"path":str(log),"sha256":hash_bytes(log.read_bytes())},
                           {"path":str(assign),"sha256":hash_bytes(assign.read_bytes())}],
        "missing_sources":[
            "CHATGPT_OCTOBER_FULL_NATIVE_EXPORT_OR_TRANSCRIPT",
            "CHATGPT_CONTINUOUS_CONVERSATION_ID_AND_MESSAGE_STREAM",
            "RECEIPT_TO_ORIGINAL_USER_CHAT_ID_LINK",
            "OCTOBER_DIALOGUE_SEMANTIC_REVIEW_AND_DECISION_CHAIN",
        ],
        "sync_instruction":"Import actual ChatGPT native exports via TAKY_CONVERSATION_SOURCE_BRIDGE before asserting full October classification.",
        "records":records,
        "no_chat_or_work_completion_inferred":True,
        "git_push_merge_deployment":False
    }
    raw=json.dumps(summary,ensure_ascii=False,indent=2)+"\n"
    if not output.parent.is_dir():raise FileNotFoundError("OUTPUT_PARENT_MISSING")
    if output.is_file() and output.read_text(encoding="utf-8")==raw:
        changed=False
    else:
        tmp=output.with_name(output.name+".tmp")
        try:
            tmp.write_text(raw,encoding="utf-8")
            os.replace(tmp,output)
        finally:tmp.unlink(missing_ok=True)
        changed=True
    actual=json.loads(output.read_text(encoding="utf-8"))
    if len(actual["records"])!=len(records) or actual["account_wide_chat_coverage_verified"] is not False:
        raise AssertionError("READBACK_MISMATCH")
    return {"output":str(output),"changed":changed,
            **{k:summary[k] for k in ("log_entries","execution_receipts","total_evidence_records",
                 "relay_duplicate_sequence_numbers","work_ids_observed_in_receipts",
                 "work_ids_exact_matched_assignment_registry","native_chat_transcripts_ingested")},
            "readback":"PASS","source_scope":summary["scope"]}
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=OUT)
    args=parser.parse_args()
    print(json.dumps(main(output=args.output),ensure_ascii=False))
