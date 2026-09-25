'use strict';
const assert=require('node:assert/strict');
const R=require('./real-evidence-receipt.js');
const Replay=require('../replay/replay-dataset.js');

const ev=(id,day,outcome,instrument='hide-v1')=>({
  event_id:id,
  observed_at:`2026-09-${String(day).padStart(2,'0')}T07:00:00.000Z`,
  member_id:'A',
  subject:'영어',
  concept_skill_target:'vocabulary',
  evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',
  source_app:'hide-seek',
  instrument_version:instrument,
  verified_outcome:outcome,
  verification:{
    authority:'LEARNING_VERIFICATION_RECEIPT',
    receipt_id:'vr-'+id,
    verifier_type:'RETRIEVAL_EXACT_MATCH',
    verifier_version:'HIDE_CODE_RED_V1'
  },
  memory:{average_strength:outcome?75:40}
});

const rows=[ev('e1',20,0),ev('e2',21,1),ev('e3',23,1)];
const issued=R.issueBatchReceipt(rows,{created_at:'2026-09-25T00:00:00.000Z'});
assert.equal(issued.ok,true);
assert.equal(issued.receipt.authority,'REAL_LEARNING_EVIDENCE_RECEIPT');
assert.equal(issued.receipt.event_count,3);
assert.equal(issued.receipt.instrument_versions.length,1);
assert.equal(R.validateBatchReceipt(issued.receipt,rows).ok,true);

const opts=R.replayOptions(issued.receipt);
assert.equal(opts.ok,true);
const built=Replay.buildDataset(rows,{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'},{
  ...opts.options,
  evidence_receipt:issued.receipt,
  created_at:'2026-09-25T00:00:00.000Z'
});
assert.equal(built.ok,true);
assert.equal(built.dataset.provenance.source_kind,'REAL_EVIDENCE');
assert.equal(built.dataset.provenance.evidence_receipt_id,issued.receipt.receipt_id);

const tampered=JSON.parse(JSON.stringify(rows));
tampered[0].verified_outcome=1;
assert.equal(R.validateBatchReceipt(issued.receipt,tampered).ok,false);
assert.equal(R.validateBatchReceipt(issued.receipt,tampered).issues.includes('EVIDENCE_DIGEST_MISMATCH'),true);

const mixed=[...rows,{...ev('e4',24,1),member_id:'B'}];
assert.equal(R.issueBatchReceipt(mixed).reason,'SCOPE_MIXED');

const duplicate=[...rows,ev('e2',25,1)];
assert.equal(R.issueBatchReceipt(duplicate).reason,'DUPLICATE_EVENT_ID');

const unverified=[...rows,{...ev('e5',25,1),verification:null}];
assert.equal(R.issueBatchReceipt(unverified).reason,'INVALID_VERIFIED_EVIDENCE');

console.log('REAL_LEARNING_EVIDENCE_RECEIPT_PASS');

const first=R.issueBatchReceipt([ev('c1',26,1),ev('c2',27,0)],{created_at:'2026-09-27T00:00:00.000Z'});
assert.equal(first.ok,true);
const second=R.extendBatchReceipt(first.receipt,first.canonical_evidence,[ev('c3',28,1)],{created_at:'2026-09-28T00:00:00.000Z'});
assert.equal(second.ok,true);
assert.equal(second.receipt.parent_receipt_id,first.receipt.receipt_id);
assert.equal(second.receipt.parent_evidence_digest_sha256,first.receipt.evidence_digest_sha256);
assert.equal(second.receipt.event_count,3);
assert.equal(second.receipt.incremental_event_count,1);
assert.equal(R.validateReceiptChain([first.receipt,second.receipt]).ok,true);

const overlap=R.extendBatchReceipt(first.receipt,first.canonical_evidence,[ev('c2',29,1)]);
assert.equal(overlap.ok,false);
assert.equal(overlap.reason,'EVENT_ALREADY_RECEIPTED');

const broken=JSON.parse(JSON.stringify(second.receipt));
broken.parent_receipt_id='wrong';
assert.equal(R.validateReceiptChain([first.receipt,broken]).ok,false);
assert.equal(R.validateReceiptChain([first.receipt,broken]).issues[0].startsWith('PARENT_RECEIPT_MISMATCH'),true);

const targetRows=[
  {...ev('t1',29,1),learning_target_id:'word:essential'},
  {...ev('t2',30,0),learning_target_id:'word:except'}
];
const targetIssued=R.issueBatchReceipt(targetRows,{created_at:'2026-09-30T00:00:00.000Z'});
assert.equal(targetIssued.ok,true);
const targetTampered=JSON.parse(JSON.stringify(targetRows));
targetTampered[0].learning_target_id='word:changed';
const targetCheck=R.validateBatchReceipt(targetIssued.receipt,targetTampered);
assert.equal(targetCheck.ok,false);
assert.equal(targetCheck.issues.includes('EVIDENCE_DIGEST_MISMATCH'),true);
