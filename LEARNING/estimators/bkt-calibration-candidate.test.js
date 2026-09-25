'use strict';
const assert=require('node:assert/strict');
const B=require('./bkt-calibration-candidate.js');

const row=(id,day,outcome)=>({
  event_id:id,
  observed_at:`2026-09-${String(day).padStart(2,'0')}T07:00:00.000Z`,
  verified_outcome:outcome,
  instrument_version:'hide-v1'
});

const sparse=[row('s1',1,0),row('s2',2,1),row('s3',3,1)];
const sparseResult=B.calibrate(sparse,{min_train:8});
assert.equal(sparseResult.ok,true);
assert.equal(sparseResult.status,'INSUFFICIENT_TRAINING_EVIDENCE');
assert.equal(sparseResult.parameters,null);
assert.equal(sparseResult.promoted,false);

const seq=[
  row('e1',1,0),row('e2',2,0),row('e3',3,1),row('e4',4,1),
  row('e5',5,1),row('e6',6,1),row('e7',7,0),row('e8',8,1),
  row('e9',9,1),row('e10',10,1),row('e11',11,1),row('e12',12,0),
  row('e13',13,1),row('e14',14,1),row('e15',15,1),row('e16',16,1)
];

const c1=B.calibrate(seq.slice(0,12),{min_train:8});
const c2=B.calibrate(seq.slice(0,12),{min_train:8});
assert.equal(c1.status,'CALIBRATED_CANDIDATE');
assert.deepEqual(c1.parameters,c2.parameters,'calibration must be deterministic');
assert.equal(c1.calibration_provenance.train_only,true);
assert.equal(c1.calibration_provenance.future_holdout_untouched,true);
assert.equal(B.selfValidate(c1).ok,true);

const evalResult=B.benchmarkWithCalibration(seq,{min_train:8,holdout_fraction:0.25});
assert.equal(evalResult.ok,true);
assert.equal(evalResult.status,'CALIBRATED_AND_HELD_OUT_EVALUATED');
assert.equal(evalResult.train_count,12);
assert.equal(evalResult.holdout_count,4);
assert.equal(evalResult.calibration.training_count,12);
assert.equal(evalResult.benchmark.total_points,4);
assert.equal(evalResult.promoted,false);
assert.equal(evalResult.scheduling_authority,false);
assert.equal(B.selfValidate(evalResult).ok,true);

console.log('BKT_CALIBRATION_CANDIDATE_PASS');
