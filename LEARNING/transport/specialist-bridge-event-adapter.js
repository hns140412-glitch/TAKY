'use strict';
/** Adapter for existing specialist EventEnvelope outputs, not a trust source. */
const VERSION='TAKY_SPECIALIST_BRIDGE_EVENT_ADAPTER_V1';
const TYPE={'hide-seek':'LEARNING_MEMORY_SIGNAL','snap-pop':'LEARNING_OUTCOME'};
const clean=x=>typeof x==='string'?x.trim():'';
function fromBridge(source_app,raw){
 if(!Object.hasOwn(TYPE,source_app)||!raw||raw.source!==source_app||
  raw.type!==TYPE[source_app]||raw.event_type!==TYPE[source_app]||
  !clean(raw.event_id)||!clean(raw.occurred_at)||!raw.payload||
  typeof raw.payload!=='object'||!clean(raw.payload.member_id))
  throw Error('EXACT_SPECIALIST_BRIDGE_EVENT_REQUIRED');
 if(raw.child_id&&raw.child_id!==raw.payload.member_id)
  throw Error('BRIDGE_CHILD_PAYLOAD_SCOPE_CONFLICT');
 return {
  source_app,type:TYPE[source_app],event_id:raw.event_id,
  occurred_at:raw.occurred_at,member_id:raw.payload.member_id,
  payload:structuredClone(raw.payload)
 };
}
function readyObservation({event_id,occurred_at,member_id,payload}={}){
 if(!clean(event_id)||!clean(occurred_at)||!clean(member_id)||
  !payload||typeof payload!=='object'||payload.member_id!==member_id||
  payload.observation_only!==true)
  throw Error('READY_EXPLICIT_OBSERVATION_REQUIRED');
 return {source_app:'ready-set',type:'READY_LEARNING_OBSERVATION',
  event_id,occurred_at,member_id,payload:structuredClone(payload)};
}
module.exports=Object.freeze({VERSION,fromBridge,readyObservation});
