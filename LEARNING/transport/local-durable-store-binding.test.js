'use strict';
const assert=require('node:assert/strict');
const os=require('node:os');
const path=require('node:path');
const fsp=require('node:fs').promises;
const {LocalJsonStrongStore}=require('./local-json-strong-store.js');
const Evidence=require('./durable-evidence-store-adapter.js');
const Growth=require('./durable-growth-strategy-store-adapter.js');

const packet=id=>({
  packet_id:'hide-seek:'+id,source_app:'hide-seek',
  context:{family_id:'F1',member_id:'A',subject:'영어',concept_skill_target:'vocabulary'},
  event:{source:'hide-seek',event_id:id,occurred_at:'2026-09-26T00:00:00.000Z',event_type:'RETRIEVAL_RESULT',payload:{
    member_id:'A',subject:'영어',concept_skill_target:'vocabulary',instrument_version:'HIDE_CODE_RED_V1',
    verification_candidate:{verifier_type:'RETRIEVAL_EXACT_MATCH',verifier_version:'HIDE_CODE_RED_V1',basis:'DETERMINISTIC_LOCAL_MATCH',outcome:1,reference_id:'word:'+id}
  }}
});
const receipt=id=>({
  authority:'REAL_LEARNING_EVIDENCE_RECEIPT',receipt_id:'real-evidence:'+id,evidence_digest_sha256:'digest-'+id,
  raw_evidence_immutable:true,scope:{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'}
});
const feedback=outcome=>({
  ok:true,
  learning_strategy_feedback:{authority:'LEARNING_OUTCOME_FEEDBACK_ONLY',verified_target:true,outcome,observation_only:false,suggested_adjustments:[]},
  mining_strategy_feedback_candidate:null
});

(async()=>{
  const root=await fsp.mkdtemp(path.join(os.tmpdir(),'taky-local-store-'));
  try{
    const store=await new LocalJsonStrongStore(root).init();
    const first=await Evidence.ingestPacket(store,packet('e1'));
    assert.equal(first.ok,true);
    assert.equal(first.durable_store.consistency,'strong');
    assert.equal(first.durable_store.conditional_write,'onlyIfNew');

    const growth=await Growth.appendFeedback(store,{
      family_id:'F1',real_evidence_receipt:receipt('g1'),outcome_feedback:feedback(1),recorded_at:'2026-09-26T00:10:00.000Z'
    });
    assert.equal(growth.ok,true);
    assert.equal(growth.entry.raw_evidence_copied,false);
    assert.equal(growth.entry.promotion_authority,false);

    const reloaded=await new LocalJsonStrongStore(root).init();
    const evidenceState=await reloaded.getWithMetadata('families/F1/members/A/learning-engine/state-v1',{type:'json',consistency:'strong'});
    const growthState=await reloaded.getWithMetadata('families/F1/members/A/learning-engine/growth-strategy-v1',{type:'json',consistency:'strong'});
    assert.ok(evidenceState&&evidenceState.etag);
    assert.ok(growthState&&growthState.etag);
    assert.equal(growthState.data.entries.length,1);

    const dup=await Growth.appendFeedback(reloaded,{
      family_id:'F1',real_evidence_receipt:receipt('g1'),outcome_feedback:feedback(1),recorded_at:'2026-09-26T00:10:00.000Z'
    });
    assert.equal(dup.ok,true);
    assert.equal(dup.idempotent,true);

    const conflict=await Growth.appendFeedback(reloaded,{
      family_id:'F1',real_evidence_receipt:receipt('g1'),outcome_feedback:feedback(0),recorded_at:'2026-09-26T00:20:00.000Z'
    });
    assert.equal(conflict.ok,false);
    assert.equal(conflict.reason,'RECEIPT_FEEDBACK_CONFLICT');
    console.log('LOCAL_CONTROLLED_DURABLE_STORE_BINDING_PASS');
  }finally{await fsp.rm(root,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exit(1);});
