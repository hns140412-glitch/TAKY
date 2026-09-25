'use strict';
const assert=require('node:assert/strict');
const L=require('./evaluation-ledger.js');

const report=(receipt,decision='HOLD',policy='TAKY_ESTIMATOR_PROMOTION_POLICY_V1')=>({
  ok:true,
  authority:'ESTIMATOR_PROMOTION_REVIEW_REPORT',
  policy_version:policy,
  scope:{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'},
  source_kind:'REAL_EVIDENCE',
  evidence_receipt_id:receipt,
  verified_target_count:20,
  dataset_blockers:decision==='HOLD'?['MIN_VERIFIED_TARGETS_NOT_MET']:[],
  candidates:{bkt:{review_eligible:decision!=='HOLD',blockers:[]}},
  promotion_review_available:decision!=='HOLD',
  auto_promotion:false,
  decision
});

let ledger=L.emptyLedger();
const first=L.appendEvaluation(ledger,report('receipt-1','HOLD'),{created_at:'2026-09-25T06:00:00.000Z'});
assert.equal(first.ok,true);
ledger=first.ledger;
assert.equal(first.entry.disposition,'HOLD_RETAINED');
assert.equal(L.validateLedger(ledger).ok,true);

const q=L.reconsiderationQueue(ledger,{
  evidence_receipt_by_scope:{'A::영어::vocabulary':'receipt-2'},
  policy_version:'TAKY_ESTIMATOR_PROMOTION_POLICY_V1'
});
assert.equal(q.length,1);
assert.deepEqual(q[0].reasons,['NEW_EVIDENCE_RECEIPT']);

const second=L.appendEvaluation(ledger,report('receipt-2','HUMAN_REVIEW_AVAILABLE'),{created_at:'2026-09-26T06:00:00.000Z'});
assert.equal(second.ok,true);
ledger=second.ledger;
assert.equal(ledger.entries.length,2);
assert.equal(L.currentProjection(ledger)[0].retained_history_count,2);

const rejected=L.appendDecision(ledger,{
  evaluation_entry_id:second.entry.entry_id,
  decision:'REJECTED',
  reviewer:'HUMAN',
  rationale:'needs more real evidence',
  created_at:'2026-09-26T06:10:00.000Z'
});
assert.equal(rejected.ok,true);
ledger=rejected.ledger;
assert.equal(ledger.entries.at(-1).disposition,'REJECTED_RETAINED');
assert.equal(ledger.entries.some(e=>e.entry_id===second.entry.entry_id),true,'source evaluation must be retained');

const third=L.appendEvaluation(ledger,report('receipt-3','HUMAN_REVIEW_AVAILABLE','TAKY_ESTIMATOR_PROMOTION_POLICY_V2'),{created_at:'2026-09-27T06:00:00.000Z'});
ledger=third.ledger;
const promoted=L.appendDecision(ledger,{
  evaluation_entry_id:third.entry.entry_id,
  decision:'PROMOTED',
  reviewer:'HUMAN',
  rationale:'passes v2 review',
  created_at:'2026-09-27T06:10:00.000Z'
});
assert.equal(promoted.ok,true);
assert.equal(L.validateLedger(promoted.ledger).ok,true);

const impossible=L.appendDecision(first.ledger,{
  evaluation_entry_id:first.entry.entry_id,
  decision:'PROMOTED',
  reviewer:'HUMAN'
});
assert.equal(impossible.ok,false);
assert.equal(impossible.reason,'PROMOTION_REVIEW_NOT_AVAILABLE');

console.log('LEARNING_EVALUATION_LEDGER_PASS');
