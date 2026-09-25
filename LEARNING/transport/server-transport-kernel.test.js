'use strict';
const assert=require('node:assert/strict');
const K=require('./server-transport-kernel.js');
const R=require('./server-state-core-reconciler.js');

const packet=(id,outcome)=>({
  packet_id:'hide-seek:'+id,
  source_app:'hide-seek',
  context:{family_id:'F1',member_id:'A',subject:'영어',concept_skill_target:'vocabulary'},
  event:{source:'hide-seek',event_id:id,occurred_at:'2026-09-25T12:00:00.000Z',event_type:'RETRIEVAL_RESULT',payload:{
    member_id:'A',subject:'영어',concept_skill_target:'vocabulary',
    learning_target_id:'word:'+id,instrument_version:'HIDE_CODE_RED_V1',
    verification_candidate:{verifier_type:'RETRIEVAL_EXACT_MATCH',verifier_version:'HIDE_CODE_RED_V1',basis:'DETERMINISTIC_LOCAL_MATCH',outcome,reference_id:'word:'+id}
  }}
});

let state=K.emptyState();
const a=K.ingest(state,packet('e1',1));
assert.equal(a.ok,true);
assert.equal(a.acknowledgement_kind,'REAL_EVIDENCE_RECEIPT');
assert.equal(a.readiness.verified_retrieval_target_count,1);
state=a.state;

const b=K.ingest(state,packet('e2',0));
assert.equal(b.ok,true);
assert.equal(b.readiness.verified_retrieval_target_count,2);
state=b.state;

const rec=R.reconcile(state,{created_at:'2026-09-25T12:05:00.000Z'});
assert.equal(rec.ok,true);
assert.equal(rec.results.length,1);
assert.equal(rec.results[0].data_readiness.scopes[0].verified_retrieval_target_count,2);
assert.equal(rec.evaluation_ledger.entries.length,1);

console.log('SERVER_TRANSPORT_KERNEL_RECONCILE_PASS');
