'use strict';
const assert=require('node:assert/strict');
const Mapper=require('./specialist-observation-packet-mapper.js');
const session={authenticated:true,family_id:'F',selected_member_id:'A'};
for(const [app,type] of Object.entries(Mapper.TYPES)){
 const event={event_id:app+'-e1',source_app:app,type,occurred_at:'2026-09-27T10:00:00Z',
  member_id:'A',payload:{member_id:'A',subject:'english',concept_skill_target:'vocabulary',observation_only:true,global_mastery_claim:false}};
 const packet=Mapper.map({source_app:app,event,session});
 assert.equal(packet.context.member_id,'A');
 assert.equal(packet.evidence_policy.observation_only,true);
 assert.equal(packet.evidence_policy.reference_issuance_claim,false);
 assert.equal(packet.evidence_policy.auto_award,false);
 assert.equal(packet.packet_id,app+':'+event.event_id);
 assert.throws(()=>Mapper.map({source_app:app,event,session:{...session,selected_member_id:'B'}}),/MEMBER_SCOPE_MISMATCH/);
 assert.throws(()=>Mapper.map({source_app:app,event:{...event,family_id:'OTHER'},session}),/FAMILY_SCOPE_MISMATCH/);
 assert.throws(()=>Mapper.map({source_app:app,event:{...event,payload:{...event.payload,member_id:'OTHER'}},session}),/PAYLOAD_MEMBER_SCOPE_CONFLICT/);
 assert.throws(()=>Mapper.map({source_app:app,event:{...event,payload:{...event.payload,child_id:'OTHER'}},session}),/PAYLOAD_MEMBER_SCOPE_CONFLICT/);
 assert.throws(()=>Mapper.map({source_app:app,event:{...event,payload:{...event.payload,family_id:'OTHER'}},session}),/FAMILY_SCOPE_MISMATCH/);
 assert.throws(()=>Mapper.map({source_app:app,event:{...event,payload:{...event.payload,auto_award:true}},session}),/AUTHORITY_ESCALATION_DENIED/);
 assert.throws(()=>Mapper.map({source_app:app,event,session:{...session,authenticated:false}}),/TRUSTED_SELECTED_MEMBER_SESSION_REQUIRED/);
 assert.throws(()=>Mapper.map({source_app:app,event:{...event,event_id:''},session}),/SPECIALIST_OBSERVATION_EVENT_REQUIRED/);
}
console.log('SPECIALIST_OBSERVATION_PACKET_MAPPER_PASS: three specialist sources, trusted scope, no authority escalation');
