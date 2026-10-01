'use strict';

const Verification=require('../verification/verification-layer.js');
const IO=require('../contracts/learning-evidence-io-contract.js');
const VERSION='TAKY_CANONICAL_LEARNING_EVIDENCE_V1';
const clean=v=>String(v??'').trim();
const finite=v=>Number.isFinite(Number(v))?Number(v):null;
const GROWTH_DIMENSIONS=new Set(['VOCABULARY','GRAMMAR','EXPRESSION','THINKING','ENGLISH_THINKING']);
const GROWTH_OUTCOMES=new Set(['SUCCESS','PARTIAL','FAIL','UNKNOWN']);

function normalizeGrowthSignals(payload={}){
  const rows=Array.isArray(payload.growth_signals)?payload.growth_signals:
    Array.isArray(payload.language_growth_signals)?payload.language_growth_signals:[];
  return rows.slice(0,32).map(raw=>{
    const x=raw&&typeof raw==='object'?raw:{};
    const dimension=clean(x.dimension).toUpperCase();
    const outcome=clean(x.outcome).toUpperCase()||'UNKNOWN';
    if(!GROWTH_DIMENSIONS.has(dimension)||!GROWTH_OUTCOMES.has(outcome))return null;
    const depth=finite(x.depth);
    return {
      dimension,
      outcome,
      assisted:x.assisted===true,
      transfer:x.transfer===true,
      direct_english:x.direct_english===true?true:x.direct_english===false?false:null,
      kind:clean(x.kind).toUpperCase()||null,
      target_id:clean(x.target_id||x.learning_target_id)||null,
      depth:Number.isFinite(depth)?Math.max(0,Math.min(5,depth)):null,
      evidence_ref:clean(x.evidence_ref)||null
    };
  }).filter(Boolean);
}

function normalizeGrowthExecutionContext(payload={}){
  const x=payload.growth_control_applied;
  if(!x||typeof x!=='object')return null;
  const depth=finite(x.question_depth);
  return {
    authority:'SPECIALIST_EXECUTION_CONTEXT_ONLY',
    growth_intent_ref:clean(payload.growth_intent_ref)||null,
    evidence_confidence:clean(x.evidence_confidence).toUpperCase()||null,
    learning_intensity:clean(x.learning_intensity).toUpperCase()||null,
    expression_level:clean(x.expression_level).toUpperCase()||null,
    question_depth:Number.isFinite(depth)?Math.max(1,Math.min(5,depth)):null,
    hint_strength:clean(x.hint_strength).toUpperCase()||null,
    hint_fade:clean(x.hint_fade).toUpperCase()||null,
    challenge_direction:clean(x.challenge_direction).toUpperCase()||null,
    engine_authority:false,
    learner_state_authority:false
  };
}

function baseFromEvent(event={},context={}){
  const payload=event.payload||{};
  const identity=IO.commonIdentity({
    member_id:context.member_id||event.member_id||event.child_id||payload.member_id,
    family_id:context.family_id||payload.family_id,
    session_id:context.session_id||payload.session_id||payload.taskContext?.session_id,
    assignment_id:context.assignment_id||payload.assignment_id,
    task_id:context.task_id||payload.task_id||payload.taskContext?.task_id,
    lap_id:context.lap_id||payload.lap_id||payload.taskContext?.lap_id,
    segment_id:context.segment_id||payload.segment_id||payload.section_id,
    subject:context.subject||payload.subject,
    concept_skill_target:context.concept_skill_target||payload.concept_skill_target,
    learning_target_id:context.learning_target_id||payload.learning_target_id||payload.lexical_id||payload.word_id||payload.item_id||payload.skill_id||payload.word,
    source_app:context.source_app||event.source||event.app,
    observed_at:event.occurred_at||event.at,
    source_event_id:event.event_id||event.id
  });
  const references=IO.normalizeRefs({
    curriculum_refs:context.curriculum_refs||payload.curriculum_refs,
    achievement_standard_refs:context.achievement_standard_refs||payload.achievement_standard_refs,
    lexical_refs:context.lexical_refs||payload.lexical_refs,
    dictionary_refs:context.dictionary_refs||payload.dictionary_refs,
    usage_refs:context.usage_refs||payload.usage_refs,
    corpus_refs:context.corpus_refs||payload.corpus_refs,
    pedagogical_refs:context.pedagogical_refs||payload.pedagogical_refs,
    learning_resource_refs:context.learning_resource_refs||payload.learning_resource_refs,
    general_refs:context.general_refs||payload.general_refs
  });
  return {
    evidence_contract:VERSION,
    io_contract:IO.VERSION,
    authority:'RAW_LEARNING_EVIDENCE_ONLY',
    learner_state_authority:false,
    schedule_authority:false,
    identity,
    references,
    event_id:identity.source_event_id,
    observed_at:identity.observed_at,
    member_id:identity.member_id,
    family_id:identity.family_id,
    session_id:identity.session_id,
    assignment_id:identity.assignment_id,
    task_id:identity.task_id,
    lap_id:identity.lap_id,
    segment_id:identity.segment_id,
    subject:identity.subject,
    concept_skill_target:identity.concept_skill_target,
    learning_target_id:identity.learning_target_id,
    evidence_type:'SPECIALIST_OUTCOME_UNKNOWN',
    source_app:identity.source_app,
    instrument_version:clean(payload.instrumentVersion||payload.instrument_version||context.instrument_version)||'UNSPECIFIED',
    interaction_mode:clean(payload.interactionMode||payload.interaction_mode||payload.mode).toUpperCase()||'UNKNOWN',
    assistance:payload.assisted===true?'ASSISTED':payload.assisted===false?'UNASSISTED':'UNKNOWN',
    assisted:payload.assisted===true?true:payload.assisted===false?false:null,
    attempt_count:Number.isInteger(payload.attemptCount)?payload.attemptCount:null,
    response_latency_ms:finite(payload.responseLatencyMs),
    verified_outcome:null,
    raw_app_signals:{},
    language_growth_signals:normalizeGrowthSignals(payload),
    provenance:{
      authority:'CANONICAL_EVIDENCE_ADAPTER_ONLY',
      source_event_type:clean(event.event_type||event.type),
      source_contract_version:clean(context.source_contract_version)||null,
      normalized_by:VERSION
    }
  };
}

function fromHide(event={},context={}){
  const out=baseFromEvent(event,{...context,source_app:'hide-seek'});
  const p=event.payload||{};
  const memory=p.memorySummary||p.trailSummary?.memorySummary||null;
  const itemSignal=(clean(event.event_type||event.type)==='LEARNING_MEMORY_SIGNAL'||p.word||p.item_id||p.skill_id)?{
    item_id:clean(p.item_id||p.skill_id||p.word_id||p.lexical_id||p.word)||null,
    word:clean(p.word)||null,
    correct:typeof p.correct==='boolean'?p.correct:null,
    confusion:p.confusion??null,
    weakness:p.weakness??null,
    spaced_evidence:p.spacedEvidence??p.spaced_evidence??null,
    next_review_priority:finite(p.nextReviewPriority??p.next_review_priority),
    hint_stage:finite(p.hint_stage??p.hintStage),
    helped:p.helped===true?true:p.helped===false?false:null,
    self_corrected:p.self_corrected===true?true:p.self_corrected===false?false:null,
    recall_degree:finite(p.recall_degree??p.recallDegree??p.recall_strength),
    connection_evidence:p.connection_evidence??p.connectionEvidence??null,
    spelling_evidence:p.spelling_evidence??p.spellingEvidence??null,
    response_latency_ms:finite(p.response_latency_ms??p.responseLatencyMs),
    mode:clean(p.mode||p.interactionMode||p.interaction_mode).toUpperCase()||null,
    word_origin:clean(p.word_origin||p.wordOrigin).toUpperCase()||null,
    source_sheet_id:clean(p.sourceSheetId||p.source_sheet_id)||null
  }:null;
  out.evidence_type=(memory||itemSignal||p.verification_candidate)?'MEMORY_RETRIEVAL_EVIDENCE':'SPECIALIST_OUTCOME_UNKNOWN';
  out.memory=(memory||itemSignal)?{
    average_strength:memory?finite(memory.averageMemoryStrength):finite(p.strength),
    review_advisories:memory&&Array.isArray(memory.reviewAdvisories)
      ?memory.reviewAdvisories.slice(0,24)
      :(Number.isFinite(itemSignal?.next_review_priority)
        ?[{learning_target_id:out.learning_target_id,nextReviewPriority:itemSignal.next_review_priority}]
        :[]),
    next_review_semantics:memory?clean(memory.prioritySemantics)||'ADVISORY_SIGNAL_NOT_DATE':'ADVISORY_SIGNAL_NOT_DATE',
    item_signal:itemSignal
  }:null;
  out.raw_app_signals={
    case_mastery:finite(p.caseMastery),
    valid_word_count:finite(p.validWordCount),
    sheet_status:clean(p.sheetStatus)||null
  };
  if(context.verification_receipt){
    const applied=Verification.applyReceipt(out,context.verification_receipt);
    if(applied.ok)return applied.evidence;
    out.verification_error=applied;
  }else if(p.verification_candidate){
    const applied=Verification.issueFromCandidate(out,p.verification_candidate);
    if(applied.ok)return applied.evidence;
    out.verification_error=applied;
  }
  return out;
}

function fromSnap(event={},context={}){
  const out=baseFromEvent(event,{...context,source_app:'snap-pop'});
  const p=event.payload||{};
  out.evidence_type='LEARNER_PRODUCTION_EVIDENCE';
  out.production={
    child_authored:p.child_authored===true,
    landmark:clean(p.landmark||p.active_landmark)||null,
    step:finite(p.step),
    vocabulary_used:Array.isArray(p.vocabulary_used)?p.vocabulary_used.slice(0,32):[],
    grammar_stability:p.grammar_stability??null,
    expression_expansion:p.expression_expansion??null,
    reasoning_evidence:p.reasoning_evidence??null,
    perspective_shift:p.perspective_shift??null,
    story_structure:p.story_structure??null,
    direct_english:p.direct_english??null,
    expression_reuse:p.expression_reuse??null,
    self_correction:p.self_correction??null,
    assistance_strength:p.assistance_strength??null
  };
  out.growth_execution_context=normalizeGrowthExecutionContext(p);
  out.raw_app_signals={
    child_authored:p.child_authored===true,
    used_handoff_word:clean(p.used_handoff_word)||null,
    growth_intent_ref:clean(p.growth_intent_ref)||null,
    growth_verification_status:clean(p.growth_verification_status).toUpperCase()||null,
    growth_review_required:p.growth_review_required===true,
    requested_growth_dimensions:Array.isArray(p.requested_growth_dimensions)
      ?p.requested_growth_dimensions.map(x=>clean(x).toUpperCase()).filter(Boolean).slice(0,5):[]
  };
  if(context.verification_receipt){const applied=Verification.applyReceipt(out,context.verification_receipt);if(applied.ok)return applied.evidence;out.verification_error=applied;}
  return out;
}

function readyRawSignals(p={}){
  return {
    ready_state:clean(p.ready_state||p.task_state||p.state)||null,
    planner_allocation:p.planner_allocation&&typeof p.planner_allocation==='object'
      ?JSON.parse(JSON.stringify(p.planner_allocation)):null,
    started_at:clean(p.started_at||p.actual_started_at)||null,
    ended_at:clean(p.ended_at||p.actual_ended_at)||null,
    actual_minutes:finite(p.actual_minutes),
    performed_quantity:finite(p.performed_quantity??p.actual_quantity),
    completion_state:clean(p.completion_state||p.task_state||p.state).toUpperCase()||null,
    blocked_reason:clean(p.blocked_reason)||null,
    parent_confirmation:p.parent_confirmation??p.parent_confirmed??null,
    self_report:p.self_report||null,
    forwarded_hide_observation:p.forwarded_source_app==='hide-seek',
    forwarded_ready_friction_observation:p.forwarded_ready_friction_observation===true
  };
}

function fromReady(event={},context={}){
  const out=baseFromEvent(event,{...context,source_app:'ready-set'});
  const p=event.payload||event;
  if(clean(context.evidence_type||p.evidence_type))out.evidence_type=clean(context.evidence_type||p.evidence_type);
  out.observation_only=p.observation_only===true;
  if(clean(out.evidence_type)==='CHILD_SELF_REPORT'||
     clean(out.evidence_type)==='READY_EXECUTION_FRICTION_OBSERVATION')
    out.verified_outcome=null;
  if(clean(out.evidence_type)==='READY_EXECUTION_FRICTION_OBSERVATION'){
    out.execution_friction={
      authority:'READY_EXECUTION_FRICTION_OBSERVATION_ONLY',
      assignment_id:clean(p.assignment_id)||null,
      source_carry_over_id:clean(p.source_carry_over_id)||null,
      carry_over_depth:finite(p.carry_over_depth),
      carry_over_state:clean(p.carry_over_state)||null,
      escalation_reason:clean(p.escalation_reason)||null,
      observation_count:finite(p.observation_count),
      friction_states:Array.isArray(p.friction_states)
        ?p.friction_states.map(clean).filter(Boolean).slice(-12):[],
      actual_minutes:Array.isArray(p.actual_minutes)
        ?p.actual_minutes.map(finite).filter(Number.isFinite).slice(-12):[],
      verified_performance:false,
      learner_state_authority:false
    };
  }
  if(context.verification_receipt){
    const applied=Verification.applyReceipt(out,context.verification_receipt);
    if(applied.ok)return {...applied.evidence,raw_app_signals:readyRawSignals(p)};
    out.verification_error=applied;
  }else if(p.verification_candidate){
    const applied=Verification.issueFromCandidate(out,p.verification_candidate);
    if(applied.ok)return {...applied.evidence,raw_app_signals:readyRawSignals(p)};
    out.verification_error=applied;
  }
  out.raw_app_signals=readyRawSignals(p);
  return out;
}

function fromImaginationCloud(event={},context={}){
  const out=baseFromEvent(event,{...context,source_app:'imagination-cloud'});
  const p=event.payload||{};
  out.evidence_type='LEARNING_SUPPORT_OBSERVATION';
  out.observation_only=true;
  out.verified_outcome=null;
  out.support_observation={
    authority:'IMAGINATION_CLOUD_SUPPORT_OBSERVATION_ONLY',
    invocation_reason:clean(p.invocation_reason||p.reason)||null,
    target_concept:clean(p.target_concept||p.concept)||null,
    visualization_used:clean(p.visualization_used||p.visualization_type)||null,
    explanation_used:clean(p.explanation_used||p.explanation_type)||null,
    response_before:p.response_before??null,
    response_after:p.response_after??null,
    additional_help_needed:p.additional_help_needed===true?true:p.additional_help_needed===false?false:null,
    curiosity_only:p.curiosity_only===true,
    learner_state_authority:false,
    schedule_authority:false
  };
  out.raw_app_signals={
    invocation_reason:out.support_observation.invocation_reason,
    target_concept:out.support_observation.target_concept,
    additional_help_needed:out.support_observation.additional_help_needed,
    curiosity_only:out.support_observation.curiosity_only
  };
  return out;
}

function normalize(event={},context={}){
  const source=clean(event.source||event.app||context.source_app);
  if(source==='hide-seek')return fromHide(event,context);
  if(source==='snap-pop')return fromSnap(event,context);
  if(source==='ready-set')return fromReady(event,context);
  if(source==='imagination-cloud'||source==='sangsang-cloud')return fromImaginationCloud(event,context);
  const out=baseFromEvent(event,context);
  out.provenance.unsupported_source=true;
  return out;
}

function validateCanonical(e={}){
  const issues=[];
  const ioCheck=IO.validateInput({
    authority:e.authority,
    learner_state_authority:e.learner_state_authority,
    schedule_authority:e.schedule_authority,
    identity:e.identity,
    references:e.references
  });
  if(!ioCheck.ok)issues.push(...ioCheck.issues.map(x=>'IO_'+x));
  for(const k of ['event_id','observed_at','member_id','subject','concept_skill_target','evidence_type','source_app','instrument_version']){
    if(!clean(e[k]))issues.push('MISSING_'+k.toUpperCase());
  }
  if(!Number.isFinite(Date.parse(e.observed_at||'')))issues.push('INVALID_TIME');
  if(e.verified_outcome!==null&&e.verified_outcome!==0&&e.verified_outcome!==1)issues.push('VERIFIED_OUTCOME_INVALID');
  if((e.verified_outcome===0||e.verified_outcome===1)&&!e.verification?.receipt_id)issues.push('VERIFIED_OUTCOME_WITHOUT_RECEIPT');
  if(e.evidence_type==='CHILD_SELF_REPORT'&&e.verified_outcome!==null)issues.push('SELF_REPORT_CANNOT_BE_VERIFIED_TARGET');
  if(e.source_app==='imagination-cloud'){
    if(e.verified_outcome!==null)issues.push('IMAGINATION_SUPPORT_CANNOT_BE_VERIFIED_TARGET');
    if(e.observation_only!==true)issues.push('IMAGINATION_SUPPORT_MUST_BE_OBSERVATION_ONLY');
    if(e.support_observation?.learner_state_authority!==false)
      issues.push('IMAGINATION_LEARNER_STATE_AUTHORITY_FORBIDDEN');
    if(e.support_observation?.schedule_authority!==false)
      issues.push('IMAGINATION_SCHEDULE_AUTHORITY_FORBIDDEN');
  }
  if(e.evidence_type==='READY_EXECUTION_FRICTION_OBSERVATION'){
    if(e.verified_outcome!==null)issues.push('FRICTION_OBSERVATION_CANNOT_BE_VERIFIED_TARGET');
    if(e.observation_only!==true)issues.push('FRICTION_OBSERVATION_MUST_BE_OBSERVATION_ONLY');
    if(e.execution_friction?.learner_state_authority!==false)
      issues.push('FRICTION_OBSERVATION_LEARNER_STATE_AUTHORITY_FORBIDDEN');
  }
  if(!Array.isArray(e.language_growth_signals))issues.push('GROWTH_SIGNALS_INVALID');
  for(const signal of (e.language_growth_signals||[])){
    if(!GROWTH_DIMENSIONS.has(clean(signal.dimension).toUpperCase()))issues.push('GROWTH_DIMENSION_INVALID');
    if(!GROWTH_OUTCOMES.has(clean(signal.outcome).toUpperCase()))issues.push('GROWTH_OUTCOME_INVALID');
  }
  if(e.source_app==='snap-pop'&&e.raw_app_signals?.growth_verification_status){
    const allowed=new Set(['PENDING_DIMENSION_REVIEW','UNVERIFIED_OBSERVATION','VERIFIED_DIMENSION_REVIEW']);
    if(!allowed.has(e.raw_app_signals.growth_verification_status))
      issues.push('GROWTH_VERIFICATION_STATUS_INVALID');
    if(e.raw_app_signals.growth_verification_status==='PENDING_DIMENSION_REVIEW'&&
       e.raw_app_signals.growth_review_required!==true)
      issues.push('PENDING_GROWTH_REVIEW_FLAG_REQUIRED');
  }
  if(e.growth_execution_context){
    if(e.growth_execution_context.authority!=='SPECIALIST_EXECUTION_CONTEXT_ONLY')
      issues.push('GROWTH_EXECUTION_CONTEXT_AUTHORITY_INVALID');
    if(e.growth_execution_context.engine_authority!==false)
      issues.push('GROWTH_EXECUTION_CONTEXT_ENGINE_AUTHORITY_FORBIDDEN');
    if(e.growth_execution_context.learner_state_authority!==false)
      issues.push('GROWTH_EXECUTION_CONTEXT_LEARNER_STATE_AUTHORITY_FORBIDDEN');
  }
  for(const k of ['schedule_date','planner_date','due_at','due_date']){
    if(Object.prototype.hasOwnProperty.call(e,k))issues.push('SCHEDULE_AUTHORITY_LEAK');
  }
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,normalize,fromHide,fromSnap,fromReady,fromImaginationCloud,validateCanonical});
