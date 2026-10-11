'use strict';

const assert=require('node:assert/strict');
const path=require('node:path');
const Resolver=require('./term-catalog-source-resolver.js');
const Engine=require('../runtime/learning-engine-runtime.js');

(async()=>{
  const elementaryPath=path.resolve(__dirname,'..','data','prelearned','subject-term-universe-elementary-v1.json');
  const resolveElementary=Resolver.create({catalogPath:elementaryPath,allowProvisional:true});

  const checks=[
    ['E1','KOREAN',20],
    ['E1','MATH',20],
    ['E2','RIGHT_LIFE',5],
    ['E3','SCIENCE',20],
    ['E3','SOCIAL',20],
    ['E4','KOREAN',20],
    ['E5','SCIENCE',30],
    ['E6','MATH',30]
  ];
  const report={};
  for(const [stage,subject,min] of checks){
    const out=await resolveElementary({subject,learner_profile:{school_stage:stage}});
    assert.equal(out.source_schema,Resolver.ELEMENTARY_SCHEMA);
    assert.equal(out.allow_provisional,false);
    assert.equal(out.learner_stage_filter,stage);
    assert.ok(out.terms.length>=min,stage+':'+subject+' too few terms');
    assert.ok(out.terms.every(x=>x.subject===subject));
    assert.ok(out.terms.every(x=>x.school_stages.includes(stage)));
    report[stage+':'+subject]=out.terms.length;
  }

  const e1Science=await resolveElementary({subject:'SCIENCE',learner_profile:{school_stage:'E1'}});
  assert.equal(e1Science.terms.length,0,'E1 must not receive E3+ science terms');

  const e1Math=await resolveElementary({subject:'MATH',learner_profile:{school_stage:'E1'}});
  assert.equal(e1Math.terms.some(x=>x.term==='퇴적암'),false);

  const e3Science=await resolveElementary({subject:'SCIENCE',learner_profile:{school_stage:'E3'}});
  const runtime=Engine.deriveTermRecommendations({
    learner_profile:{school_stage:'E3'},
    subject:'SCIENCE',
    curriculum_terms:e3Science.terms,
    term_evidence:[],
    consumer_app:'HIDE_SEEK',
    limit:12,
    allow_provisional:e3Science.allow_provisional
  });
  assert.equal(runtime.ok,true);
  assert.equal(runtime.term_recommendations.length,12);
  assert.ok(runtime.term_recommendations.every(x=>x.grade_alignment_tier==='VERIFIED'));
  assert.ok(runtime.cards.every(x=>['3-4','3','4'].includes(x.gradeBand)));

  const legacyPath=path.resolve(__dirname,'..','projection','term-decoder-mined-catalog-v1.json');
  const resolveLegacy=Resolver.create({catalogPath:legacyPath,allowProvisional:true});
  const legacy=await resolveLegacy({subject:'SCIENCE',learner_profile:{school_stage:'E5'}});
  assert.equal(legacy.source_schema,Resolver.LEGACY_SCHEMA);
  assert.equal(legacy.allow_provisional,true);
  assert.ok(legacy.terms.length>0);

  console.log('TERM_CATALOG_SOURCE_RESOLVER_TEST: PASS');
  console.log(JSON.stringify(report,null,2));
})().catch(err=>{console.error(err);process.exit(1)});
