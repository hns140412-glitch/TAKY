#!/usr/bin/env python3
"""One read-only local viewer for verified-scope Sept chats and October evidence.
No authority changes, no native ChatGPT access claims, no remote deployment.
"""
from __future__ import annotations
import collections
import html
import json
import os
from pathlib import Path
BASE=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\00_CONTROL")
SEP=BASE/"CONVERSATION_TOPIC_OVERVIEW.json"
OCT=BASE/"OCTOBER_CONVERSATION_EVIDENCE_INDEX.json"
FUTURE=BASE/"CONVERSATION_2026_10_ONWARD_TOPIC_INDEX.json"
DEST=BASE/"TAKY_CONVERSATION_UNIFIED_VIEW.html"
def esc(v):return html.escape(str(v if v is not None else ""),quote=True)
def generate(sep=SEP,oct=OCT,dest=DEST):
    a=json.loads(sep.read_text(encoding="utf-8-sig"))
    b=json.loads(oct.read_text(encoding="utf-8-sig"))
    future=json.loads(FUTURE.read_text(encoding="utf-8-sig")) if FUTURE.is_file() else {"chats":[],"topics":[]}
    if future.get("account_wide_coverage_verified") is True:raise ValueError("UNVERIFIED_COVERAGE")
    if a.get("archive_source_count")!=25 or b.get("account_wide_chat_coverage_verified") is not False:
        raise ValueError("SOURCE_COVERAGE_CLAIM_MISMATCH")
    by_work=collections.defaultdict(list)
    for r in b["records"]:
        w=r.get("work_id")
        if w:by_work[w].append(r)
    chats=[]
    for c in a["chats"]:
        source=c.get("source_urls") or []
        links="".join('<a href="'+esc(url)+'" target="_blank" rel="noopener">원문</a>' for url in source)
        title=", ".join(c["titles"])
        labels=", ".join(t["name"] for t in a["topics"] if t["topic_id"] in c["topics"])
        chats.append('<article class="entry" data-index="'+esc((title+" "+labels).casefold())+'">'
                     '<strong>'+esc(title)+'</strong><p>'+esc(labels or "주제 원문 검토 필요")+'</p>'
                     '<small>메시지 '+str(c["messages"])+' · 사용자 미분류 '+str(c.get("unclassified_user_messages",0))+
                     ' · 주제 전환 후보 '+str(c.get("topic_transition_candidate_count",0))+
                     '</small><nav>'+links+'</nav></article>')
    future_chat_rows=[]
    future_topic_labels={t["topic_id"]:t["label"] for t in future.get("topics",[])}
    for c in future.get("chats",[]):
        labels=", ".join(future_topic_labels.get(k,"검토 필요") for k in c.get("topic_ids",[]))
        search=esc((c["chat_id"]+" "+labels).casefold())
        future_chat_rows.append('<article class="entry" data-index="'+search+'"><strong>'+
            esc(c["chat_id"])+'</strong><p>'+esc(labels or "원문 주제 미분류")+
            '</p><small>계정 내보내기 원문 대화 · 메시지 '+str(c["event_count"])+
            '건 · 분류·결정 확정 아님</small></article>')
    work_rows=[]
    for work_id, recs in sorted(by_work.items()):
        recs.sort(key=lambda x:(x.get("when",""),x.get("record_id","")))
        statuses=list(dict.fromkeys(str(x.get("reported_status") or "") for x in recs))
        links="<details><summary>실행 증거 "+str(len(recs))+"건 · 상태 "+esc(", ".join(statuses))+'</summary><ol>'+              "".join("<li>"+esc(x.get("when",""))+" · "+esc(x.get("action",""))+" → "+esc(x.get("reported_status",""))+
                      " (영수증 기록, 실제 완료 검증 아님)</li>" for x in recs)+"</ol></details>"
        work_rows.append('<article class="entry" data-index="'+esc((work_id+" "+" ".join(statuses)).casefold())+'">'
                         '<strong><code>'+esc(work_id)+'</code></strong>'+links+
                         '<small>원본 ChatGPT 대화 연결 미확보</small></article>')
    relay_rows=[]
    for r in b["records"]:
        if r.get("source")!="AI_SHARED_CHAT_LOG_2026-10":continue
        topics=" / ".join(t["label"] for t in r["topic_candidates"])
        relay_rows.append('<article class="entry" data-index="'+esc((r["event_id"]+" "+r["task_id"]+" "+topics).casefold())+'">'
                          '<strong>'+esc(r["event_id"])+'</strong>'
                          '<p>'+esc(r["when"])+' · '+esc(r["event_kind"])+' · '+esc(r["reported_status"])+'</p>'
                          '<small>Task: '+esc(r["task_id"])+' · 주제 후보: '+esc(topics or "미분류")+
                          '</small><p class="muted">대화 원본 아님 / 인계 로그</p></article>')
    style="""*{box-sizing:border-box}body{font:15px system-ui,-apple-system,sans-serif;margin:0;background:#0d1724;color:#eaf3fb}
    header,main{max-width:1050px;margin:auto;padding:18px}header{padding-top:27px}
    h1{font-size:24px;margin:0 0 10px}h2{font-size:19px;margin:30px 0 12px}
    p,small{color:#bdcbd8}strong{color:#fff}
    .warn{border-left:4px solid #eca95e;background:#1b2b3d;padding:14px;border-radius:7px}
    .metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:10px}
    .metric{background:#142b42;padding:15px;border:1px solid #314b68;border-radius:12px}
    .metric b{display:block;font-size:23px;margin:7px 0}
    .switch{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}
    button{background:#203850;border:1px solid #52708b;color:white;border-radius:9px;padding:11px 14px;cursor:pointer}
    button[aria-pressed=true]{background:#215e85;border-color:#8bcfff}
    input{padding:13px;border-radius:10px;background:#0b2137;color:white;border:1px solid #55748d;width:100%;font-size:15px}
    .entry{padding:14px;background:#14263b;border:1px solid #2e445d;border-radius:12px;margin:10px 0;overflow-wrap:anywhere}
    .entry p{margin:7px 0}.entry small{display:block}.entry nav{margin-top:7px}
    a{color:#99ceff;margin-right:15px}details{margin:11px 0}summary{cursor:pointer;color:#a8d9ff}
    code{font-size:12px}li{margin:7px 0}.muted{color:#e7bb84}footer{margin-top:20px;color:#aabccc}
    [hidden]{display:none!important}"""
    sections=[
        ('sep','9월 보존 대화 원문',chats),
        ('oct-native','10월 이후 원문 대화',future_chat_rows),
        ('oct-work','10월 WORK_ID 실행 이력',work_rows),
        ('oct-relay','10월 AI 공용 대화 인계 로그',relay_rows)
    ]
    content="<header><h1>TAKY · 대화 / 오케스트레이션 통합 관제</h1>"+            '<p><a href="TAKY_CONVERSATION_PROGRESS_BOARD.html">프로젝트 · AI 작업 진행상황 관제 열기 →</a></p>'+            '<p class="warn"><strong>범위 표시:</strong> 9월 보존 대화 25개와 별도로 인입된 10월 이후 내보내기 자료만 원본 대화 ID에 연결합니다. 10월 전달 로그와 실행 영수증은 ChatGPT 일반 대화 원문이 아닙니다. AI PASS·DONE 기록은 독립 검증이나 승인 결정이 아닙니다.</p></header>'
    content+="<main><div class='metrics'>"+          "".join('<div class="metric">'+esc(label)+'<b>'+str(value)+'</b></div>' for label,value in [
          ("9월 보존 원문 대화",len(a["chats"])),("9월 메시지",a["archive_message_count"]),
          ("10월 이후 원본 대화 확보",len(future.get("chats",[]))),
          ("10월 전달·실행 증거",b["total_evidence_records"]),
          ("10월 실행 WORK_ID",b["work_ids_observed_in_receipts"]),
          ("미연결 사용자 발언",a["archive_unclassified_user_message_count"])])+"</div>"
    content+='<p>10월 인계 로그 중복 순번: '+esc(", ".join(map(str,b["relay_duplicate_sequence_numbers"])))+' · 작업표의 WORK_ID 정확 일치: '+str(b["work_ids_exact_matched_assignment_registry"])+'</p>'
    content+='<div class="switch">'+''.join('<button data-tab="'+ident+'" aria-pressed="'+('true' if ident=='sep' else 'false')+'">'+esc(label)+'</button>' for ident,label,_ in sections)+'</div>'
    content+='<input id="find" placeholder="선택한 구역에서 대화·주제·WORK_ID 검색" aria-label="대화 검색">'
    for ident,label,rows in sections:
        content+='<section id="'+ident+'" '+('' if ident=='sep' else 'hidden')+'><h2>'+esc(label)+'</h2>'
        content+='<p id="'+ident+'-count">'+str(len(rows))+'개 항목</p>'+''.join(rows)+'</section>'
    content+='<footer>원본은 Drive와 로컬 HISTORY에 유지됩니다. 표시된 분류는 검토 후보이며 TAKY CURRENT를 바꾸지 않습니다.</footer></main>'
    script="""const buttons=[...document.querySelectorAll('[data-tab]')],input=document.getElementById('find');
    let tab='sep';function refresh(){const q=input.value.trim().toLocaleLowerCase();for(const b of buttons)b.setAttribute('aria-pressed',String(b.dataset.tab===tab));
    for(const b of buttons){const section=document.getElementById(b.dataset.tab);section.hidden=b.dataset.tab!==tab;if(section.hidden)continue;
    let n=0;for(const e of section.querySelectorAll('.entry')){const ok=e.dataset.index.includes(q);e.hidden=!ok;if(ok)n++}
    section.querySelector('[id$="-count"]').textContent=n+'개 항목 표시';}}
    for(const b of buttons)b.addEventListener('click',()=>{tab=b.dataset.tab;input.value='';refresh()});
    input.addEventListener('input',refresh);refresh();"""
    doc='<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TAKY 통합 대화 관제</title><style>'+style+'</style></head><body>'+content+'<script>'+script+'</script></body></html>'
    if dest.is_file() and dest.read_text(encoding="utf-8")==doc:
        return {"path":str(dest),"changed":False,"sep_chats":len(chats),"oct_native":len(future_chat_rows),"oct_work":len(work_rows),"oct_relay":len(relay_rows)}
    tmp=dest.with_name(dest.name+".build-tmp")
    try:
        tmp.write_text(doc,encoding="utf-8")
        os.replace(tmp,dest)
    finally:tmp.unlink(missing_ok=True)
    if dest.read_text(encoding="utf-8")!=doc:raise RuntimeError("HTML_READBACK_FAILED")
    return {"path":str(dest),"changed":True,"sep_chats":len(chats),"oct_native":len(future_chat_rows),"oct_work":len(work_rows),"oct_relay":len(relay_rows)}
if __name__=="__main__":print(json.dumps(generate(),ensure_ascii=False))
