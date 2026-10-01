'use strict';
const assert=require('assert');
const P=require('./language-growth-profile.js');

const event=(id,source_app,signals,verified=false)=>({
  event_id:id,observed_at:'2026-10-02T01:00:00Z',source_app,
  ...(verified?{verified_outcome:1,verification:{authority:'LEARNING_VERIFICATION_RECEIPT'}}:{}),
  language_growth_signals:signals
});

const sparse=P.derive({
  learner_context:{grade:5},
  evidence:[
    event('s1','snap-pop',[
      {dimension:'VOCABULARY',outcome:'SUCCESS',assisted:false},
      {dimension:'THINKING',outcome:'SUCCESS',depth:3}
    ]),
    event('s2','snap-pop',[
      {dimension:'VOCABULARY',outcome:'SUCCESS',assisted:false,transfer:true},
      {dimension:'THINKING',outcome:'SUCCESS',depth:4,transfer:true},
      {dimension:'ENGLISH_THINKING',outcome:'PARTIAL',direct_english:false}
    ])
  ]
});
assert.equal(sparse.ok,true);
assert.equal(sparse.learner_context.language_load,'SIMPLE');
assert.notEqual(sparse.dimensions.VOCABULARY.state,'READY_TO_STRETCH');
assert.equal(sparse.dimensions.VOCABULARY.confidence,'MEDIUM');
assert.equal(sparse.cross_dimension.translation_dependency_signal,'UNKNOWN');

const grounded=P.derive({
  learner_context:{grade:5},
  evidence:[
    event('h1','hide-seek',[
      {dimension:'VOCABULARY',outcome:'SUCCESS',assisted:false},
      {dimension:'ENGLISH_THINKING',outcome:'PARTIAL',direct_english:false}
    ],true),
    event('s1','snap-pop',[
      {dimension:'VOCABULARY',outcome:'SUCCESS',assisted:false,transfer:true},
      {dimension:'THINKING',outcome:'SUCCESS',depth:4,transfer:true},
      {dimension:'ENGLISH_THINKING',outcome:'SUCCESS',direct_english:true}
    ]),
    event('s2','snap-pop',[
      {dimension:'VOCABULARY',outcome:'SUCCESS',assisted:false,transfer:true},
      {dimension:'THINKING',outcome:'SUCCESS',depth:4,transfer:true}
    ])
  ]
});
assert.equal(grounded.dimensions.VOCABULARY.state,'READY_TO_STRETCH');
assert.ok(['MEDIUM','HIGH'].includes(grounded.dimensions.VOCABULARY.confidence));
assert.equal(grounded.cross_dimension.cross_app_dimension_count>=1,true);
assert.equal(grounded.cross_dimension.verified_growth_signal_count>=1,true);
assert.equal(grounded.dimensions.GRAMMAR.state,'UNKNOWN');
assert.equal(P.validate(grounded).ok,true);
console.log('language-growth-profile.test.js PASS');
