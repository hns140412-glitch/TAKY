(() => {
'use strict';

if (window.TakyLearningEvidenceClientV1) return;

const VERSION='2026.10.04-learning-evidence-client-v1';
const QUEUE_KEY='taky_learning_evidence_pending_v1';
const ACK_KEY='taky_learning_evidence_acked_v1';
const MAX_PENDING=120;
const MAX_ACKED=500;
const MAX_FLUSH=20;
const ACK_KINDS=new Set(['REAL_EVIDENCE_RECEIPT','OBSERVATION_INGEST_RECEIPT']);
const ELIGIBLE=Object.freeze({
  'ready-set':new Set(['TASK_STATE_CHANGED','LAP_ENDED','SESSION_ENDED','PRACTICE_RESPONSE_RESULT']),
  'hide-seek':new Set(['RETRIEVAL_ATTEMPT_RESULT','TASK_COMPLETED','TASK_PARTIAL','TASK_BLOCKED','HELP_NEEDED']),
  'snap-pop':new Set(['TASK_COMPLETED','TASK_PARTIAL','TASK_BLOCKED','HELP_NEEDED'])
});
const clean=v=>typeof v==='string'?v.trim():'';
const object=v=>!!v&&typeof v==='object'&&!Array.isArray(v);
const clone=v=>JSON.parse(JSON.stringify(v));

function readQueue(){
  try{
    const x=JSON.parse(localStorage.getItem(QUEUE_KEY)||'[]');
    return Array.isArray(x)?x:[];
  }catch{return []}
}
function writeQueue(rows){
  const safe=Array.isArray(rows)?rows:[];
  localStorage.setItem(QUEUE_KEY,JSON.stringify(safe));
  return safe;
}
function readAcked(){
  try{const x=JSON.parse(localStorage.getItem(ACK_KEY)||'[]');return Array.isArray(x)?x:[]}catch{return []}
}
function markAck(key){
  const a=readAcked().filter(x=>x!==key);
  a.push(key);
  localStorage.setItem(ACK_KEY,JSON.stringify(a.slice(-MAX_ACKED)));
}
function keyOf(app,eventId){return clean(app)+':'+clean(eventId)}
function isAcked(key){return readAcked().includes(key)}
function stripProofFields(value){
  if(Array.isArray(value))return value.map(stripProofFields);
  if(!object(value))return value;
  const out={};
  for(const [k,v] of Object.entries(value)){
    if(['verified_outcome','verification','verification_input','verification_receipt','verification_candidate','promotion_authorized','promotion_authority','authority_transfer'].includes(k))continue;
    out[k]=stripProofFields(v);
  }
  return out;
}
function bridgeContext(app){
  try{
    if(app==='hide-seek'&&window.HideSeekBridge?.context)return window.HideSeekBridge.context()||{};
    if(app==='snap-pop'&&window.SnapPopBridge?.context)return window.SnapPopBridge.context()||{};
  }catch{}
  return {};
}
function urlScope(){
  try{
    const p=new URLSearchParams(location.search);
    return {
      member_id:clean(p.get('child_id')),
      subject:clean(p.get('subject')),
      concept_skill_target:clean(p.get('concept_skill_target')),
      learning_target_id:clean(p.get('learning_target_id'))
    };
  }catch{return {}}
}
function scopeHint(event={},options={}){
  const app=clean(event.app||event.source);
  const p=event.payload||{};
  const ls=object(p.learning_scope)?p.learning_scope:{};
  const allowAmbientScope=options.allowAmbientScope===true;
  const u=allowAmbientScope?urlScope():{},b=allowAmbientScope?bridgeContext(app):{};
  return {
    member_id:clean(event.child_id||ls.member_id||p.member_id||b.child_id||u.member_id),
    subject:clean(ls.subject||p.subject||u.subject),
    concept_skill_target:clean(ls.concept_skill_target||p.concept_skill_target||u.concept_skill_target),
    learning_target_id:clean(ls.learning_target_id||p.learning_target_id||p.lexical_id||p.word_id||p.item_id||u.learning_target_id)
  };
}
function eligible(event={}){
  const app=clean(event.app||event.source);
  const type=clean(event.type||event.event_type);
  return !!event.event_id&&!!ELIGIBLE[app]?.has(type);
}
function enqueue(event={},options={}){
  if(!eligible(event))return {ok:false,reason:'EVENT_NOT_EVIDENCE_ELIGIBLE'};
  const app=clean(event.app||event.source),eventId=clean(event.event_id),k=keyOf(app,eventId);
  const q=readQueue();
  if(isAcked(k))return {ok:true,acked:true,duplicate:true,pending:q.length};
  if(q.some(x=>x.key===k))return {ok:true,duplicate:true,pending:q.length};
  if(q.length>=MAX_PENDING)return {ok:false,reason:'PENDING_QUEUE_FULL',pending:q.length};
  const row={
    key:k,app,event_id:eventId,enqueued_at:new Date().toISOString(),
    scope_hint:scopeHint(event,options),
    event:stripProofFields(clone(event))
  };
  const next=writeQueue([...q,row]);
  return {ok:true,duplicate:false,pending:next.length};
}
function eventToCentral(row){
  const e=row.event||{},payload=stripProofFields(clone(e.payload||{}));
  return {
    source:row.app,
    event_id:row.event_id,
    occurred_at:clean(e.at||e.occurred_at),
    event_type:clean(e.type||e.event_type),
    payload
  };
}
async function buildPacket(row,runtime){
  const hint=row.scope_hint||{};
  const familyId=clean(await runtime.getFamilyId());
  if(!familyId)return {ok:false,reason:'FAMILY_SCOPE_REQUIRED'};
  if(!clean(hint.member_id))return {ok:false,reason:'MEMBER_SCOPE_REQUIRED'};
  if(!clean(hint.subject))return {ok:false,reason:'SUBJECT_SCOPE_REQUIRED'};
  if(!clean(hint.concept_skill_target))return {ok:false,reason:'CONCEPT_SKILL_SCOPE_REQUIRED'};
  const event=eventToCentral(row);
  if(!event.occurred_at||!event.event_type)return {ok:false,reason:'EVENT_TIME_TYPE_REQUIRED'};
  const context={
    family_id:familyId,
    member_id:clean(hint.member_id),
    subject:clean(hint.subject),
    concept_skill_target:clean(hint.concept_skill_target)
  };
  if(clean(hint.learning_target_id))context.learning_target_id=clean(hint.learning_target_id);
  return {ok:true,packet:{
    packet_id:keyOf(row.app,row.event_id),
    source_app:row.app,
    context,event
  }};
}
function runtime(){
  const r=window.TAKY_FAMILY_RUNTIME;
  if(!r||typeof r.getToken!=='function'||typeof r.getFamilyId!=='function'||!clean(r.apiBaseUrl))return null;
  return r;
}
let flushing=false,flushRequested=false;
async function flush(){
  if(flushing){flushRequested=true;return {ok:false,reason:'FLUSH_IN_PROGRESS'};}
  const r=runtime();
  if(!r)return {ok:false,reason:'TAKY_FAMILY_RUNTIME_REQUIRED'};
  flushing=true;
  const stats={sent:0,acked:0,pending_scope:0,failed:0};
  try{
    let q=readQueue();
    const snapshot=[...q];
    let attempted=0;
    for(const row of snapshot){
      const built=await buildPacket(row,r);
      if(!built.ok){stats.pending_scope++;continue;}
      let token;
      try{token=clean(await r.getToken())}catch{stats.failed++;continue;}
      if(token.length<16){stats.failed++;continue;}
      if(attempted>=MAX_FLUSH)break;
      attempted++;
      let res,body;
      try{
        const fetchImpl=r.fetchImpl||window.fetch?.bind(window);
        if(typeof fetchImpl!=='function'){stats.failed++;continue;}
        const endpoint=new URL('/api/learning/evidence',r.apiBaseUrl).href;
        stats.sent++;
        res=await fetchImpl(endpoint,{
          method:'POST',
          headers:{'content-type':'application/json','authorization':'Bearer '+token},
          body:JSON.stringify(built.packet),
          cache:'no-store',
          credentials:'omit'
        });
        body=await res.json().catch(()=>null);
      }catch{stats.failed++;continue;}
      if(!res?.ok||body?.ok!==true||!ACK_KINDS.has(body.acknowledgement_kind)||
         body.packet_id!==built.packet.packet_id||body.event_id!==row.event_id||
         body.storage_confirmed!==true){
        stats.failed++;continue;
      }
      markAck(row.key);
      // Remove only the acknowledged row from the latest queue. New events may
      // have been enqueued while this flush was awaiting the network response.
      q=readQueue().filter(x=>x.key!==row.key);
      writeQueue(q);
      stats.acked++;
    }
    return {ok:true,...stats,pending:readQueue().length};
  }finally{
    flushing=false;
    if(flushRequested){flushRequested=false;Promise.resolve().then(()=>flush());}
  }
}
function sourceEvents(){
  const rows=[];
  try{
    if(typeof state!=='undefined'&&Array.isArray(state?.activeSession?.rev07?.events))rows.push(...state.activeSession.rev07.events);
  }catch{}
  try{
    if(typeof S!=='undefined'&&Array.isArray(S?.takyLearningOutbox))rows.push(...S.takyLearningOutbox);
  }catch{}
  try{
    const snap=JSON.parse(sessionStorage.getItem('snap_pop_shared_outbox_v1')||'[]');
    if(Array.isArray(snap))rows.push(...snap);
  }catch{}
  return rows;
}
function scan(options={}){
  let added=0,full=0;
  for(const e of sourceEvents()){
    const r=enqueue(e,options);
    if(r.ok&&!r.duplicate)added++;
    if(r.reason==='PENDING_QUEUE_FULL')full++;
  }
  return {ok:full===0,added,queue_full:full,pending:readQueue().length};
}
function currentSnapEvents(){
  try{const x=JSON.parse(sessionStorage.getItem('snap_pop_shared_outbox_v1')||'[]');return Array.isArray(x)?x:[]}catch{return []}
}
function scanLiveSnapDelta(beforeKeys){
  let added=0;
  for(const e of currentSnapEvents()){
    const k=keyOf(clean(e.app||e.source),clean(e.event_id));
    if(beforeKeys.has(k))continue;
    const r=enqueue(e,{allowAmbientScope:true});
    if(r.ok&&!r.duplicate)added++;
  }
  return added;
}
function kick(){
  scan({allowAmbientScope:false});
  void flush();
}
window.addEventListener('taky-learning-event',event=>{
  if(event?.detail)enqueue(event.detail,{allowAmbientScope:true});
  void flush();
});
window.addEventListener('taky-central-auth-ready',()=>kick());
window.addEventListener('online',()=>kick());
window.addEventListener('focus',()=>kick());
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')kick()});
document.addEventListener('click',event=>{
  if(!event.target?.closest?.('#nextBtn'))return;
  const before=new Set(currentSnapEvents().map(e=>keyOf(clean(e.app||e.source),clean(e.event_id))));
  setTimeout(()=>{scanLiveSnapDelta(before);void flush()},250);
},true);
setTimeout(kick,120);

window.TakyLearningEvidenceClientV1=Object.freeze({
  version:VERSION,enqueue,flush,scan,pending:()=>clone(readQueue()),acked:()=>clone(readAcked()),
  buildPacket,stripProofFields,scopeHint
});
})();
