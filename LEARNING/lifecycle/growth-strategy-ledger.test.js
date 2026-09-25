'use strict';
const assert=require('node:assert/strict');
const Ledger=require('./growth-strategy-ledger.js');

const receipt={
  authority:'REAL_LEARNING_EVIDENCE_RECEIPT',
  receipt_id:'real-evidence:r1',
  evidence_digest_sha256:'abc',
  raw_evidence_immutable:true,
  scope:{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'}
};
const feedback={
  ok:true,
  learning_strategy_feedback:{
    authority:'LEARNING_OUTCOME_FEEDBACK_ONLY',
    verified_target:true,
    outcome:0,
    observation_only:false,
    suggested_adjustments:['INCREASE_TARGETED_RECOVERY']
  },
  mining_strategy_feedback_candidate:{
    authority:'MINING_STRATEGY_FEEDBACK_CANDIDATE_ONLY',
    gap_id:'g1',
    acquisition_strategy_change_authorized:false,
    canonical_classification_change_authorized:false,
    promotion_authorized:false,
    requires_mining_evaluation:true
  }
};

let state=Ledger.emptyLedger();
const first=Ledger.append(state,{
  real_evidence_receipt:receipt,
  outcome_feedback:feedback,
  prior_gap_id:'g1',
  index_gap_decision:'MINING_REQUEST',
  recorded_at:'2026-09-26T00:00:00.000Z'
});
assert.equal(first.ok,true);
assert.equal(first.idempotent,false);
assert.equal(first.entry.promotion_authority,false);
assert.equal(first.entry.raw_evidence_copied,false);
assert.equal(first.entry.source_evidence.receipt_id,'real-evidence:r1');
assert.equal(Ledger.selfValidate(first.ledger).ok,true);

const again=Ledger.append(first.ledger,{
  real_evidence_receipt:receipt,
  outcome_feedback:feedback,
  prior_gap_id:'g1',
  index_gap_decision:'MINING_REQUEST',
  recorded_at:'2026-09-26T01:00:00.000Z'
});
assert.equal(again.ok,true);
assert.equal(again.idempotent,true);
assert.equal(again.ledger.entries.length,1);

const conflicting=JSON.parse(JSON.stringify(feedback));
conflicting.learning_strategy_feedback.outcome=1;
const conflict=Ledger.append(first.ledger,{
  real_evidence_receipt:receipt,
  outcome_feedback:conflicting
});
assert.equal(conflict.ok,false);
assert.equal(conflict.reason,'RECEIPT_FEEDBACK_CONFLICT');

let multi=first.ledger;
for(let i=2;i<=5;i++){
  const r={...receipt,receipt_id:'real-evidence:r'+i,evidence_digest_sha256:'d'+i};
  const f=JSON.parse(JSON.stringify(feedback));
  f.learning_strategy_feedback.outcome=i%2;
  const next=Ledger.append(multi,{real_evidence_receipt:r,outcome_feedback:f,recorded_at:`2026-09-26T0${i}:00:00.000Z`});
  assert.equal(next.ok,true);
  multi=next.ledger;
}
const review=Ledger.evaluate(multi,{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'},{min_receipts:5});
assert.equal(review.receipt_count,5);
assert.equal(review.verified_outcome_count,5);
assert.equal(review.eligible_for_human_strategy_review,true);
assert.equal(review.promotion_authority,false);
assert.equal(review.strategy_change_authorized,false);

const badReceipt={...receipt,raw_evidence_immutable:false};
const bad=Ledger.append(Ledger.emptyLedger(),{real_evidence_receipt:badReceipt,outcome_feedback:feedback});
assert.equal(bad.ok,false);

console.log('GROWTH_STRATEGY_LEDGER_PASS');
