'use strict';
const assert=require('node:assert/strict');
const Replay=require('./replay-dataset.js');
const Bridge=require('./replay-benchmark.js');

const mk=(id,day,outcome,extra={})=>({
  event_id:id,
  observed_at:`2026-09-${String(day).padStart(2,'0')}T07:00:00.000Z`,
  member_id:'A',
  subject:'영어',
  concept_skill_target:'vocabulary',
  evidence_type:extra.evidence_type||'MEMORY_RETRIEVAL_EVIDENCE',
  source_app:extra.source_app||'hide-seek',
  instrument_version:extra.instrument_version||'hide-v1',
  verified_outcome:outcome,
  memory:{average_strength:extra.strength??70}
});

const raw=[
  mk('e1',1,0,{strength:30}),mk('e2',2,1,{strength:55}),mk('e3',3,1,{strength:65}),
  mk('e4',4,1,{strength:72}),mk('e5',5,0,{strength:50}),mk('e6',6,1,{strength:73}),
  mk('e7',7,1,{strength:76}),mk('e8',8,1,{strength:80}),mk('e9',9,0,{strength:57}),
  mk('e10',10,1,{strength:78}),
  mk('self',11,1,{evidence_type:'CHILD_SELF_REPORT',source_app:'ready-set',instrument_version:'ready-v1'})
];

const built=Replay.buildDataset(raw,{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'},{created_at:'2026-09-25T00:00:00.000Z',source_kind:'SYNTHETIC_FIXTURE'});
const out=Bridge.benchmarkReplay(built.dataset);
assert.equal(out.ok,true);
assert.equal(out.observation_only_count,1);
assert.equal(out.verified_target_count,10);
assert.equal(out.promotion_eligible,false);
assert.equal(out.promotion_blockers.includes('REAL_EVIDENCE_REQUIRED'),true);
assert.equal(out.promotion_blockers.includes('MIN_REAL_TARGET_COUNT_NOT_MET'),true);
assert.equal(Bridge.selfValidate(out).ok,true);

const real=Replay.buildDataset(raw,{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'},{created_at:'2026-09-25T00:00:00.000Z',source_kind:'REAL_EVIDENCE'});
const realOut=Bridge.benchmarkReplay(real.dataset);
assert.equal(realOut.promotion_eligible,false);
assert.equal(realOut.promotion_blockers.includes('REAL_EVIDENCE_REQUIRED'),false);
assert.equal(realOut.promotion_blockers.includes('REAL_EVIDENCE_RECEIPT_REQUIRED'),true);
assert.equal(realOut.promotion_blockers.includes('HUMAN_PROMOTION_REVIEW_REQUIRED'),true);

const receipted=Replay.buildDataset(raw,{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'},{created_at:'2026-09-25T00:00:00.000Z',source_kind:'REAL_EVIDENCE',evidence_receipt_id:'receipt_001'});
const receiptedOut=Bridge.benchmarkReplay(receipted.dataset);
assert.equal(receiptedOut.promotion_blockers.includes('REAL_EVIDENCE_RECEIPT_REQUIRED'),false);

console.log('LEARNING_REPLAY_BENCHMARK_PASS');
