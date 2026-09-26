'use strict';
const assert=require('node:assert/strict');
const A=require('./specialist-bridge-event-adapter.js');
for(const [app,type] of [['hide-seek','LEARNING_MEMORY_SIGNAL'],['snap-pop','LEARNING_OUTCOME']]){
 const raw={source:app,event_type:type,type,event_id:'e-1',occurred_at:'2026-09-27T01:00:00Z',
 child_id:'A',payload:{member_id:'A',subject:'english',concept_skill_target:'vocabulary',
 observation_only:true,contextual_evidence_only:true,global_mastery_claim:false}};
 const event=A.fromBridge(app,raw);
 assert.equal(event.event_id,'e-1');
 assert.equal(event.member_id,'A');
 assert.throws(()=>A.fromBridge(app,{...raw,payload:{...raw.payload,subject:null}}),/BRIDGE_LEARNING_SCOPE_MISSING_HOLD/);
 assert.throws(()=>A.fromBridge(app,{...raw,payload:{...raw.payload,global_mastery_claim:true}}),/ONLY_CONTRACT_REQUIRED/);
 assert.throws(()=>A.fromBridge(app,{...raw,event_id:''}),/EXACT_SPECIALIST_BRIDGE_EVENT_REQUIRED/);
 assert.throws(()=>A.fromBridge(app,{...raw,child_id:'B'}),/BRIDGE_CHILD_PAYLOAD_SCOPE_CONFLICT/);
 assert.throws(()=>A.fromBridge(app,{...raw,event_type:'TASK_COMPLETED'}),/EXACT_SPECIALIST_BRIDGE_EVENT_REQUIRED/);
}
assert.throws(()=>A.readyObservation({event_id:'r1',occurred_at:'now',member_id:'A',
 payload:{member_id:'A'}}),/READY_EXPLICIT_OBSERVATION_REQUIRED/);
assert.equal(A.readyObservation({event_id:'r1',occurred_at:'now',member_id:'A',
 payload:{member_id:'A',subject:'english',concept_skill_target:'vocabulary',observation_only:true}}).source_app,'ready-set');
console.log('SPECIALIST_BRIDGE_EVENT_ADAPTER_PASS: exact Hide/Snap envelopes, explicit Ready observation, conflicting child rejected');
