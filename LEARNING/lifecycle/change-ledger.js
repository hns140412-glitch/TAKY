'use strict';

const crypto=require('node:crypto');
const clean=v=>String(v??'').trim();
const VERSION='TAKY_LEARNING_CHANGE_LEDGER_V1';
const TYPES=new Set(['ESTIMATOR','POLICY','LEARNER_STATE','EVIDENCE_SCHEMA','PEDAGOGY_RULE','ADAPTER_CONTRACT','VALIDATION_RULE','OTHER']);
const STATES=new Set(['PROPOSED','HOLD','DEFERRED','REJECTED','APPLIED','SUPERSEDED']);

function digest(v){return crypto.createHash('sha256').update(JSON.stringify(v)).digest('hex')}
function emptyLedger(){return {ledger_version:VERSION,retention:'IMMUTABLE_HISTORY',entries:[]}}
function appendChange(ledgerInput={},input={}){
  const ledger=JSON.parse(JSON.stringify(ledgerInput?.ledger_version?ledgerInput:emptyLedger()));
  const type=clean(input.type);
  const state=clean(input.state||'PROPOSED');
  const issues=[];
  if(!TYPES.has(type))issues.push('TYPE_INVALID');
  if(!STATES.has(state))issues.push('STATE_INVALID');
  if(!clean(input.title))issues.push('TITLE_REQUIRED');
  if(!clean(input.source_ref))issues.push('SOURCE_REF_REQUIRED');
  if(!clean(input.owner))issues.push('OWNER_REQUIRED');
  if(issues.length)return {ok:false,reason:'INVALID_CHANGE_ENTRY',issues};

  const parent=ledger.entries.at(-1)||null;
  const payload={
    entry_type:'LEARNING_ENGINE_CHANGE',
    type,
    title:clean(input.title),
    description:clean(input.description)||null,
    state,
    owner:clean(input.owner),
    source_ref:clean(input.source_ref),
    evidence_refs:Array.isArray(input.evidence_refs)?input.evidence_refs.map(clean).filter(Boolean):[],
    blockers:Array.isArray(input.blockers)?input.blockers.map(clean).filter(Boolean):[],
    destination:clean(input.destination)||null,
    created_at:clean(input.created_at)||new Date(0).toISOString(),
    parent_entry_id:parent?.entry_id||null,
    retention:'IMMUTABLE_HISTORY',
    reconsider_on:state==='APPLIED'?[]:['NEW_EVIDENCE','POLICY_CHANGE','MANUAL_REVIEW','DEPENDENCY_CLOSED']
  };
  payload.entry_id='change:'+digest(payload).slice(0,24);
  if(ledger.entries.some(e=>e.entry_id===payload.entry_id)){
    return {ok:true,ledger,entry:ledger.entries.find(e=>e.entry_id===payload.entry_id),deduplicated:true};
  }
  ledger.entries.push(payload);
  return {ok:true,ledger,entry:payload,deduplicated:false};
}
function transition(ledgerInput={},entryId='',nextState='',input={}){
  const ledger=JSON.parse(JSON.stringify(ledgerInput?.ledger_version?ledgerInput:emptyLedger()));
  const source=ledger.entries.find(e=>e.entry_id===clean(entryId));
  if(!source)return {ok:false,reason:'SOURCE_ENTRY_NOT_FOUND'};
  if(!STATES.has(clean(nextState)))return {ok:false,reason:'STATE_INVALID'};
  return appendChange(ledger,{
    type:source.type,
    title:source.title,
    description:source.description,
    state:clean(nextState),
    owner:source.owner,
    source_ref:source.entry_id,
    evidence_refs:[...(source.evidence_refs||[]),...(input.evidence_refs||[])],
    blockers:input.blockers||[],
    destination:input.destination||source.destination,
    created_at:input.created_at
  });
}
function currentProjection(ledger={}){
  const latest=new Map();
  for(const e of ledger.entries||[]){
    const key=[e.type,e.title,e.owner].join('::');
    latest.set(key,e);
  }
  return [...latest.values()].map(e=>({
    entry_id:e.entry_id,type:e.type,title:e.title,state:e.state,owner:e.owner,destination:e.destination,
    blockers:Array.isArray(e.blockers)?[...e.blockers]:[],
    evidence_refs:Array.isArray(e.evidence_refs)?[...e.evidence_refs]:[],
    reconsider_on:Array.isArray(e.reconsider_on)?[...e.reconsider_on]:[],
    retained_history_count:(ledger.entries||[]).filter(x=>x.type===e.type&&x.title===e.title&&x.owner===e.owner).length,
    needs_reconsideration:e.state!=='APPLIED'&&e.state!=='SUPERSEDED'
  }));
}
function pending(ledger={}){
  return currentProjection(ledger).filter(x=>x.needs_reconsideration);
}
function validateLedger(ledger={}){
  const issues=[];
  if(ledger.ledger_version!==VERSION)issues.push('VERSION_INVALID');
  if(ledger.retention!=='IMMUTABLE_HISTORY')issues.push('RETENTION_INVALID');
  let prev=null;
  const ids=new Set();
  for(const e of ledger.entries||[]){
    if(ids.has(e.entry_id))issues.push('DUPLICATE_ENTRY_ID');
    ids.add(e.entry_id);
    if(e.parent_entry_id!==(prev?.entry_id||null))issues.push('PARENT_CHAIN_MISMATCH:'+e.entry_id);
    if(e.retention!=='IMMUTABLE_HISTORY')issues.push('ENTRY_RETENTION_INVALID:'+e.entry_id);
    prev=e;
  }
  return {ok:issues.length===0,issues};
}
module.exports=Object.freeze({VERSION,TYPES,STATES,emptyLedger,appendChange,transition,currentProjection,pending,validateLedger});
