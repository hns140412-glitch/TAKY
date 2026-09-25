'use strict';
const assert=require('node:assert/strict');
const D=require('./replay-dataset-builder.js');

const e=(id,day,outcome,opts={})=>({
  event_id:id,
  observed_at:`2026-09-${String(day).padStart(2,'0')}T07:00:00.000Z`,
  member_id:opts.member_id||'A',
  subject:opts.subject||'영어',
  concept_skill_target:opts.target||'VOCABULARY',
  evidence_type:opts.evidence_type||'MEMORY_RETRIEVAL_EVIDENCE',
  source_app:opts.source_app||'hide-seek',
  instrument_version:opts.instrument_version||'hide-v1',
  verified_outcome:outcome,
  memory:{average_strength:opts.strength}
});

const rows=[
  e('e3',23,1,{strength:70}),
  e('e1',20,0,{strength:35}),
  e('e2',21,1,{strength:55}),
  e('e4',25,1,{strength:76}),
  e('m1',22,1,{subject:'수학',target:'FRACTION'})
];

const ds=D.buildReplayDataset(rows,{minimum_train_events:3,minimum_held_out_events:1});
assert.equal(ds.ok,true);
assert.equal(ds.promotion_eligible,false);
assert.equal(ds.groups.length,2);

const vocab=ds.groups.find(x=>x.subject==='영어');
assert.deepEqual(vocab.train.map(x=>x.event_id),['e1','e2','e3']);
assert.deepEqual(vocab.held_out.map(x=>x.event_id),['e4']);
assert.equal(vocab.quality_flags.includes('HELD_OUT_LEAKAGE'),false);
assert.equal(D.selfValidate(ds).ok,true);

const duplicate=D.buildReplayDataset([...rows,e('e1',26,1)]);
assert.equal(duplicate.ok,false);
assert.deepEqual(duplicate.duplicate_event_ids,['e1']);
assert.equal(D.selfValidate(duplicate).ok,false);

const badSelf=D.buildReplayDataset([{
  ...e('s1',20,1),
  evidence_type:'CHILD_SELF_REPORT',
  verified_performance:true
}]);
assert.equal(badSelf.ok,false);
assert.equal(badSelf.invalid_events[0].issues.includes('SELF_REPORT_CANNOT_BE_VERIFIED_PERFORMANCE'),true);

const changed=D.buildReplayDataset([
  e('c1',20,0),
  e('c2',21,1),
  e('c3',22,1),
  e('c4',23,1,{instrument_version:'hide-v2'})
]);
assert.equal(changed.groups[0].quality_flags.includes('INSTRUMENT_CHANGE_BOUNDARY'),true);

const synthetic=D.buildReplayDataset(rows,{synthetic:true});
assert.equal(synthetic.summary.promotion_block_reason,'SYNTHETIC_ONLY');
assert.equal(synthetic.groups.every(x=>x.quality_flags.includes('SYNTHETIC_ONLY')),true);

const leaked=D.buildReplayDataset([{...e('l1',20,1),schedule_date:'2026-09-30'},{...e('l2',21,1)},{...e('l3',22,1)},{...e('l4',23,1)}]);
assert.equal(D.selfValidate(leaked).ok,false);
assert.equal(D.selfValidate(leaked).issues.includes('SCHEDULE_AUTHORITY_LEAK'),true);

console.log('LEARNING_REPLAY_DATASET_PASS');
