'use strict';
const assert=require('node:assert/strict');
const F=require('./feedback-intent.js');

const state={
  ok:true,
  scope:{member_id:'A',subject:'영어',concept_skill_target:'vocabulary'},
  observed:{
    self_reflection:{repeated_confusions:[{target:'except',count:2}]}
  },
  inferred:{
    repeated_confusion_signal:'REPEATED_SELF_REPORTED_CONFUSION',
    metacognitive_recall_signal:'KNEW_BUT_RECALL_FAILED_REPORTED',
    assistance_dependency_signal:'ASSISTANCE_DOMINANT',
    trend:'DECLINING'
  }
};
const out=F.derive(state);
assert.equal(out.ok,true);
assert.equal(F.validate(out).ok,true);
assert.deepEqual(out.intents.map(x=>x.intent),[
  'DISAMBIGUATE_CONFUSION',
  'SHORT_DELAY_RETRIEVAL',
  'REDUCE_ASSISTANCE_GRADUALLY',
  'RETRIEVAL_CHECKPOINT'
]);
assert.equal(out.ui_copy_owned_by,'CONSUMER_APP');
assert.equal(out.cannot_influence.includes('SCHEDULE_DATE'),true);

const quiet=F.derive({
  ok:true,
  scope:{member_id:'A',subject:'수학',concept_skill_target:'fraction'},
  observed:{},
  inferred:{}
});
assert.equal(quiet.intents[0].intent,'CONTINUE_OBSERVATION');

const leaked={...out,schedule_date:'2026-10-01'};
assert.equal(F.validate(leaked).ok,false);
assert.equal(F.validate(leaked).issues.includes('SCHEDULE_AUTHORITY_LEAK'),true);

console.log('PEDAGOGICAL_FEEDBACK_INTENT_PASS');
