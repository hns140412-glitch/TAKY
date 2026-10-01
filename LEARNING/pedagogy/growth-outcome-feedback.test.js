'use strict';
const assert=require('assert');
const F=require('./growth-outcome-feedback.js');

const prior={
  growth_control:{
    evidence_confidence:'MEDIUM',
    learning_intensity:'BUILD_CONNECT',
    expression_level:'L3_EXPANDED_SENTENCE',
    question_depth:3,
    hint_strength:'PARTIAL_FRAME',
    hint_fade:'FADE_ONE_STEP_WHEN_SUCCESSFUL',
    challenge_direction:'EXTEND'
  }
};

const success=F.derive({
  prior_growth_next_step:prior,
  outcome_evidence:{language_growth_signals:[
    {dimension:'EXPRESSION',outcome:'SUCCESS'},
    {dimension:'THINKING',outcome:'SUCCESS'}
  ]}
});
assert.equal(success.adjustment,'FADE_HINT_ONE_STEP_CANDIDATE');
assert.equal(success.suggested_next_control.hint_strength,'MINIMAL_CUE');
assert.equal(success.control_change_authorized,false);
assert.equal(F.validate(success).ok,true);

const fail=F.derive({
  prior_growth_next_step:prior,
  outcome_evidence:{language_growth_signals:[
    {dimension:'EXPRESSION',outcome:'FAIL'},
    {dimension:'THINKING',outcome:'PARTIAL'}
  ]}
});
assert.equal(fail.adjustment,'INCREASE_SUPPORT_CANDIDATE');
assert.equal(fail.suggested_next_control.learning_intensity,'SUPPORT_BUILD');
assert.equal(fail.suggested_next_control.expression_level,'L2_SIMPLE_SENTENCE');
assert.equal(fail.state_mutation_authorized,false);

const unknown=F.derive({
  prior_growth_next_step:prior,
  outcome_evidence:{language_growth_signals:[
    {dimension:'EXPRESSION',outcome:'UNKNOWN'}
  ]}
});
assert.equal(unknown.adjustment,'OBSERVE_MORE');
assert.equal(unknown.suggested_next_control,null);

console.log('growth-outcome-feedback.test.js PASS');
