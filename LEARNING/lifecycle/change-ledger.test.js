'use strict';
const assert=require('node:assert/strict');
const L=require('./change-ledger.js');

let ledger=L.emptyLedger();
const proposed=L.appendChange(ledger,{
  type:'PEDAGOGY_RULE',
  title:'Add metacognitive self-reflection evidence',
  description:'Capture easy/hard, hint-assisted recall and confusion self-report as evidence.',
  state:'HOLD',
  owner:'LEARNING_ENGINE_CORE',
  source_ref:'deep-review-2026-09-25',
  blockers:['EVIDENCE_SCHEMA_NOT_YET_IMPLEMENTED'],
  destination:'LEARNING/evidence'
});
assert.equal(proposed.ok,true);
ledger=proposed.ledger;
assert.equal(proposed.entry.state,'HOLD');
assert.equal(L.pending(ledger).length,1);

const deferred=L.transition(ledger,proposed.entry.entry_id,'DEFERRED',{
  blockers:['WAIT_FOR_CANONICAL_EVIDENCE_V2'],
  created_at:'2026-09-26T00:00:00.000Z'
});
assert.equal(deferred.ok,true);
ledger=deferred.ledger;
assert.equal(ledger.entries.length,2);
assert.equal(L.currentProjection(ledger)[0].state,'DEFERRED');
assert.equal(L.currentProjection(ledger)[0].retained_history_count,2);

const applied=L.transition(ledger,deferred.entry.entry_id,'APPLIED',{
  evidence_refs:['commit:abc123'],
  destination:'LEARNING/evidence/self-reflection.js',
  created_at:'2026-09-27T00:00:00.000Z'
});
assert.equal(applied.ok,true);
ledger=applied.ledger;
assert.equal(L.currentProjection(ledger)[0].state,'APPLIED');
assert.equal(L.pending(ledger).length,0);
assert.equal(L.validateLedger(ledger).ok,true);

const rejected=L.appendChange(ledger,{
  type:'ESTIMATOR',
  title:'Experimental opaque DKT model',
  state:'REJECTED',
  owner:'LEARNING_ENGINE_CORE',
  source_ref:'benchmark:x',
  blockers:['INSUFFICIENT_EXPLAINABILITY']
});
assert.equal(rejected.ok,true);
assert.equal(rejected.entry.retention,'IMMUTABLE_HISTORY');
assert.equal(rejected.ledger.entries.some(x=>x.title==='Experimental opaque DKT model'),true);

console.log('LEARNING_CHANGE_LEDGER_PASS');
