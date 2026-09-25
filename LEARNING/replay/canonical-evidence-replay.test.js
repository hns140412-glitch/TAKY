'use strict';
const assert=require('node:assert/strict');
const A=require('../adapters/canonical-evidence.js');
const R=require('./replay-dataset.js');

const ctx={member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY',instrument_version:'bridge-v1'};
const canonical=[
  A.fromHide({event_id:'h1',source:'hide-seek',occurred_at:'2026-09-20T07:00:00.000Z',payload:{caseMastery:90,memorySummary:{averageMemoryStrength:70}}},ctx),
  A.fromHide({event_id:'h2',source:'hide-seek',occurred_at:'2026-09-21T07:00:00.000Z',payload:{memorySummary:{averageMemoryStrength:75}}},{...ctx,verified_outcome:1}),
  A.fromSnap({event_id:'s1',source:'snap-pop',occurred_at:'2026-09-22T07:00:00.000Z',payload:{child_authored:true,landmark:'beach',step:3}},ctx),
  A.fromReady({event_id:'r1',source:'ready-set',occurred_at:'2026-09-23T07:00:00.000Z',payload:{evidence_type:'CHILD_SELF_REPORT',self_report:{felt_easy:true}}},{...ctx,evidence_type:'CHILD_SELF_REPORT',verified_outcome:1})
];

for(const row of canonical)assert.equal(A.validateCanonical(row).ok,true);

const built=R.buildDataset(canonical,{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'},{created_at:'2026-09-25T00:00:00.000Z',source_kind:'SYNTHETIC_FIXTURE'});
assert.equal(built.ok,true);
assert.equal(R.selfValidate(built.dataset).ok,true);

const byId=Object.fromEntries(built.dataset.records.map(r=>[r.event_id,r]));
assert.equal(byId.h1.label_status,'OBSERVATION_ONLY','Hide caseMastery must not auto-label');
assert.equal(byId.h2.label_status,'VERIFIED_TARGET','only explicitly verified adapter outcome may become target');
assert.equal(byId.s1.label_status,'OBSERVATION_ONLY','Snap authorship is not objective mastery');
assert.equal(byId.r1.label_status,'OBSERVATION_ONLY','self report remains observation only');

const split=R.splitDataset(built.dataset);
assert.equal(split.ok,false);
assert.equal(split.reason,'INSUFFICIENT_VERIFIED_TARGETS');

console.log('CANONICAL_EVIDENCE_TO_REPLAY_PASS');
