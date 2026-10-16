"""Build a no-network, no-approval operator review interface from verified queue."""
import hashlib
import json
import sqlite3
from pathlib import Path

import central_forming_review_queue as queue
import taky_central_source_factory as factory

DATA=queue.EVIDENCE/"TAKY_FULL_ANCHOR_REVIEW_875283c73ce17d400ac9.json"

def ui_name(manifest_sha256, html):
    if not isinstance(manifest_sha256,str) or len(manifest_sha256)!=64:
        raise ValueError("REVIEW_MANIFEST_SHA_INVALID")
    revision=hashlib.sha256(html.encode("utf-8")).hexdigest()[:12]
    return "TAKY_LOCAL_REVIEW_CONSOLE_"+manifest_sha256[:20]+"_"+revision+".html"


def validated_candidates(projection, data):
    if data is None:
        return {}
    if (not isinstance(data,dict) or data.get("schema")!="TAKY_SOURCE_APPLICATION_CANDIDATES_V1"
        or data.get("full_review_sha256")!=projection["manifest_sha256"]
        or data.get("semantic_approved") is not False
        or data.get("applied") is not False
        or not isinstance(data.get("items"),list)):
        raise ValueError("UNREVIEWED_CANDIDATE_SCOPE_OR_AUTHORITY_INVALID")
    known={p["source_id"]:p for p in projection["projected_sources"]}
    result={}
    fields=("observed_method","design_pattern","taky_gap","proposed_change","verification_test")
    for row in data["items"]:
        if not isinstance(row,dict):
            raise ValueError("CANDIDATE_RECORD_INVALID")
        sid=row.get("source_id")
        src=known.get(sid)
        if (not src or sid in result or row.get("raw_sha256")!=src["raw_sha256"]
            or row.get("review_anchor_sha256") not in
               {a["content_sha256"] for a in src["anchors"]}
            or row.get("semantic_approved") is not False):
            raise ValueError("CANDIDATE_RAW_OR_ANCHOR_NOT_BOUND")
        if any(not isinstance(row.get(k),str) or not 8<=len(row[k])<=380
               for k in fields):
            raise ValueError("CANDIDATE_TEXT_BUDGET_OR_MISSING")
        # Optional strict source-to-claim anchors for newly formed proposals.
        # Older application hypotheses remain visible but explicitly ungrounded.
        # Matching a quote proves textual grounding, never semantic approval.
        grounding=row.get("source_grounding")
        if grounding is not None:
            if (not isinstance(grounding,list) or not 1<=len(grounding)<=8):
                raise ValueError("FORMING_GROUNDING_SHAPE_INVALID")
            anchors={(a["id"],a["content_sha256"]):a for a in src["anchors"]}
            seen=set()
            checked=[]
            for proof in grounding:
                if (not isinstance(proof,dict) or set(proof)!={"field","anchor_id","content_sha256","exact_quote"}
                    or proof.get("field") not in ("observed_method","design_pattern")
                    or proof["field"] in seen
                    or not isinstance(proof.get("exact_quote"),str)
                    or not 24<=len(proof["exact_quote"])<=210):
                    raise ValueError("FORMING_GROUNDING_CLAIM_INVALID")
                anchor=anchors.get((proof["anchor_id"],proof["content_sha256"]))
                if not anchor or proof["exact_quote"] not in anchor["excerpt"]:
                    raise ValueError("FORMING_GROUNDING_QUOTE_NOT_IN_VERIFIED_SOURCE")
                seen.add(proof["field"])
                checked.append({**proof,"source_line_start":anchor.get("from_line"),
                                "source_line_end":anchor.get("to_line")})
            if seen!={"observed_method","design_pattern"}:
                raise ValueError("FORMING_GROUNDING_REQUIRED_FIELDS_MISSING")
        else:
            checked=[]
        result[sid]={**{k:row[k] for k in fields},
                     "source_grounding":checked,
                     "grounding_state":("TEXTUALLY_GROUNDED_SEMANTIC_REVIEW_PENDING"
                        if checked else "UNANCHORED_HYPOTHESIS_REVIEW_PENDING")}
    return result


def render(projection, db, application_candidates=None, candidate_stylesheet=None):
    if projection["schema"]!="TAKY_CENTRAL_FULL_ANCHOR_REVIEW_PROJECTION_V1":
        raise ValueError("INVALID_REVIEW_PROJECTION")
    payload=dict(projection); digest=payload.pop("manifest_sha256")
    if queue.digest(payload)!=digest:
        raise ValueError("REVIEW_PROJECTION_HASH_MISMATCH")
    sources=[]
    for p in projection["projected_sources"]:
        l=db.execute("""SELECT locator,name,metadata_json FROM location WHERE source_id=?
          AND provider='LOCAL_FILE' AND trust='RAW_HASH_VERIFIED'
          ORDER BY CASE WHEN LOWER(name)='source.txt' THEN 0
                        WHEN LOWER(name) LIKE '%.pdf' THEN 1 ELSE 2 END,
                   locator LIMIT 1""",(p["source_id"],)).fetchone()
        if not l:
            raise ValueError("REVIEW_SOURCE_LOCATION_MISSING")
        raw=Path(l["locator"])
        if not raw.is_file():
            raise ValueError("REVIEW_SOURCE_FILE_MISSING")
        # Prefer the existing source title from the central catalog, never
        # fall back to a meaningless content-hash filename when one exists.
        metadata=json.loads(l["metadata_json"] or "{}")
        display=str(metadata.get("title") or "").strip()
        if not display:
            display=raw.parent.name if raw.name.lower() in ("source.txt","source.html") else raw.name
        sources.append({**p,"display_name":display[:240],
                        "file_path":str(raw),"local_file_url":raw.as_uri()})
    page=HTML.replace("/*__REVIEW_DATA__*/",json.dumps(
        {"schema":"TAKY_LOCAL_REVIEW_UI_DATA_V1","projection_sha256":digest,
         "total_index_sources":projection["source_count"],
         "sources":sources,"holds":projection["existing_holds"],
         "application_candidates":validated_candidates(projection,application_candidates),
         "verbatim_reference_mentions":projection["verbatim_reference_mentions"],
         "anchor_count":projection["verified_anchor_count"]},
        ensure_ascii=False).replace("<","\\u003c").replace(">","\\u003e"))
    if candidate_stylesheet is not None:
        if (not isinstance(candidate_stylesheet,str) or not 80<len(candidate_stylesheet)<=30000
            or "</style" in candidate_stylesheet.lower() or "<script" in candidate_stylesheet.lower()):
            raise ValueError("DESIGN_CANDIDATE_CSS_INVALID")
        page=page.replace("</style></head>",
            "</style><style data-design-state='CANDIDATE_NOT_APPROVED'>"+
            candidate_stylesheet+"</style></head>",1)
        page=page.replace("DEEP MEMORY · LIGHT EXECUTION &nbsp; / &nbsp; 검토 입력 전용 · 승인 불가",
            "REFERENCE → METHOD → TAKY CHANGE / 디자인 시안 검토 중 · 미승인",1)
        page=page.replace("<title>TAKY · 근거 검토 콘솔</title>",
            "<title>TAKY 자료 판단 작업대 — 디자인 후보</title>",1)
        # Native buttons with aria-pressed are keyboard-reachable; a listbox of
        # role=option buttons without arrow-key handling would be misleading.
        page=page.replace('id="sourceList" role="listbox" aria-label="근거 목록"',
                          'id="sourceList" role="group" aria-label="원문 목록"',1)
        page=page.replace("b.setAttribute('role','option');b.setAttribute('aria-selected',s.source_id===selected?'true':'false');",
                          "b.setAttribute('aria-pressed',s.source_id===selected?'true':'false');",1)
        page=page.replace('<section id="stats"></section>',
                          '<section id="stats" aria-label="검토 현황"></section>',1)
        page=page.replace('<div class="hint" id="filtered"></div>',
                          '<div class="hint" id="filtered" role="status" aria-live="polite"></div>',1)
        page=page.replace("const controls=node('div','review-row');const sel=node('select');",
                          "const controls=node('div','review-row');const sel=node('select');sel.setAttribute('aria-label','검토 메모 상태');",1)
        page=page.replace("const area=node('textarea','','');area.placeholder=",
                          "const area=node('textarea','','');area.setAttribute('aria-label','원문 검토 메모');area.placeholder=",1)
    return page


HTML=r"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>TAKY · 근거 검토 콘솔</title>
<style>
:root{color-scheme:dark;--bg:#0b1018;--surface:#131b26;--surface2:#1a2533;--line:#2b3645;--text:#e8edf4;--muted:#92a0b4;--accent:#89d4c5;--warn:#ffc68a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.6 system-ui,-apple-system,'Malgun Gothic',sans-serif}button,input,select,textarea{font:inherit}button{cursor:pointer}a{color:var(--accent)}
#app{height:100dvh;display:flex;flex-direction:column;max-width:1800px;margin:auto}
header{height:76px;min-height:76px;display:flex;align-items:center;justify-content:space-between;padding:0 26px;border-bottom:1px solid var(--line);gap:18px}
.brand{display:flex;align-items:center;gap:15px}.symbol{background:var(--accent);color:#102329;width:40px;height:40px;border-radius:13px;display:grid;place-items:center;font-size:20px;font-weight:900;letter-spacing:-2px}
h1{margin:0;font-size:18px;line-height:1.1;letter-spacing:-.45px}header p{margin:5px 0 0;color:var(--muted);font-size:11px}
header .actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}button,.link{border:1px solid var(--line);background:var(--surface2);color:var(--text);border-radius:9px;padding:9px 13px;text-decoration:none}
button:hover,.link:hover{border-color:var(--accent)}.primary{background:var(--accent);color:#132a2c;border:0;font-weight:700}
#stats{display:flex;gap:14px;padding:16px 26px;border-bottom:1px solid var(--line);overflow:auto}.stat{flex:1;min-width:135px;padding:12px 16px;border-radius:11px;background:var(--surface);border:1px solid var(--line)}
.stat strong{display:block;font-size:23px;line-height:1.16;letter-spacing:-.7px}.stat span{font-size:13px;color:var(--muted)}.stat.warn strong{color:var(--warn)}
main{display:grid;grid-template-columns:minmax(260px,340px) minmax(0,1fr);flex:1;min-height:0}
nav{border-right:1px solid var(--line);display:flex;flex-direction:column;min-height:0}
.filters{padding:16px;display:grid;gap:10px;border-bottom:1px solid var(--line)}
input,select,textarea{width:100%;background:#0e1621;border:1px solid var(--line);border-radius:9px;padding:10px 12px;color:var(--text);outline:0}
input:focus,select:focus,textarea:focus{border-color:var(--accent)}.hint{font-size:11px;color:var(--muted)}
#sourceList{overflow-y:auto;overflow-x:hidden;padding:7px;display:grid;grid-template-columns:minmax(0,1fr);align-content:start;gap:4px}
.source{display:block;text-align:left;background:transparent;min-width:0;width:100%;padding:12px;border:1px solid transparent;border-radius:10px;color:var(--text)}
.source:hover{background:var(--surface2)}.source.selected{background:#193239;border-color:#386a68}.source .name{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:14px}
.source .meta{display:flex;gap:6px;margin-top:7px;align-items:center;flex-wrap:wrap}
.chip{font-size:10px;border:1px solid var(--line);color:var(--muted);padding:1px 6px;border-radius:5px}.chip.tint{color:var(--accent);border-color:#365a58}
#detail{overflow:auto;min-width:0;padding:25px 30px 60px}
.eyebrow{text-transform:uppercase;font-size:10px;letter-spacing:1.6px;color:var(--accent);font-weight:700}.title{font-size:24px;font-weight:750;overflow-wrap:anywhere;margin:7px 0 12px;line-height:1.35}
.description{color:var(--muted);font-size:14px}.detailbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:16px 0 26px}
.section{border-top:1px solid var(--line);padding:21px 0}.sect-head{display:flex;justify-content:space-between;gap:10px;margin-bottom:16px;align-items:center}
h2{font-size:15px;margin:0;letter-spacing:-.2px}.anchor{background:var(--surface);border:1px solid var(--line);padding:16px;border-radius:11px;margin-bottom:9px}
.anchor-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;gap:12px}.anchor-head strong{font-size:12px}
.anchor pre{font-family:inherit;margin:0;white-space:pre-wrap;overflow-wrap:anywhere;color:#c9d4e1;font-size:14px;line-height:1.75}
.anchor small{color:var(--muted);font:10px ui-monospace,monospace}.method-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:15px 0}.method-grid .anchor{min-width:0;margin-bottom:0}.method-grid .anchor:first-child{grid-column:1/-1}.marker{display:inline-flex;border:1px solid #6a5844;color:#ffd49b;border-radius:5px;padding:3px 7px;font-size:11px;margin:0 5px 7px 0}
textarea{min-height:95px;resize:vertical}.review-row{display:grid;grid-template-columns:180px 1fr;gap:12px;margin-bottom:10px}
.banner{background:#252315;border:1px solid #5b4a30;color:#e6c796;border-radius:9px;padding:10px 12px;margin:14px 0;font-size:12px}
.empty{color:var(--muted);padding:25px}.footnote{color:var(--muted);font-size:11px;margin-top:8px}
@media(max-width:740px){.method-grid{grid-template-columns:minmax(0,1fr)}.method-grid .anchor:first-child{grid-column:auto}header{height:auto;min-height:78px;padding:15px;align-items:flex-start}header .actions{justify-content:end}.brand{gap:8px}h1{font-size:15px}header p{font-size:10px}#stats{padding:9px;gap:6px}.stat{min-width:115px;padding:10px}.stat strong{font-size:19px}main{grid-template-columns:minmax(130px,35%) minmax(0,1fr)}.filters{padding:8px}#sourceList{padding:4px}.source{padding:9px}.source .name{font-size:11px}#detail{padding:15px 11px}.title{font-size:17px}.review-row{display:block}.detailbar{gap:5px}}
</style></head>
<body><div id="app">
<header><div class="brand"><div class="symbol">T.</div><div><h1>TAKY <span style="color:var(--accent)">근거 검토</span></h1><p>DEEP MEMORY · LIGHT EXECUTION &nbsp; / &nbsp; 검토 입력 전용 · 승인 불가</p></div></div>
<div class="actions"><button id="importNotes">메모 불러오기</button><button class="primary" id="exportNotes">검토 메모 내보내기 ↓</button><input id="importInput" type="file" accept=".json" style="display:none"/></div></header>
<section id="stats"></section>
<main><nav><div class="filters"><input id="search" type="search" placeholder="원문·키워드 검색 ( / )" aria-label="원문 검색"/>
<select id="domain" aria-label="도메인"><option value="">모든 분야</option></select><select id="reviewFilter" aria-label="검토 상태"><option value="">전체 상태</option><option value="none">메모 없음</option><option value="noted">메모 작성</option><option value="revisit">추가 확인</option></select>
<div class="hint" id="filtered"></div></div><div id="sourceList" role="listbox" aria-label="근거 목록"></div></nav>
<article id="detail"><p class="empty">왼쪽의 원문을 선택하세요.</p></article></main></div>
<script>
const DATA=/*__REVIEW_DATA__*/;
const $=id=>document.getElementById(id);
const notes=new Map();
let selected=null;
const all=DATA.sources;
const domains=[...new Set(all.map(x=>x.domain_hint))].sort();
for(const d of domains){const o=document.createElement('option');o.value=d;o.textContent=d;$('domain').append(o)}
const esc=s=>String(s??'');
function node(tag,cls,content){const e=document.createElement(tag);if(cls)e.className=cls;if(content!==undefined)e.textContent=content;return e}
function drawStats(){
 const noted=[...notes.values()].filter(v=>v.status!=='none'||!!String(v.text||'').trim()).length;
 $('stats').replaceChildren(...[
  [DATA.sources.length,'검토 대상 원문'],[DATA.anchor_count,'재검증한 근거'],[DATA.verbatim_reference_mentions,'조문·날짜 원문 표기'],
  [noted,'검토 메모 작성']
 ].map(([n,l])=>{const e=node('div','stat');e.append(node('strong','',n.toLocaleString()),node('span','',l));return e}))
}
function filtered(){
 const term=$('search').value.trim().toLocaleLowerCase();
 return all.filter(s=>(!$('domain').value||s.domain_hint===$('domain').value)
 && (!$('reviewFilter').value||($('reviewFilter').value==='none'?!notes.has(s.source_id):
    ($('reviewFilter').value==='noted'?notes.has(s.source_id):
      notes.get(s.source_id)?.status==='revisit')))
 && (!term||[s.display_name,s.domain_hint,s.owner_route_hint,
      ...s.anchors.map(a=>a.excerpt)].join(' ').toLocaleLowerCase().includes(term)));
}
function drawList(){
 const xs=filtered();$('filtered').textContent=`${xs.length}개 자료 · 승인되지 않은 근거`;
 $('sourceList').replaceChildren();
 const f=document.createDocumentFragment();
 for(const s of xs){
   const b=node('button','source'+(s.source_id===selected?' selected':''));
   b.type='button';b.setAttribute('role','option');b.setAttribute('aria-selected',s.source_id===selected?'true':'false');
   b.append(node('div','name',s.display_name));
   const m=node('div','meta');m.append(node('span','chip',s.domain_hint),node('span','chip',s.full_anchor_count+'개 근거'));
   if(notes.has(s.source_id))m.append(node('span','chip tint','메모 있음'));
   b.append(m);b.onclick=()=>{selected=s.source_id;drawList();drawDetail();};f.append(b);
 }
 $('sourceList').append(f);if(!selected&&xs.length){selected=xs[0].source_id;drawList();drawDetail()}
}
function drawDetail(){
 const s=all.find(s=>s.source_id===selected);const target=$('detail');target.replaceChildren();
 if(!s){target.append(node('div','empty','왼쪽에서 원문을 선택하세요.'));return}
 target.append(node('div','eyebrow','VERIFIED RAW • NON-AUTHORITATIVE'));
 target.append(node('div','title',s.display_name));
 target.append(node('p','description',`${s.domain_hint} · ${s.media_kind} · 원본 근거 ${s.full_anchor_count}개 · 검토 제안 경로 ${s.owner_route_hint}`));
 const b=node('div','banner','원문 해시와 추출 근거만 검증했습니다. 독립 의미 검토·법규 유효성·FORMING 승인·학습 반영은 모두 미완료입니다. 이 화면의 메모는 승인 증거가 아닙니다.');
 target.append(b);
 const candidate=DATA.application_candidates?.[s.source_id];
 if(candidate){
  const sec=node('section','section');
  sec.append(node('h2','','방식·디자인·TAKY 적용 가설'));
  sec.append(node('p','footnote','원문 근거에 연결된 연구 후보입니다. 독립 검증·채택·실제 구현을 의미하지 않습니다.'));
  const methodGrid=node('div','method-grid');
  for(const [key,label] of [['observed_method','기사의 기술·업무 방식'],
    ['taky_gap','TAKY 기존 구현과 대조할 항목'],
    ['proposed_change','보완·개선 후보'],
    ['design_pattern','정보 전달·디자인 방식'],
    ['verification_test','구현 후 검증할 사항']]){
     const panel=node('div','anchor');
     panel.append(node('h2','',label),node('p','description',candidate[key]));
     methodGrid.append(panel);
  }
  sec.append(methodGrid);
  const evidenceHead=node('h2','','원문 직접 근거 / 별도 추론 구분');
  sec.append(evidenceHead);
  if(candidate.source_grounding?.length){
   for(const proof of candidate.source_grounding){
    const panel=node('div','anchor');
    panel.append(node('strong','',proof.field+' · 원문 '+proof.source_line_start+'–'+proof.source_line_end+'행'));
    panel.append(node('pre','',proof.exact_quote));
    panel.append(node('small','',proof.anchor_id+' · SHA '+proof.content_sha256.slice(0,16)+'…'));
    sec.append(panel);
   }
   sec.append(node('p','footnote','직접 인용은 해시 검증된 원문과 일치합니다. TAKY 차이·제안 변경·테스트는 별도의 검토 가설이며 승인된 사실이 아닙니다.'));
  }else{
   sec.append(node('p','footnote','원문 직접 인용 검증이 없는 구형 분석 가설입니다. 독립 의미 검토 전까지 적용할 수 없습니다.'));
  }
  target.append(sec);
 }
 const actions=node('div','detailbar');const link=node('a','link','원문 파일 열기 ↗');
 link.href=s.local_file_url;link.target='_blank';link.rel='noopener';actions.append(link);
 const copy=node('button','','원문 경로 복사');copy.onclick=()=>navigator.clipboard?.writeText(s.file_path);actions.append(copy);
 actions.append(node('span','chip','RAW '+s.raw_sha256.slice(0,16)+'…'));target.append(actions);
 const review=node('section','section');review.append(node('h2','','검토 메모 · 사용자 판단 자료 (미승인)'));
 const controls=node('div','review-row');const sel=node('select');
 for(const [k,label] of [['none','미검토'],['noted','메모 작성'],['revisit','추가 확인 필요']]){const opt=node('option','',label);opt.value=k;sel.append(opt)}
 sel.value=notes.get(s.source_id)?.status||'none';
 const area=node('textarea','','');area.placeholder='원문과 대조한 검토 메모를 기록하세요. 메모는 내보내야 저장됩니다.';
 area.value=notes.get(s.source_id)?.text||'';
 function update(){const v={status:sel.value,text:area.value.trim()};if(v.status==='none'&&!v.text)notes.delete(s.source_id);else notes.set(s.source_id,v);drawStats();drawList()}
 sel.onchange=update;area.oninput=update;controls.append(sel,area);review.append(controls);
 review.append(node('p','footnote','이 메모는 INDEXING_OWNER 또는 FORMING_APPROVAL_AUTHORITY의 독립 승인으로 사용할 수 없습니다.'));target.append(review);
 const signal=s.anchors.flatMap(a=>a.lexical_signals.map(x=>({...x,anchor:a})));
 if(signal.length){
  const sec=node('section','section');const top=node('div','sect-head');top.append(node('h2','','조문·날짜 원문 표기'));top.append(node('span','chip',signal.length+'개'));sec.append(top);
  for(const x of signal.slice(0,150)){const c=node('span','marker',x.verbatim+'  ·  '+x.anchor.kind+' '+x.anchor.id);sec.append(c)}
  sec.append(node('p','footnote','표기만 검색한 결과입니다. 현행 법령·법적 효력·사업 적용 여부는 검증되지 않았습니다.'));target.append(sec);
 }
 const section=node('section','section');const top=node('div','sect-head');
 top.append(node('h2','','전체 원문 근거'));
 const counter=node('span','chip',s.anchors.length+'개 · SHA 검증');top.append(counter);section.append(top);
 const chunks=s.anchors;
 for(const a of chunks){
   const card=node('div','anchor');const head=node('div','anchor-head');
   head.append(node('strong','',a.kind==='PDF_PAGE'?'PDF '+a.page+'쪽':a.kind==='HTML_SEGMENT'?'웹 본문 '+a.segment_no+'구간':`원문 ${a.from_line}–${a.to_line}행`));
   head.append(node('small','',a.content_sha256.slice(0,16)+'…'));card.append(head);
   card.append(node('pre','',a.excerpt||'(발췌 없음)'));
   if(a.characters>a.excerpt.length)card.append(node('p','footnote',`원문 ${a.characters}자 중 앞 ${a.excerpt.length}자 표시 · 전체는 원문 파일에서 확인`));
   section.append(card);
 }
 target.append(section);
}
function rerender(){selected=null;drawList();drawStats()}
for(const id of ['search','domain','reviewFilter'])$(id).addEventListener(id==='search'?'input':'change',rerender);
window.addEventListener('keydown',e=>{if(e.key==='/'&&document.activeElement.tagName!=='TEXTAREA'){e.preventDefault();$('search').focus()}});
$('exportNotes').onclick=()=>{
 const payload={schema:'TAKY_LOCAL_REVIEW_NOTES_V1',source_projection_sha256:DATA.projection_sha256,
  non_authoritative:true,independent_approval:false,records:[...notes].map(([source_id,review])=>({source_id,...review}))};
 const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'});
 const href=URL.createObjectURL(blob);const a=node('a');a.href=href;a.download='TAKY_REVIEW_NOTES_'+DATA.projection_sha256.slice(0,12)+'.json';a.click();URL.revokeObjectURL(href)
};
$('importNotes').onclick=()=>$('importInput').click();
$('importInput').onchange=async e=>{
 const file=e.target.files[0];if(!file)return;
 try{const input=JSON.parse(await file.text());if(input.schema!=='TAKY_LOCAL_REVIEW_NOTES_V1'||input.source_projection_sha256!==DATA.projection_sha256||input.independent_approval!==false)throw Error('파일 버전 또는 권한 상태가 맞지 않습니다');
 notes.clear();for(const x of input.records||[]){if(all.some(s=>s.source_id===x.source_id)&&['none','noted','revisit'].includes(x.status))notes.set(x.source_id,{status:x.status,text:String(x.text||'').slice(0,10000)})}
 drawStats();drawList();drawDetail()
 }catch(err){alert('메모 불러오기 거부: '+err.message)}
 e.target.value='';
};
drawStats();drawList();
</script></body></html>"""


def main():
    with sqlite3.connect(factory.DB.as_uri()+"?mode=ro",uri=True,timeout=8) as db:
        db.row_factory=sqlite3.Row
        data=json.loads(DATA.read_text(encoding="utf-8"))
        html=render(data,db)
    target=DATA.with_name(ui_name(data["manifest_sha256"],html))
    if target.exists():
        if target.read_text(encoding="utf-8")!=html:
            raise ValueError("IMMUTABLE_REVIEW_CONSOLE_CONFLICT")
        created=False
    else:
        with target.open("x",encoding="utf-8") as f:
            f.write(html)
        created=True
    print(json.dumps({"status":"OFFLINE_REVIEW_UI_READY",
      "path":str(target),"created":created,"bytes":target.stat().st_size,
      "original_document_count":len(data["projected_sources"]),
      "verified_anchor_count":data["verified_anchor_count"],
      "original_files_modified":False,"network_calls":0,
      "independent_approval_enabled":False},ensure_ascii=True))


if __name__=="__main__":
    main()
