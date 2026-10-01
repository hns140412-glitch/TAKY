'use strict';

const VERSION='TAKY_LEARNING_EVIDENCE_IO_CONTRACT_V1';

const SOURCE_APPS=Object.freeze([
  'ready-set','hide-seek','snap-pop','imagination-cloud'
]);

const REFERENCE_ROLES=Object.freeze([
  'CURRICULUM_ALIGNMENT',
  'LEXICAL_SEMANTICS',
  'LANGUAGE_USAGE',
  'PEDAGOGICAL_USAGE',
  'GENERAL_REFERENCE'
]);

const OUTPUT_FIELDS=Object.freeze([
  'review_need',
  'learning_intensity',
  'recommended_quantity',
  'question_depth',
  'hint_policy',
  'growth_intent',
  'reference_gaps'
]);

const FORBIDDEN_ENGINE_OUTPUTS=Object.freeze([
  'schedule_date','planner_date','due_at','deadline',
  'allocated_date','allocated_quantity','calendar_time'
]);

const clean=v=>String(v??'').trim();
const arr=v=>Array.isArray(v)?v:[];

function normalizeRefs(input={}){
  const take=(...keys)=>{
    const values=[];
    for(const k of keys) values.push(...arr(input[k]));
    return [...new Set(values.map(clean).filter(Boolean))].slice(0,64);
  };
  return {
    curriculum_refs:take('curriculum_refs','achievement_standard_refs'),
    lexical_refs:take('lexical_refs','dictionary_refs'),
    usage_refs:take('usage_refs','corpus_refs'),
    pedagogical_refs:take('pedagogical_refs','learning_resource_refs'),
    general_refs:take('general_refs')
  };
}

function commonIdentity(input={}){
  return {
    scope_kind:clean(input.scope_kind||input.evidence_scope_kind).toUpperCase()||'SESSION_TASK',
    member_id:clean(input.member_id||input.child_id)||null,
    family_id:clean(input.family_id)||null,
    session_id:clean(input.session_id)||null,
    assignment_id:clean(input.assignment_id)||null,
    task_id:clean(input.task_id)||null,
    lap_id:clean(input.lap_id)||null,
    segment_id:clean(input.segment_id||input.section_id)||null,
    subject:clean(input.subject).toLowerCase()||null,
    concept_skill_target:clean(input.concept_skill_target).toLowerCase()||null,
    learning_target_id:clean(input.learning_target_id||input.lexical_id||input.item_id)||null,
    source_app:clean(input.source_app||input.source).toLowerCase()||null,
    observed_at:clean(input.observed_at||input.occurred_at||input.at)||null,
    source_event_id:clean(input.source_event_id||input.event_id||input.id)||null
  };
}

function validateInput(record={}){
  const issues=[];
  const id=record.identity||{};
  for(const k of ['member_id','subject','source_app','observed_at']){
    if(!clean(id[k]))issues.push('MISSING_'+k.toUpperCase());
  }
  if(id.scope_kind==='AGGREGATED_EXECUTION'){
    if(!clean(id.assignment_id))issues.push('MISSING_ASSIGNMENT_ID');
  }else{
    if(!clean(id.session_id))issues.push('MISSING_SESSION_ID');
    if(!clean(id.task_id)&&!clean(id.assignment_id))issues.push('MISSING_TASK_OR_ASSIGNMENT_ID');
  }
  if(id.source_app&&!SOURCE_APPS.includes(id.source_app))
    issues.push('SOURCE_APP_INVALID');
  if(id.observed_at&&!Number.isFinite(Date.parse(id.observed_at)))
    issues.push('OBSERVED_AT_INVALID');

  const refs=record.references||{};
  for(const k of ['curriculum_refs','lexical_refs','usage_refs','pedagogical_refs','general_refs']){
    if(!Array.isArray(refs[k]))issues.push('REFERENCE_ARRAY_INVALID:'+k);
  }

  if(record.authority!=='RAW_LEARNING_EVIDENCE_ONLY')
    issues.push('RAW_EVIDENCE_AUTHORITY_INVALID');
  if(record.learner_state_authority!==false)
    issues.push('RAW_EVIDENCE_LEARNER_STATE_AUTHORITY_FORBIDDEN');
  if(record.schedule_authority!==false)
    issues.push('RAW_EVIDENCE_SCHEDULE_AUTHORITY_FORBIDDEN');

  return {ok:issues.length===0,issues};
}

function validateLearningOutput(output={}){
  const issues=[];
  const forbiddenKeys=new Set(FORBIDDEN_ENGINE_OUTPUTS);
  const walkForbidden=value=>{
    if(!value||typeof value!=='object')return [];
    const found=[];
    for(const [key,nested] of Object.entries(value)){
      if(forbiddenKeys.has(key))found.push(key);
      found.push(...walkForbidden(nested));
    }
    return found;
  };
  if(output.authority!=='TAKY_LEARNING_ENGINE_CORE')
    issues.push('LEARNING_OUTPUT_AUTHORITY_INVALID');
  if(output.date_authority!==false)
    issues.push('LEARNING_ENGINE_DATE_AUTHORITY_FORBIDDEN');
  if(output.allocated_quantity_authority!==false)
    issues.push('LEARNING_ENGINE_ALLOCATED_QUANTITY_AUTHORITY_FORBIDDEN');

  for(const key of [...new Set(walkForbidden(output))])
    issues.push('LEARNING_ENGINE_OUTPUT_FORBIDDEN:'+key);
  if(output.recommended_quantity){
    if(output.recommended_quantity.authority!=='LEARNING_ENGINE_QUANTITY_INTENT_ONLY')
      issues.push('RECOMMENDED_QUANTITY_AUTHORITY_INVALID');
    if(output.recommended_quantity.planner_must_materialize!==true)
      issues.push('PLANNER_MATERIALIZATION_REQUIRED');
    if(output.recommended_quantity.allocated_quantity!==null)
      issues.push('ALLOCATED_QUANTITY_MUST_REMAIN_NULL');
  }
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({
  VERSION,SOURCE_APPS,REFERENCE_ROLES,OUTPUT_FIELDS,FORBIDDEN_ENGINE_OUTPUTS,
  normalizeRefs,commonIdentity,validateInput,validateLearningOutput
});
