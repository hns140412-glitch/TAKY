'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const L=require('./change-ledger.js');

const p=path.join(__dirname,'..','..','CURRENT','LEARNING_ENGINE_CHANGE_LEDGER_CURRENT.json');
const ledger=JSON.parse(fs.readFileSync(p,'utf8'));

assert.equal(L.validateLedger(ledger).ok,true);
const projection=L.currentProjection(ledger);
const titles=new Set(projection.map(x=>x.title));

for(const required of [
  'Metacognitive self-reflection evidence',
  'Pedagogical feedback intent',
  'Forgetting and retention estimator',
  'Calibrated BKT estimator',
  'Concept prerequisite and dependency graph'
]){
  assert.equal(titles.has(required),true,'missing retained change: '+required);
}
assert.equal(L.pending(ledger).length>=5,true);
assert.equal(ledger.entries.every(x=>x.retention==='IMMUTABLE_HISTORY'),true);

console.log('LEARNING_CHANGE_LEDGER_CURRENT_PASS');
