'use strict';
const assert=require('node:assert/strict');
const Core=require('./learner-state-core.js');

const e=(id,member,subject,target,opts={})=>({
  event_id:id,
  observed_at:opts.observed_at||'2026-09-25T07:00:00.000Z',
  member_id:member,
  subject,
  concept_skill_target:target,
  evidence_type:opts.evidence_type||'MEMORY_RETRIEVAL_EVIDENCE',
  source_app:opts.source_app||'hide-seek',
  instrument_version:opts.instrument_version||'hide-v1',
  assisted:opts.assisted,
  verified_performance:opts.verified_performance===true,
  memory:{average_strength:opts.strength}
});

const rows=[
  e('a1','A','영어','VOCABULARY',{strength:82,assisted:false}),
  e('a2','A','영어','VOCABULARY',{strength:75,assisted:true,observed_at:'2026-09-26T07:00:00.000Z'}),
  e('a2','A','영어','VOCABULARY',{strength:75,assisted:true,observed_at:'2026-09-26T07:00:00.000Z'}),
  e('m1','A','수학','FRACTION',{strength:20}),
  e('b1','B','영어','VOCABULARY',{strength:10}),
  e('self1','A','영어','VOCABULARY',{evidence_type:'CHILD_SELF_REPORT',source_app:'ready-set',instrument_version:'ready-v1',verified_performance:true})
];

const a=Core.deriveSkillState(rows,{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'});
assert.equal(a.ok,true);
assert.equal(a.observed.unique_evidence_count,3);
assert.deepEqual(a.observed.evidence_ids,['a1','a2','self1']);
assert.equal(a.observed.child_self_report_count,1);
assert.equal(a.observed.verified_performance_count,0,'self report must not become verified performance');
assert.deepEqual(a.observed.instrument_versions,['hide-v1','ready-v1']);
assert.equal(a.model.mastery_estimate,null);
assert.equal(a.model.retention_probability,null);
assert.equal(a.model.scheduling_authority,false);
assert.equal(Core.selfValidate(a).ok,true);

const math=Core.deriveSkillState(rows,{member_id:'A',subject:'수학',concept_skill_target:'FRACTION'});
assert.equal(math.observed.unique_evidence_count,1);
const childB=Core.deriveSkillState(rows,{member_id:'B',subject:'영어',concept_skill_target:'VOCABULARY'});
assert.equal(childB.observed.unique_evidence_count,1);

const replay=Core.deriveSkillState(rows,{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'});
assert.deepEqual(replay,a,'same input must be deterministic');

const invalid=Core.deriveSkillState([{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'}],{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'});
assert.equal(invalid.invalid_evidence_count,1);
assert.equal(invalid.observed.unique_evidence_count,0);

for(const forbidden of ['schedule_date','planner_date','due_at','due_date']){
  assert.equal(Object.prototype.hasOwnProperty.call(a,forbidden),false);
}
console.log('LEARNING_ENGINE_CORE_V2_PASS');
