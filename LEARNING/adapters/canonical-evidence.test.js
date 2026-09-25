'use strict';
const assert=require('node:assert/strict');
const A=require('./canonical-evidence.js');

const ctx={member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY',instrument_version:'bridge-v1'};

const hide=A.fromHide({
  event_id:'h1',source:'hide-seek',event_type:'TASK_COMPLETED',occurred_at:'2026-09-25T07:00:00.000Z',
  payload:{caseMastery:84,validWordCount:12,sheetStatus:'COMPLETED',memorySummary:{averageMemoryStrength:67,reviewAdvisories:[{lexicalId:'w1',nextReviewPriority:90}],prioritySemantics:'ADVISORY_SIGNAL_NOT_DATE'}}
},ctx);
assert.equal(hide.evidence_type,'MEMORY_RETRIEVAL_EVIDENCE');
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
},{...ctx,evidence_type:'CHILD_SELF_REPORT',verified_outcome:1});
assert.equal(ready.evidence_type,'CHILD_SELF_REPORT');
assert.equal(ready.verified_outcome,null);
assert.equal(A.validateCanonical(ready).ok,true);

const verifiedHide=A.fromHide({
  event_id:'h2',source:'hide-seek',event_type:'TASK_COMPLETED',occurred_at:'2026-09-26T07:00:00.000Z',
  payload:{memorySummary:{averageMemoryStrength:80}}
},{...ctx,verified_outcome:1});
assert.equal(verifiedHide.verified_outcome,1,'verified outcome must come only from adapter context/verification layer');

const leaked={...hide,due_at:'2026-09-30T07:00:00.000Z'};
assert.equal(A.validateCanonical(leaked).ok,false);
assert.equal(A.validateCanonical(leaked).issues.includes('SCHEDULE_AUTHORITY_LEAK'),true);

console.log('CANONICAL_LEARNING_EVIDENCE_ADAPTER_PASS');
