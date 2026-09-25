'use strict';

const clean=v=>String(v??'').trim();
const finite=v=>Number.isFinite(Number(v))?Number(v):null;

function normalizeAdapterEvidence(input={}){
  const source=clean(input.source_app||input.sourceApp);
  const eventId=clean(input.event_id||input.eventId);
  const observedAt=input.observed_at||input.at||input.observedAt||null;
  const subject=clean(input.subject);
  const target=clean(input.concept_skill_target||input.conceptSkillTarget);
  const memberId=clean(input.member_id||input.memberId);
  const instrumentVersion=clean(input.instrument_version||input.instrumentVersion||input.sourceVersion)||'UNSPECIFIED';
  const evidenceType=clean(input.evidence_type||input.evidenceType||'SPECIALIST_OUTCOME_UNKNOWN');
  const assistedRaw=input.assisted;
  const assistance=assistedRaw===true?'ASSISTED':assistedRaw===false?'UNASSISTED':clean(input.assistance)||'UNKNOWN';

  const normalized={
    event_id:eventId||null,
    observed_at:observedAt||null,
    member_id:memberId||null,
    subject:subject||null,
    concept_skill_target:target||null,
    evidence_type:evidenceType,
    source_app:source||null,
    instrument_version:instrumentVersion,
    interaction_mode:clean(input.interaction_mode||input.interactionMode)||'UNKNOWN',
    assistance,
    assisted:assistedRaw===true?true:assistedRaw===false?false:null,
    attempt_count:Number.isFinite(input.attempt_count)?Math.max(0,Math.floor(input.attempt_count))
      :Number.isFinite(input.attemptCount)?Math.max(0,Math.floor(input.attemptCount)):null,
    response_latency_ms:Number.isFinite(input.response_latency_ms)?Math.max(0,input.response_latency_ms)
      :Number.isFinite(input.responseLatencyMs)?Math.max(0,input.responseLatencyMs):null,
    verified_performance:input.verified_performance===true&&evidenceType!=='CHILD_SELF_REPORT',
    verified_outcome:(input.verified_outcome===0||input.verified_outcome===1)?input.verified_outcome:null,
    memory:input.memory&&typeof input.memory==='object'?{
      average_strength:finite(input.memory.average_strength),
      review_advisories:Array.isArray(input.memory.review_advisories)?input.memory.review_advisories.slice(0,64):[]
    }:undefined,
    production:input.production&&typeof input.production==='object'?{...input.production}:undefined,
    provenance:{
      authority:clean(input.authority)||null,
      interpretation_owner:clean(input.interpretation_owner)||'LEARNING_ENGINE_CORE',
      adapter_contract:clean(input.evidence_contract||input.adapter_contract)||null
    }
  };

  if(normalized.evidence_type==='CHILD_SELF_REPORT'){
    normalized.verified_performance=false;
    normalized.verified_outcome=null;
  }
  return normalized;
}

function validateNormalized(e={}){
  const issues=[];
  for(const k of ['event_id','observed_at','member_id','subject','concept_skill_target','evidence_type','source_app','instrument_version']){
    if(!clean(e[k]))issues.push('MISSING_'+k.toUpperCase());
  }
  if(!Number.isFinite(Date.parse(e.observed_at||'')))issues.push('INVALID_OBSERVED_AT');
  if(e.evidence_type==='CHILD_SELF_REPORT'&&(e.verified_performance===true||e.verified_outcome===0||e.verified_outcome===1)){
    issues.push('SELF_REPORT_PROMOTED_TO_VERIFIED_PERFORMANCE');
  }
  for(const k of ['schedule_date','planner_date','due_at','due_date']){
    if(Object.prototype.hasOwnProperty.call(e,k))issues.push('SCHEDULE_AUTHORITY_LEAK');
  }
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({normalizeAdapterEvidence,validateNormalized});
