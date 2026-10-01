'use strict';

const VERSION='TAKY_IMAGINATION_CLOUD_EVIDENCE_V1';
const clean=v=>String(v??'').trim();

function create(input={}){
  const issues=[];
  const identity={
    member_id:clean(input.member_id),
    session_id:clean(input.session_id),
    task_id:clean(input.task_id),
    lap_id:clean(input.lap_id)||null,
    subject:clean(input.subject).toLowerCase(),
    concept_skill_target:clean(input.concept_skill_target).toLowerCase(),
    learning_target_id:clean(input.learning_target_id)||null
  };
  for(const k of ['member_id','session_id','task_id','subject','concept_skill_target']){
    if(!identity[k])issues.push('MISSING_'+k.toUpperCase());
  }
  if(!clean(input.event_id))issues.push('MISSING_EVENT_ID');
  if(!Number.isFinite(Date.parse(input.observed_at||'')))issues.push('INVALID_OBSERVED_AT');
  if(!clean(input.invocation_reason))issues.push('MISSING_INVOCATION_REASON');
  if(!clean(input.target_concept))issues.push('MISSING_TARGET_CONCEPT');
  if(issues.length)return {ok:false,reason:'IMAGINATION_CLOUD_EVIDENCE_INVALID',issues};

  return {
    ok:true,
    event:{
      source:'imagination-cloud',
      event_id:clean(input.event_id),
      occurred_at:clean(input.observed_at),
      event_type:'LEARNING_SUPPORT_USED',
      payload:{
        ...identity,
        instrumentVersion:VERSION,
        interactionMode:'LEARNING_SUPPORT',
        invocation_reason:clean(input.invocation_reason),
        target_concept:clean(input.target_concept),
        visualization_used:clean(input.visualization_used)||null,
        explanation_used:clean(input.explanation_used)||null,
        response_before:input.response_before??null,
        response_after:input.response_after??null,
        additional_help_needed:input.additional_help_needed===true
          ?true:input.additional_help_needed===false?false:null,
        curiosity_only:input.curiosity_only===true,
        curriculum_refs:Array.isArray(input.curriculum_refs)?input.curriculum_refs.slice(0,32):[],
        lexical_refs:Array.isArray(input.lexical_refs)?input.lexical_refs.slice(0,32):[],
        usage_refs:Array.isArray(input.usage_refs)?input.usage_refs.slice(0,32):[],
        pedagogical_refs:Array.isArray(input.pedagogical_refs)?input.pedagogical_refs.slice(0,32):[],
        observation_only:true,
        learner_state_authority:false,
        schedule_authority:false,
        mastery_claim:false
      }
    },
    authority:'IMAGINATION_CLOUD_SUPPORT_OBSERVATION_ONLY'
  };
}

module.exports=Object.freeze({VERSION,create});
