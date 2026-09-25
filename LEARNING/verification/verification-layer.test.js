'use strict';
const assert=require('node:assert/strict');
const V=require('./verification-layer.js');

const base={
  receipt_id:'vr1',
  target_event_id:'e1',
  verified_at:'2026-09-25T07:05:00.000Z',
  verifier_type:'RETRIEVAL_EXACT_MATCH',
  verifier_version:'1.0.0',
  outcome:1,
  member_id:'A',
  subject:'영어',
  concept_skill_target:'vocabulary',
  reference_id:'answer-key:vocab-001'
};

const issued=V.issueReceipt(base);
assert.equal(issued.ok,true);
assert.equal(V.validateReceipt(issued.receipt).ok,true);

const evidence={
  event_id:'e1',
  member_id:'A',
  subject:'영어',
  concept_skill_target:'vocabulary',
  evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',
  source_app:'hide-seek',
  verified_outcome:null
};
const applied=V.applyReceipt(evidence,issued.receipt);
assert.equal(applied.ok,true);
assert.equal(applied.evidence.verified_outcome,1);
assert.equal(applied.evidence.verification.receipt_id,'vr1');

const self=V.applyReceipt({...evidence,evidence_type:'CHILD_SELF_REPORT'},issued.receipt);
assert.equal(self.ok,false);
assert.equal(self.issues.includes('SELF_REPORT_NOT_VERIFIABLE_TARGET'),true);

const wrongEvent=V.applyReceipt({...evidence,event_id:'e2'},issued.receipt);
assert.equal(wrongEvent.ok,false);
assert.equal(wrongEvent.issues.includes('EVENT_MISMATCH'),true);

const badHuman=V.issueReceipt({...base,receipt_id:'vr2',verifier_type:'HUMAN_RUBRIC_BINARY',reviewer_role:'CHILD'});
assert.equal(badHuman.ok,false);
assert.equal(badHuman.issues.includes('REVIEWER_ROLE_INVALID'),true);

const snapReceipt=V.issueReceipt({
  ...base,
  receipt_id:'vr3',
  verifier_type:'HUMAN_RUBRIC_BINARY',
  reviewer_role:'TEACHER',
  target_event_id:'s1',
  reference_id:'rubric:writing-v1'
});
assert.equal(snapReceipt.ok,true);
const snap=V.applyReceipt({
  event_id:'s1',member_id:'A',subject:'영어',concept_skill_target:'vocabulary',
  evidence_type:'LEARNER_PRODUCTION_EVIDENCE',source_app:'snap-pop',verified_outcome:null
},snapReceipt.receipt);
assert.equal(snap.ok,true);

console.log('LEARNING_VERIFICATION_LAYER_PASS');

const candidateEvidence={
  event_id:'hc1',
  observed_at:'2026-09-25T10:00:00.000Z',
  member_id:'A',
  subject:'영어',
  concept_skill_target:'vocabulary',
  source_app:'hide-seek',
  evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',
  verified_outcome:null
};
const candidateApplied=V.issueFromCandidate(candidateEvidence,{
  verifier_type:'RETRIEVAL_EXACT_MATCH',
  verifier_version:'HIDE_CODE_RED_V1',
  outcome:1,
  reference_id:'hide-word:sheet-1:w1:spelling',
  basis:'DETERMINISTIC_LOCAL_MATCH'
});
assert.equal(candidateApplied.ok,true);
assert.equal(candidateApplied.evidence.verified_outcome,1);
assert.equal(candidateApplied.evidence.verification.verifier_type,'RETRIEVAL_EXACT_MATCH');

const badCandidate=V.issueFromCandidate(candidateEvidence,{
  verifier_type:'RETRIEVAL_EXACT_MATCH',
  verifier_version:'HIDE_CODE_RED_V1',
  outcome:1,
  reference_id:'hide-word:sheet-1:w1:spelling',
  basis:'APP_SCORE_ONLY'
});
assert.equal(badCandidate.ok,false);
assert.equal(badCandidate.reason,'CANDIDATE_BASIS_INVALID');
