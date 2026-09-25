'use strict';
const assert=require('node:assert/strict');
const B=require('./estimator-benchmark.js');

const row=(id,day,outcome,strength=undefined,instrument='hide-v1')=>({
  event_id:id,
  observed_at:`2026-09-${String(day).padStart(2,'0')}T07:00:00.000Z`,
  verified_outcome:outcome,
  memory_strength:strength,
  instrument_version:instrument
});

const seq=[
  row('e1',20,0,35),
  row('e2',21,1,55),
  row('e3',23,1,68),
  row('e4',26,1,76),
  row('e5',29,0,58),
  row('e6',30,1,72)
];

const r=B.timeHeldOut(seq,{min_history:1});
assert.equal(r.ok,true);
assert.equal(r.promotion_status,'NOT_ELIGIBLE_FROM_FIXTURE_ONLY');
assert.equal(r.instrument_change_points,0);
assert.equal(r.stable_instrument_points,r.total_points);
assert.equal(B.selfValidate(r).ok,true);
for(const v of Object.values(r.brier))assert.equal(Number.isFinite(v),true);

const mixed=B.timeHeldOut([...seq,row('e7',31,1,80,'hide-v2')],{min_history:1});
assert.equal(mixed.instrument_change_points,1);
assert.equal(mixed.points.at(-1).instrument_changed,true);
assert.equal(B.selfValidate(mixed).ok,true);

const sparse=B.timeHeldOut([row('s1',20,1,80),row('s2',24,0,40)],{min_history:1});
assert.equal(sparse.total_points,1);
assert.equal(sparse.points[0].predictions.bkt.confidence,'VERY_LOW');
assert.equal(sparse.points[0].predictions.dsr.confidence,'VERY_LOW');

const bad=B.timeHeldOut([{event_id:'x',observed_at:'bad',verified_outcome:2,instrument_version:''}]);
assert.equal(bad.ok,false);
assert.equal(bad.reason,'INVALID_SEQUENCE');

const coldBkt=B.bktCandidate([]);
const coldDsr=B.dsrMemoryCandidate([]);
assert.equal(coldBkt.promoted,false);
assert.equal(coldDsr.promoted,false);
assert.equal(coldDsr.note.includes('cold-start'),true);

console.log('LEARNING_ESTIMATOR_BENCHMARK_PASS');

const targetSeq=[
  {...row('t1',20,0,35),learning_target_id:'word:a'},
  {...row('t2',21,1,55),learning_target_id:'word:b'},
  {...row('t3',22,1,70),learning_target_id:'word:c'}
];
const targetBench=B.timeHeldOut(targetSeq,{min_history:1});
assert.equal(targetBench.points[0].target_learning_target_id,'word:b');
assert.equal(targetBench.points[1].target_learning_target_id,'word:c');
