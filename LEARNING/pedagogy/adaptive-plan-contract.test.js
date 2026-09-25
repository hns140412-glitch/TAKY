'use strict';
const assert=require('node:assert/strict');
const P=require('./adaptive-plan-contract.js');

const feedback={
  ok:true,
  scope:{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'},
  intents:[
    {intent:'TARGETED_RECOVERY_PRACTICE',priority:'HIGH',bases:['UNRESOLVED_RECOVERY'],targets:['word:a']},
    {intent:'RETRIEVAL_CHECKPOINT',priority:'HIGH',basis:'RETENTION_AT_RISK'},
    {intent:'REDUCE_ASSISTANCE_GRADUALLY',priority:'MEDIUM',basis:'ASSISTANCE_DOMINANT'}
  ]
};
const out=P.derive(feedback);
assert.equal(out.ok,true);
assert.equal(out.authority,'LEARNING_ADAPTIVE_PLAN_INTENT_ONLY');
assert.equal(out.unit_span_policy,'REDUCE');
assert.equal(out.add_checkpoint,true);
assert.equal(out.add_retrieval_checkpoint,true);
assert.equal(out.recovery_floor,'HIGH');
assert.equal(out.assistance_policy,'FADE_GRADUALLY');
assert.deepEqual(out.target_learning_ids,['word:a']);
assert.equal(P.validate(out).ok,true);

const calm=P.derive({ok:true,scope:feedback.scope,intents:[{intent:'CONTINUE_OBSERVATION',priority:'LOW',basis:'NO_STRONG_PEDAGOGICAL_SIGNAL'}]});
assert.equal(calm.unit_span_policy,'KEEP');
assert.equal(calm.add_checkpoint,false);
assert.equal(calm.add_retrieval_checkpoint,false);
assert.equal(calm.recovery_floor,null);
assert.equal(calm.assistance_policy,'UNCHANGED');

const leaked={...out,schedule_date:'2026-10-01'};
assert.equal(P.validate(leaked).ok,false);
assert.equal(P.validate(leaked).issues.includes('SCHEDULE_AUTHORITY_LEAK'),true);

console.log('ADAPTIVE_PLAN_CONTRACT_PASS');
