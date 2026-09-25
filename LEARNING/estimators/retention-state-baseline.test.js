'use strict';
const assert=require('node:assert/strict');
const R=require('./retention-state-baseline.js');

const e=(id,day,outcome,strength=undefined)=>({
  event_id:id,
  observed_at:`2026-09-${String(day).padStart(2,'0')}T07:00:00.000Z`,
  evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',
  verified_outcome:outcome,
  verification:{authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'vr-'+id},
  memory:{average_strength:strength}
});

const empty=R.derive([]);
assert.equal(empty.retention_state,'UNKNOWN');
assert.equal(empty.promoted,false);
assert.equal(R.selfValidate(empty).ok,true);

const rows=[
  e('e1',20,0,35),
  e('e2',21,1,55),
  e('e3',23,1,70),
  e('e4',26,1,80)
];
const recent=R.derive(rows,{now_ms:Date.parse('2026-09-27T07:00:00.000Z')});
assert.equal(recent.ok,true);
assert.equal(recent.evidence_count,4);
assert.equal(recent.consecutive_successes,3);
assert.equal(recent.retention_state,'STABLE');
assert.equal(recent.forgetting_risk,'LOW');
assert.equal(recent.scheduling_authority,false);
assert.equal(recent.promoted,false);
assert.equal(R.selfValidate(recent).ok,true);

const stale=R.derive(rows,{now_ms:Date.parse('2026-10-25T07:00:00.000Z')});
assert.equal(stale.forgetting_risk,'HIGH');
assert.equal(stale.retention_state,'RETENTION_AT_RISK');
assert.equal(stale.retrievability_estimate<recent.retrievability_estimate,true);

const failed=R.derive([...rows,e('e5',28,0,40)],{now_ms:Date.parse('2026-09-28T07:00:00.000Z')});
assert.equal(failed.retention_state,'UNSTABLE');

const unverified=[{
  ...e('bad',29,1,90),
  verification:null
}];
assert.equal(R.derive(unverified).evidence_count,0);

console.log('RETENTION_STATE_BASELINE_PASS');
