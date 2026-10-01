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


const scaffolded=P.derive({
  learner_context:{grade:5},
  evidence:[
    {
      event_id:'x1',observed_at:'2026-10-01T00:00:00Z',source_app:'snap-pop',
      verified_outcome:1,verification:{authority:'LEARNING_VERIFICATION_RECEIPT'},
      growth_execution_context:{
        learning_intensity:'SUPPORT_BUILD',
        expression_level:'L2_SIMPLE_SENTENCE',
        question_depth:2,
        hint_strength:'STRONG_SCAFFOLD'
      },
      language_growth_signals:[
        {dimension:'EXPRESSION',outcome:'SUCCESS',assisted:false,transfer:false}
      ]
    },
    {
      event_id:'x2',observed_at:'2026-10-02T00:00:00Z',source_app:'snap-pop',
      growth_execution_context:{
        learning_intensity:'SUPPORT_BUILD',
        expression_level:'L2_SIMPLE_SENTENCE',
        question_depth:2,
        hint_strength:'STRONG_SCAFFOLD'
      },
      language_growth_signals:[
        {dimension:'EXPRESSION',outcome:'SUCCESS',assisted:false,transfer:false}
      ]
    }
  ]
});
assert.notEqual(scaffolded.dimensions.EXPRESSION.state,'READY_TO_STRETCH');
assert.equal(scaffolded.dimensions.EXPRESSION.explicit_challenge_success_count,0);

const minimallyCued=P.derive({
  learner_context:{grade:5},
  evidence:[
    {
      event_id:'m1',observed_at:'2026-10-01T00:00:00Z',source_app:'snap-pop',
      verified_outcome:1,verification:{authority:'LEARNING_VERIFICATION_RECEIPT'},
      growth_execution_context:{
        learning_intensity:'BUILD_CONNECT',
        expression_level:'L3_EXPANDED_SENTENCE',
        question_depth:3,
        hint_strength:'MINIMAL_CUE'
      },
      language_growth_signals:[
        {dimension:'EXPRESSION',outcome:'SUCCESS',assisted:false,transfer:true}
      ]
    },
    {
      event_id:'m2',observed_at:'2026-10-02T00:00:00Z',source_app:'snap-pop',
      growth_execution_context:{
        learning_intensity:'BUILD_CONNECT',
        expression_level:'L3_EXPANDED_SENTENCE',
        question_depth:3,
        hint_strength:'MINIMAL_CUE'
      },
      language_growth_signals:[
        {dimension:'EXPRESSION',outcome:'SUCCESS',assisted:false,transfer:true}
      ]
    }
  ]
});
assert.equal(minimallyCued.dimensions.EXPRESSION.state,'READY_TO_STRETCH');
assert.equal(minimallyCued.dimensions.EXPRESSION.minimal_hint_success_count,2);
assert.equal(minimallyCued.dimensions.EXPRESSION.max_success_expression_level,3);

console.log('language-growth-profile.test.js PASS');
