'use strict';

const Verification=require('../verification/verification-layer.js');
const VERSION='TAKY_CANONICAL_LEARNING_EVIDENCE_V1';
const clean=v=>String(v??'').trim();
const finite=v=>Number.isFinite(Number(v))?Number(v):null;

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
  out.raw_app_signals={
    child_authored:p.child_authored===true,
    used_handoff_word:clean(p.used_handoff_word)||null
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
  for(const k of ['schedule_date','planner_date','due_at','due_date']){
    if(Object.prototype.hasOwnProperty.call(e,k))issues.push('SCHEDULE_AUTHORITY_LEAK');
  }
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({VERSION,normalize,fromHide,fromSnap,fromReady,validateCanonical});
