'use strict';
const assert=require('node:assert/strict');
const C=require('./badge-calculation-check.js');

const row=(id,target,minute,outcome)=>({
  event_id:id,learning_target_id:target,domain:'CALCULATION',
  observed_at:`2026-10-02T10:${String(minute).padStart(2,'0')}:00.000Z`,
  verified_outcome:outcome,
  verification:{authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'vr-'+id}
});

const before=row('calc-before','math:fractions:add',1,0);
const after=row('calc-after','math:fractions:add',8,1);
const obs=C.derive(before,after,{child_check_action_ref:'child-check:fractions:1'});
assert.ok(obs);
assert.equal(C.validate(obs).ok,true);
assert.equal(obs.app_id,'LEARNING_ENGINE_CORE');
assert.equal(obs.behavior_code,'CALCULATION_CHECK');
assert.equal(obs.source_contract_id,'LEARNING_VERIFIED_CALCULATION_CHECK_V1');
assert.equal(obs.badge_award_authorized,false);

assert.equal(C.derive(before,after,{}),null);
assert.equal(C.derive({...before,domain:'MEMORY'},after,{child_check_action_ref:'x'}),null);
assert.equal(C.derive(before,{...after,learning_target_id:'math:other'},{child_check_action_ref:'x'}),null);
assert.equal(C.derive({...before,verification:null},after,{child_check_action_ref:'x'}),null);
assert.equal(C.derive({...before,verified_outcome:1},after,{child_check_action_ref:'x'}),null);
assert.equal(C.derive(before,{...after,verified_outcome:0},{child_check_action_ref:'x'}),null);

console.log('BADGE_CALCULATION_CHECK_PASS');
