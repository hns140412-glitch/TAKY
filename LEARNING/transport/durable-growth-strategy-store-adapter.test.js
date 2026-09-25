'use strict';
const assert=require('node:assert/strict');
const Adapter=require('./durable-growth-strategy-store-adapter.js');

function makeStore(){
  return {
    row:null,seq:0,conflict:false,
    async getWithMetadata(){return this.row?{data:this.row.data,etag:this.row.etag}:null;},
    async setJSON(key,value,opts={}){
      if(this.conflict){
        this.conflict=false;
        if(this.row)this.row={...this.row,etag:'e'+(++this.seq)};
        return {modified:false};
      }
      if(opts.onlyIfNew&&this.row)return {modified:false};
      if(opts.onlyIfMatch&&this.row?.etag!==opts.onlyIfMatch)return {modified:false};
      const etag='e'+(++this.seq);
      this.row={key,data:value,etag};
      return {modified:true,etag};
    }
  };
}

const receipt=id=>({
  authority:'REAL_LEARNING_EVIDENCE_RECEIPT',
  receipt_id:'real-evidence:'+id,
  evidence_digest_sha256:'digest-'+id,
  raw_evidence_immutable:true,
  scope:{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'}
});
const feedback=outcome=>({
  ok:true,
  learning_strategy_feedback:{
    authority:'LEARNING_OUTCOME_FEEDBACK_ONLY',
    verified_target:true,
    outcome,
    observation_only:false,
    suggested_adjustments:outcome?['PRESERVE_SUCCESSFUL_STRATEGY']:['INCREASE_TARGETED_RECOVERY']
  },
  mining_strategy_feedback_candidate:null
});

(async()=>{
  const store=makeStore();
  const packet={
    family_id:'F1',
    real_evidence_receipt:receipt('1'),
    outcome_feedback:feedback(0),
    recorded_at:'2026-09-26T00:00:00.000Z'
  };
  assert.equal(Adapter.stateKey(packet),'families/F1/members/A/learning-engine/growth-strategy-v1');

  const first=await Adapter.appendFeedback(store,packet);
  assert.equal(first.ok,true);
  assert.equal(first.durable_store.conditional_write,'onlyIfNew');
  assert.equal(first.entry.promotion_authority,false);
  assert.equal(Adapter.selfValidate(first).ok,true);

  const duplicate=await Adapter.appendFeedback(store,packet);
  assert.equal(duplicate.ok,true);
  assert.equal(duplicate.idempotent,true);
  assert.equal(duplicate.durable_store.conditional_write,'none-idempotent');

  store.conflict=true;
  const second=await Adapter.appendFeedback(store,{
    family_id:'F1',
    real_evidence_receipt:receipt('2'),
    outcome_feedback:feedback(1),
    recorded_at:'2026-09-26T01:00:00.000Z'
  });
  assert.equal(second.ok,true);
  assert.equal(second.durable_store.attempt,2);
  assert.equal(second.durable_store.conditional_write,'onlyIfMatch');

  for(let i=3;i<=5;i++){
    const r=await Adapter.appendFeedback(store,{
      family_id:'F1',
      real_evidence_receipt:receipt(String(i)),
      outcome_feedback:feedback(i%2),
      recorded_at:`2026-09-26T0${i}:00:00.000Z`
    });
    assert.equal(r.ok,true);
  }

  const evaluation=await Adapter.evaluateScope(store,{
    family_id:'F1',
    member_id:'A',
    scope:{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'}
  },{min_receipts:5});
  assert.equal(evaluation.ok,true);
  assert.equal(evaluation.evaluation.receipt_count,5);
  assert.equal(evaluation.evaluation.eligible_for_human_strategy_review,true);
  assert.equal(evaluation.evaluation.promotion_authority,false);
  assert.equal(evaluation.evaluation.strategy_change_authorized,false);

  const missing=await Adapter.appendFeedback(store,{member_id:'A'});
  assert.equal(missing.ok,false);
  assert.equal(missing.reason,'FAMILY_MEMBER_SCOPE_REQUIRED');

  console.log('DURABLE_GROWTH_STRATEGY_STORE_ADAPTER_PASS');
})().catch(e=>{console.error(e);process.exit(1);});
