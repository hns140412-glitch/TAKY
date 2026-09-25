'use strict';
const assert=require('node:assert/strict');

const Receipt=require('../receipts/real-evidence-receipt.js');
const Feedback=require('./outcome-growth-feedback.js');
const Store=require('../transport/durable-growth-strategy-store-adapter.js');

function makeStore(){
  return {
    row:null,seq:0,
    async getWithMetadata(){return this.row?{data:this.row.data,etag:this.row.etag}:null;},
    async setJSON(key,value,opts={}){
      if(opts.onlyIfNew&&this.row)return {modified:false};
      if(opts.onlyIfMatch&&this.row?.etag!==opts.onlyIfMatch)return {modified:false};
      const etag='e'+(++this.seq);
      this.row={key,data:value,etag};
      return {modified:true,etag};
    }
  };
}

(async()=>{
  const canonical=[{
    event_id:'evt-1',
    observed_at:'2026-09-26T00:00:00.000Z',
    member_id:'A',
    subject:'영어',
    concept_skill_target:'vocabulary',
    learning_target_id:'word:example',
    evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',
    source_app:'hide-seek',
    instrument_version:'HIDE_CODE_RED_V1',
    verified_outcome:0,
    verification:{
      authority:'LEARNING_VERIFICATION_RECEIPT',
      receipt_id:'vr:evt-1:v1',
      verifier_type:'RETRIEVAL_EXACT_MATCH',
      verifier_version:'v1'
    }
  }];

  const issued=Receipt.issueBatchReceipt(canonical,{
    receipt_id:'real-evidence:e2e-1',
    created_at:'2026-09-26T00:01:00.000Z'
  });
  assert.equal(issued.ok,true);
  assert.equal(issued.receipt.raw_evidence_immutable,true);

  const feedback=Feedback.derive({
    outcome:{
      verified_outcome:0,
      verification:{authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'vr:evt-1:v1'},
      assistance:'ASSISTED',
      assisted:true,
      attempt_count:2,
      source_app:'hide-seek',
      learning_target_id:'word:example'
    },
    prior_decision:{execution_status:'PEDAGOGICAL_ACTION_AVAILABLE'},
    prior_evidence_gap:{
      gap_id:'A:영어:vocabulary:REFERENCE_EVIDENCE_REQUIRED:LE-F01',
      gap_type:'REFERENCE_EVIDENCE_REQUIRED',
      scope:{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'}
    },
    index_gap_route:{decision:'MINING_REQUEST',index_sufficient:false}
  });
  assert.equal(feedback.ok,true);
  assert.equal(feedback.learning_strategy_feedback.verified_target,true);
  assert.equal(feedback.mining_strategy_feedback_candidate.promotion_authorized,false);

  const store=makeStore();
  const persisted=await Store.appendFeedback(store,{
    family_id:'F1',
    real_evidence_receipt:issued.receipt,
    outcome_feedback:feedback,
    prior_gap_id:'A:영어:vocabulary:REFERENCE_EVIDENCE_REQUIRED:LE-F01',
    index_gap_decision:'MINING_REQUEST',
    recorded_at:'2026-09-26T00:02:00.000Z'
  });
  assert.equal(persisted.ok,true);
  assert.equal(persisted.entry.source_evidence.receipt_id,'real-evidence:e2e-1');
  assert.equal(persisted.entry.raw_evidence_copied,false);
  assert.equal(persisted.entry.promotion_state,'CANDIDATE_ONLY');
  assert.equal(persisted.entry.promotion_authority,false);
  assert.equal(persisted.entry.mining_strategy_feedback_candidate.promotion_authorized,false);

  const evaluation=await Store.evaluateScope(store,{
    family_id:'F1',
    member_id:'A',
    scope:{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'}
  },{min_receipts:1});
  assert.equal(evaluation.evaluation.eligible_for_human_strategy_review,true);
  assert.equal(evaluation.evaluation.promotion_authority,false);
  assert.equal(evaluation.evaluation.strategy_change_authorized,false);

  console.log('REAL_OUTCOME_GROWTH_E2E_PASS');
})().catch(e=>{console.error(e);process.exit(1);});
