'use strict';
const assert=require('node:assert/strict');
const os=require('node:os');
const path=require('node:path');
const fs=require('node:fs');
const fsp=fs.promises;
const {LocalJsonStrongStore}=require('./local-json-strong-store.js');
const Adapter=require('./durable-learning-system-growth-store-adapter.js');
const ReviewQueue=require('./grow-review-queue-adapter.js');

(async()=>{
  const root=await fsp.mkdtemp(path.join(os.tmpdir(),'taky-system-growth-'));
  const store=await new LocalJsonStrongStore(root).init();
  const packet={
    family_id:'FAMILY-PRIVATE',
    rows:[
      {member_id:'MEM-A',subject:'영어',concept_skill_target:'vocabulary',verified_outcome_count:3,success_count:2,failure_count:1},
      {member_id:'MEM-B',subject:'영어',concept_skill_target:'vocabulary',verified_outcome_count:2,success_count:1,failure_count:1},
      {member_id:'MEM-C',subject:'영어',concept_skill_target:'vocabulary',verified_outcome_count:3,success_count:2,failure_count:1}
    ]
  };
  const first=await Adapter.appendAggregate(store,packet,{min_members:3,min_verified_outcomes:6});
  assert.equal(first.ok,true);
  assert.equal(first.idempotent,false);
  assert.equal(first.state.candidates.length,1);
  assert.equal(first.state.candidates[0].promotion_authorized,false);
  assert.equal(first.review_queue.attempted,true);
  assert.equal(first.review_queue.ok,true);
  assert.equal(first.review_queue.result.state.candidates.length,1);
  assert.equal(first.review_queue.result.state.candidates[0].promotion_authorized,false);
  assert.equal(first.review_queue.result.state.candidates[0].authority_transfer,false);
  assert.equal(Adapter.selfValidate(first).ok,true);

  const second=await Adapter.appendAggregate(store,packet,{min_members:3,min_verified_outcomes:6});
  assert.equal(second.ok,true);
  assert.equal(second.idempotent,true);

  const entry=await store.getWithMetadata(Adapter.stateKey(packet),{type:'json',consistency:'strong'});
  const raw=JSON.stringify(entry.data);
  assert.equal(raw.includes('MEM-A'),false);
  assert.equal(raw.includes('MEM-B'),false);
  assert.equal(raw.includes('MEM-C'),false);
  assert.equal(raw.includes('"member_id"'),false);
  assert.equal(raw.includes('"member_ref"'),false);

  const queueEntry=await store.getWithMetadata(ReviewQueue.KEY,{type:'json',consistency:'strong'});
  assert.ok(queueEntry&&queueEntry.data);
  const queueRaw=JSON.stringify(queueEntry.data);
  assert.equal(queueEntry.data.candidates.length,1);
  assert.equal(queueRaw.includes('MEM-A'),false);
  assert.equal(queueRaw.includes('MEM-B'),false);
  assert.equal(queueRaw.includes('MEM-C'),false);
  assert.equal(queueRaw.includes('"member_id"'),false);
  assert.equal(queueRaw.includes('"member_ref"'),false);
  assert.equal(ReviewQueue.selfValidate({ok:true,state:queueEntry.data}).ok,true);
  assert.equal(second.review_queue.result.idempotent,true);
  console.log('DURABLE_LEARNING_SYSTEM_GROWTH_STORE_PASS');
})().catch(e=>{console.error(e);process.exit(1);});
