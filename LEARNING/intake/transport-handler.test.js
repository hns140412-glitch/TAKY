'use strict';
const assert=require('node:assert/strict');
const H=require('./transport-handler.js');
const P=require('./specialist-event-pipeline.js');

const hidePacket={
  packet_id:'hide-seek:h1',
  source_app:'hide-seek',
  event:{
    source:'hide-seek',
    event_id:'h1',
    occurred_at:'2026-09-25T12:00:00.000Z',
    event_type:'RETRIEVAL_RESULT',
    payload:{
      member_id:'A',
      subject:'영어',
      concept_skill_target:'vocabulary',
      learning_target_id:'word:h1',
      instrument_version:'HIDE_CODE_RED_V1',
      verification_candidate:{
        verifier_type:'RETRIEVAL_EXACT_MATCH',
        verifier_version:'HIDE_CODE_RED_V1',
        basis:'DETERMINISTIC_LOCAL_MATCH',
        outcome:1,
        reference_id:'word:h1'
      }
    }
  },
  context:{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'}
};

const snapPacket={
  packet_id:'snap-pop:s1',
  source_app:'snap-pop',
  event:{
    source:'snap-pop',
    event_id:'s1',
    occurred_at:'2026-09-25T12:10:00.000Z',
    event_type:'TASK_COMPLETED',
    payload:{
      member_id:'A',
      subject:'영어',
      concept_skill_target:'sentence_production',
      learning_target_id:'sentence:s1',
      instrument_version:'SNAP_RUBRIC_V1',
      child_authored:true
    }
  },
  context:{member_id:'A',subject:'영어',concept_skill_target:'sentence_production'}
};

let state=P.emptyState();

const h=H.ingest(state,hidePacket,{created_at:'2026-09-25T12:01:00.000Z'});
assert.equal(h.ok,true);
assert.equal(h.acknowledgement_kind,'REAL_EVIDENCE_RECEIPT');
assert.ok(h.receipt_id.startsWith('real-evidence:'));
assert.equal(h.readiness[0].verified_retrieval_target_count,1);
assert.equal(H.selfValidate(h).ok,true);
state=h.state;

const s=H.ingest(state,snapPacket,{created_at:'2026-09-25T12:11:00.000Z'});
assert.equal(s.ok,true);
assert.equal(s.acknowledgement_kind,'OBSERVATION_INGEST_RECEIPT');
assert.ok(s.receipt_id.startsWith('observation:'));
assert.equal(s.observation_receipt.authority,'OBSERVATION_INGEST_RECEIPT');
assert.equal(s.observation_receipt.immutable,true);
assert.equal(H.selfValidate(s).ok,true);
state=s.state;

const s2=H.ingest(state,snapPacket,{created_at:'2026-09-25T12:12:00.000Z'});
assert.equal(s2.ok,true);
assert.equal(s2.acknowledgement_kind,'OBSERVATION_INGEST_RECEIPT');
assert.equal(s2.receipt_id,s.receipt_id);
assert.equal(s2.duplicate,true);

const snapVerified={...snapPacket,verification_input:{
  receipt_id:'vr-s1',
  target_event_id:'s1',
  verified_at:'2026-09-25T12:20:00.000Z',
  verifier_type:'HUMAN_RUBRIC_BINARY',
  verifier_version:'SNAP_RUBRIC_V1',
  outcome:1,
  member_id:'A',
  subject:'영어',
  concept_skill_target:'sentence_production',
  reference_id:'rubric:snap-writing-v1',
  reviewer_role:'TEACHER'
}};
const sv=H.ingest(state,snapVerified,{created_at:'2026-09-25T12:21:00.000Z'});
assert.equal(sv.ok,true);
assert.equal(sv.acknowledgement_kind,'REAL_EVIDENCE_RECEIPT');
assert.ok(sv.receipt_id.startsWith('real-evidence:'));

console.log('LEARNING_EVIDENCE_TRANSPORT_HANDLER_PASS');
