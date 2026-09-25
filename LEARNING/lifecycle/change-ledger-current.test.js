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
  'Concept prerequisite and dependency graph',
  'Extract remaining Ready-embedded learning logic'
]){
  assert.equal(titles.has(required),true,'missing retained change: '+required);
}
const pending=L.pending(ledger);
assert.equal(pending.length>=2,true);
assert.equal(pending.some(x=>x.title==='Forgetting and retention estimator'),true);
assert.equal(pending.some(x=>x.title==='Calibrated BKT estimator'),true);
assert.equal(pending.some(x=>x.title==='Extract remaining Ready-embedded learning logic'),true);
assert.equal(pending.some(x=>x.title==='Data-derived prerequisite relation candidates'),false);

const reflectionHistory=ledger.entries.filter(x=>x.title==='Metacognitive self-reflection evidence');
assert.equal(reflectionHistory.some(x=>x.state==='HOLD'),true);
assert.equal(reflectionHistory.some(x=>x.state==='APPLIED'),true);
const feedbackHistory=ledger.entries.filter(x=>x.title==='Pedagogical feedback intent');
assert.equal(feedbackHistory.some(x=>x.state==='HOLD'),true);
assert.equal(feedbackHistory.some(x=>x.state==='APPLIED'),true);
const graphHistory=ledger.entries.filter(x=>x.title==='Concept prerequisite and dependency graph');
assert.equal(graphHistory.some(x=>x.state==='DEFERRED'),true);
assert.equal(graphHistory.some(x=>x.state==='APPLIED'),true);
assert.equal(pending.some(x=>x.title==='Concept prerequisite and dependency graph'),false);
assert.equal(L.currentProjection(ledger).find(x=>x.title==='Concept prerequisite and dependency graph').state,'APPLIED');
const dataCandidateHistory=ledger.entries.filter(x=>x.title==='Data-derived prerequisite relation candidates');
assert.equal(dataCandidateHistory.some(x=>x.state==='HOLD'),true);
assert.equal(dataCandidateHistory.some(x=>x.state==='APPLIED'),true);
assert.equal(L.currentProjection(ledger).find(x=>x.title==='Data-derived prerequisite relation candidates').state,'APPLIED');
assert.equal(ledger.entries.every(x=>x.retention==='IMMUTABLE_HISTORY'),true);

console.log('LEARNING_CHANGE_LEDGER_CURRENT_PASS');
