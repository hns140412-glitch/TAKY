'use strict';
const assert=require('node:assert/strict');
const D=require('./decision-contract.js');

const learner={
  ok:true,
  scope:{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'},
  inferred:{
    evidence_sufficiency:'ESTABLISHED',
    trend:'DECLINING',
    retention_signal:'RETENTION_AT_RISK',
    recovery_signal:'UNRESOLVED_RECOVERY',
    assistance_dependency_signal:'ASSISTANCE_DOMINANT',
    repeated_confusion_signal:'REPEATED_SELF_REPORTED_CONFUSION',
    instrument_change_detected:false
  }
};
const feedback={
  ok:true,
  intents:[
    {intent:'TARGETED_RECOVERY_PRACTICE',priority:'HIGH',basis:'UNRESOLVED_RECOVERY'},
    {intent:'RETRIEVAL_CHECKPOINT',priority:'HIGH',basis:'RETENTION_AT_RISK'},
    {intent:'REDUCE_ASSISTANCE_GRADUALLY',priority:'MEDIUM',basis:'ASSISTANCE_DOMINANT'}
  ]
};
const readiness={
  readiness:'PREREQUISITE_RISK',
  missing_prerequisites:['phonics'],
  at_risk_prerequisites:[]
};

const out=D.derive({learner_state:learner,feedback_intent:feedback,prerequisite_readiness:readiness});
assert.equal(out.ok,true);
assert.equal(out.execution_status,'PEDAGOGICAL_ACTION_AVAILABLE');
assert.equal(out.pedagogical_actions[0].priority,'HIGH');
assert.equal(out.advisories.some(x=>x.code==='PREREQUISITE_RISK'),true);
assert.equal(out.consumer_contract.planner,'OWNS_DATED_ALLOCATION');
assert.equal(D.validate(out).ok,true);

const sparse=D.derive({
  learner_state:{...learner,inferred:{...learner.inferred,evidence_sufficiency:'SPARSE'}},
  feedback_intent:feedback
});
assert.equal(sparse.execution_status,'PEDAGOGICAL_ACTION_AVAILABLE');
assert.equal(sparse.advisories.some(x=>x.code==='SPARSE_EVIDENCE'),true);

const none=D.derive({
  learner_state:{...learner,inferred:{...learner.inferred,evidence_sufficiency:'NONE'}},
  feedback_intent:feedback
});
assert.equal(none.execution_status,'HOLD_FOR_MORE_RELIABLE_INTERPRETATION');
assert.equal(none.blockers.some(x=>x.code==='NO_EVIDENCE'),true);

const drift=D.derive({
  learner_state:{...learner,inferred:{...learner.inferred,instrument_change_detected:true}},
  feedback_intent:feedback
});
assert.equal(drift.execution_status,'HOLD_FOR_MORE_RELIABLE_INTERPRETATION');
assert.equal(drift.blockers.some(x=>x.code==='INSTRUMENT_CHANGE_HOLD'),true);

const leaked={...out,schedule_date:'2026-10-01'};
assert.equal(D.validate(leaked).ok,false);
assert.equal(D.validate(leaked).issues.includes('SCHEDULE_AUTHORITY_LEAK'),true);

console.log('LEARNING_RUNTIME_DECISION_CONTRACT_PASS');
