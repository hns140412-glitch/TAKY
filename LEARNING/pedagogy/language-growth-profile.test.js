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



const oldStrongRecentWeak=[];
for(let i=1;i<=10;i++){
  oldStrongRecentWeak.push({
    event_id:'old-'+i,
    observed_at:'2026-09-'+String(i).padStart(2,'0')+'T00:00:00Z',
    source_app:'snap-pop',
    verified_outcome:i===1?1:null,
    ...(i===1?{verification:{authority:'LEARNING_VERIFICATION_RECEIPT'}}:{}),
    growth_execution_context:{
      learning_intensity:'BUILD_CONNECT',
      expression_level:'L3_EXPANDED_SENTENCE',
      question_depth:3,
      hint_strength:'MINIMAL_CUE'
    },
    language_growth_signals:[
      {dimension:'EXPRESSION',outcome:'SUCCESS',assisted:false,transfer:true}
    ]
  });
}
oldStrongRecentWeak.push(
  {
    event_id:'recent-fail-1',observed_at:'2026-10-01T00:00:00Z',source_app:'snap-pop',
    growth_execution_context:{
      learning_intensity:'SUPPORT_BUILD',expression_level:'L2_SIMPLE_SENTENCE',
      question_depth:2,hint_strength:'STRONG_SCAFFOLD'
    },
    language_growth_signals:[{dimension:'EXPRESSION',outcome:'FAIL',assisted:false}]
  },
  {
    event_id:'recent-fail-2',observed_at:'2026-10-02T00:00:00Z',source_app:'snap-pop',
    growth_execution_context:{
      learning_intensity:'SUPPORT_BUILD',expression_level:'L2_SIMPLE_SENTENCE',
      question_depth:2,hint_strength:'STRONG_SCAFFOLD'
    },
    language_growth_signals:[{dimension:'EXPRESSION',outcome:'FAIL',assisted:false}]
  }
);
const temporarySupport=P.derive({
  learner_context:{grade:5},
  evidence:oldStrongRecentWeak,
  window_policy:{recent_limit:3,stability_limit:12}
});
assert.equal(temporarySupport.dimensions.EXPRESSION.recent_state,'NEEDS_SUPPORT');
assert.equal(temporarySupport.dimensions.EXPRESSION.stable_state,'READY_TO_STRETCH');
assert.equal(
  temporarySupport.dimensions.EXPRESSION.stability_signal,
  'TEMPORARY_SUPPORT_WITHOUT_LONG_TERM_DEMOTION'
);
assert.equal(temporarySupport.evidence_window_policy.recent_limit,3);
assert.equal(temporarySupport.evidence_window_policy.stability_limit,12);

const recentStrongOldWeak=[
  {
    event_id:'weak-old-1',observed_at:'2026-09-01T00:00:00Z',source_app:'snap-pop',
    language_growth_signals:[{dimension:'THINKING',outcome:'FAIL',assisted:false,depth:2}]
  },
  {
    event_id:'weak-old-2',observed_at:'2026-09-02T00:00:00Z',source_app:'snap-pop',
    language_growth_signals:[{dimension:'THINKING',outcome:'FAIL',assisted:false,depth:2}]
  }
];
for(let i=1;i<=3;i++){
  recentStrongOldWeak.push({
    event_id:'new-strong-'+i,
    observed_at:'2026-10-0'+i+'T00:00:00Z',
    source_app:i===1?'hide-seek':'snap-pop',
    verified_outcome:i===1?1:null,
    ...(i===1?{verification:{authority:'LEARNING_VERIFICATION_RECEIPT'}}:{}),
    growth_execution_context:{
      learning_intensity:'BUILD_CONNECT',
      expression_level:'L3_EXPANDED_SENTENCE',
      question_depth:4,
      hint_strength:'MINIMAL_CUE'
    },
    language_growth_signals:[{
      dimension:'THINKING',outcome:'SUCCESS',assisted:false,transfer:true,depth:4
    }]
  });
}
const promotionHeld=P.derive({
  learner_context:{grade:5},
  evidence:recentStrongOldWeak,
  window_policy:{recent_limit:3,stability_limit:5}
});
assert.equal(promotionHeld.dimensions.THINKING.recent_state,'READY_TO_STRETCH');
assert.notEqual(promotionHeld.dimensions.THINKING.stable_state,'READY_TO_STRETCH');
assert.equal(
  promotionHeld.dimensions.THINKING.stability_signal,
  'PROMOTION_CANDIDATE_NOT_STABLE'
);

console.log('language-growth-profile.test.js PASS');
