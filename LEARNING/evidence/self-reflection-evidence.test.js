'use strict';
const assert=require('node:assert/strict');
const S=require('./self-reflection-evidence.js');

const e1=S.create({
  event_id:'r1',observed_at:'2026-09-25T07:00:00.000Z',member_id:'A',subject:'영어',
  concept_skill_target:'vocabulary',source_app:'hide-seek',difficulty:'HARD',
  recall_state:'KNEW_BUT_COULD_NOT_RECALL',confidence:'MEDIUM',confusion_with:['accept','except'],used_hint:true
});
assert.equal(e1.ok,true);
assert.equal(e1.evidence.verified_outcome,null);
assert.equal(e1.evidence.provenance.can_directly_set_mastery,false);
assert.equal(S.validate(e1.evidence).ok,true);

const e2=S.create({
  event_id:'r2',observed_at:'2026-09-26T07:00:00.000Z',member_id:'A',subject:'영어',
  concept_skill_target:'vocabulary',source_app:'hide-seek',difficulty:'OK',
  recall_state:'RECALLED_WITH_HINT',confidence:'HIGH',confusion_with:['except']
});
const e3=S.create({
  event_id:'r3',observed_at:'2026-09-27T07:00:00.000Z',member_id:'A',subject:'영어',
  concept_skill_target:'vocabulary',source_app:'ready-set',difficulty:'EASY',
  recall_state:'KNEW_AND_RECALLED',confidence:'HIGH'
});
const sum=S.summarize([e1.evidence,e2.evidence,e3.evidence]);
assert.equal(sum.reflection_count,3);
assert.equal(sum.knew_but_could_not_recall_count,1);
assert.equal(sum.repeated_confusions[0].target,'except');
assert.equal(sum.repeated_confusions[0].count,2);

const forged={...e1.evidence,verified_outcome:1};
assert.equal(S.validate(forged).ok,false);
assert.equal(S.validate(forged).issues.includes('SELF_REFLECTION_CANNOT_BE_VERIFIED_TARGET'),true);

console.log('SELF_REFLECTION_EVIDENCE_PASS');
