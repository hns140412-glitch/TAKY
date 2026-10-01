'use strict';
const assert=require('assert');
const P=require('./language-growth-profile.js');

const e=(id,signals)=>({
  event_id:id,observed_at:'2026-10-02T01:00:00Z',
  source_app:'snap-pop',language_growth_signals:signals
});
const p=P.derive({
  learner_context:{grade:5},
  evidence:[
    e('e1',[
      {dimension:'VOCABULARY',outcome:'SUCCESS',assisted:false},
      {dimension:'EXPRESSION',outcome:'PARTIAL',assisted:true},
      {dimension:'THINKING',outcome:'SUCCESS',depth:3}
    ]),
    e('e2',[
      {dimension:'VOCABULARY',outcome:'SUCCESS',assisted:false,transfer:true},
      {dimension:'THINKING',outcome:'SUCCESS',depth:4,transfer:true},
      {dimension:'ENGLISH_THINKING',outcome:'PARTIAL',direct_english:true}
    ])
  ]
});
assert.equal(p.ok,true);
assert.equal(p.learner_context.language_load,'SIMPLE');
assert.equal(p.dimensions.VOCABULARY.state,'READY_TO_STRETCH');
assert.equal(p.dimensions.THINKING.state,'READY_TO_STRETCH');
assert.equal(p.dimensions.GRAMMAR.state,'UNKNOWN');
assert.equal(P.validate(p).ok,true);
console.log('language-growth-profile.test.js PASS');
