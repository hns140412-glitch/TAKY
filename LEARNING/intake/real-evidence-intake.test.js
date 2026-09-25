'use strict';
const assert=require('node:assert/strict');
const I=require('./real-evidence-intake.js');

const ev=(id,member,subject,target,outcome)=>({
  event_id:id,
  observed_at:'2026-09-25T07:00:00.000Z',
  member_id:member,
  subject,
  concept_skill_target:target,
  evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',
  source_app:'hide-seek',
  instrument_version:'hide-v1',
  verified_outcome:outcome,
  verification:{
    authority:'LEARNING_VERIFICATION_RECEIPT',
    receipt_id:'vr-'+id,
    verifier_type:'RETRIEVAL_EXACT_MATCH',
    verifier_version:'HIDE_CODE_RED_V1'
  }
});

const mixed=[
  ev('a1','A','영어','vocabulary',1),
  ev('a2','A','영어','vocabulary',0),
  ev('a3','A','영어','spelling',1),
  ev('b1','B','영어','vocabulary',1),
  {...ev('bad','A','영어','vocabulary',1),verification:null}
];

const p=I.partitionVerifiedEvidence(mixed);
assert.equal(p.groups.length,3);
assert.equal(p.rejected.length,1);

const out=I.issueScopeReceipts(mixed,{created_at:'2026-09-25T00:00:00.000Z'});
assert.equal(out.ok,true);
assert.equal(out.receipt_groups.length,3);
assert.equal(out.rejected.length,1);

const vocabA=out.receipt_groups.find(x=>x.scope_key==='A::영어::vocabulary');
assert.equal(vocabA.receipt.event_count,2);
assert.equal(vocabA.receipt.scope.member_id,'A');
assert.equal(vocabA.receipt.scope.concept_skill_target,'vocabulary');

const vocabB=out.receipt_groups.find(x=>x.scope_key==='B::영어::vocabulary');
assert.equal(vocabB.receipt.event_count,1);

console.log('REAL_EVIDENCE_INTAKE_PASS');
