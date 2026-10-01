'use strict';

const Verification=require('../verification/verification-layer.js');
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
  return {
    evidence_contract:VERSION,
    event_id:clean(event.event_id||event.id),
    observed_at:clean(event.occurred_at||event.at),
    member_id:clean(context.member_id||event.member_id||event.child_id||payload.member_id),
    subject:clean(context.subject||payload.subject).toLowerCase(),
    concept_skill_target:clean(context.concept_skill_target||payload.concept_skill_target).toLowerCase(),
    learning_target_id:clean(context.learning_target_id||payload.learning_target_id||payload.lexical_id||payload.word_id||payload.item_id||payload.skill_id||payload.word)||null,
    evidence_type:'SPECIALIST_OUTCOME_UNKNOWN',
    source_app:clean(event.source||event.app||context.source_app),
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
    step:finite(p.step)
  };
  out.growth_execution_context=normalizeGrowthExecutionContext(p);
  out.raw_app_signals={
    child_authored:p.child_authored===true,
    used_handoff_word:clean(p.used_handoff_word)||null,
    growth_intent_ref:clean(p.growth_intent_ref)||null
  };
  if(context.verification_receipt){const applied=Verification.applyReceipt(out,context.verification_receipt);if(applied.ok)return applied.evidence;out.verification_error=applied;}
  return out;
}

function fromReady(event={},context={}){
  const out=baseFromEvent(event,{...context,source_app:'ready-set'});
  const p=event.payload||event;
  if(clean(context.evidence_type||p.evidence_type))out.evidence_type=clean(context.evidence_type||p.evidence_type);
  if(clean(out.evidence_type)==='CHILD_SELF_REPORT')out.verified_outcome=null;
  else if(context.verification_receipt){
    const applied=Verification.applyReceipt(out,context.verification_receipt);
    if(applied.ok)return {...applied.evidence,raw_app_signals:{ready_state:clean(p.ready_state||p.task_state||p.state)||null,actual_minutes:finite(p.actual_minutes),self_report:p.self_report||null}};
    out.verification_error=applied;
  }else if(p.verification_candidate){
    const applied=Verification.issueFromCandidate(out,p.verification_candidate);
    if(applied.ok)return {...applied.evidence,raw_app_signals:{ready_state:clean(p.ready_state||p.task_state||p.state)||null,actual_minutes:finite(p.actual_minutes),self_report:p.self_report||null}};
    out.verification_error=applied;
  }
  out.raw_app_signals={
    ready_state:clean(p.ready_state||p.task_state||p.state)||null,
    actual_minutes:finite(p.actual_minutes),
    self_report:p.self_report||null
  };
  return out;
}

function normalize(event={},context={}){
  const source=clean(event.source||event.app||context.source_app);
  if(source==='hide-seek')return fromHide(event,context);
  if(source==='snap-pop')return fromSnap(event,context);
  if(source==='ready-set')return fromReady(event,context);
  const out=baseFromEvent(event,context);
  out.provenance.unsupported_source=true;
  return out;
}

function validateCanonical(e={}){
  const issues=[];
  for(const k of ['event_id','observed_at','member_id','subject','concept_skill_target','evidence_type','source_app','instrument_version']){
    if(!clean(e[k]))issues.push('MISSING_'+k.toUpperCase());
  }
  if(!Number.isFinite(Date.parse(e.observed_at||'')))issues.push('INVALID_TIME');
  if(e.verified_outcome!==null&&e.verified_outcome!==0&&e.verified_outcome!==1)issues.push('VERIFIED_OUTCOME_INVALID');
  if((e.verified_outcome===0||e.verified_outcome===1)&&!e.verification?.receipt_id)issues.push('VERIFIED_OUTCOME_WITHOUT_RECEIPT');
  if(e.evidence_type==='CHILD_SELF_REPORT'&&e.verified_outcome!==null)issues.push('SELF_REPORT_CANNOT_BE_VERIFIED_TARGET');
  if(!Array.isArray(e.language_growth_signals))issues.push('GROWTH_SIGNALS_INVALID');
  for(const signal of (e.language_growth_signals||[])){
    if(!GROWTH_DIMENSIONS.has(clean(signal.dimension).toUpperCase()))issues.push('GROWTH_DIMENSION_INVALID');
    if(!GROWTH_OUTCOMES.has(clean(signal.outcome).toUpperCase()))issues.push('GROWTH_OUTCOME_INVALID');
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

module.exports=Object.freeze({VERSION,normalize,fromHide,fromSnap,fromReady,validateCanonical});
