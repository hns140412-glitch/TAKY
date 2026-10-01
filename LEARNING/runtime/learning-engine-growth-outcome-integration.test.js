'use strict';
const assert=require('assert');
const Runtime=require('./learning-engine-runtime.js');

const runtimeResult={
  ok:true,
  scope:{member_id:'A',subject:'english',concept_skill_target:'writing'},
  decision:{execution_status:'READY'},
  evidence_gap:null,
  growth_next_step:{
    growth_control:{
      evidence_confidence:'MEDIUM',
      learning_intensity:'BUILD_CONNECT',
      expression_level:'L3_EXPANDED_SENTENCE',
      question_depth:3,
      hint_strength:'PARTIAL_FRAME',
      hint_fade:'FADE_ONE_STEP_WHEN_SUCCESSFUL',
      challenge_direction:'EXTEND'
    }
  }
};

const success=Runtime.applyOutcome({
  runtime_result:runtimeResult,
  outcome:{
    source_app:'snap-pop',
    learning_target_id:'writing:1',
    language_growth_signals:[
      {dimension:'EXPRESSION',outcome:'SUCCESS'},
      {dimension:'THINKING',outcome:'SUCCESS'}
    ]
  }
});
assert.equal(success.ok,true);
assert.equal(success.growth_outcome_feedback.adjustment,'FADE_HINT_ONE_STEP_CANDIDATE');
assert.equal(success.growth_outcome_feedback.control_change_authorized,false);
assert.equal(success.trace.growth_control_change_authorized,false);

const fail=Runtime.applyOutcome({
  runtime_result:runtimeResult,
  outcome:{
    source_app:'snap-pop',
    learning_target_id:'writing:1',
    language_growth_signals:[
      {dimension:'EXPRESSION',outcome:'FAIL'},
      {dimension:'THINKING',outcome:'PARTIAL'}
    ]
  }
});
assert.equal(fail.ok,true);
assert.equal(fail.growth_outcome_feedback.adjustment,'INCREASE_SUPPORT_CANDIDATE');
assert.equal(fail.growth_outcome_feedback.suggested_next_control.expression_level,'L2_SIMPLE_SENTENCE');

console.log('learning-engine-growth-outcome-integration.test.js PASS');
