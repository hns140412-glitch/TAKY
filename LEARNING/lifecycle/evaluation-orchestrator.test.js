'use strict';
const assert=require('node:assert/strict');
const O=require('./evaluation-orchestrator.js');
const L=require('./evaluation-ledger.js');

const bench={
  ok:true,
  source_kind:'REAL_EVIDENCE',
  evidence_receipt_id:'receipt-1',
  scope:{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'},
  verified_target_count:10,
  benchmark:{
    total_points:9,
    stable_instrument_points:9,
    instrument_change_points:0,
    brier:{observational:0.20,bkt:0.19,dsr:0.21},
    points:[]
  }
};
let ledger=L.emptyLedger();
const first=O.evaluateAndRecord(ledger,bench,{created_at:'2026-09-25T06:00:00.000Z'});
assert.equal(first.ok,true);
assert.equal(first.report.decision,'HOLD');
assert.equal(first.ledger_entry.disposition,'HOLD_RETAINED');
assert.equal(O.selfValidate(first).ok,true);
ledger=first.ledger;

const repeat=O.evaluateAndRecord(ledger,bench,{created_at:'2026-09-25T06:00:00.000Z'});
assert.equal(repeat.ok,true);
assert.equal(repeat.deduplicated,true);
assert.equal(repeat.ledger.entries.length,1);

const plan=O.reevaluationPlan(ledger,{'A::영어::vocabulary':'receipt-2'},'TAKY_ESTIMATOR_PROMOTION_POLICY_V1');
assert.equal(plan.ok,true);
assert.equal(plan.pending_count,1);
assert.equal(plan.invariant,'NO_HOLD_OR_REVIEW_RESULT_IS_DROPPED');
assert.equal(plan.queue[0].reasons.includes('NEW_EVIDENCE_RECEIPT'),true);

console.log('LEARNING_EVALUATION_ORCHESTRATOR_PASS');
