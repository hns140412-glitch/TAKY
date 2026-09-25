'use strict';
const assert=require('node:assert/strict');
const P=require('./relation-promotion-policy.js');

const candidate={
  relation_id:'cand1',
  authority:'DATA_CANDIDATE',
  state:'CANDIDATE',
  can_influence_learning_sequence:false
};

const sparse=P.evaluate(candidate,{
  observation_pairs:8,
  distinct_days:3,
  effect_consistency:0.80
});
assert.equal(sparse.ok,true);
assert.equal(sparse.personal_advisory_review_available,false);
assert.equal(sparse.personal_advisory_state,'HOLD');
assert.equal(sparse.domain_relation_promotion_available,false);
assert.equal(sparse.auto_promotion,false);
assert.equal(P.validate(sparse).ok,true);

const enough=P.evaluate(candidate,{
  observation_pairs:24,
  distinct_days:7,
  effect_consistency:0.78
});
assert.equal(enough.personal_advisory_review_available,true);
assert.equal(enough.personal_advisory_state,'HUMAN_REVIEW_AVAILABLE');
assert.equal(enough.allowed_if_personally_reviewed,'PERSONAL_SEQUENCE_ADVISORY_ONLY');
assert.equal(enough.domain_relation_promotion_available,false);
assert.equal(enough.domain_relation_blockers.includes('LEARNER_DATA_ALONE_CANNOT_DEFINE_DOMAIN_PREREQUISITE'),true);
assert.equal(P.validate(enough).ok,true);

const leaked=P.evaluate({...candidate,can_influence_learning_sequence:true},{
  observation_pairs:30,distinct_days:10,effect_consistency:0.9
});
assert.equal(leaked.personal_advisory_review_available,false);
assert.equal(leaked.blockers.includes('CANDIDATE_MUST_BE_NON_ACTIVE'),true);

console.log('RELATION_PROMOTION_POLICY_PASS');
