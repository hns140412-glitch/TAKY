'use strict';
const assert=require('node:assert/strict');
const Trigger=require('./real-evidence-evaluation-trigger.js');
const Receipt=require('../receipts/real-evidence-receipt.js');
const Ledger=require('./evaluation-ledger.js');

const ev=(id,day,outcome)=>({
  event_id:id,
  learning_target_id:'word:'+id,
  observed_at:`2026-09-${String(day).padStart(2,'0')}T07:00:00.000Z`,
  member_id:'A',
  subject:'영어',
  concept_skill_target:'vocabulary',
  evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',
  source_app:'hide-seek',
  instrument_version:'HIDE_CODE_RED_V1',
  verified_outcome:outcome,
  verification:{
    authority:'LEARNING_VERIFICATION_RECEIPT',
    receipt_id:'vr-'+id,
    verifier_type:'RETRIEVAL_EXACT_MATCH',
    verifier_version:'HIDE_CODE_RED_V1'
  },
  memory:{average_strength:outcome?75:40}
});

let ledger=Ledger.emptyLedger();

const one=[ev('a1',20,0)];
const r1=Receipt.issueBatchReceipt(one,{created_at:'2026-09-20T08:00:00.000Z'});
assert.equal(r1.ok,true);
const first=Trigger.evaluateReceipt({
  ledger,
  receipt:r1.receipt,
  canonical_evidence:r1.canonical_evidence,
  created_at:'2026-09-20T08:01:00.000Z'
});
assert.equal(first.ok,true);
assert.equal(first.benchmark_status,'HOLD_BELOW_REPLAY_MINIMUM');
assert.equal(first.report.decision,'HOLD');
assert.equal(first.ledger_entry.disposition,'HOLD_RETAINED');
assert.equal(Trigger.selfValidate(first).ok,true);
ledger=first.ledger;

const repeat=Trigger.evaluateReceipt({
  ledger,
  receipt:r1.receipt,
  canonical_evidence:r1.canonical_evidence,
  created_at:'2026-09-20T08:01:00.000Z'
});
assert.equal(repeat.ok,true);
assert.equal(repeat.deduplicated,true);
assert.equal(repeat.ledger.entries.length,1);

const two=[...one,ev('a2',21,1)];
const r2=Receipt.issueBatchReceipt(two,{created_at:'2026-09-21T08:00:00.000Z'});
assert.equal(r2.ok,true);
const second=Trigger.evaluateReceipt({
  ledger,
  receipt:r2.receipt,
  canonical_evidence:r2.canonical_evidence,
  created_at:'2026-09-21T08:01:00.000Z'
});
assert.equal(second.ok,true);
assert.equal(second.report.decision,'HOLD');
assert.equal(second.ledger.entries.length,2);
assert.equal(second.ledger.entries[0].evidence_receipt_id,r1.receipt.receipt_id);
assert.equal(second.ledger.entries[1].evidence_receipt_id,r2.receipt.receipt_id);
assert.equal(Ledger.validateLedger(second.ledger).ok,true);

const tampered=JSON.parse(JSON.stringify(two));
tampered[0].learning_target_id='word:tampered';
const bad=Trigger.evaluateReceipt({
  ledger:second.ledger,
  receipt:r2.receipt,
  canonical_evidence:tampered
});
assert.equal(bad.ok,false);
assert.equal(bad.reason,'REAL_EVIDENCE_RECEIPT_INVALID');

console.log('REAL_EVIDENCE_EVALUATION_TRIGGER_PASS');
