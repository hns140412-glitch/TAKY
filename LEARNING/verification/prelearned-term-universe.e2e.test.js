'use strict';

const assert=require('node:assert/strict');
const path=require('node:path');
const Resolver=require('../intake/term-catalog-source-resolver.js');
const Engine=require('../runtime/learning-engine-runtime.js');

const resolver=Resolver.create({
  catalogPath:path.resolve(__dirname,'..','data','prelearned','subject-term-universe-56-v1.json'),
  allowProvisional:false
});

const cases=[
  {subject:'KOREAN',unit:'빗대어 표현해요',expected:['비유']},
  {subject:'SOCIAL',unit:'법과 인권의 보장',expected:['인권','헌법']},
  {subject:'SCIENCE',unit:'날씨와 우리 생활',expected:['고기압','저기압']},
  {subject:'MATH',unit:'약분과 통분',expected:['약분','통분']}
];

(async()=>{
  const report={};
  for(const test of cases){
    const source=await resolver({
      subject:test.subject,
      learner_profile:{school_stage:'E5'}
    });
    assert.equal(source.allow_provisional,false);
    assert.ok(source.terms.length>0);
    assert.ok(source.terms.every(t=>t.school_stages.includes('E5')));

    const out=Engine.deriveTermRecommendations({
      learner_profile:{school_stage:'E5'},
      subject:test.subject,
      unit_context:[test.unit],
      curriculum_terms:source.terms,
      term_evidence:[],
      consumer_app:'HIDE_SEEK',
      limit:12,
      allow_provisional:false
    });
    assert.equal(out.ok,true);
    assert.equal(out.recommendation_state,'READY');
    assert.ok(out.term_recommendations.length>0);
    assert.ok(out.term_recommendations.every(x=>x.grade_alignment_tier==='VERIFIED'));
    assert.ok(out.term_recommendations.some(x=>x.reasons.includes('UNIT_CONTEXT_MATCH')));
    for(const term of test.expected){
      assert.ok(out.term_recommendations.some(x=>x.term===term),test.subject+':'+test.unit+' missing '+term);
    }
    report[test.subject]=out.term_recommendations.slice(0,8).map(x=>x.term);
  }

  const e5Science=await resolver({subject:'SCIENCE',learner_profile:{school_stage:'E5'}});
  const e6Science=await resolver({subject:'SCIENCE',learner_profile:{school_stage:'E6'}});
  assert.equal(e5Science.terms.some(x=>x.term==='계절'),false);
  assert.equal(e6Science.terms.some(x=>x.term==='계절'),true);

  console.log('PRELEARNED_TERM_UNIVERSE_E2E_TEST: PASS');
  console.log(JSON.stringify(report,null,2));
})().catch(err=>{console.error(err);process.exit(1)});
