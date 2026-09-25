'use strict';
const assert=require('node:assert/strict');
const R=require('./estimator-data-readiness.js');

const ev=(id,outcome)=>({
  event_id:id,
  observed_at:'2026-09-25T07:00:00.000Z',
  evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',
  instrument_version:'hide-v1',
  verified_outcome:outcome
});

const group={
  receipt:{receipt_id:'receipt-1',scope:{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'}},
  canonical_evidence:[
    ev('e1',1),ev('e2',0),ev('e3',1),
    {event_id:'obs1',evidence_type:'SELF_REFLECTION_EVIDENCE',verified_outcome:null}
  ]
};
const out=R.readiness([group],{min_verified_targets:30});
assert.equal(out.ok,true);
assert.equal(out.promotion_authority,false);
assert.equal(out.scopes[0].verified_retrieval_target_count,3);
assert.equal(out.scopes[0].remaining_verified_targets,27);
assert.equal(out.scopes[0].retention_promotion_data_ready,false);
assert.equal(out.scopes[0].bkt_promotion_data_ready,false);
assert.equal(R.selfValidate(out).ok,true);

const enough={
  ...group,
  canonical_evidence:Array.from({length:30},(_,i)=>ev('x'+i,i%2))
};
const ready=R.readiness([enough],{min_verified_targets:30});
assert.equal(ready.scopes[0].remaining_verified_targets,0);
assert.equal(ready.scopes[0].retention_promotion_data_ready,true);
assert.equal(ready.scopes[0].bkt_promotion_data_ready,true);
assert.equal(ready.promotion_authority,false);

console.log('ESTIMATOR_DATA_READINESS_PASS');
