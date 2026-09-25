'use strict';

const assert=require('node:assert/strict');
const Feedback=require('./outcome-growth-feedback.js');

const verifiedFailure=Feedback.derive({
  outcome:{
    verified_outcome:0,
    verification:{authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'vr-1'},
    assistance:'ASSISTED',
    assisted:true,
    attempt_count:2,
    source_app:'hide-seek',
    learning_target_id:'word:a'
  },
  prior_decision:{execution_status:'PEDAGOGICAL_ACTION_AVAILABLE'},
  prior_evidence_gap:{
    gap_id:'A:영어:VOCABULARY:LEARNER_EVIDENCE_SPARSE',
    gap_type:'LEARNER_EVIDENCE_SPARSE',
    scope:{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'}
  },
  index_gap_route:{decision:'MINING_REQUEST',index_sufficient:false}
});
assert.equal(verifiedFailure.ok,true);
assert.equal(verifiedFailure.learning_strategy_feedback.verified_target,true);
assert.equal(verifiedFailure.learning_strategy_feedback.outcome,0);
assert.equal(verifiedFailure.learning_strategy_feedback.suggested_adjustments.includes('INCREASE_TARGETED_RECOVERY'),true);
assert.equal(verifiedFailure.mining_strategy_feedback_candidate.requires_mining_evaluation,true);
assert.equal(verifiedFailure.mining_strategy_feedback_candidate.promotion_authorized,false);
assert.equal(verifiedFailure.mining_strategy_feedback_candidate.canonical_classification_change_authorized,false);
assert.equal(Feedback.validate(verifiedFailure).ok,true);

const observation=Feedback.derive({
  outcome:{
    verified_outcome:1,
    verification:{authority:'UNTRUSTED',receipt_id:'x'}
  }
});
assert.equal(observation.learning_strategy_feedback.verified_target,false);
assert.equal(observation.learning_strategy_feedback.observation_only,true);
assert.equal(observation.mining_strategy_feedback_candidate,null);

const indexEnough=Feedback.derive({
  outcome:{
    verified_outcome:1,
    verification:{authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'vr-2'}
  },
  prior_evidence_gap:{gap_id:'g',gap_type:'LEARNER_EVIDENCE_SPARSE',scope:{}},
  index_gap_route:{decision:'INDEX_REQUERY',index_sufficient:true}
});
assert.equal(indexEnough.mining_strategy_feedback_candidate,null);

console.log('OUTCOME_GROWTH_FEEDBACK_PASS');
