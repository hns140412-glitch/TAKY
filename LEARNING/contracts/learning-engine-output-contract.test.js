'use strict';
const assert=require('assert');
const C=require('./learning-engine-output-contract.js');

const out=C.derive({
 decision:{
  ok:true,
  adaptive_plan:{
    target_learning_ids:['w1','w2','w3'],
    add_checkpoint:true,
    add_retrieval_checkpoint:true,
    recovery_floor:'MEDIUM'
  }
 },
 growth_next_step:{
  authority:'LEARNING_ENGINE_GROWTH_INTENT_ONLY',
  version:'TAKY_GROWTH_NEXT_STEP_POLICY_V2',
  support_phase:'ELICIT_PULL',
  growth_control:{learning_intensity:'BUILD_CONNECT',expression_level:'L3_EXPANDED_SENTENCE'}
 },
 reference_gaps:[{gap_id:'g1',resolution_path:'INDEX_THEN_MINING_IF_INSUFFICIENT'}],
 evidence_ids:['e1','e2'],
 source_refs:['CURR:ENG5:1','OEWN:accept']
});
assert.equal(out.ok,true);
assert.equal(out.review_need.required,true);
assert.equal(out.learning_intensity,'BUILD_CONNECT');
assert.equal(out.recommended_quantity.target_count_hint,3);
assert.equal(out.recommended_quantity.quantity_band,'FOCUSED');
assert.equal(out.recommended_quantity.allocated_quantity,null);
assert.equal(out.recommended_quantity.planner_must_materialize,true);
assert.equal(out.date_authority,false);
assert.equal(out.allocated_quantity_authority,false);
assert.equal(out.reference_gaps[0].mining_request_authorized,false);
assert.deepEqual(out.basis.evidence_ids,['e1','e2']);
assert.deepEqual(out.basis.source_refs,['CURR:ENG5:1','OEWN:accept']);
assert.equal(out.basis.provenance_required,true);
assert.equal(C.validate(out).ok,true);

console.log('learning-engine-output-contract.test.js PASS');
