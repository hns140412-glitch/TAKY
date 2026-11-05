'use strict';
const assert=require('node:assert/strict');
const C=require('./badge-improvement-comparison.js');

const e=(id,target,day,outcome,source='hide-seek')=>({
  event_id:id,learning_target_id:target,source_app:source,
  observed_at:`2026-09-${String(day).padStart(2,'0')}T07:00:00.000Z`,
  verified_outcome:outcome,
  verification:{authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'vr-'+id}
});

const rows=[e('a1','word:a',20,0),e('a2','word:a',21,1),e('b1','word:b',20,1)];
const linked=C.derive(rows,{source_app:'hide-seek',child_action_refs:{a1:'hide-action:a1',a2:'hide-action:a2'}});
assert.equal(linked.status,'VERIFIED_COMPARISON_READY');
assert.equal(linked.comparisons.length,1);
assert.equal(C.validate(linked.comparisons[0]).ok,true);
assert.equal(linked.comparisons[0].prior_verified_outcome,0);
assert.equal(linked.comparisons[0].current_verified_outcome,1);
assert.equal(linked.badge_award_authorized,false);

const noActions=C.derive(rows,{source_app:'hide-seek'});
assert.equal(noActions.status,'ACTION_LINKAGE_REQUIRED');
assert.equal(noActions.comparisons.length,0);
assert.equal(noActions.blockers[0].code,'EXPLICIT_CHILD_ACTION_REFS_REQUIRED');

const unverified=C.derive([{...e('u1','word:u',20,0),verification:null},e('u2','word:u',21,1)],{
  source_app:'hide-seek',child_action_refs:{u1:'x',u2:'y'}
});
assert.equal(unverified.comparisons.length,0);

const wrongSource=C.derive(rows,{source_app:'snap-pop',child_action_refs:{a1:'x',a2:'y'}});
assert.equal(wrongSource.comparisons.length,0);

const forged={...linked.comparisons[0],current_receipt_id:''};
assert.equal(C.validate(forged).ok,false);

console.log('BADGE_IMPROVEMENT_COMPARISON_PASS');
