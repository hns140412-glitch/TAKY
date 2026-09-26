'use strict';
/**
 * Explicit specialist observation mapping. Never infer authenticated scope
 * from child_id, localStorage, URL query, or an untrusted cross-frame event.
 * No rubric/reference issuer claims are made by this mapper.
 */
const VERSION='TAKY_SPECIALIST_OBSERVATION_PACKET_MAPPER_V1';
const TYPES=Object.freeze({
 'ready-set':'READY_LEARNING_OBSERVATION',
 'hide-seek':'LEARNING_MEMORY_SIGNAL',
 'snap-pop':'LEARNING_OUTCOME'
});
const clean=x=>typeof x==='string'?x.trim():'';
function map({source_app,event,session}={}){
 if(!Object.hasOwn(TYPES,source_app))throw Error('SPECIALIST_SOURCE_APP_REQUIRED');
 if(session?.authenticated!==true||!clean(session.family_id)||
  !clean(session.selected_member_id))throw Error('TRUSTED_SELECTED_MEMBER_SESSION_REQUIRED');
 if(!event||typeof event!=='object'||!clean(event.event_id)||
  !clean(event.occurred_at)||event.source_app!==source_app||
  event.type!==TYPES[source_app]||!event.payload||typeof event.payload!=='object')
  throw Error('SPECIALIST_OBSERVATION_EVENT_REQUIRED');
 const member=event.member_id||event.payload.member_id||event.payload.child_id;
 if(member!==session.selected_member_id)throw Error('SPECIALIST_EVENT_MEMBER_SCOPE_MISMATCH');
 if(event.family_id&&event.family_id!==session.family_id)
  throw Error('SPECIALIST_EVENT_FAMILY_SCOPE_MISMATCH');
 const subject=clean(event.payload.subject);
 const skill=clean(event.payload.concept_skill_target);
 if(!subject||!skill)throw Error('SPECIALIST_LEARNING_SCOPE_REQUIRED');
 if(!Number.isFinite(Date.parse(event.occurred_at)))throw Error('SPECIALIST_OBSERVED_AT_INVALID');
 if(event.payload.global_mastery_claim===true||
  event.payload.auto_award===true||event.payload.planner_date!=null)
  throw Error('SPECIALIST_AUTHORITY_ESCALATION_DENIED');
 const packet={
  packet_id:source_app+':'+event.event_id,
  source_app,
  context:{family_id:session.family_id,member_id:session.selected_member_id,
   subject,concept_skill_target:skill,
   learning_target_id:clean(event.payload.learning_target_id)||null},
  event:{event_id:event.event_id,source:source_app,type:event.type,
   occurred_at:event.occurred_at,payload:structuredClone(event.payload)},
  evidence_policy:{observation_only:true,reference_issuance_claim:false,
   reviewer_approval_claim:false,planner_schedule_authority:false,
   auto_award:false}
 };
 return structuredClone(packet);
}
module.exports=Object.freeze({VERSION,TYPES,map});
