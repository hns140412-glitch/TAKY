'use strict';
const assert=require('node:assert/strict');
const Core=require('./learner-state-core.js');
const Reflection=require('../evidence/self-reflection-evidence.js');

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
  e('a3','A','영어','VOCABULARY',{strength:60,assisted:false,observed_at:'2026-09-27T07:00:00.000Z'}),
  e('m1','A','수학','FRACTION',{strength:20}),
  e('b1','B','영어','VOCABULARY',{strength:10}),
  e('self1','A','영어','VOCABULARY',{evidence_type:'CHILD_SELF_REPORT',source_app:'ready-set',instrument_version:'ready-v1',verified_performance:true})
];

const a=Core.deriveSkillState(rows,{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'});
assert.equal(a.ok,true);
assert.equal(a.observed.unique_evidence_count,4);
assert.deepEqual(a.observed.evidence_ids,['a1','self1','a2','a3']);
assert.equal(a.observed.child_self_report_count,1);
assert.equal(a.observed.verified_performance_count,0,'self report must not become verified performance');
assert.deepEqual(a.observed.instrument_versions,['hide-v1','ready-v1']);
assert.deepEqual(a.observed.memory_instrument_versions,['hide-v1']);
assert.equal(a.inferred.instrument_change_detected,false);
assert.equal(a.inferred.trend,'DECLINING');
assert.equal(a.inferred.evidence_sufficiency,'EMERGING');
assert.equal(a.model.mastery_estimate,null);
assert.equal(a.model.retention_probability,null);
assert.equal(a.model.scheduling_authority,false);
assert.equal(Core.selfValidate(a).ok,true);
const leaked=JSON.parse(JSON.stringify(a)); leaked.inferred={schedule_date:'2026-09-30'};
assert.equal(Core.selfValidate(leaked).ok,false);
assert.equal(Core.selfValidate(leaked).issues.includes('SCHEDULE_AUTHORITY_LEAK'),true);

const refl1=Reflection.create({
  event_id:'ref1',observed_at:'2026-09-28T08:00:00.000Z',member_id:'A',subject:'영어',
  concept_skill_target:'VOCABULARY',source_app:'hide-seek',difficulty:'HARD',
  recall_state:'KNEW_BUT_COULD_NOT_RECALL',confidence:'MEDIUM',confusion_with:['except']
}).evidence;
const refl2=Reflection.create({
  event_id:'ref2',observed_at:'2026-09-29T08:00:00.000Z',member_id:'A',subject:'영어',
  concept_skill_target:'VOCABULARY',source_app:'hide-seek',difficulty:'OK',
  recall_state:'RECALLED_WITH_HINT',confidence:'HIGH',confusion_with:['except'],used_hint:true
}).evidence;
const withReflection=Core.deriveSkillState([...rows,refl1,refl2],{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'});
assert.equal(withReflection.observed.self_reflection_count,2);
assert.equal(withReflection.observed.performance_evidence_count,a.observed.performance_evidence_count,'reflection must not count as performance evidence');
assert.equal(withReflection.observed.verified_performance_count,a.observed.verified_performance_count,'reflection must not become verified performance');
assert.equal(withReflection.inferred.repeated_confusion_signal,'REPEATED_SELF_REPORTED_CONFUSION');
assert.equal(withReflection.inferred.metacognitive_recall_signal,'KNEW_BUT_RECALL_FAILED_REPORTED');
assert.equal(withReflection.model.mastery_estimate,null);


const readyExecutionRow={
  event_id:'ready-exec-1',observed_at:'2026-09-28T08:30:00.000Z',
  member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY',
  evidence_type:'READY_EXECUTION_FACT',
  source_app:'ready-set',instrument_version:'READY_EXECUTION_FACT_V1',
  observation_only:true,verified_outcome:null,
  raw_app_signals:{completion_state:'PARTIAL',actual_minutes:25,performed_quantity:3}
};
const imaginationRow={
  event_id:'imagination-1',observed_at:'2026-09-28T08:45:00.000Z',
  member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY',
  evidence_type:'LEARNING_SUPPORT_OBSERVATION',
  source_app:'imagination-cloud',instrument_version:'IMAGINATION_CLOUD_V1',
  observation_only:true,verified_outcome:null,
  support_observation:{
    authority:'IMAGINATION_CLOUD_SUPPORT_OBSERVATION_ONLY',
    additional_help_needed:true,curiosity_only:false,
    learner_state_authority:false,schedule_authority:false
  }
};
const withExecutionContext=Core.deriveSkillState(
  [...rows,readyExecutionRow,imaginationRow],
  {member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'}
);
assert.equal(withExecutionContext.observed.ready_execution_fact_count,1);
assert.equal(withExecutionContext.observed.imagination_support_observation_count,1);
assert.equal(withExecutionContext.observed.performance_evidence_count,
  a.observed.performance_evidence_count);
assert.equal(withExecutionContext.observed.verified_performance_count,
  a.observed.verified_performance_count);
assert.equal(withExecutionContext.inferred.retention_signal,
  a.inferred.retention_signal,
  'Ready execution and Imagination support must not alter retention interpretation');
assert.equal(withExecutionContext.inferred.recovery_signal,
  a.inferred.recovery_signal,
  'Ready execution and Imagination support must not alter recovery interpretation');
assert.equal(withExecutionContext.model.mastery_estimate,null);

const frictionRow={
  event_id:'friction1',observed_at:'2026-09-28T09:00:00.000Z',
  member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY',
  evidence_type:'READY_EXECUTION_FRICTION_OBSERVATION',
  source_app:'ready-set',instrument_version:'READY_CARRY_FRICTION_V1',
  observation_only:true,verified_outcome:null,
  execution_friction:{
    authority:'READY_EXECUTION_FRICTION_OBSERVATION_ONLY',
    carry_over_depth:4,escalation_reason:'REPEATED_CARRY_LIMIT',
    learner_state_authority:false
  }
};
const withFriction=Core.deriveSkillState([...rows,frictionRow],
  {member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'});
assert.equal(withFriction.observed.ready_execution_friction_observation_count,1);
assert.equal(withFriction.observed.performance_evidence_count,
  a.observed.performance_evidence_count,
  'Ready execution friction must not become learner performance evidence');
assert.equal(withFriction.observed.verified_performance_count,
  a.observed.verified_performance_count);
assert.equal(withFriction.model.mastery_estimate,null);

const math=Core.deriveSkillState(rows,{member_id:'A',subject:'수학',concept_skill_target:'FRACTION'});
assert.equal(math.observed.unique_evidence_count,1);
const childB=Core.deriveSkillState(rows,{member_id:'B',subject:'영어',concept_skill_target:'VOCABULARY'});
assert.equal(childB.observed.unique_evidence_count,1);

const verifiedMemoryRows=[
  {
    ...e('vr1','A','영어','VOCABULARY',{strength:40,observed_at:'2026-09-20T07:00:00.000Z'}),
    verified_outcome:0,
    verification:{authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'vr-vr1'}
  },
  {
    ...e('vr2','A','영어','VOCABULARY',{strength:65,observed_at:'2026-09-22T07:00:00.000Z'}),
    verified_outcome:1,
    verification:{authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'vr-vr2'}
  },
  {
    ...e('vr3','A','영어','VOCABULARY',{strength:80,observed_at:'2026-09-25T07:00:00.000Z'}),
    verified_outcome:1,
    verification:{authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'vr-vr3'}
  }
];
const retentionState=Core.deriveSkillState(verifiedMemoryRows,{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'},{now_ms:Date.parse('2026-10-20T07:00:00.000Z')});
assert.equal(retentionState.inferred.retention_signal,'RETENTION_AT_RISK');
assert.equal(retentionState.observed.verified_performance_count,3);
assert.equal(retentionState.observed.verified_correct_count,2);
assert.equal(retentionState.observed.verified_incorrect_count,1);
assert.equal(retentionState.observed.verified_accuracy_rate,0.667);
assert.equal(retentionState.inferred.accuracy_signal,'VERIFIED_ACCURACY_MIXED');
assert.equal(retentionState.inferred.accuracy_instrument_mixed,false);
assert.equal(retentionState.inferred.accuracy_is_descriptive_not_mastery,true);
assert.equal(retentionState.inferred.retention_candidate.promoted,false);
assert.equal(retentionState.model.retention_probability,null,'advisory retention candidate must not become promoted runtime probability');
assert.equal(retentionState.model.scheduling_authority,false);

const recoveryRows=[
  {
    ...e('rec1','A','영어','VOCABULARY',{strength:40,observed_at:'2026-09-20T07:00:00.000Z'}),
    learning_target_id:'word:a',
    verified_outcome:0,
    assisted:true,
    assistance:'ASSISTED',
    attempt_count:2,
    verification:{authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'vr-rec1'}
  },
  {
    ...e('rec2','A','영어','VOCABULARY',{strength:70,observed_at:'2026-09-21T07:00:00.000Z'}),
    learning_target_id:'word:a',
    verified_outcome:1,
    assisted:false,
    assistance:'UNASSISTED',
    attempt_count:1,
    verification:{authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'vr-rec2'}
  },
  {
    ...e('rec3','A','영어','VOCABULARY',{strength:45,observed_at:'2026-09-21T08:00:00.000Z'}),
    learning_target_id:'word:b',
    verified_outcome:0,
    assisted:true,
    assistance:'ASSISTED',
    attempt_count:2,
    verification:{authority:'LEARNING_VERIFICATION_RECEIPT',receipt_id:'vr-rec3'}
  }
];
const recoveryState=Core.deriveSkillState(recoveryRows,{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'});
assert.equal(recoveryState.inferred.recovery_signal,'UNRESOLVED_RECOVERY');
assert.equal(recoveryState.observed.verified_performance_count,3);
assert.equal(recoveryState.observed.verified_accuracy_rate,0.333);
assert.equal(recoveryState.observed.verified_unassisted_accuracy_count,1);
assert.equal(recoveryState.observed.verified_unassisted_accuracy_rate,1);
assert.equal(recoveryState.inferred.accuracy_signal,'VERIFIED_ACCURACY_LOW');
assert.equal(recoveryState.inferred.recovery_profile.recovered_episode_count,1);
assert.equal(recoveryState.inferred.recovery_profile.unresolved_episode_count,1);
assert.equal(recoveryState.model.mastery_estimate,null);
assert.equal(recoveryState.model.scheduling_authority,false);

const mixed=[...rows,e('a4','A','영어','VOCABULARY',{strength:59,instrument_version:'hide-v2',observed_at:'2026-09-28T07:00:00.000Z'})];
const held=Core.deriveSkillState(mixed,{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'});
assert.equal(held.inferred.instrument_change_detected,true);
assert.equal(held.inferred.trend,'INSTRUMENT_CHANGE_HOLD');

const replay=Core.deriveSkillState(rows,{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'});
assert.deepEqual(replay,a,'same input must be deterministic');

const invalid=Core.deriveSkillState([{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'}],{member_id:'A',subject:'영어',concept_skill_target:'VOCABULARY'});
assert.equal(invalid.invalid_evidence_count,1);
assert.equal(invalid.observed.unique_evidence_count,0);

for(const forbidden of ['schedule_date','planner_date','due_at','due_date']){
  assert.equal(Object.prototype.hasOwnProperty.call(a,forbidden),false);
}
console.log('LEARNING_ENGINE_CORE_V2_PASS');
