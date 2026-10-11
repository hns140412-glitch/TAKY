'use strict';

const crypto=require('node:crypto');
const VALID_DOMAINS=new Set(['ARCHI_GROW','LEARNING_GROW','UNROUTED']);
const VALID_STAGES=new Set(['RAW','INDEX','LEARNING','RELATION','EXECUTION','OUTCOME','GROWTH']);
const clean=v=>String(v??'').trim();

function stable(value){
  if(Array.isArray(value))return value.map(stable);
  if(value&&typeof value==='object'){
    const out={};
    for(const k of Object.keys(value).sort())out[k]=stable(value[k]);
    return out;
  }
  return value;
}
function stableId(payload){
  const raw=JSON.stringify(stable(payload));
  return 'GLE-'+crypto.createHash('sha256').update(raw).digest('hex').slice(0,24);
}
function makeEvent({grow_domain='UNROUTED',stage,producer,source_ref,parent_refs=[],authority='EVIDENCE_ONLY',payload={},recorded_at=null}={}){
  const domain=clean(grow_domain).toUpperCase()||'UNROUTED';
  const st=clean(stage).toUpperCase();
  if(!VALID_DOMAINS.has(domain))throw new Error('GROW_DOMAIN_INVALID');
  if(!VALID_STAGES.has(st))throw new Error('GROW_STAGE_INVALID');
  const parents=[...new Set((parent_refs||[]).map(clean).filter(Boolean))].sort();
  if(['LEARNING','RELATION','EXECUTION','OUTCOME','GROWTH'].includes(st)&&parents.length===0)throw new Error('GROW_PARENT_REQUIRED');
  const identity={grow_domain:domain,stage:st,producer:clean(producer),source_ref:clean(source_ref),parent_refs:parents,payload:payload||{}};
  return {
    schema:'GROW_LINEAGE_EVENT_V1',
    event_id:stableId(identity),
    grow_domain:domain,
    stage:st,
    producer:clean(producer),
    source_ref:clean(source_ref),
    parent_refs:parents,
    authority:clean(authority)||'EVIDENCE_ONLY',
    promotion_authorized:false,
    authority_transfer:false,
    recorded_at:recorded_at||new Date().toISOString(),
    payload:payload||{}
  };
}
function validateEvent(event={}){
  const issues=[];
  for(const k of ['event_id','grow_domain','stage','producer','source_ref','authority']){
    if(!clean(event[k]))issues.push('GROW_EVENT_MISSING:'+k);
  }
  if(!VALID_DOMAINS.has(event.grow_domain))issues.push('GROW_EVENT_DOMAIN_INVALID');
  if(!VALID_STAGES.has(event.stage))issues.push('GROW_EVENT_STAGE_INVALID');
  if(event.promotion_authorized!==false)issues.push('GROW_EVENT_PROMOTION_FORBIDDEN');
  if(event.authority_transfer!==false)issues.push('GROW_EVENT_AUTHORITY_TRANSFER_FORBIDDEN');
  if(['LEARNING','RELATION','EXECUTION','OUTCOME','GROWTH'].includes(event.stage)&&!(event.parent_refs||[]).length)issues.push('GROW_EVENT_PARENT_REQUIRED');
  return {ok:issues.length===0,issues};
}
module.exports=Object.freeze({makeEvent,validateEvent});