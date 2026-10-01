'use strict';
const assert=require('assert');
const C=require('./learning-evidence-io-contract.js');

const record={
  authority:'RAW_LEARNING_EVIDENCE_ONLY',
  learner_state_authority:false,
  schedule_authority:false,
  identity:C.commonIdentity({
    member_id:'A',session_id:'S1',task_id:'T1',lap_id:'L1',
    subject:'english',source_app:'hide-seek',
    observed_at:'2026-10-02T07:30:00+09:00',
    learning_target_id:'accept'
  }),
  references:C.normalizeRefs({
    curriculum_refs:['CURR:ENG5:1'],
    lexical_refs:['OEWN:accept'],
    usage_refs:['USAGE:accept-an-idea']
  })
};
assert.equal(C.validateInput(record).ok,true);

const output={
  authority:'TAKY_LEARNING_ENGINE_CORE',
  date_authority:false,
  allocated_quantity_authority:false,
  review_need:{required:true},
  learning_intensity:'BUILD_CONNECT',
  recommended_quantity:{
    authority:'LEARNING_ENGINE_QUANTITY_INTENT_ONLY',
    unit:'LEARNING_TARGET',
    min:3,max:5,
    planner_must_materialize:true
  }
};
assert.equal(C.validateLearningOutput(output).ok,true);
assert.equal(C.validateLearningOutput({...output,schedule_date:'2026-10-03'}).ok,false);
assert.equal(C.validateLearningOutput({...output,allocated_quantity:5}).ok,false);

console.log('learning-evidence-io-contract.test.js PASS');
