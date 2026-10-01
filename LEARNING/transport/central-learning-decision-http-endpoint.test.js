'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs').promises;
const os=require('node:os'),path=require('node:path');
const {LocalJsonStrongStore}=require('./local-json-strong-store.js');
const Receipt=require('../receipts/real-evidence-receipt.js');
const Pipeline=require('../intake/specialist-event-pipeline.js');
const Durable=require('./durable-evidence-store-adapter.js');
const Decision=require('./central-learning-decision-http-endpoint.js');

const principal={authenticated:true,principal_id:'PARENT_A',
 families:[{family_id:'F1',self_member_id:'PARENT_A',
 authorized_member_ids:['CHILD_A']}]};
const token='verified-parent-token-0001';
const scope={family_id:'F1',member_id:'CHILD_A',subject:'english',
 concept_skill_target:'vocabulary'};
const req=(input=scope,bearer=token)=>({
 method:'POST',path:Decision.ENDPOINT,
 headers:{Authorization:'Bearer '+bearer,'Content-Type':'application/json'},
 body:JSON.stringify(input)
});
const parse=r=>JSON.parse(r.body);
(async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'central-decision-api-'));
 try{
  const store=await new LocalJsonStrongStore(root).init();
  const endpoint=Decision.create({store,
   verifyBearerToken:async t=>{if(t!==token)throw Error('INVALID');return principal;}});
  const empty=await endpoint.handle(req());
  assert.equal(empty.status,200,JSON.stringify(parse(empty)));
  assert.equal(parse(empty).runtime_result.decision.execution_status,
   'HOLD_FOR_MORE_RELIABLE_INTERPRETATION');
  assert.equal(parse(empty).runtime_result.trace.verified_evidence_count,0);
  assert.equal(parse(empty).observation_only_excluded,true);
  assert.equal(empty.headers['Cache-Control'],'private, no-store, max-age=0');

  const key=Durable.stateKey({context:{family_id:'F1',member_id:'CHILD_A'}});
  const observation=Pipeline.emptyState();
  observation.observation_only=[{event_id:'browser-only',member_id:'CHILD_A',
   subject:'english',concept_skill_target:'vocabulary',
   evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',verified_outcome:1}];
  await store.setJSON(key,observation,{onlyIfNew:true});
  const notPromoted=await endpoint.handle(req());
  assert.equal(notPromoted.status,200,JSON.stringify(parse(notPromoted)));
  assert.equal(parse(notPromoted).runtime_result.trace.verified_evidence_count,0);
  assert.equal(parse(notPromoted).runtime_result.decision.execution_status,
   'HOLD_FOR_MORE_RELIABLE_INTERPRETATION');

  const evidence={event_id:'server-verified-1',
   observed_at:'2026-09-26T12:00:00.000Z',member_id:'CHILD_A',
   subject:'english',concept_skill_target:'vocabulary',
   evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',source_app:'hide-seek',
   instrument_version:'HIDE_CODE_RED_V1',learning_target_id:'n1',assisted:false,verified_outcome:1,
   language_growth_signals:[
    {dimension:'VOCABULARY',outcome:'SUCCESS',assisted:false,target_id:'n1'},
    {dimension:'ENGLISH_THINKING',outcome:'PARTIAL',assisted:false,direct_english:true,target_id:'n1'}
   ],
   verification:{authority:'LEARNING_VERIFICATION_RECEIPT',
    receipt_id:'server-receipt-1',verifier_type:'RETRIEVAL_EXACT_MATCH',
    verifier_version:'HIDE_CODE_RED_V1'}};
  const issued=Receipt.issueBatchReceipt([evidence]);
  assert.equal(issued.ok,true);
  const entry=await store.getWithMetadata(key,{type:'json',consistency:'strong'});
  const state={...entry.data,scope_receipts:{
   'CHILD_A::english::vocabulary':{
    receipt:issued.receipt,canonical_evidence:issued.canonical_evidence}}};
  await store.setJSON(key,state,{onlyIfMatch:entry.etag});
  const decided=await endpoint.handle(req());
  const d=parse(decided);
  assert.equal(decided.status,200,JSON.stringify(d));
  assert.equal(d.authenticated_server_response,true);
  assert.deepEqual(d.receipt_scope,{family_id:'F1',member_id:'CHILD_A'});
  assert.equal(d.runtime_result.authority,'TAKY_LEARNING_ENGINE_CORE');
  assert.equal(d.runtime_result.decision.authority,'LEARNING_DECISION_INTENT_ONLY');
  assert.equal(d.runtime_result.decision.consumer_contract.planner,'OWNS_DATED_ALLOCATION');
  assert.equal(d.runtime_result.trace.verified_evidence_count,1);
  assert.equal(d.runtime_result.trace.verified_receipt_id,issued.receipt.receipt_id);
  assert(!decided.body.includes('scope_receipts'));
  assert(!decided.body.includes('observation_only:'));
  assert(!decided.body.includes(token));
  assert(!decided.body.includes('authorized_member_ids'));

  const hidePolicyResponse=await endpoint.handle(req({...scope,
   hide_vocabulary_context:{current_word_ids:['n1'],past_word_ids:['p1','p2']}}));
  const hidePolicy=parse(hidePolicyResponse);
  assert.equal(hidePolicyResponse.status,200,JSON.stringify(hidePolicy));
  assert.equal(hidePolicy.runtime_result.specialist_policy.hide_seek_vocabulary.authority,
   'LEARNING_ENGINE_SPECIALIST_POLICY_INTENT_ONLY');
  assert.equal(hidePolicy.runtime_result.specialist_policy.hide_seek_vocabulary
   .word_policies.find(x=>x.learning_target_id==='n1').recommended_mode,'RECALL');
  assert.equal(hidePolicy.runtime_result.specialist_policy.hide_seek_vocabulary
   .past_word_mix.current_words_mandatory,true);
  assert.equal(hidePolicy.runtime_result.specialist_policy.hide_seek_vocabulary
   .guards.planner_owns_dated_allocation,true);
  assert.equal((await endpoint.handle(req({...scope,
   hide_vocabulary_context:'browser-precomputed-policy'}))).status,400);

  // Governed derived activities are resolved by a trusted server callback.
  // The browser cannot select a source or forge the independent Index owner receipt.
  const activityRow={
   source_id:'ACTIVITY:G5:FRACTION:1',
   source_ref:'taky:activity:ACTIVITY:G5:FRACTION:1',
   source_family:'GOVERNED_DERIVED_ACTIVITY',
   source_type:'DERIVED_LEARNING_ACTIVITY',
   authority_class:'GOVERNED_DERIVED',
   detail_anchor:'DETAIL:ACTIVITY:G5:FRACTION:1',
   provenance:['GOVERNED_DERIVED_ACTIVITY_REF','OFFICIAL_SOURCE_DERIVATION_REF']
  };
  const activityOwner=(sid,ref)=>sid===activityRow.source_id&&ref===activityRow.source_ref?{
   issuer:'INDEXING_OWNER',reviewed:true,decision:'INDEXED',
   domain_use_authorized:true,source_id:sid,source_ref:ref,
   index_version:'TEST_ACTIVITY_OWNER_V1',
   review_evidence_refs:['TEST_ACTIVITY_OWNER_REVIEW'],
   source_family:activityRow.source_family,source_type:activityRow.source_type,
   authority_class:activityRow.authority_class,detail_anchor:activityRow.detail_anchor,
   provenance:[...activityRow.provenance]
  }:null;
  const activityEndpoint=Decision.create({store,
   verifyBearerToken:async t=>{if(t!==token)throw Error('INVALID');return principal;},
   independentIndexOwnerVerifier:activityOwner,
   resolveIndexedEvidence:async trustedScope=>({
    indexed_evidence_handoff:{
     query_context:{function_id:'LE-F07',consumer_app:'READY_SET',
      requested_behavior:'GOVERNED_DERIVED_ACTIVITY_REFERENCE'},
     candidates:[activityRow]
    },
    trusted_scope:trustedScope
   })
  });
  const growthRow={
   source_id:'EDU:ENG:G5:GROWTH:1',
   source_ref:'taky:edu:EDU:ENG:G5:GROWTH:1',
   source_family:'OFFICIAL_CURRICULUM',
   source_type:'OFFICIAL_EDUCATION_STANDARD',
   authority_class:'OFFICIAL',
   detail_anchor:'DETAIL:EDU:ENG:G5:GROWTH:1',
   provenance:['OFFICIAL_EDUCATION_SOURCE']
  };
  const growthOwner=(sid,ref)=>sid===growthRow.source_id&&ref===growthRow.source_ref?{
   issuer:'INDEXING_OWNER',reviewed:true,decision:'INDEXED',
   domain_use_authorized:true,source_id:sid,source_ref:ref,
   index_version:'TEST_GROWTH_OWNER_V1',
   review_evidence_refs:['TEST_GROWTH_OWNER_REVIEW'],
   source_family:growthRow.source_family,source_type:growthRow.source_type,
   authority_class:growthRow.authority_class,detail_anchor:growthRow.detail_anchor,
   provenance:[...growthRow.provenance]
  }:null;
  const growthEndpoint=Decision.create({store,
   verifyBearerToken:async t=>{if(t!==token)throw Error('INVALID');return principal;},
   independentIndexOwnerVerifier:growthOwner,
   resolveGrowthContext:async()=>({learner_context:{grade:5}}),
   resolveIndexedEvidence:async()=>({
    learning_index_handoff:{
     indexed_evidence_handoff:{
      query_context:{function_id:'LE-GROWTH-01',consumer_app:'LEARNING_ENGINE',
       requested_behavior:'CURRICULUM_GROUNDED_LANGUAGE_GROWTH'},
      candidates:[growthRow]
     },
     learning_mapping:{by_source_id:{
      'EDU:ENG:G5:GROWTH:1':{
       curriculum_version:'2022',grade:5,subject:'english',
       achievement_standard_refs:['ENG-G5-EXPR-01'],
       term:'accept',
       easy_english_definition:'to say yes to something or receive it',
       expression_chunks:['accept an idea','I can accept ...'],
       natural_collocations:['accept an invitation'],
       grammar_patterns:['accept + noun'],
       thinking_moves:['EXPLAIN','COMPARE','APPLY'],
       question_stems:['Why would someone accept it?'],
       production_targets:['USE_WORD_IN_OWN_SENTENCE'],
       english_thinking_support:['easy English meaning -> chunk -> own sentence']
      }
     }}
    }
   })
  });
  const growthResponse=await growthEndpoint.handle(req());
  const growthBody=parse(growthResponse);
  assert.equal(growthResponse.status,200,JSON.stringify(growthBody));
  assert.equal(growthBody.runtime_result.growth_profile.learner_context.grade,5);
  assert.equal(growthBody.runtime_result.growth_profile.learner_context.language_load,'SIMPLE');
  assert.equal(growthBody.runtime_result.growth_next_step.authority,'LEARNING_ENGINE_GROWTH_INTENT_ONLY');
  assert.equal(growthBody.runtime_result.growth_next_step.version,'TAKY_GROWTH_NEXT_STEP_POLICY_V2');
  assert.ok(['LOW','MEDIUM','HIGH'].includes(growthBody.runtime_result.growth_next_step.growth_control.evidence_confidence));
  assert.ok(['SUPPORT_BUILD','BUILD_CONNECT','STRETCH_TRANSFER'].includes(growthBody.runtime_result.growth_next_step.growth_control.learning_intensity));
  assert.ok(/^L[1-5]_/.test(growthBody.runtime_result.growth_next_step.growth_control.expression_level));
  assert.equal(growthBody.runtime_result.growth_next_step.growth_control.stability_guard.low_confidence_cannot_upshift_to_transfer,true);
  assert.equal(growthBody.runtime_result.growth_next_step.curriculum_grounding.verified,true);
  assert.deepEqual(growthBody.runtime_result.growth_next_step.curriculum_grounding.source_refs,
   [growthRow.source_ref]);
  assert.ok(growthBody.runtime_result.growth_next_step.language_support.easy_english_definitions.length>0);
  assert.ok(growthBody.runtime_result.growth_next_step.language_support.expression_chunks.length>0);
  assert.equal(growthBody.runtime_result.growth_next_step.hide_to_snap_handoff.child_authorship_required,true);
  assert.equal(growthBody.runtime_result.growth_next_step.hide_to_snap_handoff.final_answer_generation_forbidden,true);
  assert.equal((await growthEndpoint.handle(req({...scope,grade:5}))).status,400);

  const activityDecision=parse(await activityEndpoint.handle(req()));
  assert.equal(activityDecision.ok,true,JSON.stringify(activityDecision));
  assert.deepEqual(activityDecision.runtime_result.trace.governed_activity_refs,
   [activityRow.source_ref]);
  assert.deepEqual(activityDecision.runtime_result.trace.governed_activity_policy_ids,
   ['P-F07-READY']);
  assert.equal((await activityEndpoint.handle(req({...scope,
   source_ref:activityRow.source_ref}))).status,400);
  const resolverDown=Decision.create({store,
   verifyBearerToken:async()=>principal,
   independentIndexOwnerVerifier:activityOwner,
   resolveIndexedEvidence:async()=>{throw Error('INDEX_DOWN')}
  });
  const down=await resolverDown.handle(req());
  assert.equal(down.status,503);
  assert.equal(parse(down).reason,'INDEXED_ACTIVITY_REFERENCE_UNAVAILABLE');

  // Never take learning evidence, review dates or precomputed decisions from a browser.
  assert.equal((await endpoint.handle(req({...scope,evidence:[evidence]}))).status,400);
  assert.equal((await endpoint.handle(req({...scope,planner_date:'2026-09-28'}))).status,400);
  assert.equal((await endpoint.handle(req({...scope,member_id:'CHILD_B'}))).status,403);
  assert.equal((await endpoint.handle(req({...scope,family_id:'F2'}))).status,403);
  assert.equal((await endpoint.handle(req(scope,'invalid-parent-token-0001'))).status,401);
  assert.equal((await endpoint.handle({...req(),method:'GET'})).status,405);
  assert.equal((await endpoint.handle({...req(),path:'/api/learning/evidence'})).status,404);
  assert.equal((await endpoint.handle({...req(),body:'invalid-json'})).status,400);
  assert.equal((await endpoint.handle({...req(),body:'x'.repeat(8193)})).status,413);
  const corrupt=await store.getWithMetadata(key,{type:'json',consistency:'strong'});
  const broken=structuredClone(corrupt.data);
  broken.scope_receipts['CHILD_A::english::vocabulary'].canonical_evidence[0].verified_outcome=0;
  await store.setJSON(key,broken,{onlyIfMatch:corrupt.etag});
  const invalid=await endpoint.handle(req());
  assert.equal(invalid.status,503,JSON.stringify(parse(invalid)));
  assert.equal(parse(invalid).reason,'CENTRAL_VERIFIED_RECEIPT_INVALID');
  console.log('CENTRAL_DECISION_HTTP_PASS: authenticated scoped runtime, observation-only hold, verified receipt validation, browser input exclusion, no-store family isolation and corrupt state denial');
 }finally{await fs.rm(root,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
