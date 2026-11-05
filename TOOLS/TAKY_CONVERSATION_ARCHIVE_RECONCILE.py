#!/usr/bin/env python3
"""Reconcile accessible TAKY ChatGPT share archive with existing Workbench.

Read-only sources: existing Drive-preserved share message indexes, context-event
journals and AI assignment registry. Writes only rebuildable local indexes/view.
No full account-coverage claim, source overwrite, model invocation or deployment.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import html
import json
import os
import sys
from pathlib import Path

ROOT=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\00_CONTROL")
INGEST=ROOT/"CHAT_INGEST"
OUT=ROOT/"CONVERSATION_TOPIC_PROJECTION.json"
OVERVIEW=ROOT/"CONVERSATION_TOPIC_OVERVIEW.json"
VIEWER=ROOT/"CONVERSATION_TOPIC_VIEWER.html"
ASSIGN=ROOT/"AI_WORK_ASSIGNMENTS.json"
HISTORY=Path(r"F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\04_HISTORY")
JOURNALS=[HISTORY/"TAKY_CONVERSATION_EVENTS_taky-drive-continuity-20261008.jsonl",
          HISTORY/"TAKY_CONVERSATION_EVENTS_taky-harness-feedback-20261016.jsonl"]

sys.path.insert(0,str(Path(__file__).resolve().parent))
import TAKY_CONVERSATION_SOURCE_BRIDGE as bridge
import TAKY_CONVERSATION_TOPIC_PROJECTION as topic

def encode(path,data):
    raw=json.dumps(data,ensure_ascii=False,indent=2)+"\n"
    temp=path.with_name(path.name+".rebuild")
    try:
        temp.write_text(raw,encoding="utf-8")
        os.replace(temp,path)
    finally:
        temp.unlink(missing_ok=True)

TITLE_FALLBACKS = [
    ("Ready & Set 로직","READY-SET","app","Ready & Set"),
    ("ZPD Word 로직","LEGACY-ZPD-WORD","vocabulary-app","ZPD Word (legacy)"),
    ("Snap & Pop 로직","SNAP-POP","app","Snap & Pop"),
    ("노션 구조 수정 재개","TAKY","notion-workspace","Notion 업무공간"),
    ("노션 연결 방법 안내","TAKY","notion-workspace","Notion 업무공간"),
    ("노션 링크 폴더 만들기","TAKY","notion-workspace","Notion 업무공간"),
    ("대화 복구 진행","TAKY","c2s-continuity","C2S·대화연속성"),
    ("설계개요 엑셀 작성","TAKY_ARCHI-GROW","design-overview","설계개요·엑셀"),
    ("모바일 기능 연결","TAKY-MOBILE","webapp-management","웹앱·배포·계정"),
    ("탐험 도우미 이름 추천","EXPLORER-CREW","crew-naming","탐험대원 네이밍"),
    ("Plus 기능 활용법","CHATGPT","plus-features","ChatGPT Plus 기능"),
    ("문구 검토 Translate","WRITING","translation","문구·번역"),
    ("유튜브 요약 AI 추천","AI-TOOLS","youtube-summarization","유튜브 AI 요약"),
    ("AI WORK OS 변화 감시","TAKY","ai-workos-monitor","AI Work OS 변화 감시"),
]
def title_seed(title):
    candidates=[{"project":p,"topic_key":key,"label":label}
                for match,p,key,label in TITLE_FALLBACKS if match==title]
    if len(candidates)>1:
        raise ValueError("DUPLICATE_TITLE_FALLBACK:"+title)
    return candidates[0] if candidates else None

def enrich_rows(rows,share,names):
    """Keep title hints separate from message facts, even for single-domain titles.

    A conversation is a container, not proof that all its turns share one topic.
    Preserve original message candidate tags from user-turn source; don't
    promote title or assistant guesswork to USER intent or canonical authority.
    """
    seed=title_seed(names.get(share,""))
    result=[]
    for row in rows:
        out=dict(row)
        if seed:
            out["chat_title_hint"]=dict(seed)
            out["chat_title_hint_status"]="TITLE_ONLY_NOT_MESSAGE_CLASSIFICATION"
        if out.get("topic_refs"):
            out["classification_source"]="MESSAGE_RULE_CANDIDATE"
        else:
            out["classification_source"]="UNCLASSIFIED_MANUAL_REVIEW"
        out["review_required"]=True
        result.append(out)
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--expected-archive",type=int,default=25)
    ap.add_argument("--review-output-dir",type=Path,help="Optional review-only destination; never alters current production projection")
    args=ap.parse_args()
    global OUT,OVERVIEW,VIEWER
    if args.review_output_dir:
        if not args.review_output_dir.is_dir():
            raise ValueError("REVIEW_OUTPUT_DIRECTORY_MISSING")
        OUT=args.review_output_dir/"CONVERSATION_TOPIC_PROJECTION.review.json"
        OVERVIEW=args.review_output_dir/"CONVERSATION_TOPIC_OVERVIEW.review.json"
        VIEWER=args.review_output_dir/"CONVERSATION_TOPIC_VIEWER.review.html"
    sources=sorted(INGEST.glob("SHARE_*.jsonl"))
    if len(sources)!=args.expected_archive:
        raise ValueError(f"ARCHIVE_SOURCE_COUNT_MISMATCH:{len(sources)}:{args.expected_archive}")
    all_rows=[]
    names={}
    source_files=[]
    titles=INGEST/"SHARE_TITLE_INDEX.json"
    if titles.is_file():
        names=json.loads(titles.read_text(encoding="utf-8-sig"))
    input_counts={}
    for p in sources:
        rows=topic.load_events([p])
        if not rows:
            raise ValueError("ARCHIVE_NO_CHAT_MESSAGES:"+p.name)
        share=p.stem.removeprefix("SHARE_")
        native={r.get("conversation_id") for r in rows}
        if len(native)!=1 or not next(iter(native)):
            raise ValueError("INCONSISTENT_OR_MISSING_NATIVE_ID:"+p.name)
        if not all(str(r.get("event_id","")).startswith("SHARE-"+share+":") for r in rows):
            raise ValueError("ARCHIVE_EVENT_ID_MISMATCH:"+p.name)
        sequence=[r.get("message_index") for r in rows]
        if sequence!=list(range(1,len(rows)+1)):
            raise ValueError("ARCHIVE_MESSAGE_SEQUENCE_GAP:"+p.name)
        input_counts[share]=len(rows)
        all_rows.extend(enrich_rows(rows,share,names))
        source_files.append(p)
    for j in JOURNALS:
        if j.is_file():
            all_rows.extend(topic.load_events([j]))
            source_files.append(j)
    view=bridge.merge_events([],all_rows)
    rows_by_native=collections.defaultdict(list)
    for row in all_rows:
        if row.get("conversation_id"):
            rows_by_native[row["conversation_id"]].append(row)
    assignment=json.loads(ASSIGN.read_text(encoding="utf-8-sig"))
    view=bridge.attach_ai_assignments(view,assignment)
    source_files.append(ASSIGN)
    if titles.is_file():
        source_files.append(titles)
    view["source_manifest"]=[{"path":str(p),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in source_files]
    view["source_coverage"]="25_ARCHIVED_SHARED_CONVERSATIONS_PLUS_EXISTING_JOURNALS__ACCOUNT_TOTAL_UNVERIFIED"
    view["topic_classification"]="RULE_BASED_CANDIDATE_NOT_SEMANTICALLY_VERIFIED"
    view["reconciliation_revision"]="TAKY_SHARE_ARCHIVE_READBACK_20261018"
    view["no_git_push_merge_deploy"]=True
    encode(OUT,view)
    chats=[]
    topic_labels={x["topic_id"]:x["label"] for x in view["topics"]}
    for c in view["chats"]:
        message_rows=rows_by_native[c["native_chat_ref"]]
        user_rows=[r for r in message_rows if r.get("actor")=="USER"]
        chat_transitions=[x for x in view["transitions"] if x["chat_id"]==c["chat_id"]]
        event_positions={x["event_id"]:i+1 for i,x in enumerate(c["links"])}
        transitions=[{
            "kind":x["kind"], "message_index":event_positions.get(x["event_id"]),
            "from_topic_id":x["from_topic_id"], "to_topic_id":x["to_topic_id"],
            "from_name":topic_labels.get(x["from_topic_id"],"START"),
            "to_name":topic_labels.get(x["to_topic_id"],"UNKNOWN"),
            "event_id":x["event_id"]
            } for x in chat_transitions]
        source_ids=sorted(set(x["source_ref"].split("#")[0].removeprefix("gdrive:")
                              for x in c["links"] if x.get("source_ref","").startswith("gdrive:")))
        shares=sorted(set(x["event_id"].split(":",1)[0].removeprefix("SHARE-")
                          for x in c["links"] if x["event_id"].startswith("SHARE-")))
        chats.append({"chat_id":c["chat_id"],
                      "native_chat_ref":c["native_chat_ref"],
                      "titles":[names.get(s, "대화 원본 "+s[:8]) for s in shares],
                      "share_ids":shares,
                      "drive_file_ids":source_ids,
                      "source_urls":["https://drive.google.com/file/d/"+f+"/view" for f in source_ids],
                      "messages":c["event_count"],"topics":c["topic_ids"],
                      "user_messages":len(user_rows),
                      "unclassified_user_messages":sum(not r.get("topic_refs") for r in user_rows),
                      "nontext_user_messages":sum(bool(r.get("nontext_marker")) for r in user_rows),
                      "empty_assistant_messages":sum(r.get("actor")=="ASSISTANT" and
                          int(r.get("content_length") or 0)==0 for r in message_rows),
                      "unclassified":sum(not x["topic_ids"] for x in c["links"]),
                      "multi_topic":sum(len(x["topic_ids"])>1 for x in c["links"]),
                      "title_hint":next((title_seed(names.get(s,"")) for s in shares
                                         if title_seed(names.get(s,""))),None),
                      "title_fallback":0,
                      "topic_transitions":transitions,
                      "topic_transition_candidate_count":len(transitions),
                      "source_order_review":sum(bool(x.get("source_order_review")) for x in c["links"]),
                      "active_topic_id":c["active_topic_id"]})
    topic_summary=[]
    for t in view["topics"]:
        topic_summary.append({"topic_id":t["topic_id"],"project":t["project"],"name":t["label"],
            "topic_key":t["topic_key"],"chats":len(t["chat_ids"]),
            "messages":len(t["event_ids"]), "related_work_ids":t["work_ids"],
            "linked_ai_work":len([x for x in t.get("ai_work_links",[]) if x["binding"]=="EXPLICIT_ID_MATCH"]),
            "chat_ids":t["chat_ids"]})
    nums=view["counts"]
    project_file=ROOT/"PROJECT_REGISTRY.json"
    current_drift=[]
    if project_file.is_file():
        projects=json.loads(project_file.read_text(encoding="utf-8-sig")).get("projects",{})
        for key,val in projects.items():
            if val.get("status")=="IDLE" and key=="TAKY" and view["ai_workbench"]["total_registered"]>0:
                current_drift.append({"project":key,"registered_project_status":"IDLE",
                    "ai_work_records":view["ai_workbench"]["total_registered"],
                    "classification":"STALE_PROJECT_STATE_CANDIDATE_REQUIRES_CURRENT_AND_RUNTIME_COMPARE"})
    index={
      "schema":"TAKY_WORKBENCH_CHAT_OVERVIEW_V1",
      "status":"HISTORICAL_ARCHIVED_SHARE_REVIEW_ONLY_NOT_ACCOUNT_WIDE",
      "archive_source_count":len(sources),
      "archive_message_count":sum(input_counts.values()),
      "archive_user_message_count":sum(c["user_messages"] for c in chats),
      "archive_unclassified_user_message_count":sum(c["unclassified_user_messages"] for c in chats),
      "archive_nontext_user_message_count":sum(c["nontext_user_messages"] for c in chats),
      "archive_empty_assistant_message_count":sum(c["empty_assistant_messages"] for c in chats),
      "distinct_backing_chat_count":len(chats),
      "raw_archive_input_counts":input_counts,
      "chat_coverage":nums,
      "topic_classification":"CANDIDATE_RULE_BASED_NOT_USER_CONFIRMED",
      "project_rollup":dict(collections.Counter(t["project"] for t in topic_summary)),
      "registered_state_drift_candidates":current_drift,
      "workbench_ai_jobs_registered":view["ai_workbench"]["total_registered"],
      "ai_jobs_linked_to_verified_chat_work_id":view["ai_workbench"]["topic_linked"],
      "ai_jobs_unlinked":view["ai_workbench"]["unlinked"],
      "unverified_model_jobs":view["ai_workbench"]["unverified_or_missing"],
      "title_fallback_message_count":0,
      "chat_title_hint_count":sum(c["title_hint"] is not None for c in chats),
      "unclassified_message_count":sum(c["unclassified"] for c in chats),
      "classification_approved_count":0,
      "source_archive_time_scope":"HISTORICAL_SAVED_CHATGPT_SHARES_2026-09-12",
      "other_accessible_evidence_not_native_id_bound":[
         {"file_id":"file_00000000e0f08206b67b7c7a5527a0c3",
          "name":"TAKY_GUIDE_대화전체보존_RAW_2026-09-07_0035KST.md",
          "role":"RAW_LIKE_ORDERED_TRANSCRIPT_NEEDS_NATIVE_CHAT_BIND"},
         {"file_id":"file_00000000de2c8209b43d7ac620cc9165",
          "name":"TAKY_CHAT_FULL_TRANSCRIPT_2026-09-07.docx",
          "role":"ACCESSIBLE_HISTORICAL_TRANSCRIPT_NEEDS_NATIVE_CHAT_BIND"},
         {"file_id":"file_0000000062c481f582eab728b60fa80b",
          "name":"TAKY_CHAT_FULL_TRANSCRIPT_2026-09-06.docx",
          "role":"POSSIBLY_OVERLAPPING_HISTORICAL_TRANSCRIPT_NEEDS_DEDUP_AUDIT"}
      ],
      "existing_topic_map_reference":{
          "name":"TAKY_GLOBAL_CONVERSATION_TOPIC_MAP",
          "url":"https://docs.google.com/document/d/1cq_KwemjNakj044wHID5v4WGaouGcsqT4YZMW3SiYRI/edit",
          "authority":"REFERENCE_ONLY_NOT_CANONICAL",
          "note":"Historical L0-L4 routing; 2026-09-19 override excludes NotebookLM from active continuity"
      },
      "source_gaps":["HISTORICAL_EXPORTS_ONLY_NOT_ALL_ACCOUNT_CONVERSATIONS",
                     "CHATGPT_NEWER_CONVERSATIONS_NOT_AUTOMATICALLY_SYNCED",
                     "CHATGPT_CURRENT_CONVERSATION_NOT_IN_THIS_ARCHIVE",
                     "PROVISIONAL_CLASSIFICATION_NEEDS_SEMANTIC_REVIEW",
                     "AI_ASSIGNMENTS_LACK_EXPLICIT_CHAT_SOURCE_LINKS"],
      "chats":sorted(chats,key=lambda c:-c["messages"]),
      "topics":sorted(topic_summary,key=lambda t:-t["messages"]),
      "no_paid_model_calls":True,"no_git_push_or_deploy":True
    }
    encode(OVERVIEW,index)
    # This is an index of unresolved USER-origin turns, not a copy of their text.
    # Short corrections and non-text turns remain in the queue; content length
    # is reported but never used to discard or silently declare irrelevance.
    review_queue=[]
    for c in chats:
        for row in rows_by_native[c["native_chat_ref"]]:
            if row.get("actor")=="USER" and not row.get("topic_refs"):
                review_queue.append({
                    "chat_id":c["chat_id"],"title":c["titles"][0],
                    "source_ref":row.get("source_ref"),
                    "event_id":row["event_id"],"message_index":row.get("message_index"),
                    "captured_at":row.get("captured_at"),
                    "content_length":row.get("content_length"),
                    "nontext_marker":bool(row.get("nontext_marker")),
                    "title_hint_not_authority":c.get("title_hint"),
                    "status":"USER_INTENT_NEEDS_ORIGINAL_TURN_REVIEW",
                    "no_decision_or_work_id_inferred":True})
    review_queue.sort(key=lambda r:(str(r["captured_at"] or ""),
                                    str(r["chat_id"]),int(r["message_index"] or 0)))
    queue={"schema":"TAKY_CHAT_UNCLASSIFIED_USER_REVIEW_QUEUE_V1",
           "scope":"25_HISTORICAL_SHARED_CHAT_ARCHIVES_NOT_ACCOUNT_COMPLETE",
           "authority":"REVIEW_QUEUE_DERIVED_NOT_CANONICAL",
           "count":len(review_queue),
           "unverified_nontext_count":sum(r["nontext_marker"] for r in review_queue),
           "original_text_stored_in_queue":False,"requires_original_turn_recovery":True,
           "items":review_queue}
    if args.review_output_dir:
        queue_path=args.review_output_dir/"CONVERSATION_UNCLASSIFIED_USER_QUEUE.review.json"
    else:
        queue_path=ROOT/"CONVERSATION_UNCLASSIFIED_USER_QUEUE.json"
    encode(queue_path,queue)
    cards=[]
    for c in index["chats"]:
        title=" · ".join(c["titles"])
        links=" ".join(f'<a target="_blank" rel="noopener" href="{html.escape(url,quote=True)}">보존 원문 보기</a>' for url in c["source_urls"])
        labels=", ".join(t["name"] for t in topic_summary if t["topic_id"] in c["topics"])
        search=html.escape((title+" "+labels).casefold(),quote=True)
        hint=c.get("title_hint")
        hint_html=('<p class="muted">제목 기반 참고 분류: '+html.escape(hint["label"])+
                   ' (메시지별 분류 증거로 사용하지 않음)</p>') if hint else ""
        steps="".join("<li>메시지 #"+str(x["message_index"] or "?")+": "+
                      html.escape(x["kind"])+": "+html.escape(x["from_name"])+
                      " → "+html.escape(x["to_name"])+"</li>"
                      for x in c["topic_transitions"])
        details=('<details><summary>주제 시작·전환·복귀 후보 '+
                 str(c["topic_transition_candidate_count"])+'건</summary><ol>'+steps+
                 '</ol></details>') if c["topic_transitions"] else ""
        cards.append(
            '<article class="entry" data-search="'+search+'" data-topic-ids="'+
            html.escape(" ".join(c["topics"]),quote=True)+'"><div><strong>'+html.escape(title)+
            '</strong><small> · '+str(c["messages"])+'개 메시지 · 미분류 '+str(c["unclassified"])+
            ' · 미분류 사용자 발언 '+str(c["unclassified_user_messages"])+
            ' · 복수 주제 '+str(c["multi_topic"])+'</small></div><p>'+
            html.escape(labels or "원문 기반 주제 미확인")+'</p>'+hint_html+
            details+'<div class="links">'+links+'</div></article>')
    topic_cards=[]
    for t in index["topics"]:
        topic_cards.append(
            '<button type="button" class="topic-filter" data-topic-id="'+
            html.escape(t["topic_id"],quote=True)+'"><strong>'+html.escape(t["name"])+
            '</strong><small> · '+html.escape(t["project"])+' · '+str(t["chats"])+
            '개 대화 · '+str(t["messages"])+'개 메시지 후보</small><code>'+
            html.escape(t["topic_id"])+'</code></button>')
    work_cards=[]
    for w in index["ai_jobs_unlinked"]:
        work_cards.append('<article class="entry"><strong>'+html.escape(str(w["executor"]))
            +'</strong> <small>'+html.escape(str(w["registry_status"]))
            +' · 결과 '+str(w["output_count"])+' · 증거 '+str(w["evidence_count"])
            +'</small><p><code>'+html.escape(w["work_id"])
            +'</code></p><p>대화 주제와의 원문 WORK_ID 연결 근거 미확보</p></article>')
    markup='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TAKY 대화 관제 · 보존 원문 검수</title><style>
    :root{color-scheme:dark}body{background:#0d1624;color:#f1f5fb;font:14px system-ui,sans-serif;max-width:1100px;margin:0 auto;padding:20px}
    h1{font-size:23px}h2{font-size:17px}p,small{color:#b7c4d5}input{background:#17283d;color:#fff;border:1px solid #4a6785;border-radius:12px;padding:15px;width:calc(100% - 32px);font-size:16px}
    .row{display:flex;gap:12px;flex-wrap:wrap}.metric{border:1px solid #2a405b;border-radius:14px;padding:15px;flex:1;min-width:135px;background:#13243a}
    .metric b{display:block;font-size:24px}.entry{background:#14243a;border:1px solid #2d4059;margin:10px 0;padding:14px;border-radius:14px}
    .entry strong{font-size:15px}.entry p{margin:8px 0}.links a{color:#9ccdff;margin-right:14px}.warn{border-left:3px solid #ffbf69;padding:10px;background:#1d2a3d}
    .topic-filter{display:inline-flex;flex-direction:column;gap:5px;text-align:left;background:#14243a;color:#e5effb;border:1px solid #304b68;border-radius:12px;padding:12px;margin:5px;cursor:pointer}
    .topic-filter[aria-pressed="true"]{outline:2px solid #79b9ff;background:#1a3958}.topic-filter code{font-size:11px;color:#94b8df}
    .muted{color:#e0c69c!important}details{margin:12px 0}summary{cursor:pointer;color:#a8d1ff}ol li{margin:5px 0}
    button{cursor:pointer}#clear-topic{padding:9px;background:#253f59;border:1px solid #5d87a3;border-radius:8px;color:#fff}
    </style><h1>TAKY 대화 통합 관제</h1><p class="warn">Google Drive에 보존된 과거 공유 대화 일부입니다. 계정 전체 실시간 목록이나 확정 CURRENT가 아닙니다. 주제 분류는 규칙 기반 검토 후보입니다.</p>
    <div class="row"><div class="metric">보존 대화<b>__CHATS__</b></div><div class="metric">전체 메시지<b>__MESSAGES__</b></div><div class="metric">사용자 발언<b>__USER_MESSAGES__</b></div><div class="metric">사용자 발언 분류 대기<b>__USER_UNCLASSIFIED__</b></div><div class="metric">주제 후보<b>__TOPICS__</b></div><div class="metric">연결된 AI 작업<b>__WORK__</b></div></div>
    <h2>원문 메시지 기반 주제 후보</h2><p>아래 주제를 선택하면 연결 후보 대화만 표시합니다. 제목에서 나온 힌트는 메시지 주제로 자동 승격하지 않습니다.</p>
    <button type="button" id="clear-topic">전체 대화 보기</button><p id="active-filter" aria-live="polite">전체 대화</p><div id="topic-list">__TOPIC_CARDS__</div>
    <h2>보존 대화 검색</h2><input id="q" placeholder="대화명 또는 주제 검색" aria-label="대화 검색"><div id="results">__CARDS__</div>
    <h2>AI 작업공간 · 연결 대기</h2><p>GPT·Claude·Codex 배정기록을 대화와 강제 연결하지 않았습니다. 원문 WORK_ID 확인이 필요합니다.</p>__AI_WORK_CARDS__
    <script>
    const input=document.getElementById("q"),active=document.getElementById("active-filter"),buttons=[...document.querySelectorAll(".topic-filter")];let selected="";
    function update(){const q=input.value.trim().toLowerCase();let visible=0;document.querySelectorAll("#results .entry").forEach(e=>{const match=(!selected||e.dataset.topicIds.split(" ").includes(selected))&&e.dataset.search.includes(q);e.hidden=!match;if(match)visible++});
      buttons.forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.topicId===selected)));
      const label=buttons.find(b=>b.dataset.topicId===selected)?.querySelector("strong")?.textContent||"전체 대화";
      active.textContent=label+" · "+visible+"개 대화 표시";
    }
    input.addEventListener("input",update);
    buttons.forEach(b=>b.addEventListener("click",()=>{selected=selected===b.dataset.topicId?"":b.dataset.topicId;update();document.getElementById("results").scrollIntoView({behavior:"smooth",block:"start"})}));
    document.getElementById("clear-topic").addEventListener("click",()=>{selected="";input.value="";update()});
    update();
    </script></html>'''
    markup=(markup.replace("__CHATS__",str(len(chats))).replace("__MESSAGES__",str(index["archive_message_count"]))
            .replace("__TOPICS__",str(len(topic_summary))).replace("__WORK__",str(index["ai_jobs_linked_to_verified_chat_work_id"]))
            .replace("__USER_MESSAGES__",str(index["archive_user_message_count"]))
            .replace("__USER_UNCLASSIFIED__",str(index["archive_unclassified_user_message_count"]))
            .replace("__CARDS__","\n".join(cards)).replace("__TOPIC_CARDS__","\n".join(topic_cards))
            .replace("__AI_WORK_CARDS__","\n".join(work_cards)))
    tmp=VIEWER.with_name(VIEWER.name+".rebuild")
    try:
        tmp.write_text(markup,encoding="utf-8")
        os.replace(tmp,VIEWER)
    finally:tmp.unlink(missing_ok=True)
    print(json.dumps({"archive_sources":len(sources),"chats":len(chats),"messages":index["archive_message_count"],
                      "topics":len(topic_summary),"unclassified":sum(c["unclassified"] for c in chats),
                      "multi_topic":sum(c["multi_topic"] for c in chats),
                      "ai_jobs_registered":index["workbench_ai_jobs_registered"],
                      "ai_work_ids_bound":index["ai_jobs_linked_to_verified_chat_work_id"],
                      "unbound_legacy_events":len(view["unbound_events"]),
                      "top_topics":[{"name":t["name"],"messages":t["messages"]} for t in index["topics"][:10]],
                      "projection_path":str(OUT),"overview_path":str(OVERVIEW),"viewer_path":str(VIEWER)},ensure_ascii=False))

if __name__=="__main__":
    main()
