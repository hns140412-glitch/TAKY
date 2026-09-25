'use strict';

const Ledger=require('../lifecycle/growth-strategy-ledger.js');

const VERSION='TAKY_DURABLE_GROWTH_STRATEGY_STORE_ADAPTER_V1';
const clean=v=>String(v??'').trim();

function stateKey(packet={}){
  const family=clean(packet.family_id||packet?.context?.family_id);
  const member=clean(packet.member_id||packet?.context?.member_id||packet?.real_evidence_receipt?.scope?.member_id);
  if(!family||!member)return null;
  return 'families/'+encodeURIComponent(family)+'/members/'+encodeURIComponent(member)+'/learning-engine/growth-strategy-v1';
}

async function readState(store,key){
  const entry=await store.getWithMetadata(key,{type:'json',consistency:'strong'});
  if(!entry||entry.data==null)return {exists:false,state:Ledger.emptyLedger(),etag:null};
  return {exists:true,state:entry.data,etag:entry.etag||null};
}

async function writeState(store,key,state,{etag,exists}={}){
  const opts=exists?{onlyIfMatch:etag}:{onlyIfNew:true};
  return store.setJSON(key,state,opts);
}

async function appendFeedback(store,packet={},options={}){
  const key=stateKey(packet);
  if(!key)return {ok:false,reason:'FAMILY_MEMBER_SCOPE_REQUIRED'};
  const maxAttempts=Math.max(1,Number(options.max_attempts)||4);

  for(let attempt=1;attempt<=maxAttempts;attempt++){
    const current=await readState(store,key);
    const appended=Ledger.append(current.state,{
      real_evidence_receipt:packet.real_evidence_receipt,
      outcome_feedback:packet.outcome_feedback,
      prior_gap_id:packet.prior_gap_id,
      index_gap_decision:packet.index_gap_decision,
      recorded_at:packet.recorded_at
    });
    if(!appended.ok)return appended;

    if(appended.idempotent){
      return {
        ...appended,
        durable_store:{
          adapter_version:VERSION,
          key,
          consistency:'strong',
          conditional_write:'none-idempotent',
          attempt,
          etag:current.etag
        }
      };
    }

    const write=await writeState(store,key,appended.ledger,{etag:current.etag,exists:current.exists});
    if(write?.modified!==false){
      return {
        ...appended,
        durable_store:{
          adapter_version:VERSION,
          key,
          consistency:'strong',
          conditional_write:current.exists?'onlyIfMatch':'onlyIfNew',
          attempt,
          etag:write?.etag||null
        }
      };
    }
  }

  return {
    ok:false,
    reason:'DURABLE_GROWTH_STORE_CONFLICT_RETRY_EXHAUSTED',
    key,
    retryable:true
  };
}

async function evaluateScope(store,packet={},options={}){
  const key=stateKey(packet);
  if(!key)return {ok:false,reason:'FAMILY_MEMBER_SCOPE_REQUIRED'};
  const current=await readState(store,key);
  const scope=packet.scope||packet?.real_evidence_receipt?.scope||{};
  return {
    ok:true,
    durable_store:{adapter_version:VERSION,key,consistency:'strong',etag:current.etag},
    evaluation:Ledger.evaluate(current.state,scope,options)
  };
}

function selfValidate(result={}){
  const issues=[];
  if(!result.ok)issues.push('RESULT_NOT_OK');
  if(result.ok&&result.durable_store?.adapter_version!==VERSION)issues.push('ADAPTER_VERSION_INVALID');
  if(result.ok&&result.durable_store?.consistency!=='strong')issues.push('STRONG_CONSISTENCY_REQUIRED');
  if(result.entry?.promotion_authority!==false)issues.push('PROMOTION_AUTHORITY_FORBIDDEN');
  if(result.entry?.raw_evidence_copied!==false)issues.push('RAW_EVIDENCE_COPY_FORBIDDEN');
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,stateKey,readState,writeState,appendFeedback,evaluateScope,selfValidate});
