'use strict';

const Agg=require('../lifecycle/learning-system-growth-aggregate.js');
const ReviewQueue=require('./grow-review-queue-adapter.js');
const crypto=require('node:crypto');

const VERSION='TAKY_DURABLE_LEARNING_SYSTEM_GROWTH_STORE_ADAPTER_V1';
const clean=v=>String(v??'').trim();
const digest=v=>crypto.createHash('sha256').update(String(v)).digest('hex');

function stateKey(packet={}){
  const family=clean(packet.family_id||packet?.context?.family_id);
  if(!family)return null;
  return 'families/'+encodeURIComponent(family)+'/learning-engine/system-growth-v1';
}

function emptyState(){
  return {
    version:'TAKY_LEARNING_SYSTEM_GROWTH_LEDGER_V1',
    authority:'LEARNING_SYSTEM_GROWTH_CANDIDATE_ONLY',
    promotion_authorized:false,
    candidates:[],
    event_ids:[]
  };
}

async function readState(store,key){
  const entry=await store.getWithMetadata(key,{type:'json',consistency:'strong'});
  if(!entry||entry.data==null)return {exists:false,state:emptyState(),etag:null};
  return {exists:true,state:entry.data,etag:entry.etag||null};
}

async function writeState(store,key,state,{etag,exists}={}){
  const opts=exists?{onlyIfMatch:etag}:{onlyIfNew:true};
  return store.setJSON(key,state,opts);
}

async function enqueueReviewBestEffort(store,aggregate){
  try{
    const result=await ReviewQueue.enqueue(store,aggregate.candidates||[]);
    return {attempted:true,ok:result.ok===true,result};
  }catch(e){
    return {attempted:true,ok:false,non_blocking:true,error_type:e?.name||'Error'};
  }
}

function mergeAggregate(state,aggregate){
  const next=JSON.parse(JSON.stringify(state||emptyState()));
  const known=new Set(next.event_ids||[]);
  let changed=false;
  for(const c of aggregate.candidates||[]){
    const event=c.grow_lineage_event;
    if(!event?.event_id||known.has(event.event_id))continue;
    next.candidates.push({
      candidate_id:'LSG-'+digest(event.event_id).slice(0,20),
      grow_lineage_event:event,
      member_count:c.member_count,
      verified_outcome_count:c.verified_outcome_count,
      suggested_review:c.suggested_review,
      promotion_authorized:false
    });
    known.add(event.event_id);
    changed=true;
  }
  next.event_ids=[...known].sort();
  return {state:next,changed};
}

async function appendAggregate(store,packet={},options={}){
  const key=stateKey(packet);
  if(!key)return {ok:false,reason:'FAMILY_SCOPE_REQUIRED'};
  const aggregate=Agg.aggregate(packet.rows||[],options);
  const checked=Agg.validate(aggregate);
  if(!checked.ok)return {ok:false,reason:'AGGREGATE_INVALID',issues:checked.issues};

  const maxAttempts=Math.max(1,Number(options.max_attempts)||4);
  for(let attempt=1;attempt<=maxAttempts;attempt++){
    const current=await readState(store,key);
    const merged=mergeAggregate(current.state,aggregate);
    if(!merged.changed){
      const review_queue=await enqueueReviewBestEffort(store,aggregate);
      return {
        ok:true,idempotent:true,aggregate,review_queue,
        durable_store:{adapter_version:VERSION,key,consistency:'strong',conditional_write:'none-idempotent',attempt,etag:current.etag}
      };
    }
    const write=await writeState(store,key,merged.state,{etag:current.etag,exists:current.exists});
    if(write?.modified!==false){
      const review_queue=await enqueueReviewBestEffort(store,aggregate);
      return {
        ok:true,idempotent:false,aggregate,state:merged.state,review_queue,
        durable_store:{adapter_version:VERSION,key,consistency:'strong',conditional_write:current.exists?'onlyIfMatch':'onlyIfNew',attempt,etag:write?.etag||null}
      };
    }
  }
  return {ok:false,reason:'DURABLE_SYSTEM_GROWTH_STORE_CONFLICT_RETRY_EXHAUSTED',key,retryable:true};
}

function selfValidate(result={}){
  const issues=[];
  if(!result.ok)issues.push('RESULT_NOT_OK');
  if(result.ok&&result.durable_store?.adapter_version!==VERSION)issues.push('ADAPTER_VERSION_INVALID');
  if(result.ok&&result.durable_store?.consistency!=='strong')issues.push('STRONG_CONSISTENCY_REQUIRED');
  if(result.ok&&result.review_queue?.attempted!==true)issues.push('GROW_REVIEW_QUEUE_NOT_ATTEMPTED');
  const serialized=JSON.stringify(result.state||{});
  if(/"member_id"|"member_ref"/.test(serialized))issues.push('MEMBER_IDENTIFIER_PERSISTED');
  for(const [i,c] of (result.state?.candidates||[]).entries()){
    if(c.promotion_authorized!==false)issues.push('AUTO_PROMOTION_FORBIDDEN:'+i);
    if(c.grow_lineage_event?.payload?.scope_kind!=='SYSTEM_AGGREGATE')issues.push('AGGREGATE_SCOPE_REQUIRED:'+i);
  }
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,stateKey,emptyState,readState,writeState,mergeAggregate,appendAggregate,selfValidate});
