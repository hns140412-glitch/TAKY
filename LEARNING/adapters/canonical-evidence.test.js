'use strict';
const assert=require('node:assert/strict');
const A=require('./canonical-evidence.js');
const V=require('../verification/verification-layer.js');

const ctx={member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY',instrument_version:'bridge-v1'};

const hide=A.fromHide({
  event_id:'h1',source:'hide-seek',event_type:'TASK_COMPLETED',occurred_at:'2026-09-25T07:00:00.000Z',
  payload:{word_id:'w1',caseMastery:84,validWordCount:12,sheetStatus:'COMPLETED',memorySummary:{averageMemoryStrength:67,reviewAdvisories:[{lexicalId:'w1',nextReviewPriority:90}],prioritySemantics:'ADVISORY_SIGNAL_NOT_DATE'}}
},ctx);
assert.equal(hide.evidence_type,'MEMORY_RETRIEVAL_EVIDENCE');
assert.equal(hide.learning_target_id,'w1');
assert.equal(hide.memory.average_strength,67);
assert.equal(hide.raw_app_signals.case_mastery,84);
assert.equal(hide.verified_outcome,null,'app mastery score must not become verified outcome');
assert.equal(A.validateCanonical(hide).ok,true);

const snap=A.fromSnap({
  event_id:'s1',source:'snap-pop',event_type:'TASK_COMPLETED',occurred_at:'2026-09-25T08:00:00.000Z',
  payload:{child_authored:true,landmark:'forest',step:3,used_handoff_word:'ocean'}
},ctx);
assert.equal(snap.evidence_type,'LEARNER_PRODUCTION_EVIDENCE');
assert.equal(snap.production.child_authored,true);
assert.equal(snap.verified_outcome,null,'child authored completion is not objective mastery');
assert.equal(A.validateCanonical(snap).ok,true);

const ready=A.fromReady({
  event_id:'r1',source:'ready-set',occurred_at:'2026-09-25T09:00:00.000Z',
  payload:{evidence_type:'CHILD_SELF_REPORT',self_report:{difficulty:'HARD'}}
},{...ctx,evidence_type:'CHILD_SELF_REPORT'});
assert.equal(ready.evidence_type,'CHILD_SELF_REPORT');
assert.equal(ready.verified_outcome,null);
assert.equal(A.validateCanonical(ready).ok,true);

const receipt=V.issueReceipt({
  receipt_id:'vr-h2',
  target_event_id:'h2',
  verified_at:'2026-09-26T07:01:00.000Z',
  verifier_type:'RETRIEVAL_EXACT_MATCH',
  verifier_version:'1.0.0',
  outcome:1,
  member_id:'A',
  subject:'영어',
  concept_skill_target:'vocabulary',
  reference_id:'answer-key:vocab-001'
}).receipt;
const verifiedHide=A.fromHide({
  event_id:'h2',source:'hide-seek',event_type:'TASK_COMPLETED',occurred_at:'2026-09-26T07:00:00.000Z',
  payload:{memorySummary:{averageMemoryStrength:80}}
},{...ctx,verification_receipt:receipt});
assert.equal(verifiedHide.verified_outcome,1,'verified outcome must require a valid verification receipt');
assert.equal(verifiedHide.verification.receipt_id,'vr-h2');

const forged={...hide,verified_outcome:1};
assert.equal(A.validateCanonical(forged).ok,false);
assert.equal(A.validateCanonical(forged).issues.includes('VERIFIED_OUTCOME_WITHOUT_RECEIPT'),true);

const leaked={...hide,due_at:'2026-09-30T07:00:00.000Z'};
assert.equal(A.validateCanonical(leaked).ok,false);
assert.equal(A.validateCanonical(leaked).issues.includes('SCHEDULE_AUTHORITY_LEAK'),true);

console.log('CANONICAL_LEARNING_EVIDENCE_ADAPTER_PASS');

const autoVerified=A.fromHide({
  event_id:'h3',
  source:'hide-seek',
  event_type:'RETRIEVAL_ATTEMPT_RESULT',
  occurred_at:'2026-09-27T07:00:00.000Z',
  payload:{
    instrumentVersion:'HIDE_CODE_RED_V1',
    interactionMode:'CORE',
    assisted:false,
    attemptCount:1,
    responseLatencyMs:1200,
    verification_candidate:{
      verifier_type:'RETRIEVAL_EXACT_MATCH',
      verifier_version:'HIDE_CODE_RED_V1',
      target_semantics:'UNASSISTED_EXACT_RETRIEVAL',
      outcome:1,
      reference_id:'hide-word:sheet-1:w1:spelling',
      basis:'DETERMINISTIC_LOCAL_MATCH',
      result_type:'CORRECT'
    }
  }
},ctx);
assert.equal(autoVerified.evidence_type,'MEMORY_RETRIEVAL_EVIDENCE');
assert.equal(autoVerified.verified_outcome,1);
assert.equal(autoVerified.verification.verifier_type,'RETRIEVAL_EXACT_MATCH');
assert.equal(autoVerified.instrument_version,'HIDE_CODE_RED_V1');
assert.equal(autoVerified.assistance,'UNASSISTED');
assert.equal(A.validateCanonical(autoVerified).ok,true);
