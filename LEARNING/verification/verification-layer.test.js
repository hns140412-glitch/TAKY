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



const production={
  event_id:'snap-growth-1',observed_at:'2026-10-02T01:00:00.000Z',
  member_id:'A',subject:'english',concept_skill_target:'writing',
  learning_target_id:'writing:1',
  evidence_type:'LEARNER_PRODUCTION_EVIDENCE',
  source_app:'snap-pop',instrument_version:'SNAP_PRODUCTION_V1',
  verified_outcome:null,
  language_growth_signals:[
    {dimension:'EXPRESSION',outcome:'UNKNOWN',assisted:false},
    {dimension:'GRAMMAR',outcome:'UNKNOWN',assisted:false},
    {dimension:'THINKING',outcome:'UNKNOWN',assisted:false}
  ]
};
const growthReceipt=V.issueReceipt({
  receipt_id:'vr-growth-1',
  target_event_id:'snap-growth-1',
  verified_at:'2026-10-02T01:05:00.000Z',
  verifier_type:'HUMAN_GROWTH_RUBRIC',
  verifier_version:'SNAP_GROWTH_RUBRIC_V1',
  outcome:null,
  member_id:'A',
  subject:'english',
  concept_skill_target:'writing',
  reference_id:'rubric:snap-growth-v1',
  reviewer_role:'TEACHER',
  growth_dimensions:[
    {dimension:'EXPRESSION',outcome:'SUCCESS',assisted:false,transfer:true,depth:4,target_id:'writing:1'},
    {dimension:'GRAMMAR',outcome:'PARTIAL',assisted:false,target_id:'writing:1'},
    {dimension:'THINKING',outcome:'SUCCESS',assisted:false,transfer:true,depth:4,target_id:'writing:1'}
  ]
});
assert.equal(growthReceipt.ok,true,JSON.stringify(growthReceipt));
const appliedGrowth=V.applyReceipt(production,growthReceipt.receipt);
assert.equal(appliedGrowth.ok,true,JSON.stringify(appliedGrowth));
assert.equal(appliedGrowth.evidence.verified_outcome,null,'dimension rubric must not create global correctness');
assert.equal(appliedGrowth.evidence.verification.verifier_type,'HUMAN_GROWTH_RUBRIC');
assert.deepEqual(appliedGrowth.evidence.language_growth_signals.map(x=>[x.dimension,x.outcome]),[
  ['EXPRESSION','SUCCESS'],['GRAMMAR','PARTIAL'],['THINKING','SUCCESS']
]);
assert.equal(appliedGrowth.evidence.language_growth_signals[0].evidence_ref,'verification:vr-growth-1');

const badGrowthOutcome=V.issueReceipt({
  receipt_id:'vr-growth-bad',target_event_id:'snap-growth-1',
  verified_at:'2026-10-02T01:05:00.000Z',
  verifier_type:'HUMAN_GROWTH_RUBRIC',verifier_version:'V1',
  outcome:1,member_id:'A',subject:'english',concept_skill_target:'writing',
  reference_id:'rubric:snap-growth-v1',reviewer_role:'TEACHER',
  growth_dimensions:[{dimension:'EXPRESSION',outcome:'SUCCESS'}]
});
assert.equal(badGrowthOutcome.ok,false);
assert.ok(badGrowthOutcome.issues.includes('GROWTH_RUBRIC_GLOBAL_OUTCOME_FORBIDDEN'));

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
