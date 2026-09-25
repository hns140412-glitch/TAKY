'use strict';
const assert=require('node:assert/strict');
const P=require('./specialist-event-pipeline.js');

const hideEvent=(id,day,outcome)=>({
  source:'hide-seek',
  event_id:id,
  occurred_at:`2026-09-${String(day).padStart(2,'0')}T07:00:00.000Z`,
  event_type:'RETRIEVAL_RESULT',
  payload:{
    member_id:'A',
    subject:'영어',
    concept_skill_target:'vocabulary',
    learning_target_id:'word:'+id,
    instrument_version:'HIDE_CODE_RED_V1',
    interaction_mode:'RECALL',
    assisted:false,
    attemptCount:1,
    responseLatencyMs:800,
    verification_candidate:{
      verifier_type:'RETRIEVAL_EXACT_MATCH',
      verifier_version:'HIDE_CODE_RED_V1',
      basis:'DETERMINISTIC_LOCAL_MATCH',
      outcome,
      reference_id:'word:'+id
    }
  }
});

const readyEvidence={
  event_id:'ready1',
  observed_at:'2026-09-22T08:00:00.000Z',
  member_id:'A',
  subject:'영어',
  concept_skill_target:'vocabulary',
  learning_target_id:'word:ready1',
  evidence_type:'STRUCTURED_PRACTICE_EVIDENCE',
  source_app:'ready-set',
  instrument_version:'READY_ANSWER_KEY_V1',
  interaction_mode:'STRUCTURED_PRACTICE',
  verification_candidate:{
    verifier_type:'ANSWER_KEY_EXACT',
    verifier_version:'READY_ANSWER_KEY_V1',
    basis:'DETERMINISTIC_LOCAL_MATCH',
    outcome:1,
    reference_id:'assignment:a1:item:ready1'
  }
};

const snapEvent={
  source:'snap-pop',
  event_id:'snap1',
  occurred_at:'2026-09-23T09:00:00.000Z',
  event_type:'TASK_COMPLETED',
  payload:{
    member_id:'A',
    subject:'영어',
    concept_skill_target:'sentence_production',
    learning_target_id:'sentence:snap1',
    instrument_version:'SNAP_RUBRIC_V1',
    child_authored:true,
    landmark:'beach'
  }
};

let state=P.emptyState();
let r=P.ingest(state,[
  {source_app:'hide-seek',event:hideEvent('h1',20,1)},
  {source_app:'hide-seek',event:hideEvent('h2',21,0)},
  {source_app:'ready-set',evidence:readyEvidence},
  {source_app:'snap-pop',event:snapEvent}
],{created_at:'2026-09-23T10:00:00.000Z'});

assert.equal(r.ok,true);
assert.equal(r.accepted_count,4);
assert.equal(r.verified_count,3);
assert.equal(r.observation_only_count,1);
assert.equal(r.state.observation_only.length,1);
assert.equal(r.evaluations.length,1);
assert.equal(r.evaluations[0].event_count,3);
assert.equal(r.evaluations[0].data_readiness.scopes[0].verified_retrieval_target_count,2);
assert.equal(r.evaluations[0].data_readiness.scopes[0].remaining_verified_targets,28);
assert.equal(P.currentReadiness(r.state)[0].verified_retrieval_target_count,2);
assert.equal(P.selfValidate(r).ok,true);
state=r.state;

const duplicate=P.ingest(state,[
  {source_app:'hide-seek',event:hideEvent('h1',20,1)}
],{created_at:'2026-09-24T10:00:00.000Z'});
assert.equal(duplicate.ok,true);
assert.equal(duplicate.evaluations[0].deduplicated,true);
assert.equal(duplicate.state.scope_receipts['A::영어::vocabulary'].receipt.event_count,3);
state=duplicate.state;

const extended=P.ingest(state,[
  {source_app:'hide-seek',event:hideEvent('h3',24,1)}
],{created_at:'2026-09-24T10:00:00.000Z'});
assert.equal(extended.ok,true);
const group=extended.state.scope_receipts['A::영어::vocabulary'];
assert.equal(group.receipt.event_count,4);
assert.equal(group.receipt.incremental_event_count,1);
assert.ok(group.receipt.parent_receipt_id);
assert.equal(P.currentReadiness(extended.state)[0].verified_retrieval_target_count,3);
state=extended.state;

const snapVerified=P.ingest(state,[{
  source_app:'snap-pop',
  event:snapEvent,
  verification_input:{
    receipt_id:'vr-snap1',
    target_event_id:'snap1',
    verified_at:'2026-09-23T10:00:00.000Z',
    verifier_type:'HUMAN_RUBRIC_BINARY',
    verifier_version:'SNAP_RUBRIC_V1',
    outcome:1,
    member_id:'A',
    subject:'영어',
    concept_skill_target:'sentence_production',
    reference_id:'rubric:snap-writing-v1',
    reviewer_role:'TEACHER'
  }
}],{created_at:'2026-09-24T11:00:00.000Z'});
assert.equal(snapVerified.ok,true);
assert.equal(snapVerified.verified_count,1);
assert.equal(snapVerified.state.scope_receipts['A::영어::sentence_production'].receipt.event_count,1);

const badSnap=P.ingest(state,[{
  source_app:'snap-pop',
  event:snapEvent,
  verification_input:{
    receipt_id:'vr-bad',
    target_event_id:'snap1',
    verified_at:'2026-09-23T10:00:00.000Z',
    verifier_type:'HUMAN_RUBRIC_BINARY',
    verifier_version:'SNAP_RUBRIC_V1',
    outcome:1,
    member_id:'A',
    subject:'영어',
    concept_skill_target:'sentence_production',
    reference_id:'rubric:snap-writing-v1',
    reviewer_role:'CHILD'
  }
}]);
assert.equal(badSnap.ok,false);
assert.equal(badSnap.rejected[0].reason,'SNAP_VERIFICATION_RECEIPT_INVALID');

console.log('SPECIALIST_EVENT_PIPELINE_PASS');
