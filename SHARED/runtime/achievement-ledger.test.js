'use strict';
const assert=require('node:assert/strict');
const L=require('./achievement-ledger.js');

const base=L.empty('C1');
const award={
 achievement_id:'achievement:R1:C1:E1',member_id:'C1',badge_id:'B1',rule_id:'R1',
 source_event_id:'E1',source_event_type:'TASK_COMPLETED',awarded_at:'2026-09-26T00:00:00.000Z'
};
const first=L.append(base,award);
assert.equal(first.ok,true);
assert.equal(first.reason,'RECORDED');
assert.equal(first.ledger.entries.length,1);
assert.equal(first.ledger.revision,1);

const dup=L.append(first.ledger,award);
assert.equal(dup.reason,'IDEMPOTENT_ALREADY_RECORDED');
assert.equal(dup.ledger.entries.length,1);

const sameSource=L.append(first.ledger,{...award,achievement_id:'achievement:R2:C1:E1',rule_id:'R2'});
assert.equal(sameSource.reason,'IDEMPOTENT_SOURCE_ALREADY_RECORDED');
assert.equal(sameSource.ledger.entries.length,1);

const wrong=L.append(first.ledger,{...award,achievement_id:'X2',member_id:'C2',source_event_id:'E2'});
assert.equal(wrong.ok,false);
assert.equal(wrong.reason,'ACHIEVEMENT_MEMBER_SCOPE_MISMATCH');

assert.equal(L.hasAward(first.ledger,'B1','E1'),true);
assert.equal(L.byBadge(first.ledger,'B1').length,1);

console.log('TAKY_ACHIEVEMENT_LEDGER_V1_PASS');
