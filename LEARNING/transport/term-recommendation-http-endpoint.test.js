'use strict';

const assert=require('node:assert/strict');
const Endpoint=require('./term-recommendation-http-endpoint.js');
const catalog=require('../projection/term-decoder-mined-catalog-v1.json');

const token='abcdefghijklmnopqrstuvwxyz123456';
const verifyBearerToken=async value=>{
  assert.equal(value,token);
  return {
    authenticated:true,
    principal_id:'principal-1',
    active_family_id:'family-1',
    families:[{
      family_id:'family-1',
      self_member_id:'guardian-1',
      authorized_member_ids:['child-1']
    }]
  };
};

const endpoint=Endpoint.create({
  verifyBearerToken,
  resolveLearnerProfile:async({family_id,member_id})=>{
    assert.equal(family_id,'family-1');
    assert.equal(member_id,'child-1');
    return {school_stage:'E5'};
  },
  resolveCurriculumTerms:async({subject})=>({
    source_ref:catalog.source_ref,
    allow_provisional:true,
    unit_text:'자료를 조사하고 결과를 비교하여 변화 과정을 설명한다. 조사한 자료를 확인한다.',
    academic_vocab_explicit_terms:['자료','조사'],
    terms:catalog.terms.filter(x=>x.subject===subject)
  }),
  resolveTermEvidence:async()=>[
    {learning_target_id:'sci-hanraengjeonseon',interaction_mode:'CORE',result_type:'WRONG',observed_at:'2026-10-07T01:00:00Z'},
    {learning_target_id:'sci-hanraengjeonseon',interaction_mode:'LINK',result_type:'HINT_USED',assisted:true,observed_at:'2026-10-07T01:01:00Z'}
  ]
});

(async()=>{
  const res=await endpoint.handle({
    method:'POST',
    path:Endpoint.ENDPOINT,
    headers:{
      'content-type':'application/json',
      'authorization':'Bearer '+token
    },
    body:JSON.stringify({
      family_id:'family-1',
      member_id:'child-1',
      subject:'SCIENCE',
      unit_context:['전선','날씨'],
      limit:8
    })
  });
  assert.equal(res.status,200);
  const body=JSON.parse(res.body);
  assert.equal(body.ok,true);
  assert.equal(body.authority,'TAKY_LEARNING_ENGINE_CORE');
  assert.equal(body.learner_context.school_stage,'E5');
  assert.equal(body.term_recommendations.length,8);
  assert.equal(body.term_recommendations[0].term_id,'sci-hanraengjeonseon');
  assert.equal(body.term_recommendations[0].priority,'RECOVERY');
  assert.equal(body.cards.length,8);
  assert.ok(body.cards.every(x=>x.subject==='SCIENCE'));
  assert.equal(body.trace.evidence_count,2);
  assert.equal(body.academic_vocabulary_stage_policy.primary,2);
  assert.deepEqual(body.academic_vocabulary_stage_policy.foundation,[1]);
  assert.equal(body.academic_vocabulary_targets.ok,true);
  assert.ok(body.academic_vocabulary_targets.selected.some(x=>x.term==='자료'&&x.academic_role==='PRIMARY'));
  assert.ok(body.academic_vocabulary_targets.selected.some(x=>x.term==='결과'&&x.academic_role==='FOUNDATION'));
  assert.ok(body.literacy_intent.consumers.hide_seek.academic_vocabulary_targets.some(x=>x.term==='자료'));
  assert.equal(body.literacy_intent.ok,true);
  assert.equal(body.literacy_intent.consumers.hide_seek.intent,'TERM_DECODING_AND_RETRIEVAL');
  assert.deepEqual(body.literacy_intent.consumers.hide_seek.targets[0].mode_bias,['CORE','RECALL']);
  assert.equal(body.literacy_intent.consumers.ready_set.intent,'FOCUSED_REMEDIATION');
  assert.equal(body.literacy_intent.consumers.snap_pop.activity_sequence[3].intent,'APPLY_TO_NEW_CONTEXT');
  assert.ok(body.cannot_influence.includes('SCHEDULE_DATE'));

  const denied=await endpoint.handle({
    method:'POST',path:Endpoint.ENDPOINT,
    headers:{'content-type':'application/json','authorization':'Bearer '+token},
    body:JSON.stringify({family_id:'family-1',member_id:'other-child',subject:'SCIENCE'})
  });
  assert.equal(denied.status,403);

  console.log('TERM_RECOMMENDATION_HTTP_ENDPOINT_TEST: PASS');
})().catch(err=>{console.error(err);process.exit(1)});
