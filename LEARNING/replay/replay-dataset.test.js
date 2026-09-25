'use strict';
const assert=require('node:assert/strict');
const R=require('./replay-dataset.js');

const e=(id,day,outcome,opts={})=>({
  event_id:id,
  observed_at:`2026-09-${String(day).padStart(2,'0')}T07:00:00.000Z`,
  member_id:opts.member_id||'A',
  subject:opts.subject||'영어',
  concept_skill_target:opts.target||'vocabulary',
  evidence_type:opts.evidence_type||'MEMORY_RETRIEVAL_EVIDENCE',
  source_app:opts.source_app||'hide-seek',
  instrument_version:opts.instrument_version||'hide-v1',
  interaction_mode:'RECALL',
  assistance:opts.assistance||'UNASSISTED',
  verified_outcome:outcome,
  verification:(outcome===0||outcome===1)&&opts.evidence_type!=='CHILD_SELF_REPORT'?{
    authority:'LEARNING_VERIFICATION_RECEIPT',
    receipt_id:'vr-'+id,
    verifier_type:'RETRIEVAL_EXACT_MATCH',
    verifier_version:'1.0.0'
  }:null,
  memory:{average_strength:opts.strength??70}
});

const raw=[
  e('e1',20,0,{strength:35}),
  e('e2',21,1,{strength:55}),
  e('e2',21,1,{strength:55}),
  e('self1',22,1,{evidence_type:'CHILD_SELF_REPORT',source_app:'ready-set',instrument_version:'ready-v1'}),
  e('e3',23,1,{strength:68}),
  e('m1',23,1,{subject:'수학',target:'fraction'}),
  e('e4',24,null,{strength:75}),
  {...e('bad',25,1),instrument_version:''}
];

const built=R.buildDataset(raw,{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'},{created_at:'2026-09-25T00:00:00.000Z',source_kind:'SYNTHETIC_FIXTURE',holdout_fraction:0.34});
assert.equal(built.ok,true);
assert.equal(R.selfValidate(built.dataset).ok,true);
assert.deepEqual(built.dataset.records.map(x=>x.event_id),['e1','e2','self1','e3','e4']);
assert.equal(built.dataset.records.find(x=>x.event_id==='self1').label_status,'OBSERVATION_ONLY');
assert.equal(built.dataset.records.find(x=>x.event_id==='self1').verified_outcome,1);
assert.equal(built.dataset.records.find(x=>x.event_id==='e4').label_status,'OBSERVATION_ONLY');
assert.equal(built.rejected.length,1);

const split=R.splitDataset(built.dataset);
assert.equal(split.ok,true);
assert.equal(split.train.length,2);
assert.equal(split.holdout.length,1);
assert.equal(split.diagnostics.verified_count,3);
assert.equal(split.diagnostics.observation_only_count,2);
assert.equal(split.diagnostics.instrument_drift_into_holdout,false);
assert.equal(Date.parse(split.train.at(-1).observed_at)<=Date.parse(split.holdout[0].observed_at),true);

const drift=R.buildDataset([
  e('d1',20,1),
  e('d2',21,1),
  e('d3',22,0,{instrument_version:'hide-v2'})
],{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'},{created_at:'2026-09-25T00:00:00.000Z',holdout_fraction:0.34});
const driftSplit=R.splitDataset(drift.dataset);
assert.equal(driftSplit.diagnostics.instrument_drift_into_holdout,true);

const invalid=JSON.parse(JSON.stringify(built.dataset));
invalid.records.find(x=>x.event_id==='self1').label_status='VERIFIED_TARGET';
assert.equal(R.selfValidate(invalid).ok,false);
assert.equal(R.selfValidate(invalid).issues.includes('SELF_REPORT_PROMOTED'),true);

console.log('LEARNING_REPLAY_DATASET_PASS');

const targetRecord=R.toReplayRecord({
  ...e('tid1',28,1),
  learning_target_id:'word:essential',
  verification:{authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'vr-tid1',verifier_type:'RETRIEVAL_EXACT_MATCH',verifier_version:'1'}
});
assert.equal(targetRecord.learning_target_id,'word:essential');
