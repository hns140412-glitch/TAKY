'use strict';

const crypto=require('node:crypto');
const GrowLineage=require('../lifecycle/grow-lineage-packet.js');

const VERSION='TAKY_GROW_REVIEW_QUEUE_ADAPTER_V1';
const KEY='taky/grow/review-queue-v1';
const digest=v=>crypto.createHash('sha256').update(String(v)).digest('hex');

function emptyQueue(){
  return {
    version:'TAKY_GROW_REVIEW_QUEUE_V1',
    authority:'GROW_REVIEW_QUEUE_CANDIDATE_ONLY',
    promotion_authorized:false,
    authority_transfer:false,
    candidate_ids:[],
    candidates:[]
  };
}

async function readQueue(store){
  const entry=await store.getWithMetadata(KEY,{type:'json',consistency:'strong'});
  if(!entry||entry.data==null)return {exists:false,state:emptyQueue(),etag:null};
  return {exists:true,state:entry.data,etag:entry.etag||null};
}

async function writeQueue(store,state,{etag,exists}={}){
  const opts=exists?{onlyIfMatch:etag}:{onlyIfNew:true};
  return store.setJSON(KEY,state,opts);
}

function sanitizeCandidate(candidate={}){
  const event=candidate.grow_lineage_event||candidate.event||candidate;
  const checked=GrowLineage.validateEvent(event);
  if(!checked.ok)return {ok:false,reason:'LINEAGE_EVENT_INVALID',issues:checked.issues};
  if(event.grow_domain!=='LEARNING_GROW')return {ok:false,reason:'GROW_DOMAIN_INVALID'};
  if(event.stage!=='GROWTH')return {ok:false,reason:'GROWTH_STAGE_REQUIRED'};
  if(event.payload?.scope_kind!=='SYSTEM_AGGREGATE')return {ok:false,reason:'SYSTEM_AGGREGATE_REQUIRED'};
  const raw=JSON.stringify(event);
  if(/"member_id"|"member_ref"/.test(raw))return {ok:false,reason:'MEMBER_IDENTIFIER_FORBIDDEN'};
  return {
    ok:true,
    candidate:{
      candidate_id:'GRQ-'+digest(event.event_id).slice(0,20),
      grow_domain:event.grow_domain,
      event_id:event.event_id,
      source_ref:event.source_ref,
      authority:event.authority,
      promotion_authorized:false,
      authority_transfer:false,
      payload:event.payload,
      parent_refs:event.parent_refs,
      producer:event.producer,
      recorded_at:event.recorded_at
    }
  };
}

async function enqueue(store,candidates=[],options={}){
  const sanitized=[];
  for(const c of candidates||[]){
    const s=sanitizeCandidate(c);
    if(!s.ok)return s;
    sanitized.push(s.candidate);
  }
  const maxAttempts=Math.max(1,Number(options.max_attempts)||4);
  for(let attempt=1;attempt<=maxAttempts;attempt++){
    const current=await readQueue(store);
    const known=new Set(current.state.candidate_ids||[]);
    const next=JSON.parse(JSON.stringify(current.state));
    let changed=false;
    for(const c of sanitized){
      if(known.has(c.candidate_id))continue;
      next.candidates.push(c);
      known.add(c.candidate_id);
      changed=true;
    }
    next.candidate_ids=[...known].sort();
    if(!changed){
      return {
        ok:true,idempotent:true,state:current.state,
        durable_store:{adapter_version:VERSION,key:KEY,consistency:'strong',conditional_write:'none-idempotent',attempt,etag:current.etag}
      };
    }
    const write=await writeQueue(store,next,{etag:current.etag,exists:current.exists});
    if(write?.modified!==false){
      return {
        ok:true,idempotent:false,state:next,
        durable_store:{adapter_version:VERSION,key:KEY,consistency:'strong',conditional_write:current.exists?'onlyIfMatch':'onlyIfNew',attempt,etag:write?.etag||null}
      };
    }
  }
  return {ok:false,reason:'GROW_REVIEW_QUEUE_CONFLICT_RETRY_EXHAUSTED',retryable:true};
}

function selfValidate(result={}){
  const issues=[];
  if(!result.ok)issues.push('RESULT_NOT_OK');
  const state=result.state||{};
  if(state.promotion_authorized!==false)issues.push('AUTO_PROMOTION_FORBIDDEN');
  if(state.authority_transfer!==false)issues.push('AUTHORITY_TRANSFER_FORBIDDEN');
  const raw=JSON.stringify(state);
  if(/"member_id"|"member_ref"/.test(raw))issues.push('MEMBER_IDENTIFIER_PERSISTED');
  for(const [i,c] of (state.candidates||[]).entries()){
    if(c.promotion_authorized!==false)issues.push('CANDIDATE_AUTO_PROMOTION_FORBIDDEN:'+i);
    if(c.authority_transfer!==false)issues.push('CANDIDATE_AUTHORITY_TRANSFER_FORBIDDEN:'+i);
    if(c.payload?.scope_kind!=='SYSTEM_AGGREGATE')issues.push('SYSTEM_AGGREGATE_SCOPE_REQUIRED:'+i);
  }
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,KEY,emptyQueue,readQueue,writeQueue,sanitizeCandidate,enqueue,selfValidate});
