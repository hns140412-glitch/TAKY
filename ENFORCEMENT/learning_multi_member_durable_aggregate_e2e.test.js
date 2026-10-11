'use strict';
const assert=require('node:assert/strict');
const fsp=require('node:fs').promises;
const os=require('node:os'),path=require('node:path');
const Evidence=require('../LEARNING/transport/central-learning-http-endpoint.js');
const {LocalJsonStrongStore}=require('../LEARNING/transport/local-json-strong-store.js');
const ServerVerifier=require('../LEARNING/verification/server-specialist-verifier.js');
const DurableAggregate=require('../LEARNING/transport/durable-learning-system-growth-store-adapter.js');

const members=['A','B','C'];
const principal={authenticated:true,principal_id:'PARENT',identity_provider:'TEST',
  families:[{family_id:'F1',self_member_id:'PARENT',authorized_member_ids:members}]};

function packet(member,id,response){
  return {
    packet_id:'hide-seek:'+id,source_app:'hide-seek',
    context:{family_id:'F1',member_id:member,subject:'English',concept_skill_target:'vocabulary',learning_target_id:'word:apple'},
    event:{source:'hide-seek',event_id:id,occurred_at:'2026-10-04T03:45:00.000Z',
      event_type:'RETRIEVAL_ATTEMPT_RESULT',payload:{
        instrument_version:'HIDE_CODE_RED_V1',
        verification_observation:{response_value:response}
      }}
  };
}
function req(body){return {method:'POST',path:'/api/learning/evidence',headers:{authorization:'Bearer validated-bearer-token-001','content-type':'application/json'},body:JSON.stringify(body)}}

(async()=>{
  const dir=await fsp.mkdtemp(path.join(os.tmpdir(),'taky-multi-member-aggregate-'));
  try{
    const store=await new LocalJsonStrongStore(dir).init();
    const verifier=ServerVerifier.create({
      resolveReference:async s=>({
        authority:'SERVER_OWNED_LEARNING_REFERENCE',reference_id:'REF:'+s.learning_target_id,
        source_app:s.source_app,subject:s.subject,concept_skill_target:s.concept_skill_target,
        learning_target_id:s.learning_target_id,verifier_type:s.verifier_type,
        verifier_version:'REF_V1',match_rule:'CASEFOLD_TRIM',expected_values:['apple']
      }),
      resolveHumanReview:async()=>null
    });
    const endpoint=Evidence.create({store,verifyBearerToken:async()=>principal,verifySpecialistEvidence:verifier});

    const patterns={A:['apple','apple'],B:['apple','banana'],C:['banana','banana']};
    for(const m of members){
      for(let i=0;i<2;i++){
        const id=m+'-'+(i+1);
        const out=await endpoint.handle(req(packet(m,id,patterns[m][i])));
        assert.equal(out.status,200,out.body);
        const body=JSON.parse(out.body);
        assert.equal(body.acknowledgement_kind,'REAL_EVIDENCE_RECEIPT');
        assert.equal(body.storage_confirmed,true);
      }
    }

    const rows=[];
    for(const m of members){
      const key='families/F1/members/'+m+'/learning-engine/state-v1';
      const e=await store.getWithMetadata(key,{type:'json',consistency:'strong'});
      assert(e&&e.data,'member state missing '+m);
      const events=Object.values(e.data.scope_receipts||{}).flatMap(x=>x.canonical_evidence||[]).filter(x=>x.verified_outcome===0||x.verified_outcome===1);
      assert.equal(events.length,2,'verified durable receipt count for '+m);
      rows.push({
        member_id:m,subject:'English',concept_skill_target:'vocabulary',
        verified_outcome_count:events.length,
        success_count:events.filter(x=>x.verified_outcome===1).length,
        failure_count:events.filter(x=>x.verified_outcome===0).length
      });
    }

    const result=await DurableAggregate.appendAggregate(store,{family_id:'F1',rows},{min_members:3,min_verified_outcomes:6});
    assert.equal(result.ok,true);
    assert.equal(result.aggregate.candidate_count,1);
    assert.equal(result.aggregate.candidates[0].member_count,3);
    assert.equal(result.aggregate.candidates[0].verified_outcome_count,6);
    assert.equal(result.review_queue.attempted,true);
    assert.equal(result.review_queue.ok,true);
    assert.equal(result.state.candidates.length,1);
    assert.equal(result.state.candidates[0].promotion_authorized,false);
    assert.equal(DurableAggregate.selfValidate(result).ok,true);
    const serialized=JSON.stringify(result.state);
    for(const m of members)assert.equal(serialized.includes('"member_id":"'+m+'"'),false);

    const persisted=await store.getWithMetadata('families/F1/learning-engine/system-growth-v1',{type:'json',consistency:'strong'});
    assert(persisted&&persisted.data&&persisted.data.candidates&&persisted.data.candidates.length===1);
    console.log('LEARNING_MULTI_MEMBER_DURABLE_AGGREGATE_E2E_PASS');
    console.log(JSON.stringify({member_count:3,verified_outcomes:6,durable:true,review_queue:true,promotion_authorized:false}));
  }finally{await fsp.rm(dir,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exit(1)});
